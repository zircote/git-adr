"""Implementation of `git adr rm` command.

Removes an ADR from git notes storage.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from git_adr.core import (
    ConfigManager,
    GitError,
    NotesManager,
    get_git,
)

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
        # Get git and config
        git = get_git(cwd=Path.cwd())

        if not git.is_repository():
            err_console.print("[red]Error:[/red] Not a git repository")
            raise typer.Exit(1)

        config_manager = ConfigManager(git)
        config = config_manager.load()

        # Check if initialized
        if not config_manager.get("initialized"):
            err_console.print(
                "[red]Error:[/red] git-adr not initialized. Run `git adr init` first."
            )
            raise typer.Exit(1)

        # Get ADR to verify it exists
        notes_manager = NotesManager(git, config)
        adr = notes_manager.get(adr_id)

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
        result = notes_manager.remove(adr_id)

        if result:
            console.print(f"[green]✓[/green] Removed ADR: {adr_id}")
        else:
            err_console.print(f"[red]Error:[/red] Failed to remove ADR: {adr_id}")
            raise typer.Exit(1)

    except GitError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
