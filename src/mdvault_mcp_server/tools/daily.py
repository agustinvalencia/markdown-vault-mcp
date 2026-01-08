from datetime import date

from fastmcp import FastMCP

from ..config import DAILY_NOTE_FORMAT, VAULT_PATH
from .common import append_content_logic


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
                # Initialize with a title - defaulting to the date or filename
                # We could make the title format configurable too, but for now simple is best
                filename.write_text(f"# {today.strftime('%Y-%m-%d')}\n\n", encoding="utf-8")

            existing = filename.read_text(encoding="utf-8")
            new_content, created_new = append_content_logic(existing, content, subsection)

            filename.write_text(new_content, encoding="utf-8")

            if created_new:
                return f"Created subsection '{subsection}' and appended content to {rel_path_str}"
            elif subsection:
                return f"Appended content to subsection '{subsection}' in {rel_path_str}"
            else:
                return f"Appended content to {rel_path_str}"

        except Exception as e:
            return f"Error updating daily note: {e}"
