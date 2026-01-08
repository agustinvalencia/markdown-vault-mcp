import re


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
