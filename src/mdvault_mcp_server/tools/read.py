# pyright: reportUnusedFunction=false
# pyright is being too picky in these ones as the callers are outside of this context

import json

from fastmcp import FastMCP

from ..config import VAULT_PATH, validate_file
from .frontmatter import parse_note


def register_read_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def read_note(note_path: str, max_lines: int | None = None) -> str:
        """Read a note from the vault.

        Args:
            note_path: Path to the note relative to vault root
            max_lines: Optional maximum number of lines to return.
                       If omitted, returns the full note.

        Returns:
            Note content (possibly truncated) or error description
        """
        full_path = VAULT_PATH / note_path
        result = validate_file(full_path)
        if not result.ok:
            return result.msg

        try:
            content = full_path.read_text(encoding="utf-8")
            if max_lines is None:
                return content
            lines = content.splitlines()
            if len(lines) <= max_lines:
                return content
            excerpt = "\n".join(lines[:max_lines])
            return f"{excerpt}\n\n({len(lines) - max_lines} more lines)"
        except Exception as e:
            return f"Error reading note: {e!s}"

    @mcp.tool()
    def get_metadata(note_path: str) -> str:
        """Get the frontmatter metadata from a note as JSON.

        Args:
            note_path: Path to the note relative to vault root

        Returns:
            JSON string with metadata or error description
        """
        full_path = VAULT_PATH / note_path
        result = validate_file(full_path)
        if not result.ok:
            return result.msg

        try:
            metadata, _ = parse_note(full_path)
            return json.dumps(metadata, indent=2, default=str)
        except Exception as e:
            return f"Error reading metadata: {e}"
