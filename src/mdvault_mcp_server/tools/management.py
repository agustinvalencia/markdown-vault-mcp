from fastmcp import FastMCP

from .common import run_mdv_command

_DEFAULT_ACTIVITY_DAYS = 30


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
        note coverage, project progress stats, and actionable sections
        (overdue tasks, upcoming deadlines, high priority, stale notes).
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

    @mcp.tool()
    def get_dashboard_report(
        project: str | None = None,
        activity_days: int = _DEFAULT_ACTIVITY_DAYS,
    ) -> str:
        """Get a structured dashboard report with project metrics, velocity, and activity.

        Returns a JSON report containing vault summary (notes/tasks by type and
        status), per-project breakdowns (task counts, progress %, velocity,
        recent completions), daily activity data, and actionable task lists
        (overdue, high_priority, upcoming_deadlines). Use for rich status
        checks, project reviews, and weekly/monthly reporting.

        Args:
            project: Scope to a specific project (ID or folder name).
                     Omit for vault-wide report.
            activity_days: Days of activity history to include (default: 30).

        Returns:
            JSON dashboard report or error message.
        """
        args = ["report", "--dashboard", "--json"]
        if project:
            args.extend(["--project", project])
        if activity_days != _DEFAULT_ACTIVITY_DAYS:
            args.extend(["--activity-days", str(activity_days)])
        return run_mdv_command(args)

    @mcp.tool()
    def generate_visual_report(
        project: str | None = None,
    ) -> str:
        """Generate a visual PNG dashboard with charts and save it to the vault.

        Produces a multi-panel PNG image with task status pie chart, project
        progress bars, activity timeline, and velocity comparison. The image
        is saved to assets/dashboards/ in the vault and can be embedded in
        notes via standard markdown image syntax.

        Args:
            project: Scope to a specific project (ID or folder name).
                     Omit for vault-wide dashboard.

        Returns:
            Success message with path to the generated PNG, or error message.
        """
        args = ["report", "--dashboard", "--visual"]
        if project:
            args.extend(["--project", project])
        return run_mdv_command(args)
