from fastmcp import FastMCP

from .common import run_mdv_command


def register_management_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def get_daily_dashboard() -> str:
        """Get the daily dashboard summary (today's tasks, events, etc).

        Returns:
            The output of 'mdv today', summarizing the day.
        """
        return run_mdv_command(["today"])

    @mcp.tool()
    def get_activity_report(
        month: str | None = None,
        week: str | None = None,
    ) -> str:
        """Generate a metrics-centric activity report for a time period.

        Returns aggregate productivity metrics: activity heatmap, daily
        note coverage, top completed tasks, and project activity counts.
        Supports both weekly and monthly periods (context week does not
        support monthly).

        For task-level detail (individual task lists, in-progress tracking,
        per-day focus), use get_context_week instead.

        Args:
            month: Month in YYYY-MM format (e.g. '2025-01' for January 2025).
                   Cannot be used with 'week'.
            week: Week in YYYY-Wxx format (e.g. '2025-W05' for week 5 of 2025).
                  Cannot be used with 'month'.

        Returns:
            Activity report for the specified period.
        """
        if month and week:
            return "Error: Cannot specify both 'month' and 'week'. Choose one."
        if not month and not week:
            return "Error: Must specify either 'month' (YYYY-MM) or 'week' (YYYY-Wxx)."

        args = ["report"]
        if month:
            args.extend(["--month", month])
        if week:
            args.extend(["--week", week])
        return run_mdv_command(args)
