from fastmcp import FastMCP

from .tools import (
    register_context_tools,
    register_daily_tools,
    register_list_tools,
    register_macro_tools,
    register_management_tools,
    register_read_tools,
    register_search_tools,
    register_tasks_projects_tools,
    register_update_tools,
    register_zettelkasten_tools,
)


def create_server() -> FastMCP:
    """
    Create and configure the Markdown MCP server.

    Returns:
        Configured FastMCP server instance
    """
    from .config import require_vault_path

    require_vault_path()  # Fail fast if vault not configured

    mcp = FastMCP("Markdown Vault")

    # Register all tool groups
    register_list_tools(mcp)
    register_read_tools(mcp)
    register_search_tools(mcp)
    register_update_tools(mcp)
    register_zettelkasten_tools(mcp)
    register_daily_tools(mcp)
    register_macro_tools(mcp)
    register_context_tools(mcp)
    register_tasks_projects_tools(mcp)
    register_management_tools(mcp)

    return mcp
