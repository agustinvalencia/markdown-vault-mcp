"""Tests for mdvault_mcp_server.tools.common module."""

import subprocess
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from mdvault_mcp_server.tools.common import (
    append_content_logic,
    format_log_entry,
    run_mdv_command,
)


# ---------------------------------------------------------------------------
# format_log_entry
# ---------------------------------------------------------------------------


class TestFormatLogEntry:
    """Tests for format_log_entry."""

    def test_basic_format(self):
        """Should produce `- [[YYYY-MM-DD]] - HH:MM: Content`."""
        fixed = datetime(2026, 3, 8, 14, 5)
        with patch("mdvault_mcp_server.tools.common.datetime") as mock_dt:
            mock_dt.now.return_value = fixed
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            result = format_log_entry("Did something useful")

        assert result == "- [[2026-03-08]] - 14:05: Did something useful"

    def test_preserves_content_as_is(self):
        """Content string should be embedded verbatim."""
        fixed = datetime(2025, 1, 1, 0, 0)
        with patch("mdvault_mcp_server.tools.common.datetime") as mock_dt:
            mock_dt.now.return_value = fixed

            result = format_log_entry("  spaces & [[links]]  ")

        assert result.endswith(": " + "  spaces & [[links]]  ")


# ---------------------------------------------------------------------------
# run_mdv_command
# ---------------------------------------------------------------------------


class TestRunMdvCommand:
    """Tests for run_mdv_command."""

    def test_mdv_not_found(self):
        """Should return an error string when mdv is not in PATH."""
        with patch("mdvault_mcp_server.tools.common.shutil.which", return_value=None):
            result = run_mdv_command(["list"])

        assert "not found" in result.lower()

    def test_successful_command(self):
        """Should return stripped stdout on success."""
        fake_result = MagicMock(returncode=0, stdout="  output text\n", stderr="")
        with (
            patch("mdvault_mcp_server.tools.common.shutil.which", return_value="/usr/local/bin/mdv"),
            patch("mdvault_mcp_server.tools.common.subprocess.run", return_value=fake_result) as mock_run,
        ):
            result = run_mdv_command(["list", "--json"])

        assert result == "output text"
        call_args = mock_run.call_args
        assert call_args[0][0] == ["/usr/local/bin/mdv", "list", "--json"]

    def test_failed_command(self):
        """Should return error with stderr/stdout on non-zero exit."""
        fake_result = MagicMock(returncode=1, stdout="", stderr="bad arg\n")
        with (
            patch("mdvault_mcp_server.tools.common.shutil.which", return_value="/usr/local/bin/mdv"),
            patch("mdvault_mcp_server.tools.common.subprocess.run", return_value=fake_result),
        ):
            result = run_mdv_command(["bad-cmd"])

        assert "Error executing command" in result
        assert "bad arg" in result

    def test_exception_during_execution(self):
        """Should catch exceptions and return a friendly error."""
        with (
            patch("mdvault_mcp_server.tools.common.shutil.which", return_value="/usr/local/bin/mdv"),
            patch(
                "mdvault_mcp_server.tools.common.subprocess.run",
                side_effect=OSError("permission denied"),
            ),
        ):
            result = run_mdv_command(["list"])

        assert "Failed to execute" in result
        assert "permission denied" in result


# ---------------------------------------------------------------------------
# append_content_logic
# ---------------------------------------------------------------------------


class TestAppendContentLogicNoSubsection:
    """Appending without a subsection (to end of file)."""

    def test_append_to_empty(self):
        new, created = append_content_logic("", "hello", None)
        assert new == "hello"
        assert created is False

    def test_append_to_existing_with_trailing_newline(self):
        new, created = append_content_logic("line1\n", "line2", None)
        assert new == "line1\nline2"
        assert created is False

    def test_append_to_existing_without_trailing_newline(self):
        """Should add a newline before content when existing has none."""
        new, created = append_content_logic("line1", "line2", None)
        assert new == "line1\nline2"
        assert created is False

    def test_subsection_empty_string_treated_as_none(self):
        """Empty string subsection should behave like None."""
        new, created = append_content_logic("existing\n", "new", "")
        assert new == "existing\nnew"
        assert created is False


class TestAppendContentLogicNewSubsection:
    """Creating a new subsection when it doesn't exist."""

    def test_creates_h2_subsection(self):
        existing = "# Title\n\nSome text\n"
        new, created = append_content_logic(existing, "- entry", "Logs")
        assert created is True
        assert "## Logs\n\n- entry" in new

    def test_creates_subsection_on_empty_content(self):
        new, created = append_content_logic("", "- entry", "Notes")
        assert created is True
        assert "## Notes\n\n- entry" in new

    def test_creates_subsection_adds_blank_line_separator(self):
        """Should have a blank line between existing content and new subsection."""
        existing = "some content"
        new, created = append_content_logic(existing, "- item", "Section")
        assert created is True
        assert "some content\n\n## Section\n\n- item" in new

    def test_creates_subsection_no_extra_blanks_when_already_separated(self):
        existing = "some content\n\n"
        new, created = append_content_logic(existing, "- item", "Section")
        assert created is True
        assert new == "some content\n\n## Section\n\n- item"


class TestAppendContentLogicExistingSubsection:
    """Appending to an existing subsection."""

    def test_append_to_last_section(self):
        existing = "# Title\n\n## Logs\n\n- first entry\n"
        new, created = append_content_logic(existing, "- second entry", "Logs")
        assert created is False
        assert "- first entry\n- second entry" in new

    def test_append_to_section_with_next_section(self):
        """Content should be inserted before the next section."""
        existing = "# Title\n\n## Logs\n\n- entry1\n\n## Other\n\nstuff\n"
        new, created = append_content_logic(existing, "- entry2", "Logs")
        assert created is False
        # entry2 should appear before ## Other
        logs_pos = new.index("## Logs")
        entry2_pos = new.index("- entry2")
        other_pos = new.index("## Other")
        assert logs_pos < entry2_pos < other_pos

    def test_consecutive_appends_no_blank_lines(self):
        """Multiple appends to the same subsection must NOT produce blank lines between entries."""
        existing = "# Daily\n\n## Logs\n\n"
        # First append
        result1, _ = append_content_logic(existing, "- first", "Logs")
        # Second append
        result2, _ = append_content_logic(result1, "- second", "Logs")
        # Third append
        result3, _ = append_content_logic(result2, "- third", "Logs")

        # Entries should be on consecutive lines with no blank line between them
        assert "- first\n- second\n- third" in result3

    def test_consecutive_appends_with_next_section(self):
        """Consecutive appends before a next section preserve ordering and next section."""
        existing = "# Daily\n\n## Logs\n\n## Tasks\n\n- task1\n"
        r1, _ = append_content_logic(existing, "- log1", "Logs")
        r2, _ = append_content_logic(r1, "- log2", "Logs")

        # Both entries appear before the next section
        log1_pos = r2.index("- log1")
        log2_pos = r2.index("- log2")
        tasks_pos = r2.index("## Tasks")
        assert log1_pos < log2_pos < tasks_pos
        # Next section must still exist with its content
        assert "## Tasks" in r2
        assert "- task1" in r2

    def test_no_blank_line_when_cli_left_gap_before_next_section(self):
        """When the CLI writes entries and leaves a \\n\\n gap before the next
        section, a subsequent MCP append must NOT produce a blank line between
        the existing entry and the new one."""
        # Simulate CLI having written an entry with a blank line before next section
        existing = (
            "# Daily\n\n"
            "## Logs\n"
            "- **10:27**: CLI entry\n"
            "\n"
            "## Closing Thoughts\n"
        )
        new, created = append_content_logic(existing, "- **10:36**: MCP entry", "Logs")
        assert created is False
        # Entries must be on consecutive lines — no blank line between them
        assert "- **10:27**: CLI entry\n- **10:36**: MCP entry\n" in new
        # Next section must still be separated by a blank line
        assert "MCP entry\n\n## Closing Thoughts" in new

    def test_no_blank_line_when_multiple_cli_gaps(self):
        """Multiple trailing blank lines in prefix should all be collapsed."""
        existing = (
            "# Daily\n\n"
            "## Logs\n"
            "- entry1\n"
            "\n\n\n"
            "## Other\n"
        )
        new, _ = append_content_logic(existing, "- entry2", "Logs")
        assert "- entry1\n- entry2\n" in new
        assert "entry2\n\n## Other" in new


class TestAppendContentLogicHeadingLevels:
    """Subsections at different heading levels."""

    def test_h3_subsection(self):
        existing = "# Title\n\n### Deep Section\n\nold content\n"
        new, created = append_content_logic(existing, "new line", "Deep Section")
        assert created is False
        assert "old content\nnew line" in new

    def test_h3_does_not_match_h2_as_next(self):
        """An h4 after the target h3 should act as next section, but h4 under h3 should too."""
        existing = "# Title\n\n### Logs\n\n- entry\n\n### Other\n\ntext\n"
        new, created = append_content_logic(existing, "- new", "Logs")
        assert created is False
        entry_pos = new.index("- new")
        other_pos = new.index("### Other")
        assert entry_pos < other_pos

    def test_deeper_heading_inside_section_not_treated_as_boundary(self):
        """A heading deeper than the target should NOT be treated as next section boundary."""
        existing = "# Title\n\n## Logs\n\n### Sub-log\n\ndetail\n\n## Other\n"
        new, created = append_content_logic(existing, "- appended", "Logs")
        assert created is False
        appended_pos = new.index("- appended")
        other_pos = new.index("## Other")
        assert appended_pos < other_pos


class TestAppendContentLogicEdgeCases:
    """Edge cases."""

    def test_empty_existing_no_subsection(self):
        new, created = append_content_logic("", "content", None)
        assert new == "content"
        assert created is False

    def test_existing_without_trailing_newline_with_subsection(self):
        existing = "# Title\n\n## Logs\n\n- entry"
        new, created = append_content_logic(existing, "- another", "Logs")
        assert created is False
        assert "- entry\n- another" in new

    def test_content_with_multiline(self):
        existing = "# Title\n\n## Notes\n\n"
        new, created = append_content_logic(existing, "line1\nline2\nline3", "Notes")
        assert created is False
        assert "line1\nline2\nline3" in new

    def test_subsection_name_with_special_chars(self):
        """Subsection names with regex-special chars should be escaped properly."""
        existing = "# Title\n\n## Q&A (2026)\n\nold\n"
        new, created = append_content_logic(existing, "new", "Q&A (2026)")
        assert created is False
        assert "old\nnew" in new

    def test_similar_subsection_names_no_false_match(self):
        """Should not match 'Logs Extra' when looking for 'Logs'."""
        existing = "# Title\n\n## Logs Extra\n\nwrong\n"
        new, created = append_content_logic(existing, "- entry", "Logs")
        # Should create a new section since 'Logs' doesn't exist
        assert created is True
        assert "## Logs\n\n- entry" in new
