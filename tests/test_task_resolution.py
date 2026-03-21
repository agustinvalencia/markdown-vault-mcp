"""Tests for task ID resolution in complete_task and cancel_task."""

from unittest.mock import call, patch

from fastmcp import FastMCP

from mdvault_mcp_server.tools.tasks_projects import _resolve_task_path, register_tasks_projects_tools


def _get_tool(name: str):
    """Register tools and return a specific tool function."""
    mcp = FastMCP("test")
    register_tasks_projects_tools(mcp)
    return mcp._tool_manager._tools[name].fn


class TestResolveTaskPath:
    def test_path_passthrough(self):
        """Paths with / or .md are returned as-is."""
        assert _resolve_task_path("Projects/foo/Tasks/BAR-001.md") == "Projects/foo/Tasks/BAR-001.md"
        assert _resolve_task_path("tasks/my-task.md") == "tasks/my-task.md"

    def test_task_id_resolved(self):
        """Task IDs are resolved via mdv task status."""
        status_output = (
            "Task: Do something [MDV-001]\n"
            "\n"
            "  Status:       todo\n"
            "  Project:      markdownvault-development\n"
            "  Created:      -\n"
            "  Path:         Projects/markdownvault-development/Tasks/MDV-001-do-something.md"
        )
        with patch(
            "mdvault_mcp_server.tools.tasks_projects.run_mdv_command",
            return_value=status_output,
        ) as mock_run:
            result = _resolve_task_path("MDV-001")

        assert result == "Projects/markdownvault-development/Tasks/MDV-001-do-something.md"
        mock_run.assert_called_once_with(["task", "status", "MDV-001"])

    def test_task_id_not_found_fallback(self):
        """If task status doesn't return a path, the original ID is returned."""
        with patch(
            "mdvault_mcp_server.tools.tasks_projects.run_mdv_command",
            return_value="Error: task not found",
        ):
            result = _resolve_task_path("FAKE-999")

        assert result == "FAKE-999"

    def test_md_suffix_is_path(self):
        """Strings ending in .md are treated as paths."""
        assert _resolve_task_path("note.md") == "note.md"

    def test_plain_id_calls_mdv(self):
        """Plain IDs (no slash, no .md) trigger resolution."""
        with patch(
            "mdvault_mcp_server.tools.tasks_projects.run_mdv_command",
            return_value="  Path:         tasks/X-001.md",
        ):
            result = _resolve_task_path("X-001")
        assert result == "tasks/X-001.md"


class TestCompleteTaskWithId:
    def test_complete_task_resolves_id(self):
        """complete_task should resolve task IDs before calling mdv task done."""
        tool = _get_tool("complete_task")
        status_output = (
            "Task: Fix bug [BUG-001]\n"
            "  Path:         Projects/dev/Tasks/BUG-001-fix-bug.md"
        )
        with patch(
            "mdvault_mcp_server.tools.tasks_projects.run_mdv_command",
        ) as mock_run:
            mock_run.side_effect = [
                status_output,  # First call: task status for resolution
                "OK   mdv task done",  # Second call: task done
            ]
            result = tool(task_id="BUG-001", summary="Fixed it")

        assert mock_run.call_count == 2
        mock_run.assert_any_call(["task", "status", "BUG-001"])
        mock_run.assert_any_call(
            ["task", "done", "Projects/dev/Tasks/BUG-001-fix-bug.md", "-s", "Fixed it"]
        )

    def test_complete_task_with_path_skips_resolution(self):
        """complete_task with a file path should not call task status."""
        tool = _get_tool("complete_task")
        with patch(
            "mdvault_mcp_server.tools.tasks_projects.run_mdv_command",
            return_value="OK   mdv task done",
        ) as mock_run:
            tool(task_id="Projects/dev/Tasks/BUG-001.md")

        # Only one call — no resolution needed
        mock_run.assert_called_once_with(
            ["task", "done", "Projects/dev/Tasks/BUG-001.md"]
        )


class TestCancelTaskWithId:
    def test_cancel_task_resolves_id(self):
        """cancel_task should resolve task IDs before calling mdv task cancel."""
        tool = _get_tool("cancel_task")
        status_output = "  Path:         tasks/X-001.md"
        with patch(
            "mdvault_mcp_server.tools.tasks_projects.run_mdv_command",
        ) as mock_run:
            mock_run.side_effect = [status_output, "OK   mdv task cancel"]
            tool(task_id="X-001", reason="No longer needed")

        mock_run.assert_any_call(["task", "status", "X-001"])
        mock_run.assert_any_call(
            ["task", "cancel", "tasks/X-001.md", "-r", "No longer needed"]
        )

    def test_cancel_task_with_path_skips_resolution(self):
        """cancel_task with a file path should not call task status."""
        tool = _get_tool("cancel_task")
        with patch(
            "mdvault_mcp_server.tools.tasks_projects.run_mdv_command",
            return_value="OK",
        ) as mock_run:
            tool(task_id="tasks/X-001.md")

        mock_run.assert_called_once_with(["task", "cancel", "tasks/X-001.md"])
