"""Implementation of `git adr ai draft` command.

AI-guided ADR creation with interactive elicitation.
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from git_adr.commands._shared import setup_command_context
from git_adr.core import (
    ADR,
    ADRMetadata,
    ADRStatus,
    GitError,
    generate_adr_id,
)

console = Console()
err_console = Console(stderr=True)


def run_ai_draft(
    title: str,
    batch: bool = False,
    from_commits: str | None = None,
    context: str | None = None,
    template: str | None = None,
) -> None:
    """Generate an ADR draft using AI.

    Args:
        title: Title for the new ADR.
        batch: One-shot generation (no interactive prompts).
        from_commits: Analyze commits (e.g., 'HEAD~5..HEAD').
        context: Additional context for the AI.
        template: Override template format.

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
            console.print()
            console.print("Supported providers:")
            console.print("  • openai (GPT-4, GPT-4-mini)")
            console.print("  • anthropic (Claude)")
            console.print("  • google (Gemini)")
            console.print("  • ollama (local models)")
            raise typer.Exit(1)

        # Interactive elicitation (unless batch mode)
        options: list[str] = []
        drivers: list[str] = []
        elicited_context = context

        if not batch:
            console.print(
                Panel(
                    f"[bold]AI-Assisted ADR Creation[/bold]\n\n"
                    f"Topic: [cyan]{title}[/cyan]\n"
                    f"Provider: [dim]{ctx.config.ai_provider}[/dim]",
                    title="git adr ai draft",
                )
            )
            console.print()

            # Gather context
            if not elicited_context:
                elicited_context = Prompt.ask(
                    "[bold]Context[/bold]\nWhat problem are you solving?",
                    default="",
                )

            # Gather options
            console.print()
            console.print("[bold]Options[/bold]")
            console.print("Enter options considered (empty line to finish):")
            while True:
                option = Prompt.ask("  Option", default="")
                if not option:
                    break
                options.append(option)

            # Gather drivers
            console.print()
            console.print("[bold]Decision Drivers[/bold]")
            console.print(
                "What factors are driving this decision? (empty line to finish):"
            )
            while True:
                driver = Prompt.ask("  Driver", default="")
                if not driver:
                    break
                drivers.append(driver)

        # Get commit context if requested
        commit_context = ""
        if from_commits:
            try:
                result = ctx.git.run(["log", "--oneline", from_commits])
                if result.exit_code == 0:
                    commit_context = f"\n\nRecent commits:\n{result.stdout}"
            except Exception:  # nosec B110 - commit context is optional; graceful degradation
                pass

        # Generate ADR using AI
        console.print()
        console.print("[dim]Generating ADR with AI...[/dim]")

        try:
            from git_adr.ai import AIService

            ai_service = AIService(ctx.config)

            # Combine context
            full_context = elicited_context or ""
            if commit_context:
                full_context += commit_context

            response = ai_service.draft_adr(
                title=title,
                context=full_context if full_context else None,
                options=options if options else None,
                drivers=drivers if drivers else None,
            )

            # Display generated content
            console.print()
            console.print(Panel(Markdown(response.content), title="Generated ADR"))
            console.print()
            console.print(f"[dim]Model: {response.model} ({response.provider})[/dim]")

            # Ask to save
            if not batch:
                console.print()
                if not typer.confirm("Save this ADR?", default=True):
                    console.print("[yellow]Aborted[/yellow]")
                    return

            # Create and save ADR
            from datetime import date

            existing_ids = {adr.id for adr in ctx.notes_manager.list_all()}
            adr_id = generate_adr_id(title, existing_ids)

            metadata = ADRMetadata(
                id=adr_id,
                title=title,
                date=date.today(),
                status=ADRStatus.PROPOSED,
                format=template or ctx.config.template,
            )

            adr = ADR(metadata=metadata, content=response.content)
            ctx.notes_manager.add(adr)

            console.print()
            console.print(f"[green]✓[/green] Created ADR: [cyan]{adr_id}[/cyan]")
            console.print("  Status: proposed (review before accepting)")
            console.print()
            console.print(f"[dim]Edit with: git adr edit {adr_id}[/dim]")

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
