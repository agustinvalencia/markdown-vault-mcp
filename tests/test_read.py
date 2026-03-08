"""Tests for read tools: read_note, get_metadata."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def vault_tmp(tmp_path):
    """Set up a temporary vault directory."""
    return tmp_path


@pytest.fixture
def sample_note(vault_tmp):
    """Create a sample markdown note with frontmatter."""
    note = vault_tmp / "notes" / "sample.md"
    note.parent.mkdir(parents=True)
    note.write_text(
        "---\ntitle: Sample Note\ntype: zettel\ntags:\n  - python\n  - testing\n---\n\n"
        "# Sample Note\n\nThis is a sample note.\nLine 3.\nLine 4.\nLine 5.\n",
        encoding="utf-8",
    )
    return note


@pytest.fixture
def _patch_vault(vault_tmp):
    """Patch VAULT_PATH for read and config modules."""
    with (
        patch("mdvault_mcp_server.tools.read.VAULT_PATH", vault_tmp),
        patch("mdvault_mcp_server.config.VAULT_PATH", vault_tmp),
    ):
        yield


class TestReadNote:
    """Tests for read_note tool."""

    @pytest.mark.usefixtures("_patch_vault")
    def test_read_full_note(self, vault_tmp, sample_note):
        """Should return full note content when max_lines is None."""
        from mdvault_mcp_server.tools.read import register_read_tools
        from fastmcp import FastMCP

        mcp = FastMCP("test")
        register_read_tools(mcp)

        # Access the inner function directly
        read_note = mcp._tool_manager._tools["read_note"].fn
        result = read_note("notes/sample.md")

        assert "# Sample Note" in result
        assert "This is a sample note." in result
        assert "title: Sample Note" in result

    @pytest.mark.usefixtures("_patch_vault")
    def test_read_note_with_max_lines(self, vault_tmp, sample_note):
        """Should truncate output when max_lines is specified."""
        from mdvault_mcp_server.tools.read import register_read_tools
        from fastmcp import FastMCP

        mcp = FastMCP("test")
        register_read_tools(mcp)

        read_note = mcp._tool_manager._tools["read_note"].fn
        result = read_note("notes/sample.md", max_lines=3)

        # Should contain truncation message
        assert "more lines" in result

    @pytest.mark.usefixtures("_patch_vault")
    def test_read_note_max_lines_exceeds_content(self, vault_tmp, sample_note):
        """When max_lines exceeds note length, return full content without truncation message."""
        from mdvault_mcp_server.tools.read import register_read_tools
        from fastmcp import FastMCP

        mcp = FastMCP("test")
        register_read_tools(mcp)

        read_note = mcp._tool_manager._tools["read_note"].fn
        result = read_note("notes/sample.md", max_lines=1000)

        assert "more lines" not in result
        assert "# Sample Note" in result

    @pytest.mark.usefixtures("_patch_vault")
    def test_read_note_missing_file(self, vault_tmp):
        """Should return an error message for a non-existent note."""
        from mdvault_mcp_server.tools.read import register_read_tools
        from fastmcp import FastMCP

        mcp = FastMCP("test")
        register_read_tools(mcp)

        read_note = mcp._tool_manager._tools["read_note"].fn
        result = read_note("notes/nonexistent.md")

        assert "does not exist" in result.lower() or "not found" in result.lower()

    @pytest.mark.usefixtures("_patch_vault")
    def test_read_note_non_markdown(self, vault_tmp):
        """Should reject non-markdown files."""
        txt_file = vault_tmp / "notes" / "file.txt"
        txt_file.parent.mkdir(parents=True, exist_ok=True)
        txt_file.write_text("not markdown", encoding="utf-8")

        from mdvault_mcp_server.tools.read import register_read_tools
        from fastmcp import FastMCP

        mcp = FastMCP("test")
        register_read_tools(mcp)

        read_note = mcp._tool_manager._tools["read_note"].fn
        result = read_note("notes/file.txt")

        assert "markdown" in result.lower()


class TestGetMetadata:
    """Tests for get_metadata tool."""

    @pytest.mark.usefixtures("_patch_vault")
    def test_get_metadata_returns_json(self, vault_tmp, sample_note):
        """Should return frontmatter as valid JSON."""
        from mdvault_mcp_server.tools.read import register_read_tools
        from fastmcp import FastMCP

        mcp = FastMCP("test")
        register_read_tools(mcp)

        get_metadata = mcp._tool_manager._tools["get_metadata"].fn
        result = get_metadata("notes/sample.md")

        parsed = json.loads(result)
        assert parsed["title"] == "Sample Note"
        assert parsed["type"] == "zettel"
        assert "python" in parsed["tags"]

    @pytest.mark.usefixtures("_patch_vault")
    def test_get_metadata_missing_file(self, vault_tmp):
        """Should return error for non-existent file."""
        from mdvault_mcp_server.tools.read import register_read_tools
        from fastmcp import FastMCP

        mcp = FastMCP("test")
        register_read_tools(mcp)

        get_metadata = mcp._tool_manager._tools["get_metadata"].fn
        result = get_metadata("notes/missing.md")

        assert "does not exist" in result.lower() or "not found" in result.lower()

    @pytest.mark.usefixtures("_patch_vault")
    def test_get_metadata_no_frontmatter(self, vault_tmp):
        """Should return empty JSON for a note without frontmatter."""
        note = vault_tmp / "bare.md"
        note.write_text("# Just a heading\n\nNo frontmatter here.\n", encoding="utf-8")

        from mdvault_mcp_server.tools.read import register_read_tools
        from fastmcp import FastMCP

        mcp = FastMCP("test")
        register_read_tools(mcp)

        get_metadata = mcp._tool_manager._tools["get_metadata"].fn
        result = get_metadata("bare.md")

        parsed = json.loads(result)
        assert parsed == {}
