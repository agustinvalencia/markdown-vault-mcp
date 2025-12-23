# pyright: reportUnknownMemberType=false
# python-frontmatter doesn't have type stubs

from pathlib import Path
from typing import Any

import frontmatter


def parse_note(path: Path) -> tuple[dict[str, Any], str]:
    """
    Parse a markdown note into frontmatter metadata and content.

    Args:
        path: Path to the markdown file

    Returns:
        Tuple of (metadata dict, content string)
    """
    post = frontmatter.load(path)
    return dict(post.metadata), post.content


def update_note_metadata(path: Path, updates: dict[str, Any]) -> str:
    """
    Update frontmatter metadata in a note, preserving existing fields.

    Args:
        path: Path to the markdown file
        updates: Dictionary of metadata fields to update/add

    Returns:
        The updated file content as a string
    """
    post = frontmatter.load(path)

    for key, value in updates.items():
        post.metadata[key] = value

    return frontmatter.dumps(post)


def write_note(path: Path, metadata: dict[str, Any], content: str) -> str:
    """
    Write a note with frontmatter metadata and content.

    Args:
        path: Path to the markdown file
        metadata: Dictionary of metadata fields
        content: The markdown content

    Returns:
        The file content as a string
    """
    post = frontmatter.Post(content, **metadata)
    return frontmatter.dumps(post)
