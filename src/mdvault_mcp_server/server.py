from fastmcp import FastMCP

from .tools import (
    register_daily_tools,
    register_list_tools,
    register_read_tools,
    register_search_tools,
    register_update_tools,
    register_zettelkasten_tools,
)


def create_server() -> FastMCP:
    """
    Create and configure the Markdown MCP server.

    Returns:
        Configured FastMCP server instance
    """
    mcp = FastMCP("Markdown Vault")

    # Register all tool groups
    register_list_tools(mcp)
    register_read_tools(mcp)
    register_search_tools(mcp)
    register_update_tools(mcp)
    register_zettelkasten_tools(mcp)
    register_daily_tools(mcp)

    return mcp
