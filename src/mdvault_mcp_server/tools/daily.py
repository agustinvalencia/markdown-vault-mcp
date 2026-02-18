from datetime import date

from fastmcp import FastMCP

from ..config import DAILY_NOTE_FORMAT, VAULT_PATH
from .common import append_content_logic, format_log_entry, run_mdv_command
from .frontmatter import update_note_content


def _add_to_daily_note_impl(content: str, subsection: str | None = None) -> str:
    """Internal implementation of add_to_daily_note."""
    today = date.today()
    # Strftime supports basic formatting, but we might want to ensure standard datetime codes
    # are used
    rel_path_str = today.strftime(DAILY_NOTE_FORMAT)
    filename = VAULT_PATH / rel_path_str
    
    # Ensure parent directory exists
    if not filename.parent.exists():
        filename.parent.mkdir(parents=True, exist_ok=True)

    try:
        if not filename.exists():
            run_mdv_command(["new", "daily", "--batch"])

        def modifier(body: str) -> tuple[str, str]:
            new_body, created_new = append_content_logic(body, content, subsection)
            if created_new:
                msg = f"Created subsection '{subsection}' and appended content to {rel_path_str}"
            elif subsection:
                msg = f"Appended content to subsection '{subsection}' in {rel_path_str}"
            else:
                msg = f"Appended content to {rel_path_str}"
            return new_body, msg

        return update_note_content(filename, modifier)

    except Exception as e:
        return f"Error updating daily note: {e}"


def _create_daily_note_impl(
    date: str | None = None,
    extra_vars: dict[str, str] | None = None,
) -> str:
    """Internal implementation of create_daily_note."""
    args = ["new", "daily", "--batch"]
    if date:
        args.extend(["--var", f"date={date}"])
    if extra_vars:
        for k, v in extra_vars.items():
            args.extend(["--var", f"{k}={v}"])
    return run_mdv_command(args)


def register_daily_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def create_daily_note(
        date: str | None = None,
        extra_vars: dict[str, str] | None = None,
    ) -> str:
        """Create today's daily note from the configured template.

        Uses the vault's daily template to create a fully structured note with
        all standard frontmatter fields and sections. If the note already exists,
        returns a message without overwriting.

        Args:
            date: Optional date in YYYY-MM-DD format. Defaults to today.
            extra_vars: Optional dictionary of additional template variables.

        Returns:
            Result of the creation or message if note already exists.
        """
        return _create_daily_note_impl(date, extra_vars)

    @mcp.tool()
    def add_to_daily_note(content: str, subsection: str | None = None) -> str:
        """Append content to today's daily note.

        Creates the daily note and its parent directories if they don't exist.
        The note path matches the configured 'daily_format' (default: 'daily/YYYY-MM-DD.md').

        Args:
            content: Content to append
            subsection: Optional heading title to append under.

        Returns:
            Success message or error description
        """
        return _add_to_daily_note_impl(content, subsection)

    @mcp.tool()
    def log_to_daily_note(content: str) -> str:
        """Append a log entry to the 'Logs' section of today's daily note.

        Format: - [[YYYY-MM-DD]] - HH:MM: Content

        Args:
            content: The log message to append.

        Returns:
            Success message or error description.
        """
        formatted_log = format_log_entry(content)
        return _add_to_daily_note_impl(formatted_log, subsection="Logs")
