"""Tests for config: validate_path, validate_file, require_vault_path, load_config."""

from pathlib import Path
from unittest.mock import patch

import pytest

from mdvault_mcp_server.config import Result, validate_file, validate_path, require_vault_path


@pytest.fixture
def vault_tmp(tmp_path):
    """Set up a temporary vault directory."""
    return tmp_path


@pytest.fixture
def _patch_vault(vault_tmp):
    """Patch VAULT_PATH to use tmp directory."""
    with patch("mdvault_mcp_server.config.VAULT_PATH", vault_tmp):
        yield


class TestValidatePath:
    """Tests for validate_path."""

    @pytest.mark.usefixtures("_patch_vault")
    def test_valid_path(self, vault_tmp):
        """Should accept a path within the vault."""
        subdir = vault_tmp / "notes"
        subdir.mkdir()

        result = validate_path(subdir)
        assert result.ok is True
        assert result.msg == ""

    @pytest.mark.usefixtures("_patch_vault")
    def test_path_outside_vault(self, vault_tmp):
        """Should reject a path outside the vault."""
        outside = Path("/tmp/outside_vault")
        outside.mkdir(parents=True, exist_ok=True)

        result = validate_path(outside)
        assert result.ok is False
        assert "Invalid path" in result.msg

    @pytest.mark.usefixtures("_patch_vault")
    def test_nonexistent_path(self, vault_tmp):
        """Should reject a path that doesn't exist."""
        missing = vault_tmp / "nonexistent"

        result = validate_path(missing)
        assert result.ok is False
        assert "does not exist" in result.msg.lower()

    def test_vault_not_configured(self):
        """Should return error when VAULT_PATH is None."""
        with patch("mdvault_mcp_server.config.VAULT_PATH", None):
            result = validate_path(Path("/some/path"))
            assert result.ok is False
            assert "Failed to validate" in result.msg


class TestValidateFile:
    """Tests for validate_file."""

    @pytest.mark.usefixtures("_patch_vault")
    def test_valid_markdown_file(self, vault_tmp):
        """Should accept a .md file within the vault."""
        md_file = vault_tmp / "note.md"
        md_file.write_text("# Test", encoding="utf-8")

        result = validate_file(md_file)
        assert result.ok is True

    @pytest.mark.usefixtures("_patch_vault")
    def test_non_markdown_file(self, vault_tmp):
        """Should reject non-.md files."""
        txt_file = vault_tmp / "note.txt"
        txt_file.write_text("text", encoding="utf-8")

        result = validate_file(txt_file)
        assert result.ok is False
        assert "markdown" in result.msg.lower()

    @pytest.mark.usefixtures("_patch_vault")
    def test_missing_markdown_file(self, vault_tmp):
        """Should reject files that don't exist."""
        missing = vault_tmp / "missing.md"

        result = validate_file(missing)
        assert result.ok is False

    @pytest.mark.usefixtures("_patch_vault")
    def test_file_outside_vault(self, vault_tmp, tmp_path):
        """Should reject files outside vault even if they're .md."""
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            outside = Path(f.name)
            outside.write_text("# Outside", encoding="utf-8")

        try:
            result = validate_file(outside)
            assert result.ok is False
            assert "Invalid path" in result.msg
        finally:
            outside.unlink()


class TestRequireVaultPath:
    """Tests for require_vault_path."""

    def test_returns_path_when_set(self, vault_tmp):
        """Should return the vault path when configured."""
        with patch("mdvault_mcp_server.config.VAULT_PATH", vault_tmp):
            result = require_vault_path()
            assert result == vault_tmp

    def test_raises_when_none(self):
        """Should raise ValueError when VAULT_PATH is None."""
        with patch("mdvault_mcp_server.config.VAULT_PATH", None):
            with pytest.raises(ValueError, match="MARKDOWN_VAULT_PATH"):
                require_vault_path()


class TestResult:
    """Tests for the Result dataclass."""

    def test_ok_result(self):
        """Should correctly represent a successful result."""
        r = Result(ok=True, msg="")
        assert r.ok is True
        assert r.msg == ""

    def test_error_result(self):
        """Should correctly represent an error result."""
        r = Result(ok=False, msg="something went wrong")
        assert r.ok is False
        assert r.msg == "something went wrong"


class TestLoadConfig:
    """Tests for load_config."""

    def test_returns_empty_when_no_config_file(self, tmp_path):
        """Should return empty dict when config file doesn't exist."""
        with patch("mdvault_mcp_server.config.os.path.expanduser", return_value=str(tmp_path / "nope")):
            from mdvault_mcp_server.config import load_config

            result = load_config()
            assert result == {}

    def test_loads_valid_toml(self, tmp_path):
        """Should parse valid TOML config."""
        config_file = tmp_path / "mcp_config.toml"
        config_file.write_text(
            'vault_path = "/home/user/vault"\ndaily_format = "Journal/%Y-%m-%d.md"\n',
            encoding="utf-8",
        )

        with patch("mdvault_mcp_server.config.os.path.expanduser", return_value=str(tmp_path)):
            # We need to patch the Path construction in load_config
            with patch("mdvault_mcp_server.config.Path") as mock_path_cls:
                mock_path_cls.return_value = config_file

                from mdvault_mcp_server.config import load_config

                result = load_config()
                assert result["vault_path"] == "/home/user/vault"
                assert result["daily_format"] == "Journal/%Y-%m-%d.md"
