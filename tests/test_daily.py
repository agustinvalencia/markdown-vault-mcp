from datetime import date
from unittest.mock import patch

import pytest


@pytest.fixture
def vault_tmp(tmp_path):
    """Set up a temporary vault with daily note directory."""
    daily_dir = tmp_path / "Journal" / "Daily"
    daily_dir.mkdir(parents=True)
    return tmp_path


@pytest.fixture
def _patch_config(vault_tmp):
    """Patch vault config to use tmp directory."""
    with (
        patch("mdvault_mcp_server.tools.daily.VAULT_PATH", vault_tmp),
        patch("mdvault_mcp_server.tools.daily.DAILY_NOTE_FORMAT", "Journal/Daily/%Y-%m-%d.md"),
    ):
        yield


class TestAddToDailyNoteImpl:
    """Tests for _add_to_daily_note_impl template-based creation."""

    @pytest.mark.usefixtures("_patch_config")
    def test_creates_note_via_mdv_when_missing(self, vault_tmp):
        """When daily note doesn't exist, should call mdv new daily --batch."""
        today = date.today()
        expected_path = vault_tmp / "Journal" / "Daily" / today.strftime("%Y-%m-%d.md")

        # Simulate mdv creating the file with template content.
        def fake_mdv_new(args):
            expected_path.write_text(
                "---\ntype: daily\ndate: 2026-02-18\n---\n\n# Wednesday\n\n## Logs\n",
                encoding="utf-8",
            )
            return "OK   mdv new\ntype:   daily"

        with patch("mdvault_mcp_server.tools.daily.run_mdv_command", side_effect=fake_mdv_new) as mock_cmd:
            from mdvault_mcp_server.tools.daily import _add_to_daily_note_impl

            result = _add_to_daily_note_impl("test log entry", subsection="Logs")

            mock_cmd.assert_called_once_with(["new", "daily", "--batch"])
            assert "Logs" in result

    @pytest.mark.usefixtures("_patch_config")
    def test_does_not_call_mdv_when_note_exists(self, vault_tmp):
        """When daily note already exists, should NOT call mdv new."""
        today = date.today()
        note_path = vault_tmp / "Journal" / "Daily" / today.strftime("%Y-%m-%d.md")
        note_path.write_text(
            "---\ntype: daily\n---\n\n# Today\n\n## Logs\n",
            encoding="utf-8",
        )

        with patch("mdvault_mcp_server.tools.daily.run_mdv_command") as mock_cmd:
            from mdvault_mcp_server.tools.daily import _add_to_daily_note_impl

            result = _add_to_daily_note_impl("test entry", subsection="Logs")

            mock_cmd.assert_not_called()
            assert "Logs" in result


class TestCreateDailyNoteImpl:
    """Tests for _create_daily_note_impl."""

    def test_creates_with_default_args(self):
        """Should call mdv new daily --batch with no extra args."""
        with patch("mdvault_mcp_server.tools.daily.run_mdv_command", return_value="OK") as mock_cmd:
            from mdvault_mcp_server.tools.daily import _create_daily_note_impl

            result = _create_daily_note_impl()

            mock_cmd.assert_called_once_with(["new", "daily", "--batch"])
            assert result == "OK"

    def test_creates_with_specific_date(self):
        """Should pass date as --var when specified."""
        with patch("mdvault_mcp_server.tools.daily.run_mdv_command", return_value="OK") as mock_cmd:
            from mdvault_mcp_server.tools.daily import _create_daily_note_impl

            result = _create_daily_note_impl(date="2026-03-01")

            mock_cmd.assert_called_once_with(["new", "daily", "--batch", "--var", "date=2026-03-01"])

    def test_creates_with_extra_vars(self):
        """Should pass extra_vars as --var pairs."""
        with patch("mdvault_mcp_server.tools.daily.run_mdv_command", return_value="OK") as mock_cmd:
            from mdvault_mcp_server.tools.daily import _create_daily_note_impl

            result = _create_daily_note_impl(extra_vars={"meds": "true"})

            mock_cmd.assert_called_once_with(["new", "daily", "--batch", "--var", "meds=true"])
