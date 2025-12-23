# pyright: reportUnusedFunction=false
# pyright is being too picky in these ones as the callers are outside of this context

import re
from pathlib import Path

from fastmcp import FastMCP

from ..config import VAULT_PATH, validate_file, validate_path

# Regex patterns for link extraction
WIKILINK_PATTERN = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+\.md)\)")


def extract_links(content: str) -> set[str]:
    """
    Extract all links from markdown content.

    Handles both [[wikilinks]] and [text](path.md) formats.

    Args:
        content: Markdown content to parse

    Returns:
        Set of linked note names/paths (without .md extension for wikilinks)
    """
    links: set[str] = set()

    # Extract wikilinks: [[note]] or [[note|alias]]
    for match in WIKILINK_PATTERN.finditer(content):
        link_target = match.group(1).strip()
        # Normalize: remove .md if present
        if link_target.endswith(".md"):
            link_target = link_target[:-3]
        links.add(link_target)

    # Extract markdown links: [text](path.md)
    for match in MARKDOWN_LINK_PATTERN.finditer(content):
        link_path = match.group(2).strip()
        # Only include internal .md links, skip URLs
        if not link_path.startswith(("http://", "https://", "/")):
            # Remove .md extension for consistency
            if link_path.endswith(".md"):
                link_path = link_path[:-3]
            links.add(link_path)

    return links


def normalize_note_name(note_path: str) -> str:
    """Normalize a note path to just the note name without extension."""
    return Path(note_path).stem


def find_note_path(note_name: str) -> Path | None:
    """
    Find the full path to a note by name.

    Searches for exact matches and .md extension matches.

    Args:
        note_name: Note name (with or without .md)

    Returns:
        Full path to the note, or None if not found
    """
    # Try direct path first
    if note_name.endswith(".md"):
        direct_path = VAULT_PATH / note_name
        if direct_path.exists():
            return direct_path
    else:
        direct_path = VAULT_PATH / f"{note_name}.md"
        if direct_path.exists():
            return direct_path

    # Search recursively for the note
    search_name = note_name if note_name.endswith(".md") else f"{note_name}.md"
    for md_file in VAULT_PATH.rglob("*.md"):
        if md_file.name == search_name or md_file.stem == note_name:
            return md_file

    return None


def register_zettelkasten_tools(mcp: FastMCP) -> None:  # noqa: PLR0915
    @mcp.tool()
    def find_backlinks(note_path: str) -> str:
        """Find all notes that link to the specified note.

        Args:
            note_path: Path to the note relative to vault root

        Returns:
            Newline-separated list of notes linking to this note, or message if none
        """
        full_path = VAULT_PATH / note_path
        result = validate_file(full_path)
        if not result.ok:
            return result.msg

        target_name = normalize_note_name(note_path)
        target_stem = Path(note_path).stem
        backlinks: list[str] = []

        for md_file in VAULT_PATH.rglob("*.md"):
            # Skip the target note itself
            if md_file == full_path:
                continue

            try:
                content = md_file.read_text(encoding="utf-8")
                links = extract_links(content)

                # Check if any link points to our target
                for link in links:
                    link_stem = Path(link).stem if "/" in link else link
                    if link_stem == target_stem or link == target_name:
                        relative_path = md_file.relative_to(VAULT_PATH)
                        backlinks.append(str(relative_path))
                        break
            except Exception:
                continue

        if not backlinks:
            return f"No backlinks found for {note_path}"

        return "\n".join(sorted(backlinks))

    @mcp.tool()
    def find_outgoing_links(note_path: str) -> str:
        """Find all notes that the specified note links to.

        Args:
            note_path: Path to the note relative to vault root

        Returns:
            Newline-separated list of linked notes, or message if none
        """
        full_path = VAULT_PATH / note_path
        result = validate_file(full_path)
        if not result.ok:
            return result.msg

        try:
            content = full_path.read_text(encoding="utf-8")
            links = extract_links(content)

            if not links:
                return f"No outgoing links found in {note_path}"

            # Resolve links to actual paths where possible
            resolved_links: list[str] = []
            for link in sorted(links):
                found_path = find_note_path(link)
                if found_path:
                    relative = found_path.relative_to(VAULT_PATH)
                    resolved_links.append(str(relative))
                else:
                    # Link to non-existent note (broken link)
                    resolved_links.append(f"{link}.md (not found)")

            return "\n".join(resolved_links)
        except Exception as e:
            return f"Error reading note: {e}"

    @mcp.tool()
    def find_orphan_notes(folder: str = "") -> str:
        """Find notes with no incoming or outgoing links.

        Args:
            folder: Optional subfolder to limit search scope

        Returns:
            Newline-separated list of orphan notes, or message if none
        """
        search_path = VAULT_PATH / folder if folder else VAULT_PATH
        result = validate_path(search_path)
        if not result.ok:
            return result.msg

        # Build a map of all links in the vault
        all_notes: set[str] = set()
        notes_with_outgoing: set[str] = set()
        notes_with_incoming: set[str] = set()

        # First pass: collect all notes and their outgoing links
        note_links: dict[str, set[str]] = {}
        for md_file in search_path.rglob("*.md"):
            relative_path = str(md_file.relative_to(VAULT_PATH))
            all_notes.add(relative_path)

            try:
                content = md_file.read_text(encoding="utf-8")
                links = extract_links(content)
                note_links[relative_path] = links

                if links:
                    notes_with_outgoing.add(relative_path)
            except Exception:
                continue

        # Second pass: find which notes have incoming links
        for _source_note, links in note_links.items():
            for link in links:
                # Try to resolve the link to an actual note
                found_path = find_note_path(link)
                if found_path:
                    relative = str(found_path.relative_to(VAULT_PATH))
                    notes_with_incoming.add(relative)

        # Orphans have neither incoming nor outgoing links
        orphans = all_notes - notes_with_outgoing - notes_with_incoming

        # Also consider notes that only have outgoing but no incoming
        # (these are "source" orphans - they link out but nothing links to them)
        # For now, we define orphan as completely isolated

        if not orphans:
            return "No orphan notes found"

        return "\n".join(sorted(orphans))

    @mcp.tool()
    def suggest_related_notes(note_path: str, max_suggestions: int = 5) -> str:
        """Suggest related notes based on shared links.

        Finds notes that share common outgoing links with the specified note.

        Args:
            note_path: Path to the note relative to vault root
            max_suggestions: Maximum number of suggestions to return

        Returns:
            Newline-separated list of related notes with shared link count
        """
        full_path = VAULT_PATH / note_path
        result = validate_file(full_path)
        if not result.ok:
            return result.msg

        try:
            content = full_path.read_text(encoding="utf-8")
            target_links = extract_links(content)

            if not target_links:
                return f"No links in {note_path} to find related notes"

            # Find other notes and their links
            related_scores: dict[str, int] = {}

            for md_file in VAULT_PATH.rglob("*.md"):
                if md_file == full_path:
                    continue

                try:
                    other_content = md_file.read_text(encoding="utf-8")
                    other_links = extract_links(other_content)

                    # Count shared links
                    shared = target_links & other_links
                    if shared:
                        relative_path = str(md_file.relative_to(VAULT_PATH))
                        related_scores[relative_path] = len(shared)
                except Exception:
                    continue

            if not related_scores:
                return f"No related notes found for {note_path}"

            # Sort by score descending
            sorted_related = sorted(related_scores.items(), key=lambda x: x[1], reverse=True)[
                :max_suggestions
            ]

            result_lines = [
                f"{path} ({score} shared link{'s' if score > 1 else ''})"
                for path, score in sorted_related
            ]

            return "\n".join(result_lines)
        except Exception as e:
            return f"Error analyzing note: {e}"
