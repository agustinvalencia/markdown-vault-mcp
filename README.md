# markdown-vault-mcp

[![CI](https://github.com/agustinvalencia/markdown-vault-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/agustinvalencia/markdown-vault-mcp/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/agustinvalencia/markdown-vault-mcp/graph/badge.svg)](https://codecov.io/gh/agustinvalencia/markdown-vault-mcp)

**Python MCP server for programmatic access to markdown-based knowledge vaults**

A sister project to [mdvault](https://github.com/agustinvalencia/mdvault), providing AI assistants with seamless access to your markdown vault through the [Model Context Protocol](https://modelcontextprotocol.io/).

## Overview

While **mdvault** provides a Rust CLI and TUI for human interaction with your vault (templates, captures, macros, validation), **markdown-vault-mcp** exposes your vault to AI assistants through MCP. Together, they form a complete toolkit for managing markdown-based knowledge systems.

```mermaid
flowchart TB
    A[AI Assistant<br/>Claude, etc.] -->|MCP| B[markdown-vault-mcp<br/>Python/FastMCP]
    B --> C[Markdown Vault<br/>.md files]
    B -.->|future| D[mdvault<br/>Rust CLI]
    D -.-> C
```

## Features

- **Browse**: List notes and folders in your vault
- **Read**: Access note content and YAML frontmatter metadata
- **Search**: Find notes by content with contextual results
- **Update**: Modify frontmatter, append content, toggle tasks
- **Navigate**: Explore backlinks, outgoing links, orphans, and related notes
- **Context**: Get activity summaries for days, weeks, and notes
- **Focus**: Set and track active project context
- **Tasks & Projects**: Create tasks, projects, and meetings with auto-generated IDs
- **Reports**: Generate activity reports and daily dashboards

## Installation

Requires Python 3.14+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/agustinvalencia/markdown-vault-mcp.git
cd markdown-vault-mcp
uv sync
```

## Configuration

Set the vault path environment variable:

```bash
export MARKDOWN_VAULT_PATH="/path/to/your/vault"
```

### Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "markdown-vault": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/markdown-vault-mcp", "python", "-m", "mdvault_mcp_server"],
      "env": {
        "MARKDOWN_VAULT_PATH": "/path/to/your/vault"
      }
    }
  }
}
```

### Claude Code

Add to your Claude Code MCP settings:

```bash
claude mcp add markdown-vault -- uv run --directory /path/to/markdown-vault-mcp python -m mdvault_mcp_server
```

## Available Tools

**42 tools** organized into 10 categories:

| Category | Key Tools |
|----------|-----------|
| **List** | `list_notes`, `list_folders` |
| **Read** | `read_note`, `read_note_excerpt`, `get_metadata` |
| **Search** | `search_notes`, `search_notes_with_context` |
| **Update** | `update_metadata`, `append_to_note`, `update_task_status`, `capture_content` |
| **Daily** | `add_to_daily_note`, `log_to_daily_note` |
| **Zettelkasten** | `find_backlinks`, `find_outgoing_links`, `find_orphan_notes`, `suggest_related_notes` |
| **Context** | `get_active_context`, `get_context_day`, `get_context_week`, `get_context_note`, `get_context_focus` |
| **Tasks & Projects** | `create_task`, `create_project`, `create_meeting`, `complete_task`, `archive_project`, `list_tasks`, `list_projects` |
| **Macros** | `run_macro` |
| **Management** | `get_daily_dashboard`, `get_activity_report`, `validate_vault`, `rename_note` |

See [docs/tools.md](docs/tools.md) for detailed documentation of each tool.

## Usage Examples

Once configured, your AI assistant can interact with your vault:

> "What notes do I have about Python?"

```
I'll search your vault for Python-related notes.

Found 5 notes mentioning Python:
- concepts/python.md
- projects/learning-plan.md
- daily/2024-01-15.md
...
```

> "Show me what links to my programming concepts note"

```
Looking for backlinks to concepts/programming.md...

3 notes link to this:
- concepts/python.md
- concepts/rust.md
- projects/learning-plan.md
```

> "Mark the 'Review PR' task as complete in today's daily note"

```
Updated daily/2024-01-20.md:
- [x] Review PR comments
```

## Development

```bash
# Install dependencies
uv sync

# Run the server (for testing)
MARKDOWN_VAULT_PATH=/path/to/vault uv run python -m mdvault_mcp_server

# Run with debug logging
MARKDOWN_VAULT_MCP_DEBUG=true uv run python -m mdvault_mcp_server

# Lint
uv run ruff check src/

# Format
uv run ruff format src/
```

## Relationship with mdvault

> **Compatibility:** Requires mdvault v0.3.5+

| Feature | mdvault (Rust) | markdown-vault-mcp (Python) |
|---------|----------------|----------------------------|
| **Purpose** | Human CLI/TUI interaction | AI assistant integration |
| **Tasks/Projects** | Yes | Yes (via mdvault CLI) |
| **Meetings** | Yes (v0.3.0+) | Yes (via mdvault CLI) |
| **Templates** | Yes | Yes (via mdvault CLI) |
| **Captures** | Yes (Lua) | Yes (via mdvault CLI) |
| **Macros** | Yes (Lua) | Yes (via mdvault CLI) |
| **Focus Mode** | Yes | Yes (via mdvault CLI) |
| **Context Queries** | Yes | Yes (via mdvault CLI) |
| **Activity Reports** | Yes | Yes (via mdvault CLI) |
| **Reading** | Via CLI commands | MCP tools + CLI |
| **Search** | SQLite index | Direct file search |
| **Link Graph** | SQLite index | Real-time parsing |
| **Validation** | Type schemas | Yes (via mdvault CLI) |

The MCP server delegates complex operations (tasks, projects, meetings, captures, macros) to the mdvault CLI, ensuring consistent behavior between human and AI interactions.

## License

MIT License - see [LICENSE](LICENSE) for details.
