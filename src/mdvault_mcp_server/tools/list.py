# pyright: reportUnusedFunction=false
# pyright is being too picky in these ones as the callers are outside of this context

from pathlib import Path

from fastmcp import FastMCP

from ..config import VAULT_PATH, validate_path


def validated_path(folder: str) -> tuple[bool, str]:
    search_path = VAULT_PATH / folder if folder else VAULT_PATH
    if not search_path.exists():
        return (False, f"Folder not found: {folder}")

    if not validate_path(search_path):
        return (False, f"Invalid path, must be within vault: {search_path}")

    return (True, str(search_path))


def register_list_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def list_notes(folder: str = "") -> str:
        ok, result = validated_path(folder)
        if not ok:
            return result

        search_path = Path(result)
        notes: list[str] = []
        for md_file in search_path.rglob("*.md"):
            relative_path = md_file.relative_to(VAULT_PATH)
            notes.append(str(relative_path))

        return "\n".join(sorted(notes)) if notes else "No notes found"

    @mcp.tool()
    def list_folders(folder: str = "") -> str:
        ok, result = validated_path(folder)
        if not ok:
            return result

        search_path = Path(result)
        folders: list[str] = []
        for item in search_path.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                relative_path = item.relative_to(VAULT_PATH)
                folders.append(str(relative_path))

        return "\n".join(sorted(folders)) if folders else "No folders found"
