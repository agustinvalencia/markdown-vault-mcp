from fastmcp import FastMCP

from .common import run_mdv_command


def register_context_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def get_active_context() -> str:
        """Get the current focus context for the vault.

        Returns the active project and any associated note.
        Use this to understand what the user is currently working on.
        """
        return run_mdv_command(["focus", "--json"])

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
