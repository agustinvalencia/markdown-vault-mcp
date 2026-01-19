import tomllib
from pathlib import Path

from fastmcp import FastMCP

from ..config import VAULT_PATH


def get_active_context_dict(vault_root: Path) -> dict | None:
    """Read the active focus context from the vault."""
    state_file = vault_root / ".mdvault" / "state" / "context.toml"

    if not state_file.exists():
        return None

    try:
        with open(state_file, "rb") as f:
            state = tomllib.load(f)
        return state.get("focus")
    except Exception:
        # If the file is corrupted or unreadable, we return None
        return None


def register_context_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def get_active_context() -> str:
        """Get the current focus context for the vault.

        Returns the active project and any associated note.
        Use this to understand what the user is currently working on.
        """
        # The schema docs suggest re-reading MARKDOWN_VAULT_PATH, 
        # but we already have VAULT_PATH from config.
        context = get_active_context_dict(VAULT_PATH)

        if context is None:
            return "No active focus set."

        result = f"Active project: {context.get('project', 'Unknown')}"
        if note := context.get("note"):
            result += f"\nNote: {note}"
        if started := context.get("started_at"):
            result += f"\nFocused since: {started}"

        return result
