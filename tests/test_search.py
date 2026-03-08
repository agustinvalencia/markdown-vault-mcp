"""Tests for search tools: search_notes."""

from unittest.mock import patch

import pytest


@pytest.fixture
def vault_tmp(tmp_path):
    """Set up a temporary vault with notes."""
    # Create several notes for searching
    notes_dir = tmp_path / "notes"
    notes_dir.mkdir()

    (notes_dir / "python.md").write_text(
        "---\ntitle: Python Guide\n---\n\n"
        "# Python Guide\n\n"
        "Python is a great language.\n"
        "It supports dynamic typing.\n",
        encoding="utf-8",
    )

    (notes_dir / "rust.md").write_text(
        "---\ntitle: Rust Guide\n---\n\n"
        "# Rust Guide\n\n"
        "Rust is a systems language.\n"
        "It has strong static typing.\n",
        encoding="utf-8",
    )

    journal_dir = tmp_path / "journal"
    journal_dir.mkdir()

    (journal_dir / "2026-01-01.md").write_text(
        "---\ntype: daily\n---\n\n"
        "# January 1\n\n"
        "Started learning Python today.\n",
        encoding="utf-8",
    )

    return tmp_path


@pytest.fixture
def _patch_vault(vault_tmp):
    """Patch VAULT_PATH for search and config modules."""
    with (
        patch("mdvault_mcp_server.tools.search.VAULT_PATH", vault_tmp),
        patch("mdvault_mcp_server.config.VAULT_PATH", vault_tmp),
    ):
        yield


def _get_search_tool():
    """Register search tools and return search_notes function."""
    from mdvault_mcp_server.tools.search import register_search_tools
    from fastmcp import FastMCP

    mcp = FastMCP("test")
    register_search_tools(mcp)
    return mcp._tool_manager._tools["search_notes"].fn


class TestSearchNotes:
    """Tests for search_notes tool."""

    @pytest.mark.usefixtures("_patch_vault")
    def test_search_finds_matching_notes(self, vault_tmp):
        """Should return paths of notes containing the query."""
        search = _get_search_tool()
        result = search("Python")

        assert "notes/python.md" in result or "notes\\python.md" in result
        # Also matches journal entry mentioning Python
        assert "journal/2026-01-01.md" in result or "journal\\2026-01-01.md" in result

    @pytest.mark.usefixtures("_patch_vault")
    def test_search_case_insensitive(self, vault_tmp):
        """Should match regardless of case."""
        search = _get_search_tool()
        result = search("python")

        assert "python.md" in result

    @pytest.mark.usefixtures("_patch_vault")
    def test_search_no_matches(self, vault_tmp):
        """Should return 'No matches found' for unmatched query."""
        search = _get_search_tool()
        result = search("xyznonexistent")

        assert result == "No matches found"

    @pytest.mark.usefixtures("_patch_vault")
    def test_search_with_folder_filter(self, vault_tmp):
        """Should limit search to specified folder."""
        search = _get_search_tool()
        result = search("Python", folder="notes")

        assert "python.md" in result
        # Should NOT include journal entry
        assert "journal" not in result

    @pytest.mark.usefixtures("_patch_vault")
    def test_search_with_context_lines(self, vault_tmp):
        """Should return context around matches when context_lines > 0."""
        search = _get_search_tool()
        result = search("dynamic typing", context_lines=1)

        # Should contain context header and line reference
        assert "Line" in result
        # Should contain surrounding context
        assert "dynamic typing" in result

    @pytest.mark.usefixtures("_patch_vault")
    def test_search_invalid_folder(self, vault_tmp):
        """Should return error for non-existent folder."""
        search = _get_search_tool()
        result = search("anything", folder="nonexistent_folder")

        assert "does not exist" in result.lower() or "not found" in result.lower()

    @pytest.mark.usefixtures("_patch_vault")
    def test_search_results_sorted(self, vault_tmp):
        """When no context, results should be sorted alphabetically."""
        search = _get_search_tool()
        result = search("typing")

        lines = result.strip().split("\n")
        assert len(lines) == 2
        assert lines == sorted(lines)

    @pytest.mark.usefixtures("_patch_vault")
    def test_search_only_md_files(self, vault_tmp):
        """Should only search .md files, ignoring others."""
        # Create a non-md file containing the query
        (vault_tmp / "notes" / "data.txt").write_text("Python data", encoding="utf-8")

        search = _get_search_tool()
        result = search("Python data")

        # Should not find the .txt file
        assert "data.txt" not in result
