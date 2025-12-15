"""Implementation of `git adr ai suggest` command.

AI-powered suggestions to improve ADRs.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from git_adr.core import (
    ConfigManager,
    GitError,
    NotesManager,
    get_git,
)

console = Console()
err_console = Console(stderr=True)


def run_ai_suggest(
    adr_id: str,
    aspect: str = "all",
) -> None:
    """Get AI suggestions to improve an ADR.

    Args:
        adr_id: ADR ID to improve.
        aspect: Focus area (context, options, consequences, all).

    Raises:
        typer.Exit: On error.
    """
    try:
        git = get_git(cwd=Path.cwd())

        if not git.is_repository():
            err_console.print("[red]Error:[/red] Not a git repository")
            raise typer.Exit(1)

        config_manager = ConfigManager(git)
        config = config_manager.load()

        if not config_manager.get("initialized"):
            err_console.print(
                "[red]Error:[/red] git-adr not initialized. Run `git adr init` first."
            )
            raise typer.Exit(1)

        notes_manager = NotesManager(git, config)

        # Verify ADR exists
        adr = notes_manager.get(adr_id)
        if adr is None:
            err_console.print(f"[red]Error:[/red] ADR not found: {adr_id}")
            raise typer.Exit(1)

        # Check AI configuration
        if not config.ai_provider:
            err_console.print(
                "[red]Error:[/red] AI provider not configured.\n"
                "Run: git adr config set ai.provider <openai|anthropic|google|ollama>"
            )
            raise typer.Exit(1)

        console.print(
            Panel(
                f"[bold]Analyzing ADR for improvements[/bold]\n\n"
                f"ADR: [cyan]{adr_id}[/cyan]\n"
                f"Title: {adr.metadata.title}\n"
                f"Focus: {aspect}",
                title="AI Suggest",
            )
        )
        console.print()
        console.print("[dim]Generating suggestions...[/dim]")

        try:
            from git_adr.ai import AIService

            ai_service = AIService(config)
            response = ai_service.suggest_improvements(adr)

            # Display suggestions
            console.print()
            console.print(
                Panel(Markdown(response.content), title="Improvement Suggestions")
            )
            console.print()
            console.print(f"[dim]Model: {response.model} ({response.provider})[/dim]")

            console.print()
            console.print("[bold]Next steps:[/bold]")
            console.print(
                f"  • [cyan]git adr edit {adr_id}[/cyan] - Apply improvements"
            )
            console.print(
                f"  • [cyan]git adr show {adr_id}[/cyan] - Review current content"
            )

        except ImportError:
            err_console.print(
                "[red]Error:[/red] AI features require additional dependencies.\n"
                "Install with: pip install git-adr[ai]"
            )
            raise typer.Exit(1)
        except Exception as e:
            err_console.print(f"[red]AI Error:[/red] {e}")
            raise typer.Exit(1)

    except GitError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
