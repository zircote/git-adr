"""Implementation of `git adr stats` command.

Displays statistics about ADRs in the repository.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from typing import cast

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from git_adr.commands._shared import setup_command_context
from git_adr.core import GitError
from git_adr.core.adr import ADRStatus
from git_adr.core.index import IndexManager

console = Console()
err_console = Console(stderr=True)


def run_stats(
    velocity: bool = False,
) -> None:
    """Display ADR statistics.

    Args:
        velocity: Show decision velocity metrics.

    Raises:
        typer.Exit: On error.
    """
    try:
        # Initialize command context with index manager
        ctx = setup_command_context(require_index=True)
        index_manager = cast(IndexManager, ctx.index_manager)

        # Rebuild index to ensure accuracy
        index_manager.rebuild()

        # Get all ADRs
        all_adrs = ctx.notes_manager.list_all()

        if not all_adrs:
            console.print("[dim]No ADRs found[/dim]")
            return

        # Calculate statistics
        status_counts: Counter[str] = Counter()
        format_counts: Counter[str] = Counter()
        author_counts: Counter[str] = Counter()
        total_artifacts = 0
        adrs_with_links = 0

        for adr in all_adrs:
            status_counts[adr.metadata.status.value] += 1
            format_counts[adr.metadata.format] += 1
            # Track deciders (first decider as primary author)
            if adr.metadata.deciders:
                author_counts[adr.metadata.deciders[0]] += 1
            else:
                author_counts["unknown"] += 1

            # Count artifacts
            artifacts = ctx.notes_manager.list_artifacts(adr.metadata.id)
            total_artifacts += len(artifacts)

            # Count linked ADRs
            if adr.metadata.linked_commits:
                adrs_with_links += 1

        # Display statistics
        console.print()
        console.print(
            Panel(
                f"[bold cyan]{len(all_adrs)}[/bold cyan] total ADRs",
                title="ADR Statistics",
                expand=False,
            )
        )

        # Status breakdown
        console.print()
        console.print("[bold]By Status:[/bold]")
        status_table = Table(show_header=False, box=None, padding=(0, 2))
        status_table.add_column("Status", style="cyan")
        status_table.add_column("Count", justify="right")
        status_table.add_column("Bar")

        max_count = max(status_counts.values()) if status_counts else 1
        for status in ADRStatus:
            count = status_counts.get(status.value, 0)
            bar_len = int((count / max_count) * 20) if max_count > 0 else 0
            bar = "█" * bar_len
            status_table.add_row(status.value, str(count), f"[green]{bar}[/green]")

        console.print(status_table)

        # Format breakdown
        if len(format_counts) > 1:
            console.print()
            console.print("[bold]By Format:[/bold]")
            for fmt, count in format_counts.most_common():
                console.print(f"  {fmt}: {count}")

        # Top authors
        console.print()
        console.print("[bold]Top Authors:[/bold]")
        for author, count in author_counts.most_common(5):
            console.print(f"  {author}: {count}")

        # Velocity metrics
        if velocity:
            console.print()
            console.print("[bold]Decision Velocity:[/bold]")
            _display_velocity(all_adrs)

        # Additional stats
        console.print()
        console.print("[bold]Additional Info:[/bold]")
        console.print(f"  Artifacts attached: {total_artifacts}")
        console.print(f"  ADRs with linked commits: {adrs_with_links}")

    except GitError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def _display_velocity(all_adrs: list) -> None:
    """Display decision velocity metrics.

    Args:
        all_adrs: List of all ADRs.
    """
    today = date.today()

    # Calculate ADRs created in different periods
    periods = [
        ("Last 7 days", 7),
        ("Last 30 days", 30),
        ("Last 90 days", 90),
        ("Last year", 365),
    ]

    velocity_table = Table(show_header=True, box=None, padding=(0, 2))
    velocity_table.add_column("Period", style="dim")
    velocity_table.add_column("ADRs", justify="right")
    velocity_table.add_column("Rate", justify="right", style="cyan")

    for period_name, days in periods:
        cutoff = today - timedelta(days=days)
        count = sum(1 for adr in all_adrs if adr.metadata.date >= cutoff)
        rate = count / days * 30 if days > 0 else 0  # Monthly rate
        velocity_table.add_row(period_name, str(count), f"{rate:.1f}/mo")

    console.print(velocity_table)

    # Show trend sparkline (last 12 weeks)
    console.print()
    console.print("[dim]Weekly trend (last 12 weeks):[/dim]")

    weekly_counts = []
    for week in range(12):
        week_start = today - timedelta(days=(week + 1) * 7)
        week_end = today - timedelta(days=week * 7)
        count = sum(1 for adr in all_adrs if week_start <= adr.metadata.date < week_end)
        weekly_counts.append(count)

    # Reverse to show oldest first
    weekly_counts = list(reversed(weekly_counts))

    # Create simple sparkline
    max_weekly = max(weekly_counts) if weekly_counts else 1
    sparkline_chars = "▁▂▃▄▅▆▇█"

    sparkline = ""
    for count in weekly_counts:
        if max_weekly > 0:
            idx = min(
                int((count / max_weekly) * (len(sparkline_chars) - 1)),
                len(sparkline_chars) - 1,
            )
            sparkline += sparkline_chars[idx]
        else:
            sparkline += sparkline_chars[0]

    console.print(f"  [green]{sparkline}[/green]")
    console.print("  [dim]↑ older          newer ↑[/dim]")

    # Show oldest and newest ADR
    if all_adrs:
        sorted_adrs = sorted(all_adrs, key=lambda a: a.metadata.date)
        oldest = sorted_adrs[0]
        newest = sorted_adrs[-1]
        console.print()
        console.print(f"  Oldest: {oldest.metadata.id} ({oldest.metadata.date})")
        console.print(f"  Newest: {newest.metadata.id} ({newest.metadata.date})")
