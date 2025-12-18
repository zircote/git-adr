"""Implementation of `git adr report` command.

Generates comprehensive ADR reports in various formats.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, cast

import typer
from rich.console import Console

from git_adr.commands._shared import setup_command_context
from git_adr.core import GitError
from git_adr.core.adr import ADRStatus
from git_adr.core.index import IndexManager

if TYPE_CHECKING:
    from git_adr.core.notes import NotesManager

console = Console()
err_console = Console(stderr=True)


def run_report(
    format_: str = "terminal",
    output: str | None = None,
    team: bool = False,
) -> None:
    """Generate an ADR analytics report/dashboard.

    Args:
        format_: Output format (terminal, html, json, markdown).
        output: Output file path.
        team: Include team collaboration metrics.

    Raises:
        typer.Exit: On error.
    """
    try:
        # Initialize command context with index manager
        ctx = setup_command_context(require_index=True)
        index_manager = cast(IndexManager, ctx.index_manager)

        # Rebuild index
        index_manager.rebuild()

        # Get all ADRs
        all_adrs = ctx.notes_manager.list_all()

        if format_ == "json":
            report = _generate_json_report(all_adrs, ctx.notes_manager)
        elif format_ == "html":
            report = _generate_html_report(all_adrs, ctx.notes_manager)
        elif format_ == "terminal":
            # For terminal, just display using rich
            _display_terminal_report(all_adrs, ctx.notes_manager, team)
            return
        else:
            report = _generate_markdown_report(all_adrs, ctx.notes_manager)

        if output:
            output_path = Path(output)
            output_path.write_text(report)
            console.print(f"[green]✓[/green] Report written to {output_path}")
        else:
            console.print(report)

    except GitError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def _get_author(adr) -> str:
    """Get the primary author from ADR deciders."""
    if adr.metadata.deciders:
        return adr.metadata.deciders[0]
    return "unknown"


def _generate_markdown_report(all_adrs: list, notes_manager: NotesManager) -> str:
    """Generate a Markdown report."""
    lines = [
        "# Architecture Decision Records Report",
        "",
        f"Generated: {datetime.now(UTC).isoformat()}",
        "",
        "## Summary",
        "",
        f"Total ADRs: {len(all_adrs)}",
        "",
    ]

    # Status breakdown
    status_counts: Counter[str] = Counter()
    for adr in all_adrs:
        status_counts[adr.metadata.status.value] += 1

    lines.append("### By Status")
    lines.append("")
    for status in ADRStatus:
        count = status_counts.get(status.value, 0)
        lines.append(f"- {status.value}: {count}")
    lines.append("")

    # List all ADRs
    lines.append("## ADR List")
    lines.append("")

    for adr in sorted(all_adrs, key=lambda a: a.metadata.date):
        lines.append(f"### {adr.metadata.id}: {adr.metadata.title}")
        lines.append("")
        lines.append(f"- **Status**: {adr.metadata.status.value}")
        lines.append(f"- **Decider**: {_get_author(adr)}")
        lines.append(f"- **Date**: {adr.metadata.date}")
        if adr.metadata.tags:
            lines.append(f"- **Tags**: {', '.join(adr.metadata.tags)}")
        lines.append("")

    return "\n".join(lines)


def _generate_html_report(all_adrs: list, notes_manager: NotesManager) -> str:
    """Generate an HTML report."""
    html = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "<title>ADR Report</title>",
        "<style>",
        "body { font-family: system-ui, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }",
        "h1 { color: #333; }",
        "table { border-collapse: collapse; width: 100%; }",
        "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
        "th { background-color: #f5f5f5; }",
        ".status-accepted { color: green; }",
        ".status-rejected { color: red; }",
        ".status-deprecated { color: orange; }",
        "</style>",
        "</head>",
        "<body>",
        "<h1>Architecture Decision Records Report</h1>",
        f"<p>Generated: {datetime.now().isoformat()}</p>",
        f"<p>Total ADRs: {len(all_adrs)}</p>",
        "<table>",
        "<tr><th>ID</th><th>Title</th><th>Status</th><th>Author</th><th>Created</th></tr>",
    ]

    for adr in sorted(all_adrs, key=lambda a: a.metadata.date):
        status_class = f"status-{adr.metadata.status.value}"
        html.append(
            f"<tr>"
            f"<td>{adr.metadata.id}</td>"
            f"<td>{adr.metadata.title}</td>"
            f"<td class='{status_class}'>{adr.metadata.status.value}</td>"
            f"<td>{_get_author(adr)}</td>"
            f"<td>{adr.metadata.date}</td>"
            f"</tr>"
        )

    html.extend(["</table>", "</body>", "</html>"])
    return "\n".join(html)


def _display_terminal_report(
    all_adrs: list, notes_manager: NotesManager, team: bool
) -> None:
    """Display report in terminal using rich."""
    from rich.panel import Panel
    from rich.table import Table

    status_counts: Counter[str] = Counter()
    author_counts: Counter[str] = Counter()
    for adr in all_adrs:
        status_counts[adr.metadata.status.value] += 1
        author_counts[_get_author(adr)] += 1

    console.print()
    console.print(
        Panel(
            f"[bold cyan]{len(all_adrs)}[/bold cyan] total ADRs",
            title="ADR Report",
            expand=False,
        )
    )

    # Status table
    console.print()
    table = Table(title="By Status", show_header=True)
    table.add_column("Status", style="cyan")
    table.add_column("Count", justify="right")

    for status, count in status_counts.most_common():
        table.add_row(status, str(count))

    console.print(table)

    # Team metrics
    if team:
        console.print()
        team_table = Table(title="Team Contributions", show_header=True)
        team_table.add_column("Author", style="cyan")
        team_table.add_column("ADRs", justify="right")

        for author, count in author_counts.most_common(10):
            team_table.add_row(author, str(count))

        console.print(team_table)


def _generate_json_report(all_adrs: list, notes_manager: NotesManager) -> str:
    """Generate a JSON report."""
    status_counts: Counter[str] = Counter()
    for adr in all_adrs:
        status_counts[adr.metadata.status.value] += 1

    report_data = {
        "generated": datetime.now(UTC).isoformat(),
        "total": len(all_adrs),
        "by_status": dict(status_counts),
        "adrs": [
            {
                "id": adr.metadata.id,
                "title": adr.metadata.title,
                "status": adr.metadata.status.value,
                "decider": _get_author(adr),
                "date": str(adr.metadata.date),
                "tags": adr.metadata.tags,
            }
            for adr in all_adrs
        ],
    }

    return json.dumps(report_data, indent=2)
