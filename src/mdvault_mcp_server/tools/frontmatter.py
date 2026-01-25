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


def try_parse_datetime(value: Any) -> Any:
    """Try to parse a string value as a datetime object."""
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass
    return value


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
        post.metadata[key] = try_parse_datetime(value)

    # Use datetime object for updated_at so it serializes as timestamp
    post.metadata["updated_at"] = datetime.now()

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
    # Ensure metadata values are parsed as datetimes if possible
    processed_metadata = {k: try_parse_datetime(v) for k, v in metadata.items()}

    if "updated_at" not in processed_metadata:
        processed_metadata["updated_at"] = datetime.now()
    if "created" not in processed_metadata:
        # Check if 'created_at' exists as a fallback or preference, but keep 'created' logic
        processed_metadata["created"] = datetime.now().date()
        
    post = frontmatter.Post(content, **processed_metadata)
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
    post.metadata["updated_at"] = datetime.now()
    
    # Write back
    path.write_text(frontmatter.dumps(post), encoding="utf-8")
    
    return result