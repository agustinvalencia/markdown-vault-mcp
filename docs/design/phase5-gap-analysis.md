# Phase 5 Gap Analysis — CLI Commands Needed for MCP Integration

> Generated 2026-03-08. Reference for mdvault#66.

## Current State

| Module | File Ops | CLI Coverage | Status |
|--------|----------|--------------|--------|
| list.py | rglob, iterdir | None | Full rewrite needed |
| read.py | read_text | None | Full rewrite needed |
| search.py | rglob, read_text | None | Full rewrite needed |
| update.py | write_text | capture only | Missing metadata/append/task cmds |
| daily.py | mkdir, write_text | new only | Missing append cmd |
| zettelkasten.py | rglob, read_text | new only | Not using mdv links |
| frontmatter.py | write_text | None | All direct writes |
| tasks_projects.py | None | all | Full CLI |
| context.py | None | all | Full CLI |
| management.py | None | all | Full CLI |
| macro.py | None | all | Full CLI |

## Required New CLI Commands

### Critical — Must implement to unblock Phase 5

1. **`mdv read <note_path>`** — Read and output note content
   - Support `--max-lines N`
   - Support `--metadata-only` (JSON)

2. **`mdv append <note_path> <content>`** — Append content to note
   - Support `--section "Section Name"` for subsection targeting
   - Auto-create subsection if not found
   - Example: `mdv append Journal/2026-03-08.md "- [ ] Task" --section Inbox`

3. **`mdv update-metadata <note_path> <json>`** — Update frontmatter
   - Preserve existing fields not mentioned
   - Auto-set `updated_at` timestamp
   - Validate against type schema
   - Run lifecycle hook: `on_update`

4. **`mdv task-toggle <note_path> <pattern>`** — Update checkbox status
   - Pattern matches task text content
   - Support `--done` / `--undo`

### Important — Enhancements to existing commands

5. **`mdv list --json [--folder path] [--recursive]`** — Ensure full filtering support
6. **`mdv search --content-only`** — Full-text content search matching MCP's substring semantics
7. **`mdv links --json`** — Ensure JSON output and `--backlinks-only` / `--outlinks-only` flags

## Phase 5 Refactoring Plan

### Phase 5.1: Implement CLI commands (mdvault repo)
- [ ] `mdv read`
- [ ] `mdv append`
- [ ] `mdv update-metadata`
- [ ] `mdv task-toggle`
- [ ] Enhance `mdv list` JSON + folder filtering
- [ ] Enhance `mdv links` JSON output

### Phase 5.2: Refactor MCP modules (markdown-vault-mcp repo)
- [ ] `list.py` → `mdv list --json`
- [ ] `read.py` → `mdv read`
- [ ] `search.py` → `mdv search`
- [ ] `update.py` → `mdv update-metadata`, `mdv append`, `mdv task-toggle`
- [ ] `daily.py` → `mdv append` for log/inbox operations
- [ ] `zettelkasten.py` → `mdv links --json`
- [ ] `frontmatter.py` → deprecate (replaced by CLI operations)

## Benefits
- Index consistency (all writes trigger reindex)
- Type validation on every operation
- Lifecycle hooks fire properly
- Atomic write tracking for future undo/revert
- ~1000 LOC reduction in MCP server

## Risks
- Search semantics: MCP's substring search vs CLI's FTS may differ
- Link resolution: MCP's regex vs CLI's logic may differ
- Performance: subprocess overhead vs in-process
