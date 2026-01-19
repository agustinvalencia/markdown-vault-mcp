import os
import re
import shutil
import subprocess

from ..config import VAULT_PATH


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

    # Prefix spacing
    if not prefix.endswith("\n\n"):
        if prefix.endswith("\n"):
            content_to_insert = "\n" + content_to_insert
        else:
            content_to_insert = "\n\n" + content_to_insert

    # Suffix spacing
    if suffix:
        if not content_to_insert.endswith("\n"):
            content_to_insert += "\n"
        if not content_to_insert.endswith("\n\n"):
            content_to_insert += "\n"

    return prefix + content_to_insert + suffix, False
