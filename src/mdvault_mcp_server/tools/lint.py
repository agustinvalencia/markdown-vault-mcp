"""Vault lint tools — structural correctness checking via mdv check."""

import json

from fastmcp import FastMCP

from .common import run_mdv_command

MAX_ISSUES_PER_CATEGORY = 5


def register_lint_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def vault_lint(category: str | None = None, fix: bool = False) -> str:
        """Check vault structural correctness (broken links, schema violations, orphans, etc.).

        Runs `mdv check` and returns an AI-friendly summary of vault health.

        Args:
            category: Optional category to check (broken_references, malformed_wikilinks,
                      schema_violations, structural_consistency, orphaned_notes, db_sync).
                      Omit to run all checks.
            fix: If True, attempt to auto-fix fixable issues (not yet implemented).

        Returns:
            Vault health report with issues grouped by category.
        """
        args = ["check", "--json"]
        if category:
            args.extend(["--category", category])

        raw = run_mdv_command(args)

        # Check for execution errors
        if raw.startswith("Error"):
            return raw

        try:
            report = json.loads(raw)
        except json.JSONDecodeError:
            return f"Failed to parse lint output:\n{raw}"

        return _format_report(report)


def _format_report(report: dict) -> str:
    """Format a lint JSON report into an AI-readable summary."""
    summary = report.get("summary", {})
    categories = report.get("categories", [])

    total_notes = summary.get("total_notes", 0)
    total_errors = summary.get("total_errors", 0)
    total_warnings = summary.get("total_warnings", 0)
    health_score = summary.get("health_score", 1.0)
    score_pct = round(health_score * 100)

    lines = [f"Vault Health: {score_pct}% ({total_notes} notes)"]
    lines.append("")

    # Clean categories first
    clean = [c["label"] for c in categories if not c["errors"] and not c["warnings"]]
    if clean:
        lines.append(f"Clean: {', '.join(clean)}")
        lines.append("")

    # Categories with issues
    for cat in categories:
        errors = cat.get("errors", [])
        warnings = cat.get("warnings", [])
        if not errors and not warnings:
            continue

        lines.append(f"### {cat['label']} ({len(errors)} errors, {len(warnings)} warnings)")

        # Show capped issues
        all_issues = [("ERROR", i) for i in errors] + [("WARN", i) for i in warnings]
        shown = all_issues[:MAX_ISSUES_PER_CATEGORY]
        remaining = len(all_issues) - len(shown)

        for severity, issue in shown:
            path = issue.get("path", "")
            line = issue.get("line")
            msg = issue.get("message", "")
            loc = f"{path}:{line}" if path and line else (path or "(vault)")
            lines.append(f"  {severity} {loc}: {msg}")
            if issue.get("suggestion"):
                lines.append(f"    → {issue['suggestion']}")

        if remaining > 0:
            lines.append(f"  ... and {remaining} more — ask to see the full list")
        lines.append("")

    # Summary
    if total_errors == 0 and total_warnings == 0:
        lines.append("No issues found.")
    else:
        lines.append(f"Total: {total_errors} error(s), {total_warnings} warning(s)")

    return "\n".join(lines)
