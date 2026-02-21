# pyright: reportUnusedFunction=false
# pyright is being too picky in these ones as the callers are outside of this context

from fastmcp import FastMCP

from ..config import VAULT_PATH, validate_path


def register_search_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def search_notes(query: str, folder: str = "", context_lines: int = 0) -> str:
        """Search notes containing the query text (case-insensitive).

        Args:
            query: Text to search for
            folder: Optional subfolder to limit search scope
            context_lines: Number of lines before/after each match to include.
                           When 0 (default), returns only matching file paths.
                           When > 0, returns matches with surrounding context.

        Returns:
            Newline-separated list of matching note paths, or formatted
            results with context for each match
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
                if query_lower not in content.lower():
                    continue
                relative_path = md_file.relative_to(VAULT_PATH)

                if context_lines <= 0:
                    results.append(str(relative_path))
                else:
                    lines = content.splitlines()
                    matches: list[str] = []
                    for i, line in enumerate(lines):
                        if query_lower in line.lower():
                            start = max(0, i - context_lines)
                            end = min(len(lines), i + context_lines + 1)
                            context = "\n".join(lines[start:end])
                            matches.append(f"Line {i + 1}:\n{context}")
                    if matches:
                        results.append(f"\n### {relative_path}\n" + "\n\n".join(matches))
            except Exception:
                continue

        if not results:
            return "No matches found"
        if context_lines <= 0:
            return "\n".join(sorted(results))
        return "\n".join(results)
