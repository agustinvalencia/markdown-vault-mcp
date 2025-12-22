# pyright: reportUnusedFunction=false
# pyright is being too picky in these ones as the callers are outside of this context

from fastmcp import FastMCP

from ..config import VAULT_PATH, validate_file


def register_read_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def read_note(note_path: str) -> str:
        full_path = VAULT_PATH / note_path
        result = validate_file(full_path)
        if not result.ok:
            return result.msg

        try:
            return full_path.read_text(encoding="utf-8")
        except Exception as e:
            return f"Error reading {full_path} : {str(e)}"

    @mcp.tool()
    def read_note_excerpt(note_path: str, max_lines: int = 50) -> str:
        full_path = VAULT_PATH / note_path
        result = validate_file(full_path)
        if not result.ok:
            return result.msg

        try:
            content = full_path.read_text(encoding="utf-8")
            lines = content.splitlines()
            if len(lines) <= max_lines:
                return content
            excerpt = "\n".join(lines[:max_lines])
            return f"{excerpt}\n\n({len(lines) - max_lines} more lines)"
        except Exception as e:
            return f"Error reading note : {str(e)}"
