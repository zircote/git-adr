"""Implementation of `git adr rm` command.

Removes an ADR from git notes storage.
"""

from __future__ import annotations

import typer
from rich.console import Console

from git_adr.commands._shared import setup_command_context
from git_adr.core import GitError

console = Console()
err_console = Console(stderr=True)


def run_rm(
    adr_id: str,
    force: bool = False,
) -> None:
    """Remove an ADR from git notes.

    Args:
        adr_id: ADR ID to remove.
        force: Skip confirmation prompt.

    Raises:
        typer.Exit: On error.
    """
    try:
        # Initialize command context
        ctx = setup_command_context()

        # Get ADR to verify it exists
        adr = ctx.notes_manager.get(adr_id)

        if adr is None:
            err_console.print(f"[red]Error:[/red] ADR not found: {adr_id}")
            raise typer.Exit(1)

        # Confirm deletion unless --force
        if not force:
            console.print(f"[bold]ADR:[/bold] {adr.metadata.title}")
            console.print(f"[bold]ID:[/bold] {adr.metadata.id}")
            console.print(f"[bold]Status:[/bold] {adr.metadata.status.value}")
            console.print()

            # Check if ADR has linked commits
            if adr.metadata.linked_commits:
                commits = ", ".join(c[:8] for c in adr.metadata.linked_commits)
                console.print(
                    f"[yellow]Warning:[/yellow] ADR is linked to commits: {commits}"
                )

            # Check if ADR supersedes another
            if adr.metadata.supersedes:
                console.print(
                    f"[yellow]Warning:[/yellow] ADR supersedes: {adr.metadata.supersedes}"
                )

            # Check if ADR is superseded by another
            if adr.metadata.superseded_by:
                console.print(
                    f"[yellow]Warning:[/yellow] ADR is superseded by: {adr.metadata.superseded_by}"
                )

            confirm = typer.confirm("Remove this ADR?")
            if not confirm:
                console.print("[dim]Aborted[/dim]")
                raise typer.Exit(0)

        # Remove the ADR
        result = ctx.notes_manager.remove(adr_id)

        if result:
            console.print(f"[green]✓[/green] Removed ADR: {adr_id}")
        else:
            err_console.print(f"[red]Error:[/red] Failed to remove ADR: {adr_id}")
            raise typer.Exit(1)

    except GitError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
