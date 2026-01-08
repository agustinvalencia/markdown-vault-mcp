import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

# Default configuration
DEFAULT_DAILY_FORMAT = "daily/%Y-%m-%d.md"

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
    raise ValueError("MARKDOWN_VAULT_PATH environment variable is not set and 'vault_path' not found in mcp_config.toml")

DAILY_NOTE_FORMAT = _config.get("daily_format", DEFAULT_DAILY_FORMAT)

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
        if not path.resolve().is_relative_to(VAULT_PATH.resolve()):
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
