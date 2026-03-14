ci: test

test:
    uv run pytest --cov=src --cov-report=term

lint:
    uv run ruff check src/

fmt:
    uv run ruff format src/

fmt-check:
    uv run ruff format --check src/

run:
    MARKDOWN_VAULT_PATH="${MARKDOWN_VAULT_PATH}" uv run python -m mdvault_mcp_server

sync:
    uv sync --all-extras --dev
