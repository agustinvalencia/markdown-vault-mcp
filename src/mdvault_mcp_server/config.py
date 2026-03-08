import logging
import os
import re
import shutil
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path

# Default configuration
DEFAULT_DAILY_FORMAT = "Journal/%Y/Daily/%Y-%m-%d.md"

def load_config() -> dict[str, str]:
    config_path = Path(os.path.expanduser("~/.config/mdvault/mcp_config.toml"))
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path, "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        # We assume no config if it fails to load, but logging would be good in production
        print(f"Warning: Failed to load {config_path}: {e}")
        return {}

_config = load_config()

# Vault Path Priority:
# 1. Environment Variable MARKDOWN_VAULT_PATH
# 2. Config file 'vault_path'
MARKDOWN_VAULT_PATH = os.getenv("MARKDOWN_VAULT_PATH") or _config.get("vault_path")

if MARKDOWN_VAULT_PATH:
    VAULT_PATH = Path(MARKDOWN_VAULT_PATH)
else:
    VAULT_PATH = None  # type: ignore[assignment]


def require_vault_path() -> Path:
    """Return VAULT_PATH or raise if not configured. Use at runtime, not import time."""
    if VAULT_PATH is None:
        raise ValueError(
            "MARKDOWN_VAULT_PATH environment variable is not set "
            "and 'vault_path' not found in mcp_config.toml"
        )
    return VAULT_PATH

DAILY_NOTE_FORMAT = _config.get("daily_format", DEFAULT_DAILY_FORMAT)

# Minimum mdv CLI version required for full functionality
MIN_MDV_VERSION = "0.4.0"

logger = logging.getLogger(__name__)


def _parse_version(version_str: str) -> tuple[int, ...]:
    """Parse a semver-like version string into a tuple of ints."""
    match = re.search(r"(\d+(?:\.\d+)*)", version_str)
    if not match:
        raise ValueError(f"Could not parse version from: {version_str!r}")
    return tuple(int(part) for part in match.group(1).split("."))


def check_mdv_version() -> None:
    """Check that the mdv CLI binary is installed and meets the minimum version.

    Logs a warning if mdv is not found or is too old. Never raises.
    """
    try:
        mdv_path = shutil.which("mdv")
        if not mdv_path:
            logger.warning(
                "mdv CLI not found in PATH. Some tools will not work. "
                "Install mdvault: https://github.com/agustinvalencia/mdvault"
            )
            return

        result = subprocess.run(
            [mdv_path, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )

        if result.returncode != 0:
            logger.warning(
                "mdv --version returned non-zero exit code (%d). "
                "Cannot verify CLI version.",
                result.returncode,
            )
            return

        version_output = result.stdout.strip()
        installed = _parse_version(version_output)
        minimum = _parse_version(MIN_MDV_VERSION)

        if installed < minimum:
            logger.warning(
                "mdv version %s is older than the minimum required %s. "
                "Please upgrade mdvault.",
                version_output,
                MIN_MDV_VERSION,
            )
        else:
            logger.info("mdv CLI version %s found (minimum: %s)", version_output, MIN_MDV_VERSION)

    except Exception as e:
        logger.warning("Failed to check mdv version: %s", e)

@dataclass
class Result:
    ok: bool
    msg: str


def validate_path(path: Path) -> Result:
    """
    Safety check to validate that a path is within the vault

    Args:
        path: Path to validate
    Returns:
        Result object with ok=True and a valid path if it is valid or ok=False and an error message if the path is not valid
    """
    try:
        vault = require_vault_path()
        if not path.resolve().is_relative_to(vault.resolve()):
            res = f"Invalid path, must be within vault: {path!s}"
            return Result(False, res)

        if not path.exists():
            res = f"Path does not exists : {path!s}"
            return Result(False, res)

        return Result(True, "")

    except (ValueError, RuntimeError) as e:
        return Result(False, f"Failed to validate path {path}: {e}")


def validate_file(path: Path) -> Result:
    """
    Safety check to validate that a path to a file is within the vault

    Args:
        path: File path to validate
    Returns:
        Result object with ok=True and a valid path if it is valid or ok=False and an error message if the path is not valid
    """
    valid_path = validate_path(path)
    if not valid_path.ok:
        return valid_path

    ok = path.suffix == ".md"
    res = "" if ok else "Only markdown files are supported"
    return Result(ok, res)
