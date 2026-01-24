import tomllib
from pathlib import Path

from fastmcp import FastMCP

from ..config import VAULT_PATH
from .common import run_mdv_command


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

    @mcp.tool()
    def get_context_day(date: str = "today") -> str:
        """Get activity context for a specific day including tasks, notes modified, and logs.

        Args:
            date: Date in YYYY-MM-DD format, or 'today', 'yesterday', or date expression.
        """
        args = ["context", "day", date, "--format", "json"]
        return run_mdv_command(args)

    @mcp.tool()
    def get_context_week(week: str | None = None) -> str:
        """Get activity context for a specific week.

        Args:
            week: Week identifier ('current', 'last', YYYY-Wxx), or None for current.
        """
        args = ["context", "week"]
        if week:
            args.append(week)
        args.extend(["--format", "json"])
        return run_mdv_command(args)

    @mcp.tool()
    def get_context_note(note_path: str, activity_days: int = 7) -> str:
        """Get context for a specific note including metadata, sections, activity, and references.

        Args:
            note_path: Path to the note relative to vault root.
            activity_days: Number of days of activity history to include.
        """
        args = ["context", "note", note_path, "--format", "json", "--activity-days", str(activity_days)]
        return run_mdv_command(args)

    @mcp.tool()
    def get_context_focus() -> str:
        """Get context for the currently focused project.

        Returns the active project with task counts, recent tasks, and activity.
        Use this to understand what the user is currently working on.
        """
        args = ["context", "focus", "--format", "json"]
        return run_mdv_command(args)
