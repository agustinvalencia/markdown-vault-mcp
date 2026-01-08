from datetime import date

from fastmcp import FastMCP

from ..config import VAULT_PATH
from .common import append_content_logic


def register_daily_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def add_to_daily_note(content: str, subsection: str | None = None) -> str:
        """Append content to today's daily note.

        Creates the daily note (and daily/ folder) if they don't exist.
        The note is created at 'daily/YYYY-MM-DD.md'.

        Args:
            content: Content to append
            subsection: Optional heading title to append under.

        Returns:
            Success message or error description
        """
        today = date.today()
        daily_dir = VAULT_PATH / "daily"
        filename = daily_dir / f"{today.strftime('%Y-%m-%d')}.md"
        rel_path = f"daily/{today.strftime('%Y-%m-%d')}.md"

        try:
            if not daily_dir.exists():
                daily_dir.mkdir(parents=True, exist_ok=True)

            if not filename.exists():
                # Initialize with a title
                filename.write_text(f"# {today.strftime('%Y-%m-%d')}\n\n", encoding="utf-8")

            existing = filename.read_text(encoding="utf-8")
            new_content, created_new = append_content_logic(existing, content, subsection)

            filename.write_text(new_content, encoding="utf-8")

            if created_new:
                return f"Created subsection '{subsection}' and appended content to {rel_path}"
            elif subsection:
                return f"Appended content to subsection '{subsection}' in {rel_path}"
            else:
                return f"Appended content to {rel_path}"

        except Exception as e:
            return f"Error updating daily note: {e}"
