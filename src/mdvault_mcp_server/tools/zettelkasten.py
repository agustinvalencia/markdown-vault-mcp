# pyright: reportUnusedFunction=false
# pyright is being too picky in these ones as the callers are outside of this context

import re
from pathlib import Path

from fastmcp import FastMCP

from ..config import VAULT_PATH, validate_file
from .common import run_mdv_command

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
    def create_zettel(
        title: str,
        short_title: str,
        source: str | None = None,
        body: str | None = None,
        connections: list[str] | None = None,
        extra_vars: dict[str, str] | None = None,
    ) -> str:
        """Create a new zettel (atomic knowledge note).

        Zettels are stored in the Zettel/ directory (or as configured by the
        vault's type definition). Each zettel captures a single atomic insight.

        Args:
            title: Title of the zettel (the atomic insight).
            short_title: Short slug for the filename (e.g. "attention-mechanism").
            source: Optional source reference as a wikilink (e.g. "[[literature-note]]").
            body: Optional body text elaborating on the insight.
            connections: Optional list of related note wikilinks (e.g. ["[[note-1]]", "[[note-2]]"]).
            extra_vars: Optional dictionary of additional template variables.

        Returns:
            Result of the creation including the file path.
        """
        args = ["new", "zettel", title, "--batch"]
        args.extend(["--var", f"short_title={short_title}"])
        if source:
            args.extend(["--var", f"source={source}"])
        if extra_vars:
            for k, v in extra_vars.items():
                args.extend(["--var", f"{k}={v}"])

        result = run_mdv_command(args)

        # If body or connections provided, append them to the created note
        if body or connections:
            # Extract the file path from the result
            # Result format typically includes the path
            created_path = None
            for line in result.splitlines():
                line_stripped = line.strip()
                if line_stripped.endswith(".md"):
                    # Try to find a path-like string
                    for word in line_stripped.split():
                        if word.endswith(".md"):
                            candidate = VAULT_PATH / word
                            if candidate.exists():
                                created_path = candidate
                                break
                    if created_path:
                        break

            if created_path and created_path.exists():
                try:
                    content = created_path.read_text(encoding="utf-8")
                    additions = []

                    if body:
                        additions.append(f"\n## Core Idea\n\n{body}\n")

                    if connections:
                        links_text = "\n".join(f"- {conn}" for conn in connections)
                        additions.append(f"\n## Connections\n\n{links_text}\n")

                    if source and f"[[{source.strip('[]')}]]" not in content:
                        additions.append(f"\n## Source\n\n- {source}\n")

                    if additions:
                        content += "\n".join(additions)
                        created_path.write_text(content, encoding="utf-8")
                except Exception as e:
                    result += f"\n(Warning: created note but failed to append body/connections: {e})"

        return result
