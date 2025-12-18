"""Implementation of `git adr list` command.

Lists all Architecture Decision Records with filtering options.
"""

from __future__ import annotations

import json
from datetime import date
from typing import cast

import typer
from rich.console import Console
from rich.table import Table

from git_adr.commands._shared import get_status_style, setup_command_context
from git_adr.core import ADRStatus, GitError
from git_adr.core.index import IndexManager

console = Console()
err_console = Console(stderr=True)


def run_list(
    status: str | None = None,
    tag: str | None = None,
    since: str | None = None,
    until: str | None = None,
    format_: str = "table",
    reverse: bool = False,
) -> None:
    """List all ADRs with optional filtering.

    Args:
        status: Filter by status.
        tag: Filter by tag.
        since: Filter by date (YYYY-MM-DD).
        until: Filter by date (YYYY-MM-DD).
        format_: Output format (table, json, csv, oneline).
        reverse: Reverse chronological order.

    Raises:
        typer.Exit: On error.
    """
    try:
        # Initialize command context with index manager
        ctx = setup_command_context(require_index=True)
        index_manager = cast(IndexManager, ctx.index_manager)

        # Parse filters
        parsed_status = None
        if status:
            try:
                parsed_status = ADRStatus.from_string(status)
            except ValueError:
                err_console.print(f"[red]Error:[/red] Invalid status: {status}")
                valid = ", ".join(s.value for s in ADRStatus)
                err_console.print(f"Valid statuses: {valid}")
                raise typer.Exit(1)

        since_date = _parse_date(since) if since else None
        until_date = _parse_date(until) if until else None

        # Query index
        result = index_manager.query(
            status=parsed_status,
            tag=tag,
            since=since_date,
            until=until_date,
            reverse=reverse,
        )

        # Output based on format
        if format_ == "table":
            _output_table(result.entries)
        elif format_ == "json":
            _output_json(result.entries)
        elif format_ == "csv":
            _output_csv(result.entries)
        elif format_ == "oneline":
            _output_oneline(result.entries)
        else:
            err_console.print(f"[red]Error:[/red] Unknown format: {format_}")
            raise typer.Exit(1)

        # Show summary
        if format_ == "table" and result.entries:
            console.print()
            console.print(
                f"[dim]{result.filtered_count} of {result.total_count} ADRs[/dim]"
            )

    except GitError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def _parse_date(date_str: str) -> date | None:
    """Parse a date string.

    Args:
        date_str: Date in YYYY-MM-DD format.

    Returns:
        Parsed date, or None on error.
    """
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        err_console.print(f"[red]Error:[/red] Invalid date format: {date_str}")
        err_console.print("Expected format: YYYY-MM-DD")
        raise typer.Exit(1)


def _output_table(entries: list) -> None:
    """Output entries as a rich table.

    Args:
        entries: List of index entries.
    """
    if not entries:
        console.print("[dim]No ADRs found[/dim]")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Status", style="dim")
    table.add_column("Date")
    table.add_column("Title")
    table.add_column("Tags", style="dim")

    for entry in entries:
        # Color status
        status_style = get_status_style(entry.status)
        status_text = f"[{status_style}]{entry.status.value}[/{status_style}]"

        table.add_row(
            entry.id,
            status_text,
            entry.date.isoformat(),
            entry.title,
            ", ".join(entry.tags) if entry.tags else "",
        )

    console.print(table)


def _output_json(entries: list) -> None:
    """Output entries as JSON.

    Args:
        entries: List of index entries.
    """
    data = [
        {
            "id": e.id,
            "title": e.title,
            "status": e.status.value,
            "date": e.date.isoformat(),
            "tags": list(e.tags),
            "linked_commits": list(e.linked_commits),
            "supersedes": e.supersedes,
            "superseded_by": e.superseded_by,
        }
        for e in entries
    ]
    console.print(json.dumps(data, indent=2))


def _output_csv(entries: list) -> None:
    """Output entries as CSV.

    Args:
        entries: List of index entries.
    """
    import csv
    import sys

    writer = csv.writer(sys.stdout)
    writer.writerow(["id", "status", "date", "title", "tags"])

    for entry in entries:
        writer.writerow(
            [
                entry.id,
                entry.status.value,
                entry.date.isoformat(),
                entry.title,
                ";".join(entry.tags),
            ]
        )


def _output_oneline(entries: list) -> None:
    """Output entries one per line.

    Args:
        entries: List of index entries.
    """
    for entry in entries:
        status = entry.status.value[:3].upper()
        console.print(f"[cyan]{entry.id}[/cyan] [{status}] {entry.title}")
