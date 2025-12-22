# pyright: reportUnusedFunction=false
# pyright is being too picky in these ones as the callers are outside of this context

from pathlib import Path
from fastmcp import FastMCP

from ..config import VAULT_PATH, validate_path


def register_search_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def search_notes(query: str, folder: str = "") -> str:
        """
        Search notes containing the query text (case-insensitive).

        Args:
            query: Text to search for
            folder: Optional subfolder to limit search scope

        Returns:
            Newline-separated list of matching note paths
        """
        search_path = VAULT_PATH / folder if folder else VAULT_PATH
        valid = validate_path(search_path)
        if not valid.ok:
            return valid.msg

        results: list[str] = []
        query_lower = query.lower()

        for md_file in search_path.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                if query_lower in content.lower():
                    relative_path = md_file.relative_to(VAULT_PATH)
                    results.append(str(relative_path))
            except Exception:
                # just skip files we cannot read
                continue
        return "\n".join(sorted(results)) if results else "No matches found"

    @mcp.tool()
    def search_notes_with_context(query: str, folder: str = "", context_lines: int = 2) -> str:
        """
        Search notes and return matches with surrounding context.

        Args:
            query: Text to search for
            folder: Optional subfolder to limit search scope
            context_lines: Number of lines before/after match to include

        Returns:
            Formatted results with context for each match
        """
        search_path = VAULT_PATH / folder if folder else VAULT_PATH
        valid = validate_path(search_path)
        if not valid.ok:
            return valid.msg

        results: list[str] = []
        query_lower = query.lower()
        for md_file in search_path.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                lines = content.splitlines()
                matches: list[str] = []
                for i, line in enumerate(lines):
                    if query_lower in line.lower():
                        start = max(0, i - context_lines)
                        end = min(len(lines), i + context_lines + 1)
                        context = "\n".join(lines[start:end])
                        matches.append(f"Line {i + 1}:\n{context}")

                if matches:
                    relative_path = md_file.relative_to(VAULT_PATH)
                    result = f"\n### {relative_path}\n" + "\n\n".join(matches)
                    results.append(result)
            except Exception:
                continue
        return "\n".join(results) if results else "No matches found"
