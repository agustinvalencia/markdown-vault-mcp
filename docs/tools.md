# MCP Tools Reference

This document describes all available tools provided by the markdown-vault-mcp server.

> **Compatibility:** This version is compatible with mdvault v0.3.5+

## Overview

The server provides tools organized into 10 categories:

| Category | Tools | Description |
|----------|-------|-------------|
| [List](#list-tools) | 2 | Browse vault structure |
| [Read](#read-tools) | 3 | Read note content and metadata |
| [Search](#search-tools) | 2 | Find notes by content |
| [Update](#update-tools) | 5 | Modify notes and metadata |
| [Daily](#daily-tools) | 2 | Daily note operations |
| [Zettelkasten](#zettelkasten-tools) | 4 | Navigate the knowledge graph |
| [Context](#context-tools) | 5 | Activity context and focus management |
| [Tasks & Projects](#tasks--projects-tools) | 13 | Manage tasks, projects, and meetings |
| [Macros](#macro-tools) | 1 | Run automated workflows |
| [Management](#management-tools) | 5 | Vault maintenance, status, and reporting |

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

### `capture_content`

Capture content into a configured capture location.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `name` | string | Yes | - | Name of the capture (e.g., 'inbox') |
| `text` | string | Yes | - | Main content to capture |
| `extra_vars` | dict | No | - | Additional variables for the capture |

**Returns:** Result of the capture command.

---

## Daily Tools

Tools for managing daily notes.

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

### `log_to_daily_note`

Append a timestamped log entry to today's daily note.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `content` | string | Yes | The log message to append |

**Returns:** Success message or error description.

**Format:** `- [[YYYY-MM-DD]] - HH:MM: Content`

**Example:**
```
Input: content="Started working on OAuth implementation"
Result: Appended log entry to 'Logs' section in daily/2026-01-08.md
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

## Context Tools

Tools for managing focus and retrieving activity context.

### `get_active_context`

Get the current focus context for the vault as JSON.

**Returns:** JSON with focused project, note, and timestamp.

**Example:**
```json
{
  "project": "MCP",
  "note": "Working on OAuth implementation",
  "started_at": "2026-01-18T10:30:00+01:00"
}
```

---

### `get_context_day`

Get activity context for a specific day including tasks, notes modified, and logs.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `date` | string | No | `"today"` | Date in YYYY-MM-DD format, or 'today', 'yesterday' |

**Returns:** JSON with day's activity summary.

---

### `get_context_week`

Get activity context for a specific week.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `week` | string | No | current | Week identifier ('current', 'last', YYYY-Wxx) |

**Returns:** JSON with week's activity summary.

---

### `get_context_note`

Get rich context for a specific note including metadata, sections, activity, and references.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `note_path` | string | Yes | - | Path to note relative to vault root |
| `activity_days` | integer | No | 7 | Days of activity history to include |

**Returns:** JSON with comprehensive note context.

---

### `get_context_focus`

Get context for the currently focused project including task counts and recent activity.

**Returns:** JSON with focused project details.

---

### `set_focus`

Set the active project focus.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `project` | string | Yes | - | Project ID or name to focus on |
| `note` | string | No | - | Optional note about current work |

**Returns:** Success message or error description.

**Example:**
```
Input: project="MCP", note="Implementing new tools"
Output: Focus set to: MCP
```

---

### `clear_focus`

Clear the active project focus.

**Returns:** Success message.

---

## Tasks & Projects Tools

Tools for managing tasks and projects using the `mdv` CLI.

### `list_projects`

List all projects with task counts.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `status_filter` | string | No | - | Filter by status (e.g., 'active', 'archived') |

**Returns:** Table of projects with task counts.

### `get_project_info`

Get rich context for a project using mdvault's context command. Includes metadata, sections, activity history, and references.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `project_name` | string | Yes | Name or ID of the project |

**Returns:** JSON object with comprehensive project context (same format as `get_context_note`).

### `get_project_status`

Show detailed status of a specific project (Kanban view).

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `project_name` | string | Yes | Name or ID of the project |

**Returns:** Kanban-style view of tasks in the project.

### `get_project_progress`

Show progress metrics for a project or all projects.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `project_name` | string | No | - | Specific project to get metrics for |

**Returns:** Progress bars, completion stats, and velocity metrics.

### `create_project`

Create a new project.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `title` | string | Yes | - | Title of the new project |
| `context` | string | Yes | - | Project context (e.g. 'work', 'personal') |
| `description` | string | No | - | Optional description (max 1024 chars) |
| `status` | string | No | - | Project status (e.g. 'open', 'closed') |
| `extra_vars` | dict | No | - | Additional variables for the template |

**Returns:** Result of the creation command.

### `list_tasks`

List tasks with optional filters.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `project_filter` | string | No | - | Filter tasks by project name |
| `status_filter` | string | No | - | Filter tasks by status |

**Returns:** Table of matching tasks.

### `get_task_details`

Show details for a specific task.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `task_id` | string | Yes | The ID of the task |

**Returns:** Detailed task information.

### `create_task`

Create a new task. If no project is specified, mdvault automatically uses the active focus context. Context inheritance from the project is handled automatically.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `title` | string | Yes | - | Title of the task |
| `description` | string | No | - | Optional description (max 1024 chars) |
| `project` | string | No | (Active Focus) | Project name - auto-inherits from focus if omitted |
| `due_date` | string | No | - | Optional due date (YYYY-MM-DD) |
| `priority` | string | No | - | Optional priority (e.g. 'low', 'medium', 'high') |
| `status` | string | No | - | Optional status (e.g. 'todo', 'doing', 'done') |
| `extra_vars` | dict | No | - | Additional variables for the template |

**Returns:** Result of the creation command.

---

### `create_meeting`

Create a new meeting note. Meeting notes have auto-generated IDs (MTG-YYYY-MM-DD-NNN) and are stored in the Meetings/ folder. Creation is logged to the daily note.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `title` | string | Yes | - | Title of the meeting (e.g. "Team Sync") |
| `attendees` | string | No | - | Who's attending (e.g. "Alice, Bob") |
| `date` | string | No | today | Meeting date in YYYY-MM-DD format |
| `extra_vars` | dict | No | - | Additional variables for the template |

**Returns:** Result including the generated meeting ID.

**Example:**
```
Input: title="Design Review", attendees="Alice, Bob"
Output: Created meeting: Meetings/MTG-2026-02-03-001.md
```

### `complete_task`

Mark a task as done.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `task_path` | string | Yes | - | Path to task file |
| `summary` | string | No | - | Optional completion summary |

**Returns:** Confirmation message.

---

### `cancel_task`

Cancel a task.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `task_path` | string | Yes | - | Path to task file |
| `reason` | string | No | - | Optional cancellation reason |

**Returns:** Confirmation message.

---

### `archive_project`

Archive a completed project. Moves project and tasks to `Projects/_archive/`, cancels open tasks, clears focus if set, and logs the event.

Only projects with `status: done` can be archived.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `project_name` | string | Yes | The project ID or folder name to archive |

**Returns:** Result of the archive operation.

**Example:**
```
Input: project_name="MCP"
Output: OK   mdv project archive
  Archived project: My Cool Project
  - 2 open tasks cancelled
  - Files moved to Projects/_archive/my-cool-project/
```

---

### `log_to_project_note`

Append a timestamped log entry to a project note's 'Logs' section.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `project_path` | string | Yes | Path to project note relative to vault root |
| `content` | string | Yes | The log message to append |

**Returns:** Success message or error description.

**Format:** `- [[YYYY-MM-DD]] - HH:MM: Content`

---

### `log_to_task_note`

Append a timestamped log entry to a task note's 'Logs' section.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `task_path` | string | Yes | Path to task note relative to vault root |
| `content` | string | Yes | The log message to append |

**Returns:** Success message or error description.

**Format:** `- [[YYYY-MM-DD]] - HH:MM: Content`

---

## Macro Tools

Tools for running automated workflows.

### `run_macro`

Run a predefined macro using the mdv CLI.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `name` | string | Yes | - | Name of the macro to run |
| `args` | list[str] | No | - | Optional arguments for the macro |
| `variables` | dict | No | - | Optional variables to pass to the macro |

**Returns:** Output of the macro execution.

**Example:**
```
Input: name="daily-standup"
Output: Macro 'daily-standup' executed successfully.
```

---

## Management Tools

Tools for vault maintenance and status.

### `rename_note`

Rename a note and update all references (backlinks) to it.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `source` | string | Yes | - | Source file path |
| `destination` | string | Yes | - | Destination file path |

**Returns:** Result of the rename operation.

### `validate_vault`

Validate all notes in the vault against their type definitions.

**Returns:** Validation report.

### `list_templates`

List available templates that can be used with create_project/create_task.

**Returns:** List of template names.

### `get_daily_dashboard`

Get the daily dashboard summary (today's tasks, events, etc).

**Returns:** The output of 'mdv today'.

---

### `get_activity_report`

Generate an activity report for a specific time period. Shows tasks completed/created, activity heatmap, and productivity metrics.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `month` | string | No* | - | Month in YYYY-MM format (e.g. '2025-01') |
| `week` | string | No* | - | Week in YYYY-Wxx format (e.g. '2025-W05') |

*Must specify exactly one of `month` or `week`.

**Returns:** Activity report for the specified period.

**Example:**
```
Input: month="2026-01"
Output: Activity report showing tasks, completions, and heatmap for January 2026
```

---

## Error Handling

All tools return error messages as strings rather than raising exceptions. Common error patterns:

| Error | Cause |
|-------|-------|
| "Note not found: {path}" | The specified note doesn\'t exist |
| "Invalid path, must be within vault: {path}" | Path traversal attempt outside vault |
| "Only markdown files are supported" | Attempted to read a non-.md file |
| "Invalid JSON: {details}" | Malformed JSON in metadata_json parameter |
| "No backlinks found for {path}" | Note has no incoming links |
| "Error: 'mdv' executable not found" | The mdv CLI tool is not installed or not in PATH |
