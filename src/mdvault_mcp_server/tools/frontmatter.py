# pyright: reportUnknownMemberType=false
# python-frontmatter doesn't have type stubs

from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

import frontmatter


def get_current_timestamp() -> str:
    """Return current timestamp in ISO format."""
    return datetime.now().isoformat()


def parse_note(path: Path) -> tuple[dict[str, Any], str]:
    """
    Parse a markdown note into frontmatter metadata and content.

    Args:
        path: Path to the markdown file

    Returns:
        Tuple of (metadata dict, content string)
    """
    post = frontmatter.load(str(path))
    return dict(post.metadata), post.content


def update_note_metadata(path: Path, updates: dict[str, Any]) -> str:
    """
    Update frontmatter metadata in a note, preserving existing fields.
    Automatically updates 'updated_at' field.

    Args:
        path: Path to the markdown file
        updates: Dictionary of metadata fields to update/add

    Returns:
        The updated file content as a string
    """
    post = frontmatter.load(str(path))

    for key, value in updates.items():
        post.metadata[key] = value

    post.metadata["updated_at"] = get_current_timestamp()

    return frontmatter.dumps(post)


def write_note(path: Path, metadata: dict[str, Any], content: str) -> str:
    """
    Write a note with frontmatter metadata and content.
    Automatically adds 'updated_at' field if not present.

    Args:
        path: Path to the markdown file
        metadata: Dictionary of metadata fields
        content: The markdown content

    Returns:
        The file content as a string
    """
    if "updated_at" not in metadata:
        metadata["updated_at"] = get_current_timestamp()
    if "created" not in metadata:
        metadata["created"] = datetime.now().date().isoformat()
        
    post = frontmatter.Post(content, **metadata)
    return frontmatter.dumps(post)


def update_note_content(path: Path, modifier_fn: Callable[[str], tuple[str, Any]]) -> Any:
    """
    Update note content using a modifier function.
    Automatically updates 'updated_at' field.

    Args:
        path: Path to the markdown file
        modifier_fn: Function that takes current content string and returns (new_content, result)
                     The result is what will be returned to the caller.

    Returns:
        The second element of the tuple returned by modifier_fn
    """
    post = frontmatter.load(str(path))
    
    # Run the modifier on the body content
    new_content, result = modifier_fn(post.content)
    post.content = new_content
    
    # Update timestamp
    post.metadata["updated_at"] = get_current_timestamp()
    
    # Write back
    path.write_text(frontmatter.dumps(post), encoding="utf-8")
    
    return result