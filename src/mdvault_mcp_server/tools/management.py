from fastmcp import FastMCP

from .common import run_mdv_command


def register_management_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def rename_note(source: str, destination: str) -> str:
        """Rename a note and update all references (backlinks) to it.
        
        This is safer than moving files directly as it preserves link integrity.

        Args:
            source: Source file path relative to vault root (e.g. 'inbox/draft.md')
            destination: Destination file path relative to vault root (e.g. 'notes/final.md')

        Returns:
            Result of the rename operation.
        """
        return run_mdv_command(["rename", source, destination, "--yes"])

    @mcp.tool()
    def validate_vault() -> str:
        """Validate all notes in the vault against their type definitions.
        
        Checks for missing required frontmatter fields and other consistency issues.

        Returns:
            Validation report.
        """
        return run_mdv_command(["validate"])

    @mcp.tool()
    def list_templates() -> str:
        """List available templates that can be used with create_project/create_task.

        Returns:
            List of template names.
        """
        return run_mdv_command(["list-templates"])

    @mcp.tool()
    def get_daily_dashboard() -> str:
        """Get the daily dashboard summary (today's tasks, events, etc).

        Returns:
            The output of 'mdv today', summarizing the day.
        """
        return run_mdv_command(["today"])
