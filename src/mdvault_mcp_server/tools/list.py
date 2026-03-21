# pyright: reportUnusedFunction=false
# pyright is being too picky in these ones as the callers are outside of this context

from pathlib import Path

from fastmcp import FastMCP

from ..config import VAULT_PATH, validate_path


def _has_content(directory: Path) -> bool:
    """Check whether a directory contains any non-hidden files (recursively)."""
    try:
        return any(
            not part.startswith(".") for f in directory.rglob("*") if f.is_file()
            for part in f.relative_to(directory).parts
        )
    except OSError:
        return False


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
        """List all markdown notes in the vault, optionally scoped to a folder.

        Args:
            folder: Subfolder to list notes from (relative to vault root).
                    If empty, lists all notes in the vault.

        Returns:
            Newline-separated list of note paths relative to vault root.
        """
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
        """List subfolders in the vault, optionally scoped to a parent folder.

        Skips hidden directories and empty folders.

        Args:
            folder: Parent folder to list subfolders from (relative to vault root).
                    If empty, lists top-level vault folders.

        Returns:
            Newline-separated list of folder paths relative to vault root.
        """
        ok, result = validated_path(folder)
        if not ok:
            return result

        search_path = Path(result)
        folders: list[str] = []
        for item in search_path.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                # Skip empty directories — they are likely stale legacy paths
                if _has_content(item):
                    relative_path = item.relative_to(VAULT_PATH)
                    folders.append(str(relative_path))

        return "\n".join(sorted(folders)) if folders else "No folders found"
