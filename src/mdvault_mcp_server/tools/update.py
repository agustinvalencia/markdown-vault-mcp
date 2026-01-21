# pyright: reportUnusedFunction=false
# pyright is being too picky in these ones as the callers are outside of this context

import json
import re
from typing import Any

from fastmcp import FastMCP

from ..config import VAULT_PATH, validate_file
from .common import append_content_logic, run_mdv_command
from .frontmatter import update_note_content, update_note_metadata


def register_update_tools(mcp: FastMCP) -> None:  # noqa: PLR0915
    @mcp.tool()
    def capture_content(
        name: str,
        text: str,
        extra_vars: dict[str, str] | None = None,
    ) -> str:
        """Capture content into a configured capture location.

        Args:
            name: Name of the capture (e.g., 'inbox', 'log').
            text: Main content to capture (passed as 'text' variable).
            extra_vars: Optional dictionary of additional variables.

        Returns:
            Result of the capture command.
        """
        args = ["capture", name, "--batch", "--var", f"text={text}"]
        if extra_vars:
            for k, v in extra_vars.items():
                args.extend(["--var", f"{k}={v}"])
        return run_mdv_command(args)

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
    def append_to_note(note_path: str, content: str, subsection: str | None = None) -> str:
        """Append content to a note, optionally within a specific subsection.

        Args:
            note_path: Path to the note relative to vault root
            content: Content to append
            subsection: Optional heading title to append under. If not found, creates it at end.

        Returns:
            Success message or error description
        """
        full_path = VAULT_PATH / note_path
        result = validate_file(full_path)
        if not result.ok:
            return result.msg

        try:
            def modifier(body: str) -> tuple[str, str]:
                new_body, created_new = append_content_logic(body, content, subsection)
                
                if created_new:
                    msg = f"Created subsection '{subsection}' and appended content in {note_path}"
                elif subsection:
                    msg = f"Appended content to subsection '{subsection}' in {note_path}"
                else:
                    msg = f"Appended content to {note_path}"
                return new_body, msg

            return update_note_content(full_path, modifier)

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
            def modifier(body: str) -> tuple[str, str]:
                # Pattern matches markdown task: - [ ] or - [x] followed by text
                # We look for tasks containing the task_pattern
                task_regex = re.compile(
                    r"^(\s*[-*]\s*)\[([ xX])\](\s+" + re.escape(task_pattern) + r".*?)$",
                    re.MULTILINE,
                )

                match = task_regex.search(body)
                if not match:
                    # Try a more lenient search - pattern anywhere in task text
                    task_regex_lenient = re.compile(
                        r"^(\s*[-*]\s*)\[([ xX])\](\s+.*?" + re.escape(task_pattern) + r".*?)$",
                        re.MULTILINE,
                    )
                    match = task_regex_lenient.search(body)

                if not match:
                    # Return original body and error message
                    # But wait, helper expects success. 
                    # If we raise exception here, it will be caught by the try/except block
                    raise ValueError(f"No task found matching: {task_pattern}")

                new_status = "x" if completed else " "
                replacement = f"{match.group(1)}[{new_status}]{match.group(3)}"
                new_body = body[: match.start()] + replacement + body[match.end() :]

                status_text = "completed" if completed else "incomplete"
                return new_body, f"Marked task as {status_text}: {task_pattern}"

            return update_note_content(full_path, modifier)

        except Exception as e:
            return f"Error updating task: {e}"