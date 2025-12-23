# pyright: reportUnusedFunction=false
# pyright is being too picky in these ones as the callers are outside of this context

import json
import re
from typing import Any

from fastmcp import FastMCP

from ..config import VAULT_PATH, validate_file
from .frontmatter import update_note_metadata


def register_update_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def update_metadata(note_path: str, metadata_json: str) -> str:
        """Update frontmatter metadata in a note, preserving existing fields.

        Args:
            note_path: Path to the note relative to vault root
            metadata_json: JSON string with metadata fields to update/add

        Returns:
            Success message or error description
        """
        full_path = VAULT_PATH / note_path
        result = validate_file(full_path)
        if not result.ok:
            return result.msg

        try:
            updates: dict[str, Any] = json.loads(metadata_json)
        except json.JSONDecodeError as e:
            return f"Invalid JSON: {e}"

        if not isinstance(updates, dict):
            return "metadata_json must be a JSON object"

        try:
            updated_content = update_note_metadata(full_path, updates)
            full_path.write_text(updated_content, encoding="utf-8")
            return f"Updated metadata in {note_path}"
        except Exception as e:
            return f"Error updating metadata: {e}"

    @mcp.tool()
    def append_to_note(note_path: str, content: str) -> str:
        """Append content to the end of a note.

        Args:
            note_path: Path to the note relative to vault root
            content: Content to append (will be added after a newline)

        Returns:
            Success message or error description
        """
        full_path = VAULT_PATH / note_path
        result = validate_file(full_path)
        if not result.ok:
            return result.msg

        try:
            existing = full_path.read_text(encoding="utf-8")
            # Ensure there's a newline before appending
            if existing and not existing.endswith("\n"):
                existing += "\n"
            new_content = existing + content
            full_path.write_text(new_content, encoding="utf-8")
            return f"Appended content to {note_path}"
        except Exception as e:
            return f"Error appending to note: {e}"

    @mcp.tool()
    def update_task_status(note_path: str, task_pattern: str, completed: bool) -> str:
        """Update the status of a task checkbox in a note.

        Args:
            note_path: Path to the note relative to vault root
            task_pattern: Text pattern to identify the task (matches task content)
            completed: True to mark as completed [x], False to mark as incomplete [ ]

        Returns:
            Success message or error description
        """
        full_path = VAULT_PATH / note_path
        result = validate_file(full_path)
        if not result.ok:
            return result.msg

        try:
            content = full_path.read_text(encoding="utf-8")

            # Pattern matches markdown task: - [ ] or - [x] followed by text
            # We look for tasks containing the task_pattern
            task_regex = re.compile(
                r"^(\s*[-*]\s*)\[([ xX])\](\s+" + re.escape(task_pattern) + r".*?)$",
                re.MULTILINE,
            )

            match = task_regex.search(content)
            if not match:
                # Try a more lenient search - pattern anywhere in task text
                task_regex_lenient = re.compile(
                    r"^(\s*[-*]\s*)\[([ xX])\](\s+.*?" + re.escape(task_pattern) + r".*?)$",
                    re.MULTILINE,
                )
                match = task_regex_lenient.search(content)

            if not match:
                return f"No task found matching: {task_pattern}"

            new_status = "x" if completed else " "
            replacement = f"{match.group(1)}[{new_status}]{match.group(3)}"
            new_content = content[: match.start()] + replacement + content[match.end() :]

            full_path.write_text(new_content, encoding="utf-8")

            status_text = "completed" if completed else "incomplete"
            return f"Marked task as {status_text}: {task_pattern}"
        except Exception as e:
            return f"Error updating task: {e}"
