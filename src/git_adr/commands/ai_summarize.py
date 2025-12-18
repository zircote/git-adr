"""Implementation of `git adr ai summarize` command.

AI-powered ADR summarization and digest generation.
"""

from __future__ import annotations

import re
from datetime import date, timedelta

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from git_adr.commands._shared import setup_command_context
from git_adr.core import GitError

console = Console()
err_console = Console(stderr=True)


def run_ai_summarize(
    period: str = "30d",
    format_: str = "markdown",
) -> None:
    """Generate a natural language summary of recent decisions.

    Args:
        period: Time period (7d, 30d, 90d, etc.).
        format_: Output format (markdown, slack, email, standup).

    Raises:
        typer.Exit: On error.
    """
    try:
        # Initialize command context
        ctx = setup_command_context()

        # Check AI configuration
        if not ctx.config.ai_provider:
            err_console.print(
                "[red]Error:[/red] AI provider not configured.\n"
                "Run: git adr config set ai.provider <openai|anthropic|google|ollama>"
            )
            raise typer.Exit(1)

        # Parse period
        days = _parse_period(period)
        cutoff = date.today() - timedelta(days=days)

        # Get ADRs within period
        all_adrs = ctx.notes_manager.list_all()
        recent_adrs = [adr for adr in all_adrs if adr.metadata.date >= cutoff]

        if not recent_adrs:
            console.print(f"[yellow]No ADRs found in the last {period}[/yellow]")
            return

        console.print(
            Panel(
                f"[bold]Generating Summary[/bold]\n\n"
                f"Period: {period} ({days} days)\n"
                f"ADRs found: {len(recent_adrs)}\n"
                f"Format: {format_}",
                title="AI Summarize",
            )
        )
        console.print()
        console.print("[dim]Generating summary...[/dim]")

        try:
            from git_adr.ai import AIService

            ai_service = AIService(ctx.config)
            response = ai_service.summarize_adrs(recent_adrs, format_=format_)

            # Display summary
            console.print()
            if format_ == "markdown":
                console.print(
                    Panel(Markdown(response.content), title=f"ADR Summary ({period})")
                )
            else:
                console.print(Panel(response.content, title=f"ADR Summary ({period})"))

            console.print()
            console.print(f"[dim]Model: {response.model} ({response.provider})[/dim]")

        except ImportError:
            err_console.print(
                "[red]Error:[/red] AI features require additional dependencies.\n"
                "Install with: pip install 'git-adr\\[ai]'"
            )
            raise typer.Exit(1)
        except Exception as e:
            err_console.print(f"[red]AI Error:[/red] {e}")
            raise typer.Exit(1)

    except GitError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def _parse_period(period: str) -> int:
    """Parse a period string like '30d', '2w', '3m' into days."""
    match = re.match(r"^(\d+)([dwm])$", period.lower())
    if not match:
        return 30  # Default to 30 days

    value = int(match.group(1))
    unit = match.group(2)

    if unit == "d":
        return value
    elif unit == "w":
        return value * 7
    elif unit == "m":
        return value * 30
    return 30
