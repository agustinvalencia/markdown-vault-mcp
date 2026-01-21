from datetime import date

from fastmcp import FastMCP

from ..config import DAILY_NOTE_FORMAT, VAULT_PATH
from .common import append_content_logic, format_log_entry
from .frontmatter import update_note_content, write_note


def register_daily_tools(mcp: FastMCP) -> None:
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
        today = date.today()
        # Strftime supports basic formatting, but we might want to ensure standard datetime codes are used
        rel_path_str = today.strftime(DAILY_NOTE_FORMAT)
        filename = VAULT_PATH / rel_path_str
        
        # Ensure parent directory exists
        if not filename.parent.exists():
            filename.parent.mkdir(parents=True, exist_ok=True)

        try:
            if not filename.exists():
                # Initialize with a title and metadata
                title = today.strftime("%Y-%m-%d")
                initial_content = f"# {title}\n\n"
                metadata = {"title": title}
                # write_note adds 'created' and 'updated_at' automatically
                filename.write_text(write_note(filename, metadata, initial_content), encoding="utf-8")

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
        return add_to_daily_note(formatted_log, subsection="Logs")
