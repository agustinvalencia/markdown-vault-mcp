"""Vault lint tools — structural correctness checking and type validation."""

import json
import os
import shutil
import subprocess

from fastmcp import FastMCP

from .common import VAULT_PATH

MAX_ISSUES_PER_CATEGORY = 5
MAX_VALIDATE_RESULTS = 10


def _run_mdv_json(args: list[str]) -> dict | str:
    """Run an mdv command that outputs JSON, returning parsed dict or error string.

    Unlike run_mdv_command, this extracts JSON from stdout even when the
    process exits non-zero (e.g. mdv validate exits 1 when notes fail).
    """
    mdv_path = shutil.which("mdv")
    if not mdv_path:
        return "Error: 'mdv' executable not found in PATH."

    env = os.environ.copy()
    if "MARKDOWN_VAULT_PATH" not in env:
        env["MARKDOWN_VAULT_PATH"] = str(VAULT_PATH)

    try:
        result = subprocess.run(
            [mdv_path, *args], capture_output=True, text=True, env=env, check=False
        )
    except Exception as e:
        return f"Failed to execute mdv command: {e}"

    stdout = result.stdout.strip()
    if not stdout:
        return f"Error executing command: mdv {' '.join(args)}\n{result.stderr}"

    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return f"Failed to parse mdv output:\n{stdout}\n{result.stderr}"


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

        report = _run_mdv_json(args)
        if isinstance(report, str):
            return report

        return _format_report(report)

    @mcp.tool()
    def validate_note(
        path: str | None = None,
        note_type: str | None = None,
        fix: bool = False,
        limit: int | None = None,
    ) -> str:
        """Validate notes against Lua type definitions (frontmatter schema).

        Runs `mdv validate` to check that note frontmatter conforms to the
        type definition schemas (required fields, types, enums, defaults).

        Args:
            path: Specific note path to validate (relative to vault root).
                  Omit to validate all notes.
            note_type: Only validate notes of this type (daily, task, project, etc.).
            fix: Auto-fix safe issues (missing defaults, enum case normalisation).
            limit: Maximum number of notes to validate.

        Returns:
            Validation report with per-note errors and fixes applied.
        """
        args = ["validate", "--output", "json"]
        if path:
            args.append(path)
        if note_type:
            args.extend(["--type", note_type])
        if fix:
            args.append("--fix")
        if limit is not None:
            args.extend(["--limit", str(limit)])

        report = _run_mdv_json(args)
        if isinstance(report, str):
            return report

        return _format_validate_report(report)


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


def _format_validate_report(report: dict) -> str:
    """Format a validate JSON report into an AI-readable summary."""
    total = report.get("total", 0)
    valid = report.get("valid", 0)
    errors = report.get("errors", 0)
    fixed = report.get("fixed", 0)
    results = report.get("results", [])

    lines = [f"Validation: {valid}/{total} notes valid, {errors} with errors"]

    if fixed:
        lines[0] += f", {fixed} fixed"

    if not results:
        lines.append("All notes pass type validation.")
        return "\n".join(lines)

    lines.append("")

    shown = results[:MAX_VALIDATE_RESULTS]
    for r in shown:
        path = r.get("path", "")
        ntype = r.get("note_type", "unknown")
        lines.append(f"  {path} ({ntype})")
        for err in r.get("errors", []):
            lines.append(f"    ERROR: {err}")
        for fix in r.get("fixes_applied", []):
            lines.append(f"    FIXED: {fix}")

    remaining = len(results) - len(shown)
    if remaining > 0:
        lines.append(f"  ... and {remaining} more")

    return "\n".join(lines)
