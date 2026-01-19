
from fastmcp import FastMCP

from .common import run_mdv_command


def register_tasks_projects_tools(mcp: FastMCP) -> None:  # noqa: PLR0915
    # --- Context / Focus ---

    @mcp.tool()
    def set_focus(project: str, note: str | None = None) -> str:
        """Set the active project focus.

        Args:
            project: The project ID or name to focus on.
            note: Optional note about what you are working on.
        """
        args = ["focus", project]
        if note:
            args.extend(["--note", note])
        return run_mdv_command(args)

    @mcp.tool()
    def clear_focus() -> str:
        """Clear the active project focus."""
        return run_mdv_command(["focus", "--clear"])

    # --- Projects ---

    @mcp.tool()
    def list_projects(status_filter: str | None = None) -> str:
        """List all projects with task counts.

        Args:
            status_filter: Filter projects by status (e.g., 'active', 'archived').
        """
        args = ["project", "list"]
        if status_filter:
            args.extend(["--status", status_filter])
        return run_mdv_command(args)

    @mcp.tool()
    def get_project_status(project_name: str) -> str:
        """Show detailed status of a project (Kanban view).

        Args:
            project_name: Name or ID of the project.
        """
        return run_mdv_command(["project", "status", project_name])

    @mcp.tool()
    def get_project_progress(project_name: str | None = None) -> str:
        """Show progress metrics for a project or all projects.

        Args:
            project_name: Optional project name to get detailed progress for.
                          If omitted, shows summary for all projects.
        """
        args = ["project", "progress"]
        if project_name:
            args.append(project_name)
        return run_mdv_command(args)

    @mcp.tool()
    def create_project(
        title: str,
        context: str | None = None,
        status: str | None = None,
        extra_vars: dict[str, str] | None = None,
    ) -> str:
        """Create a new project.

        Args:
            title: Title of the new project.
            context: Project context (e.g. 'work', 'personal').
            status: Project status (e.g. 'open', 'closed').
            extra_vars: Optional dictionary of additional variables for the template.
        """
        args = ["new", "project", title, "--batch"]
        if context:
            args.extend(["--var", f"context={context}"])
        if status:
            args.extend(["--var", f"status={status}"])
        if extra_vars:
            for k, v in extra_vars.items():
                args.extend(["--var", f"{k}={v}"])
        return run_mdv_command(args)

    # --- Tasks ---

    @mcp.tool()
    def list_tasks(project_filter: str | None = None, status_filter: str | None = None) -> str:
        """List tasks with optional filters.

        Args:
            project_filter: Filter tasks by project name.
            status_filter: Filter tasks by status (e.g., 'todo', 'doing', 'done').
        """
        args = ["task", "list"]
        if project_filter:
            args.extend(["--project", project_filter])
        if status_filter:
            args.extend(["--status", status_filter])
        return run_mdv_command(args)

    @mcp.tool()
    def get_task_details(task_id: str) -> str:
        """Show details for a specific task.

        Args:
            task_id: The ID of the task.
        """
        return run_mdv_command(["task", "status", task_id])

    @mcp.tool()
    def create_task(  # noqa: PLR0913
        title: str,
        project: str | None = None,
        due_date: str | None = None,
        priority: str | None = None,
        status: str | None = None,
        extra_vars: dict[str, str] | None = None,
    ) -> str:
        """Create a new task.

        Args:
            title: Title of the task.
            project: Optional project name. If omitted, uses the active focus context.
            due_date: Optional due date (YYYY-MM-DD).
            priority: Optional priority (e.g. 'low', 'medium', 'high').
            status: Optional status (e.g. 'todo', 'doing', 'done').
            extra_vars: Optional dictionary of additional variables for the template.
        """
        args = ["new", "task", title, "--batch"]
        if project:
            args.extend(["--var", f"project={project}"])
        if due_date:
            args.extend(["--var", f"due_date={due_date}"])
        if priority:
            args.extend(["--var", f"priority={priority}"])
        if status:
            args.extend(["--var", f"status={status}"])
        if extra_vars:
            for k, v in extra_vars.items():
                args.extend(["--var", f"{k}={v}"])
        return run_mdv_command(args)

    @mcp.tool()
    def complete_task(task_path: str, summary: str | None = None) -> str:
        """Mark a task as done.

        Args:
            task_path: Path to the task file relative to vault root.
            summary: Optional summary of what was done (appended to task body).
        """
        args = ["task", "done", task_path]
        if summary:
            args.append(summary)
        return run_mdv_command(args)
