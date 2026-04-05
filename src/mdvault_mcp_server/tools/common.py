import json
import os
import re
import shutil
import subprocess
from datetime import date, datetime
from typing import Annotated

from pydantic import BeforeValidator

from ..config import VAULT_PATH


def _coerce_extra_vars(v: object) -> dict[str, str] | None:
    """Accept both a dict and a JSON string for extra_vars."""
    if v is None:
        return None
    if isinstance(v, dict):
        return v
    if isinstance(v, str):
        try:
            parsed = json.loads(v)
        except json.JSONDecodeError:
            msg = f"extra_vars must be a JSON object, got invalid JSON: {v!r}"
            raise ValueError(msg) from None
        if not isinstance(parsed, dict):
            msg = f"extra_vars must be a JSON object, got {type(parsed).__name__}"
            raise ValueError(msg)
        return parsed
    msg = f"extra_vars must be a dict or JSON string, got {type(v).__name__}"
    raise ValueError(msg)


ExtraVars = Annotated[dict[str, str] | None, BeforeValidator(_coerce_extra_vars)]


def format_log_entry(content: str, target_date: date | str | None = None) -> str:
    """
    Formats a log entry with a timestamp.

    If *target_date* is today (or None and the caller doesn't know the
    target), the behaviour differs:
      - target_date == today  → short format:  ``- **HH:MM**: Content``
      - target_date is None or a different date → long format with date
        link: ``- [[YYYY-MM-DD]] - HH:MM: Content``
    """
    now = datetime.now()
    time_str = now.strftime("%H:%M")

    # Normalise target_date to a date object (if provided as str)
    if isinstance(target_date, str):
        target_date = date.fromisoformat(target_date)

    if target_date is not None and target_date == date.today():
        return f"- **{time_str}**: {content}"

    date_str = now.strftime("%Y-%m-%d")
    return f"- [[{date_str}]] - {time_str}: {content}"


def run_mdv_command(args: list[str]) -> str:
    """
    Helper to run mdv CLI commands.
    """
    mdv_path = shutil.which("mdv")
    if not mdv_path:
        return "Error: 'mdv' executable not found in PATH."

    command = [mdv_path, *args]
    
    # Ensure the vault path is passed to the CLI via environment
    env = os.environ.copy()
    if "MARKDOWN_VAULT_PATH" not in env:
        env["MARKDOWN_VAULT_PATH"] = str(VAULT_PATH)

    try:
        result = subprocess.run(
            command, capture_output=True, text=True, env=env, check=False
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error executing command: {' '.join(command)}\n{result.stderr}\n{result.stdout}"
            
    except Exception as e:
        return f"Failed to execute mdv command: {e}"


DEFAULT_PROTECTED_TAIL_SECTIONS: list[str] = ["Logs", "Closing Thoughts"]


def _find_earliest_protected_section(existing: str, protected: list[str]) -> int | None:
    """Return the character offset of the earliest protected section heading, or None."""
    earliest: int | None = None
    for section_name in protected:
        pattern = re.compile(
            r"^#{1,6}\s+" + re.escape(section_name) + r"\s*$", re.MULTILINE
        )
        match = pattern.search(existing)
        if match and (earliest is None or match.start() < earliest):
            earliest = match.start()
    return earliest


def _protected_insertion_point(existing: str, protected: list[str]) -> int:
    """Return the offset where new content should be inserted, respecting protected tails."""
    if protected:
        earliest = _find_earliest_protected_section(existing, protected)
        if earliest is not None:
            return earliest
    return len(existing)


def _insert_raw_content(existing: str, content: str, protected: list[str]) -> str:
    """Insert raw content (no subsection) before protected tail sections."""
    insertion_point = _protected_insertion_point(existing, protected)
    prefix = existing[:insertion_point]
    suffix = existing[insertion_point:]

    if prefix and not prefix.endswith("\n"):
        prefix += "\n"
    if suffix and not content.endswith("\n"):
        content += "\n"
    if suffix and not content.endswith("\n\n"):
        content += "\n"

    return prefix + content + suffix


def _create_new_subsection(
    existing: str, content: str, subsection: str, protected: list[str],
) -> str:
    """Create a new subsection, inserting before protected tail sections."""
    insertion_point = _protected_insertion_point(existing, protected)
    prefix = existing[:insertion_point]
    suffix = existing[insertion_point:]

    if prefix and not prefix.endswith("\n"):
        prefix += "\n"
    if prefix and not prefix.endswith("\n\n"):
        prefix += "\n"

    new_section = f"## {subsection}\n\n{content}"
    if suffix:
        if not new_section.endswith("\n"):
            new_section += "\n"
        if not new_section.endswith("\n\n"):
            new_section += "\n"

    return prefix + new_section + suffix


def append_content_logic(
    existing: str,
    content: str,
    subsection: str | None,
    protected_tail_sections: list[str] | None = None,
) -> tuple[str, bool]:
    """
    Appends content to existing markdown.
    Returns (new_content, created_subsection).

    When *protected_tail_sections* is provided, new subsections (and raw
    appends without a subsection) are inserted before the first protected
    section rather than at EOF.  This keeps sections like "Logs" and
    "Closing Thoughts" at the bottom of the note.
    """
    protected = protected_tail_sections or []

    if not subsection:
        return _insert_raw_content(existing, content, protected), False

    pattern = re.compile(r"^(#{1,6})\s+" + re.escape(subsection) + r"\s*$", re.MULTILINE)
    match = pattern.search(existing)

    if not match:
        return _create_new_subsection(existing, content, subsection, protected), True

    # Subsection found
    header_level = len(match.group(1))
    end_of_header_line = match.end()

    next_section_pattern = re.compile(r"^(#{1," + str(header_level) + r"})\s+", re.MULTILINE)
    next_match = next_section_pattern.search(existing, end_of_header_line)

    insertion_point = len(existing)
    if next_match:
        insertion_point = next_match.start()

    prefix = existing[:insertion_point]
    suffix = existing[insertion_point:]

    # Normalise trailing whitespace on prefix: collapse any trailing blank
    # lines down to a single newline so that new content sits directly
    # after existing entries (no spurious blank line).  The suffix spacing
    # below re-adds the required gap before the next section.
    if prefix.endswith("\n"):
        prefix = prefix.rstrip("\n") + "\n"

    content_to_insert = content

    # Prefix spacing: ensure content starts on a new line, but don't add
    # a blank line between consecutive entries in the same section.
    if not prefix.endswith("\n"):
        content_to_insert = "\n" + content_to_insert

    # Suffix spacing
    if suffix:
        if not content_to_insert.endswith("\n"):
            content_to_insert += "\n"
        if not content_to_insert.endswith("\n\n"):
            content_to_insert += "\n"

    return prefix + content_to_insert + suffix, False
