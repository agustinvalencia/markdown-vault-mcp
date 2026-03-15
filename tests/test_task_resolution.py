"""Tests for task ID resolution in complete_task and cancel_task."""

from unittest.mock import patch

from mdvault_mcp_server.tools.tasks_projects import _resolve_task_path


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
