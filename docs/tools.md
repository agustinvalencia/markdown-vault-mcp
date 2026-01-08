# MCP Tools Reference

This document describes all available tools provided by the markdown-vault-mcp server.

## Overview

The server provides 14 tools organized into 5 categories:

| Category | Tools | Description |
|----------|-------|-------------|
| [List](#list-tools) | 2 | Browse vault structure |
| [Read](#read-tools) | 3 | Read note content and metadata |
| [Search](#search-tools) | 2 | Find notes by content |
| [Update](#update-tools) | 3 | Modify notes and metadata |
| [Zettelkasten](#zettelkasten-tools) | 4 | Navigate the knowledge graph |

---

## List Tools

Tools for browsing the vault structure.

### `list_notes`

List all markdown notes in a folder.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `folder` | string | No | `""` (root) | Subfolder to list notes from |

**Returns:** Newline-separated list of note paths relative to vault root.

**Example:**
```
Input: folder="projects"
Output:
projects/website-redesign.md
projects/api-migration.md
projects/archive/old-project.md
```

---

### `list_folders`

List subfolders in a directory.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `folder` | string | No | `""` (root) | Parent folder to list subfolders from |

**Returns:** Newline-separated list of folder paths relative to vault root.

**Example:**
```
Input: folder=""
Output:
projects
daily
references
```

---

## Read Tools

Tools for reading note content and metadata.

### `read_note`

Read the full content of a note.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `note_path` | string | Yes | Path to note relative to vault root |

**Returns:** Full content of the note including frontmatter.

**Example:**
```
Input: note_path="projects/website.md"
Output:
---
title: Website Redesign
status: active
---

# Website Redesign

Project notes here...
```

---

### `read_note_excerpt`

Read the beginning of a note with a line limit.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `note_path` | string | Yes | - | Path to note relative to vault root |
| `max_lines` | integer | No | 50 | Maximum lines to return |

**Returns:** First N lines of the note. If truncated, includes count of remaining lines.

**Example:**
```
Input: note_path="long-note.md", max_lines=10
Output:
---
title: Long Note
---

# Introduction

First few paragraphs...

(150 more lines)
```

---

### `get_metadata`

Get the YAML frontmatter metadata from a note as JSON.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `note_path` | string | Yes | Path to note relative to vault root |

**Returns:** JSON object with all frontmatter fields.

**Example:**
```
Input: note_path="projects/website.md"
Output:
{
  "title": "Website Redesign",
  "status": "active",
  "tags": ["project", "web"],
  "created": "2024-01-15"
}
```

---

## Search Tools

Tools for finding notes by content.

### `search_notes`

Search for notes containing specific text (case-insensitive).

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `query` | string | Yes | - | Text to search for |
| `folder` | string | No | `""` (root) | Subfolder to limit search scope |

**Returns:** Newline-separated list of matching note paths.

**Example:**
```
Input: query="API endpoint", folder="projects"
Output:
projects/api-migration.md
projects/backend-docs.md
```

---

### `search_notes_with_context`

Search for notes and return matches with surrounding context.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `query` | string | Yes | - | Text to search for |
| `folder` | string | No | `""` (root) | Subfolder to limit search scope |
| `context_lines` | integer | No | 2 | Lines of context before/after match |

**Returns:** Formatted results showing each match with surrounding lines.

**Example:**
```
Input: query="TODO", context_lines=1
Output:
=== daily/2024-01-15.md ===
Line 23:
  - Review PR comments
  - TODO: Update documentation
  - Send weekly report

=== projects/website.md ===
Line 45:
  ## Next Steps
  TODO: Add authentication
  - Research OAuth providers
```

---

## Update Tools

Tools for modifying notes and metadata.

### `update_metadata`

Update or add frontmatter fields in a note. Preserves existing fields not specified in the update.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `note_path` | string | Yes | Path to note relative to vault root |
| `metadata_json` | string | Yes | JSON object with fields to update/add |

**Returns:** Success message or error description.

**Example:**
```
Input: note_path="projects/website.md", metadata_json='{"status": "completed", "completed_date": "2024-01-20"}'
Result: Updates frontmatter, preserving existing fields like title and tags
```

---

### `append_to_note`

Append content to a note, optionally within a specific subsection.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `note_path` | string | Yes | - | Path to note relative to vault root |
| `content` | string | Yes | - | Content to append |
| `subsection` | string | No | - | Optional heading to append under |

**Returns:** Success message or error description.

**Example:**
```
Input: note_path="daily/2024-01-15.md", content="\n## Evening Update\n\nFinished the API review."
Result: Content appended to end of note
```

---

### `add_to_daily_note`

Append content to today's daily note. Automatically creates the note and directory if they don't exist.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `content` | string | Yes | - | Content to append |
| `subsection` | string | No | - | Optional heading to append under |

**Returns:** Success message or error description.

**Configuration:**
- Uses `daily_format` from `mcp_config.toml` if present (default: `daily/YYYY-MM-DD.md`).

**Example:**
```
Input: content="Finished the API review", subsection="Evening Update"
Result: Appended content to subsection 'Evening Update' in daily/2026-01-08.md
```

---

### `update_task_status`

Toggle a markdown task checkbox in a note.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `note_path` | string | Yes | Path to note relative to vault root |
| `task_pattern` | string | Yes | Text pattern to identify the task |
| `completed` | boolean | Yes | `true` to mark `[x]`, `false` to mark `[ ]` |

**Returns:** Success message or error description.

**Example:**
```
Input: note_path="daily/2024-01-15.md", task_pattern="Review PR", completed=true
Before: - [ ] Review PR comments
After:  - [x] Review PR comments
```

---

## Zettelkasten Tools

Tools for navigating the knowledge graph and understanding note relationships.

### `find_backlinks`

Find all notes that link to the specified note.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `note_path` | string | Yes | Path to note relative to vault root |

**Returns:** Newline-separated list of notes that contain links to this note.

**Supported link formats:**
- Wikilinks: `[[note]]` or `[[note|alias]]`
- Markdown links: `[text](note.md)`

**Example:**
```
Input: note_path="concepts/programming.md"
Output:
concepts/python.md
concepts/rust.md
projects/learning-plan.md
```

---

### `find_outgoing_links`

Find all notes that the specified note links to.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `note_path` | string | Yes | Path to note relative to vault root |

**Returns:** Newline-separated list of linked notes. Broken links are marked with "(not found)".

**Example:**
```
Input: note_path="projects/website.md"
Output:
concepts/web-development.md
references/oauth-spec.md
deleted-note.md (not found)
```

---

### `find_orphan_notes`

Find notes with no incoming or outgoing links (isolated notes).

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `folder` | string | No | `""` (root) | Subfolder to limit search scope |

**Returns:** Newline-separated list of orphan notes.

**Example:**
```
Input: folder=""
Output:
scratch/random-idea.md
archive/old-draft.md
```

---

### `suggest_related_notes`

Suggest related notes based on shared outgoing links.

Notes that link to the same targets are likely related. This tool finds notes with the most link overlap.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `note_path` | string | Yes | - | Path to note relative to vault root |
| `max_suggestions` | integer | No | 5 | Maximum suggestions to return |

**Returns:** List of related notes with shared link count.

**Example:**
```
Input: note_path="concepts/python.md", max_suggestions=3
Output:
concepts/rust.md (3 shared links)
projects/learning-plan.md (2 shared links)
daily/2024-01-10.md (1 shared link)
```

---

## Error Handling

All tools return error messages as strings rather than raising exceptions. Common error patterns:

| Error | Cause |
|-------|-------|
| `"Note not found: {path}"` | The specified note doesn't exist |
| `"Invalid path, must be within vault: {path}"` | Path traversal attempt outside vault |
| `"Only markdown files are supported"` | Attempted to read a non-.md file |
| `"Invalid JSON: {details}"` | Malformed JSON in metadata_json parameter |
| `"No backlinks found for {path}"` | Note has no incoming links |
