import os
import re
import shutil
import subprocess
from datetime import date, datetime

from ..config import VAULT_PATH


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


def append_content_logic(existing: str, content: str, subsection: str | None) -> tuple[str, bool]:
    """
    Appends content to existing markdown.
    Returns (new_content, created_subsection).
    """
    if not subsection:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        return existing + content, False

    pattern = re.compile(r"^(#{1,6})\s+" + re.escape(subsection) + r"\s*$", re.MULTILINE)
    match = pattern.search(existing)

    if not match:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        if existing and not existing.endswith("\n\n"):
            existing += "\n"
        return existing + f"## {subsection}\n\n{content}", True

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
