"""Tests for vault lint MCP tool."""

from unittest.mock import patch

from mdvault_mcp_server.tools.lint import _format_report, register_lint_tools


def _get_tools():
    """Register lint tools on a test MCP and return tool functions by name."""
    from fastmcp import FastMCP

    mcp = FastMCP("test")
    register_lint_tools(mcp)
    return {name: t.fn for name, t in mcp._tool_manager._tools.items()}


def _get_tool():
    """Return the vault_lint tool function."""
    return _get_tools()["vault_lint"]


# ── _format_report tests ─────────────────────────────────────────────────


class TestFormatReport:
    def test_empty_vault(self):
        report = {
            "summary": {
                "total_notes": 0,
                "total_errors": 0,
                "total_warnings": 0,
                "health_score": 1.0,
                "reindex_performed": False,
            },
            "categories": [],
        }
        result = _format_report(report)
        assert "100%" in result
        assert "0 notes" in result
        assert "No issues found" in result

    def test_clean_categories(self):
        report = {
            "summary": {
                "total_notes": 50,
                "total_errors": 0,
                "total_warnings": 0,
                "health_score": 1.0,
                "reindex_performed": False,
            },
            "categories": [
                {"name": "broken_references", "label": "Broken References", "errors": [], "warnings": []},
                {"name": "orphaned_notes", "label": "Orphaned Notes", "errors": [], "warnings": []},
            ],
        }
        result = _format_report(report)
        assert "Clean: Broken References, Orphaned Notes" in result
        assert "No issues found" in result

    def test_errors_shown(self):
        report = {
            "summary": {
                "total_notes": 10,
                "total_errors": 1,
                "total_warnings": 0,
                "health_score": 0.9,
                "reindex_performed": False,
            },
            "categories": [
                {
                    "name": "broken_references",
                    "label": "Broken References",
                    "errors": [
                        {
                            "path": "notes/a.md",
                            "line": 5,
                            "message": "broken link -> missing.md",
                            "suggestion": None,
                            "fixable": False,
                        }
                    ],
                    "warnings": [],
                },
            ],
        }
        result = _format_report(report)
        assert "90%" in result
        assert "Broken References" in result
        assert "notes/a.md:5" in result
        assert "broken link" in result

    def test_warnings_shown(self):
        report = {
            "summary": {
                "total_notes": 5,
                "total_errors": 0,
                "total_warnings": 1,
                "health_score": 0.8,
                "reindex_performed": False,
            },
            "categories": [
                {
                    "name": "orphaned_notes",
                    "label": "Orphaned Notes",
                    "errors": [],
                    "warnings": [
                        {
                            "path": "tasks/lonely.md",
                            "message": "task note has no incoming links",
                            "suggestion": "link to this note",
                            "fixable": False,
                        }
                    ],
                },
            ],
        }
        result = _format_report(report)
        assert "WARN" in result
        assert "lonely.md" in result
        assert "link to this note" in result

    def test_issue_capping(self):
        """Issues beyond MAX_ISSUES_PER_CATEGORY are summarised."""
        errors = [
            {
                "path": f"notes/{i}.md",
                "message": f"error {i}",
                "fixable": False,
            }
            for i in range(8)
        ]
        report = {
            "summary": {
                "total_notes": 20,
                "total_errors": 8,
                "total_warnings": 0,
                "health_score": 0.6,
                "reindex_performed": False,
            },
            "categories": [
                {
                    "name": "broken_references",
                    "label": "Broken References",
                    "errors": errors,
                    "warnings": [],
                },
            ],
        }
        result = _format_report(report)
        assert "and 3 more" in result

    def test_suggestion_shown(self):
        report = {
            "summary": {
                "total_notes": 1,
                "total_errors": 0,
                "total_warnings": 1,
                "health_score": 0.0,
                "reindex_performed": False,
            },
            "categories": [
                {
                    "name": "malformed_wikilinks",
                    "label": "Malformed Wikilinks",
                    "errors": [],
                    "warnings": [
                        {
                            "path": "notes/a.md",
                            "line": 3,
                            "message": "bare ID",
                            "suggestion": "use alias",
                            "fixable": False,
                        }
                    ],
                },
            ],
        }
        result = _format_report(report)
        assert "use alias" in result

    def test_vault_path_without_line(self):
        """Issues without a line number show just the path."""
        report = {
            "summary": {
                "total_notes": 1,
                "total_errors": 1,
                "total_warnings": 0,
                "health_score": 0.0,
                "reindex_performed": False,
            },
            "categories": [
                {
                    "name": "schema_violations",
                    "label": "Schema Violations",
                    "errors": [
                        {
                            "path": "tasks/t.md",
                            "message": "missing required field",
                            "fixable": True,
                        }
                    ],
                    "warnings": [],
                },
            ],
        }
        result = _format_report(report)
        assert "tasks/t.md:" in result
        # No line number — no colon+number after path
        assert "tasks/t.md: missing" in result

    def test_vault_level_issue(self):
        """Issues with empty path show (vault)."""
        report = {
            "summary": {
                "total_notes": 0,
                "total_errors": 0,
                "total_warnings": 1,
                "health_score": 1.0,
                "reindex_performed": False,
            },
            "categories": [
                {
                    "name": "db_sync",
                    "label": "Index Sync",
                    "errors": [],
                    "warnings": [
                        {
                            "path": "",
                            "message": "3 new file(s)",
                            "fixable": False,
                        }
                    ],
                },
            ],
        }
        result = _format_report(report)
        assert "(vault)" in result


# ── vault_lint tool tests ─────────────────────────────────────────────────


class TestVaultLint:
    def test_mdv_not_found(self):
        tool = _get_tool()
        with patch("mdvault_mcp_server.tools.lint._run_mdv_json", return_value="Error: 'mdv' executable not found in PATH."):
            result = tool()
        assert "Error" in result

    def test_successful_run(self):
        tool = _get_tool()
        report = {
            "summary": {
                "total_notes": 10,
                "total_errors": 0,
                "total_warnings": 0,
                "health_score": 1.0,
                "reindex_performed": False,
            },
            "categories": [],
        }
        with patch("mdvault_mcp_server.tools.lint._run_mdv_json", return_value=report):
            result = tool()
        assert "100%" in result
        assert "No issues found" in result

    def test_json_parse_error(self):
        tool = _get_tool()
        with patch("mdvault_mcp_server.tools.lint._run_mdv_json", return_value="Failed to parse mdv output:\nnot json {{{"):
            result = tool()
        assert "Failed to parse" in result

    def test_category_filter_passed(self):
        tool = _get_tool()
        report = {
            "summary": {"total_notes": 0, "total_errors": 0, "total_warnings": 0, "health_score": 1.0, "reindex_performed": False},
            "categories": [],
        }
        with patch("mdvault_mcp_server.tools.lint._run_mdv_json", return_value=report) as mock_run:
            tool(category="broken_references")
        mock_run.assert_called_once_with(["check", "--json", "--category", "broken_references"])

    def test_no_category_passes_no_filter(self):
        tool = _get_tool()
        report = {
            "summary": {"total_notes": 0, "total_errors": 0, "total_warnings": 0, "health_score": 1.0, "reindex_performed": False},
            "categories": [],
        }
        with patch("mdvault_mcp_server.tools.lint._run_mdv_json", return_value=report) as mock_run:
            tool()
        mock_run.assert_called_once_with(["check", "--json"])


# ── validate_note tool tests ────────────────────────────────────────────


class TestValidateNote:
    def _get_validate_tool(self):
        return _get_tools()["validate_note"]

    def test_all_valid(self):
        tool = self._get_validate_tool()
        report = {"total": 5, "valid": 5, "errors": 0, "fixed": 0, "results": []}
        with patch("mdvault_mcp_server.tools.lint._run_mdv_json", return_value=report):
            result = tool()
        assert "5/5" in result
        assert "All notes pass" in result

    def test_errors_shown(self):
        tool = self._get_validate_tool()
        report = {
            "total": 1,
            "valid": 0,
            "errors": 1,
            "fixed": 0,
            "results": [
                {
                    "path": "Journal/2026/Daily/2026-04-05.md",
                    "note_type": "daily",
                    "valid": False,
                    "errors": ["missing required field: created_at", "missing required field: week"],
                    "warnings": [],
                }
            ],
        }
        with patch("mdvault_mcp_server.tools.lint._run_mdv_json", return_value=report):
            result = tool(path="Journal/2026/Daily/2026-04-05.md")
        assert "0/1" in result
        assert "created_at" in result
        assert "week" in result

    def test_fixes_shown(self):
        tool = self._get_validate_tool()
        report = {
            "total": 1,
            "valid": 0,
            "errors": 0,
            "fixed": 1,
            "results": [
                {
                    "path": "Journal/2026/Daily/2026-04-05.md",
                    "note_type": "daily",
                    "valid": False,
                    "errors": ["missing required field: week"],
                    "warnings": [],
                    "fixes_applied": ["Added missing field 'week' with default '[[2026-W14]]'"],
                }
            ],
        }
        with patch("mdvault_mcp_server.tools.lint._run_mdv_json", return_value=report):
            result = tool(path="Journal/2026/Daily/2026-04-05.md", fix=True)
        assert "1 fixed" in result
        assert "FIXED" in result

    def test_type_filter_passed(self):
        tool = self._get_validate_tool()
        report = {"total": 0, "valid": 0, "errors": 0, "fixed": 0, "results": []}
        with patch("mdvault_mcp_server.tools.lint._run_mdv_json", return_value=report) as mock_run:
            tool(note_type="daily", limit=10)
        mock_run.assert_called_once_with(["validate", "--output", "json", "--type", "daily", "--limit", "10"])

    def test_mdv_error(self):
        tool = self._get_validate_tool()
        with patch("mdvault_mcp_server.tools.lint._run_mdv_json", return_value="Error: 'mdv' executable not found in PATH."):
            result = tool()
        assert "Error" in result
