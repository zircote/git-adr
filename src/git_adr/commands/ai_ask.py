"""Implementation of `git adr ai ask` command.

Natural language Q&A about ADRs using RAG.
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from git_adr.commands._shared import setup_command_context
from git_adr.core import GitError

console = Console()
err_console = Console(stderr=True)


def run_ai_ask(
    question: str,
    include_superseded: bool = False,
    tag: str | None = None,
) -> None:
    """Ask a question about architectural decisions.

    Uses RAG (Retrieval Augmented Generation) to find
    relevant ADRs and answer questions about architecture.

    Args:
        question: Natural language question.
        include_superseded: Include superseded ADRs in search.
        tag: Filter ADRs by tag for focused context.

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

        # Get ADRs for context
        all_adrs = ctx.notes_manager.list_all()

        # Filter superseded unless explicitly included
        if not include_superseded:
            all_adrs = [a for a in all_adrs if a.metadata.status.value != "superseded"]

        # Filter by tag if specified
        if tag:
            all_adrs = [
                a
                for a in all_adrs
                if a.metadata.tags
                and tag.lower() in [t.lower() for t in a.metadata.tags]
            ]

        if not all_adrs:
            if tag:
                err_console.print(f"[yellow]No ADRs found with tag '{tag}'[/yellow]")
            else:
                err_console.print("[yellow]No ADRs found in repository[/yellow]")
            return

        console.print(
            Panel(
                f"[bold]Searching ADR Knowledge Base[/bold]\n\n"
                f"Question: [cyan]{question}[/cyan]\n"
                f"Context: {len(all_adrs)} ADRs"
                + (f" (tag: {tag})" if tag else "")
                + (" (including superseded)" if include_superseded else ""),
                title="AI Ask",
            )
        )
        console.print()
        console.print("[dim]Searching for relevant decisions...[/dim]")

        try:
            from git_adr.ai import AIService

            ai_service = AIService(ctx.config)
            response = ai_service.ask_question(question, all_adrs)

            # Display answer
            console.print()
            console.print(Panel(Markdown(response.content), title="Answer"))
            console.print()
            console.print(f"[dim]Model: {response.model} ({response.provider})[/dim]")

            # Suggest follow-up actions
            console.print()
            console.print("[bold]Related commands:[/bold]")
            console.print("  • [cyan]git adr search <term>[/cyan] - Full-text search")
            console.print(
                "  • [cyan]git adr list --status accepted[/cyan] - List by status"
            )
            console.print("  • [cyan]git adr show <id>[/cyan] - View specific ADR")

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
