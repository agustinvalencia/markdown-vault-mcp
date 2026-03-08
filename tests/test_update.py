"""Tests for update tools: update_metadata, append_to_note, update_task_status."""

import json
from unittest.mock import patch

import pytest


@pytest.fixture
def vault_tmp(tmp_path):
    """Set up a temporary vault directory."""
    return tmp_path


@pytest.fixture
def note_with_tasks(vault_tmp):
    """Create a note with task checkboxes."""
    note = vault_tmp / "tasks.md"
    note.write_text(
        "---\ntitle: Tasks\ntype: daily\n---\n\n"
        "# Tasks\n\n"
        "- [ ] Buy groceries\n"
        "- [x] Write tests\n"
        "- [ ] Review PR for backend\n",
        encoding="utf-8",
    )
    return note


@pytest.fixture
def note_with_sections(vault_tmp):
    """Create a note with multiple sections."""
    note = vault_tmp / "sections.md"
    note.write_text(
        "---\ntitle: Sections\n---\n\n"
        "# Main Title\n\n"
        "## Logs\n\n"
        "- existing log entry\n\n"
        "## Notes\n\n"
        "Some notes here.\n",
        encoding="utf-8",
    )
    return note


@pytest.fixture
def simple_note(vault_tmp):
    """Create a simple note for metadata tests."""
    note = vault_tmp / "simple.md"
    note.write_text(
        "---\ntitle: Simple\nstatus: draft\n---\n\nContent here.\n",
        encoding="utf-8",
    )
    return note


@pytest.fixture
def _patch_vault(vault_tmp):
    """Patch VAULT_PATH for update and config modules."""
    with (
        patch("mdvault_mcp_server.tools.update.VAULT_PATH", vault_tmp),
        patch("mdvault_mcp_server.config.VAULT_PATH", vault_tmp),
    ):
        yield


def _get_tool(name):
    """Register update tools and return a specific tool function."""
    from mdvault_mcp_server.tools.update import register_update_tools
    from fastmcp import FastMCP

    mcp = FastMCP("test")
    register_update_tools(mcp)
    return mcp._tool_manager._tools[name].fn


class TestUpdateMetadata:
    """Tests for update_metadata tool."""

    @pytest.mark.usefixtures("_patch_vault")
    def test_updates_existing_field(self, vault_tmp, simple_note):
        """Should update an existing frontmatter field."""
        update_metadata = _get_tool("update_metadata")
        result = update_metadata("simple.md", json.dumps({"status": "published"}))

        assert "Updated metadata" in result

        content = simple_note.read_text(encoding="utf-8")
        assert "status: published" in content

    @pytest.mark.usefixtures("_patch_vault")
    def test_adds_new_field(self, vault_tmp, simple_note):
        """Should add a new frontmatter field."""
        update_metadata = _get_tool("update_metadata")
        result = update_metadata("simple.md", json.dumps({"priority": "high"}))

        assert "Updated metadata" in result

        content = simple_note.read_text(encoding="utf-8")
        assert "priority: high" in content
        # Original fields preserved
        assert "title: Simple" in content

    @pytest.mark.usefixtures("_patch_vault")
    def test_sets_updated_at_timestamp(self, vault_tmp, simple_note):
        """Should automatically set updated_at timestamp."""
        update_metadata = _get_tool("update_metadata")
        update_metadata("simple.md", json.dumps({"status": "done"}))

        content = simple_note.read_text(encoding="utf-8")
        assert "updated_at:" in content

    @pytest.mark.usefixtures("_patch_vault")
    def test_invalid_json(self, vault_tmp, simple_note):
        """Should return error for invalid JSON input."""
        update_metadata = _get_tool("update_metadata")
        result = update_metadata("simple.md", "not valid json {{{")

        assert "Invalid JSON" in result

    @pytest.mark.usefixtures("_patch_vault")
    def test_non_object_json(self, vault_tmp, simple_note):
        """Should reject non-object JSON (e.g., array)."""
        update_metadata = _get_tool("update_metadata")
        result = update_metadata("simple.md", json.dumps(["a", "b"]))

        assert "must be a JSON object" in result

    @pytest.mark.usefixtures("_patch_vault")
    def test_missing_file(self, vault_tmp):
        """Should return error for non-existent file."""
        update_metadata = _get_tool("update_metadata")
        result = update_metadata("nonexistent.md", json.dumps({"k": "v"}))

        assert "does not exist" in result.lower() or "not found" in result.lower()


class TestAppendToNote:
    """Tests for append_to_note tool."""

    @pytest.mark.usefixtures("_patch_vault")
    def test_append_to_end(self, vault_tmp, note_with_sections):
        """Should append content at end when no subsection specified."""
        append_to_note = _get_tool("append_to_note")
        result = append_to_note("sections.md", "New content at end")

        assert "Appended content to sections.md" in result

        content = note_with_sections.read_text(encoding="utf-8")
        assert "New content at end" in content

    @pytest.mark.usefixtures("_patch_vault")
    def test_append_to_subsection(self, vault_tmp, note_with_sections):
        """Should append content under an existing subsection."""
        append_to_note = _get_tool("append_to_note")
        result = append_to_note("sections.md", "- new log", subsection="Logs")

        assert "Logs" in result

        content = note_with_sections.read_text(encoding="utf-8")
        assert "- new log" in content

    @pytest.mark.usefixtures("_patch_vault")
    def test_append_creates_missing_subsection(self, vault_tmp, note_with_sections):
        """Should create subsection if it doesn't exist."""
        append_to_note = _get_tool("append_to_note")
        result = append_to_note("sections.md", "action item", subsection="Actions")

        assert "Created subsection" in result

        content = note_with_sections.read_text(encoding="utf-8")
        assert "## Actions" in content
        assert "action item" in content

    @pytest.mark.usefixtures("_patch_vault")
    def test_append_missing_file(self, vault_tmp):
        """Should return error for non-existent file."""
        append_to_note = _get_tool("append_to_note")
        result = append_to_note("missing.md", "content")

        assert "does not exist" in result.lower() or "not found" in result.lower()


class TestUpdateTaskStatus:
    """Tests for update_task_status tool."""

    @pytest.mark.usefixtures("_patch_vault")
    def test_mark_task_complete(self, vault_tmp, note_with_tasks):
        """Should mark an incomplete task as complete."""
        update_task_status = _get_tool("update_task_status")
        result = update_task_status("tasks.md", "Buy groceries", completed=True)

        assert "completed" in result.lower()

        content = note_with_tasks.read_text(encoding="utf-8")
        assert "- [x] Buy groceries" in content

    @pytest.mark.usefixtures("_patch_vault")
    def test_mark_task_incomplete(self, vault_tmp, note_with_tasks):
        """Should mark a completed task as incomplete."""
        update_task_status = _get_tool("update_task_status")
        result = update_task_status("tasks.md", "Write tests", completed=False)

        assert "incomplete" in result.lower()

        content = note_with_tasks.read_text(encoding="utf-8")
        assert "- [ ] Write tests" in content

    @pytest.mark.usefixtures("_patch_vault")
    def test_task_not_found(self, vault_tmp, note_with_tasks):
        """Should return error when task pattern doesn't match."""
        update_task_status = _get_tool("update_task_status")
        result = update_task_status("tasks.md", "nonexistent task", completed=True)

        assert "error" in result.lower() or "no task found" in result.lower()

    @pytest.mark.usefixtures("_patch_vault")
    def test_partial_match(self, vault_tmp, note_with_tasks):
        """Should match task by partial pattern."""
        update_task_status = _get_tool("update_task_status")
        result = update_task_status("tasks.md", "Review PR", completed=True)

        assert "completed" in result.lower()

        content = note_with_tasks.read_text(encoding="utf-8")
        assert "- [x] Review PR for backend" in content

    @pytest.mark.usefixtures("_patch_vault")
    def test_missing_file(self, vault_tmp):
        """Should return error for non-existent file."""
        update_task_status = _get_tool("update_task_status")
        result = update_task_status("missing.md", "some task", completed=True)

        assert "does not exist" in result.lower() or "not found" in result.lower()
