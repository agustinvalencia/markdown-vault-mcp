import json
import re

from fastmcp import FastMCP

from ..config import VAULT_PATH, validate_file
from .common import append_content_logic, format_log_entry, run_mdv_command
from .frontmatter import update_note_content


def resolve_project_path(project_name: str) -> tuple[str, str] | None:
    """
    Resolve a project name or ID to its (title, path).
    Returns None if not found.
    """
    # 1. Get all projects paths
    list_output = run_mdv_command(["list", "--type", "project", "--json"])
    try:
        projects = json.loads(list_output)
    except json.JSONDecodeError:
        return None

    # 2. Try to match by Title first
    for p in projects:
        if project_name.lower() in p["title"].lower():
            return p["title"], p["path"]
    
    # 3. Try to match by ID
    # We need to run `mdv project list` to see IDs
    proj_list_out = run_mdv_command(["project", "list"])
    
    # Parse lines like: │ MMCP │ MarkdownVault MCP ...
    pattern = r"│\s*" + re.escape(project_name) + r"\s*│\s*([^│]+)\s*│"
    match = re.search(pattern, proj_list_out, re.IGNORECASE)
    
    if match:
        full_title = match.group(1).strip()
        # Find this title in the json list
        for p in projects:
            if full_title.lower() == p["title"].lower():
                return p["title"], p["path"]

    return None


def _create_literature_note_impl(  # noqa: PLR0913
    title: str,
    short_title: str,
    authors: str | None = None,
    year: int | None = None,
    url: str | None = None,
    source_type: str | None = None,
    extra_vars: dict[str, str] | None = None,
) -> str:
    """Internal implementation of create_literature_note."""
    args = ["new", "literature", title, "--batch"]
    args.extend(["--var", f"short_title={short_title}"])
    if authors:
        args.extend(["--var", f"authors={authors}"])
    if year is not None:
        args.extend(["--var", f"year={year}"])
    if url:
        args.extend(["--var", f"url={url}"])
    if source_type:
        args.extend(["--var", f"source_type={source_type}"])
    if extra_vars:
        for k, v in extra_vars.items():
            args.extend(["--var", f"{k}={v}"])
    return run_mdv_command(args)


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
    def get_project_info(project_name: str) -> str:
        """Get detailed information about a project (metrics, path, backlinks, etc.).

        Uses mdvault's context command for rich project information including
        metadata, sections, activity history, and references.

        Args:
            project_name: Name or ID of the project.
        """
        resolved = resolve_project_path(project_name)
        if not resolved:
            return f"Project '{project_name}' not found."

        _title, path = resolved
        return run_mdv_command(["context", "note", path, "--format", "json"])

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
        context: str,
        description: str | None = None,
        status: str | None = None,
        extra_vars: dict[str, str] | None = None,
    ) -> str:
        """Create a new project.

        Args:
            title: Title of the new project.
            context: Project context (e.g. 'work', 'personal').
            description: Optional description of the project (max 1024 chars).
            status: Project status (e.g. 'open', 'closed').
            extra_vars: Optional dictionary of additional variables for the template.
        """
        args = ["new", "project", title, "--batch"]
        args.extend(["--var", f"context={context}"])
        if description:
            if len(description) > 1024:
                return "Error: Description must be 1024 characters or less."
            args.extend(["--var", f"description={description}"])
        if status:
            args.extend(["--var", f"status={status}"])
        if extra_vars:
            for k, v in extra_vars.items():
                args.extend(["--var", f"{k}={v}"])
        return run_mdv_command(args)

    # --- Meetings ---

    @mcp.tool()
    def create_meeting(
        title: str,
        attendees: str | None = None,
        date: str | None = None,
        extra_vars: dict[str, str] | None = None,
    ) -> str:
        """Create a new meeting note.

        Meeting notes have auto-generated IDs (MTG-YYYY-MM-DD-NNN) and are
        stored in the Meetings/ folder. Creation is logged to the daily note.

        Args:
            title: Title of the meeting (e.g. "Team Sync", "Design Review").
            attendees: Who's attending (e.g. "Alice, Bob, Charlie").
            date: Meeting date in YYYY-MM-DD format. Defaults to today.
            extra_vars: Optional dictionary of additional variables for the template.

        Returns:
            Result of the meeting creation including the generated meeting ID.
        """
        args = ["new", "meeting", title, "--batch"]
        if attendees:
            args.extend(["--var", f"attendees={attendees}"])
        if date:
            args.extend(["--var", f"date={date}"])
        if extra_vars:
            for k, v in extra_vars.items():
                args.extend(["--var", f"{k}={v}"])
        return run_mdv_command(args)

    # --- Literature Notes ---

    @mcp.tool()
    def create_literature_note(  # noqa: PLR0913
        title: str,
        short_title: str,
        authors: str | None = None,
        year: int | None = None,
        url: str | None = None,
        source_type: str | None = None,
        extra_vars: dict[str, str] | None = None,
    ) -> str:
        """Create a new literature note from the template.

        Literature notes are stored in Zettel/Literature/ and track reading
        progress through multi-pass reading (skimming, reading, completed).

        Args:
            title: Full title of the paper/book/article.
            short_title: Short title for the filename slug (e.g. "attention-is-all-you-need").
            authors: Author names, comma-separated (e.g. "Vaswani, Shazeer, Parmar").
            year: Year of publication.
            url: URL or DOI link to the source.
            source_type: Type of source (article, book, video, podcast, other).
            extra_vars: Optional dictionary of additional template variables.

        Returns:
            Result of the creation.
        """
        return _create_literature_note_impl(
            title, short_title, authors, year, url, source_type, extra_vars
        )

    @mcp.tool()
    def log_to_project_note(project_path: str, content: str) -> str:
        """Append a log entry to the 'Logs' section of a project note.

        Format: - [[YYYY-MM-DD]] - HH:MM: Content

        Args:
            project_path: Path to the project note relative to vault root.
            content: The log message to append.

        Returns:
            Success message or error description.
        """
        full_path = VAULT_PATH / project_path
        result = validate_file(full_path)
        if not result.ok:
            return result.msg

        try:
            formatted_log = format_log_entry(content)
            
            def modifier(body: str) -> tuple[str, str]:
                new_body, created_new = append_content_logic(body, formatted_log, subsection="Logs")
                if created_new:
                    msg = f"Created subsection 'Logs' and appended content to {project_path}"
                else:
                    msg = f"Appended log to {project_path}"
                return new_body, msg

            return update_note_content(full_path, modifier)
        except Exception as e:
            return f"Error updating project note: {e}"

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
        description: str | None = None,
        project: str | None = None,
        due_date: str | None = None,
        priority: str | None = None,
        status: str | None = None,
        extra_vars: dict[str, str] | None = None,
    ) -> str:
        """Create a new task.

        If no project is specified, mdvault automatically uses the active focus
        context. Context inheritance from the project is handled automatically.

        Args:
            title: Title of the task.
            description: Optional description of the task (max 1024 chars).
            project: Optional project name. If omitted, uses the active focus context.
            due_date: Optional due date (YYYY-MM-DD).
            priority: Optional priority (e.g. 'low', 'medium', 'high').
            status: Optional status (e.g. 'todo', 'doing', 'done').
            extra_vars: Optional dictionary of additional variables for the template.
        """
        args = ["new", "task", title, "--batch"]

        if description:
            if len(description) > 1024:
                return "Error: Description must be 1024 characters or less."
            args.extend(["--var", f"description={description}"])
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
            args.extend(["-s", summary])
        return run_mdv_command(args)

    @mcp.tool()
    def log_to_task_note(task_path: str, content: str) -> str:
        """Append a log entry to the 'Logs' section of a task note.

        Format: - [[YYYY-MM-DD]] - HH:MM: Content

        Args:
            task_path: Path to the task note relative to vault root.
            content: The log message to append.

        Returns:
            Success message or error description.
        """
        full_path = VAULT_PATH / task_path
        result = validate_file(full_path)
        if not result.ok:
            return result.msg

        try:
            formatted_log = format_log_entry(content)
            
            def modifier(body: str) -> tuple[str, str]:
                new_body, created_new = append_content_logic(body, formatted_log, subsection="Logs")
                if created_new:
                    msg = f"Created subsection 'Logs' and appended content to {task_path}"
                else:
                    msg = f"Appended log to {task_path}"
                return new_body, msg

            return update_note_content(full_path, modifier)
        except Exception as e:
            return f"Error updating task note: {e}"
