# Test Plan & Coverage Strategy

**Objective:** Increase code coverage from ~16% to >80% to ensure stability and prevent regressions, prioritizing critical data-handling components.

## 1. Testing Infrastructure
- **Tooling:** `pytest` for test runner, `pytest-cov` for coverage analysis.
- **Location:** `tests/` directory, mirroring `src/` structure where possible.
- **Command:** `uv run pytest --cov=src --cov-report=term-missing tests/`

## 2. Priority Levels

### Phase 1: Core Utilities & Data Integrity (Current Focus)
*Why: These modules handle file I/O, parsing, and configuration. Bugs here corrupt data.*
- [x] **`tools/frontmatter.py`** (Partial coverage exists)
    - [ ] Test `write_note` (creation logic).
    - [ ] Test `update_note_content` (modifier function logic).
- [ ] **`tools/common.py`**
    - [ ] Test `format_log_entry`.
    - [ ] Test `append_content_logic` (crucial for ensuring note structure isn't broken when appending).
    - [ ] Mock `run_mdv_command` to test failure/success paths without running actual CLI.
- [ ] **`config.py`**
    - [ ] Test validation logic for paths (`validate_file`).

### Phase 2: Read/Write Operations
*Why: High-frequency user interactions.*
- [ ] **`tools/read.py`**
    - [ ] Test `read_note` handles missing files gracefully.
    - [ ] Test `read_note_excerpt` logic for truncation.
    - [ ] Test `get_metadata` JSON extraction.
- [ ] **`tools/update.py`**
    - [ ] Test `append_to_note` integration with `append_content_logic`.
    - [ ] Test `update_task_status` regex logic (various task formats).

### Phase 3: Complex Logic (Tasks, Projects, Zettelkasten)
*Why: Complex parsing logic that is prone to edge cases.*
- [ ] **`tools/tasks_projects.py`**
    - [ ] Test `resolve_project_path` matching logic.
    - [ ] Test `get_project_info` metric calculation.
    - [ ] Test `create_task` argument handling.
- [ ] **`tools/zettelkasten.py`**
    - [ ] Test backlink parsing regex.
    - [ ] Test orphan detection logic.

### Phase 4: Integration & Server
*Why: Ensures wiring is correct.*
- [ ] **`server.py`** / **`__main__.py`**
    - [ ] Smoke tests to ensure server starts and registers tools.

## 3. Implementation Guidelines
- **Mocking:** Use `unittest.mock` to mock filesystem operations (`pathlib.Path.read_text`, `write_text`) and subprocess calls (`subprocess.run`) to avoid touching the actual vault during unit tests.
- **Fixtures:** Use `pytest` fixtures for:
    - Temporary directories/vaults (`tmp_path`).
    - Dummy markdown content.
- **Regression:** Every bug fix must include a reproduction test case (as demonstrated with `test_frontmatter.py`).

## 4. Immediate Next Steps
1. Create `tests/test_common.py` to cover `append_content_logic`.
2. Create `tests/test_update.py` to cover `update_task_status`.
