"""Implementation of `git adr onboard` command.

Interactive onboarding wizard for new team members.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from git_adr.commands._shared import setup_command_context
from git_adr.core import GitError
from git_adr.core.adr import ADRStatus
from git_adr.core.index import IndexManager

if TYPE_CHECKING:
    from git_adr.core.notes import NotesManager

console = Console()
err_console = Console(stderr=True)


def run_onboard(
    role: str = "developer",
    quick: bool = False,
    continue_: bool = False,
    status_: bool = False,
) -> None:
    """Run the interactive onboarding wizard.

    Args:
        role: User role (developer, reviewer, architect).
        quick: 5-minute executive summary only.
        continue_: Resume from last position.
        status_: Show onboarding progress.

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

        if not all_adrs:
            console.print("[dim]No ADRs found in this repository.[/dim]")
            console.print()
            console.print("To get started:")
            console.print('  git adr new "Title of your first decision"')
            return

        # Show status if requested
        if status_:
            _show_onboard_status(all_adrs)
            return

        # Continue from last position
        if continue_:
            console.print("[dim]Resuming onboarding...[/dim]")
            # TODO: Load last position from config
            console.print("[yellow]Resume feature coming soon[/yellow]")
            return

        if quick:
            _quick_onboard(all_adrs, role)
        else:
            _interactive_onboard(all_adrs, ctx.notes_manager, role)

    except GitError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def _show_onboard_status(all_adrs: list) -> None:
    """Show onboarding progress status."""
    accepted = [a for a in all_adrs if a.metadata.status == ADRStatus.ACCEPTED]

    console.print()
    console.print("[bold]Onboarding Status[/bold]")
    console.print()
    console.print(f"  Total ADRs: {len(all_adrs)}")
    console.print(f"  Key decisions: {len(accepted)}")
    console.print()
    console.print("[dim]Progress tracking coming soon[/dim]")


def _quick_onboard(all_adrs: list, role: str) -> None:
    """Quick onboarding - show key ADRs."""
    console.print()
    console.print(
        Panel(
            f"[bold]Welcome to the Architecture Decision Records![/bold]\n\n"
            f"This project uses ADRs to document significant technical decisions.\n"
            f"Your role: {role}",
            title="Quick Onboarding",
        )
    )

    # Show accepted ADRs (most important)
    accepted = [a for a in all_adrs if a.metadata.status == ADRStatus.ACCEPTED]

    console.print()
    console.print(f"[bold]Key Decisions ({len(accepted)} accepted ADRs):[/bold]")
    console.print()

    for adr in sorted(accepted, key=lambda a: a.metadata.date):
        tags = f" [{', '.join(adr.metadata.tags)}]" if adr.metadata.tags else ""
        console.print(f"  [cyan]{adr.metadata.id}[/cyan]: {adr.metadata.title}{tags}")

    console.print()
    console.print("[dim]To view an ADR: git adr show <id>[/dim]")
    console.print("[dim]To see all ADRs: git adr list[/dim]")


def _interactive_onboard(
    all_adrs: list, notes_manager: NotesManager, role: str
) -> None:
    """Interactive onboarding - guided tour."""
    console.print()
    console.print(
        Panel(
            f"[bold]Welcome to the Architecture Decision Records![/bold]\n\n"
            f"Let's take a guided tour of the key technical decisions "
            f"that shape this project.\n\n"
            f"Your role: {role}",
            title="Interactive Onboarding",
        )
    )

    # Categorize ADRs
    accepted = [a for a in all_adrs if a.metadata.status == ADRStatus.ACCEPTED]
    superseded = [a for a in all_adrs if a.metadata.status == ADRStatus.SUPERSEDED]

    # Overview
    console.print()
    console.print("[bold]Overview:[/bold]")
    console.print(f"  Total ADRs: {len(all_adrs)}")
    console.print(f"  Active decisions: {len(accepted)}")
    console.print(f"  Superseded: {len(superseded)}")

    if not accepted:
        console.print()
        console.print(
            "[yellow]No accepted ADRs yet. Still in decision-making phase.[/yellow]"
        )
        return

    # Group by tags
    tag_groups: dict[str, list] = {}
    for adr in accepted:
        for tag in adr.metadata.tags or ["general"]:
            tag_groups.setdefault(tag, []).append(adr)

    console.print()
    console.print("[bold]ADRs by Topic:[/bold]")

    for tag, adrs in sorted(tag_groups.items()):
        console.print()
        console.print(f"[cyan]{tag.upper()}[/cyan]")
        for adr in adrs:
            console.print(f"  • {adr.metadata.id}: {adr.metadata.title}")

    # Interactive viewing
    console.print()
    if typer.confirm("Would you like to read through key ADRs now?"):
        for i, adr in enumerate(accepted[:5], 1):  # Show top 5
            console.print()
            console.print(
                f"[bold]({i}/{min(5, len(accepted))}) {adr.metadata.id}: {adr.metadata.title}[/bold]"
            )
            console.print()

            # Show a summary (first 500 chars of content)
            preview = adr.content[:500]
            if len(adr.content) > 500:
                preview += "..."

            console.print(Markdown(preview))

            console.print()
            if i < min(5, len(accepted)):
                if not typer.confirm("Continue to next ADR?"):
                    break

    console.print()
    console.print("[green]Onboarding complete![/green]")
    console.print()
    console.print("Useful commands:")
    console.print("  [cyan]git adr list[/cyan]     - List all ADRs")
    console.print("  [cyan]git adr show <id>[/cyan] - View an ADR")
    console.print("  [cyan]git adr search <q>[/cyan] - Search ADRs")
    console.print("  [cyan]git adr stats[/cyan]    - View statistics")
