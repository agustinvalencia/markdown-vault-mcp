"""Entry point for running the Obsidian MCP server."""

from .server import create_server


def main() -> None:
    """Create and run the MCP server."""
    mcp = create_server()
    mcp.run()


if __name__ == "__main__":
    main()
