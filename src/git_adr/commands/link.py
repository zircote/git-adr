"""Implementation of `git adr link` command.

Associates ADRs with commits for bidirectional traceability.
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


def run_link(
    adr_id: str,
    commits: list[str],
    unlink: bool = False,
) -> None:
    """Link or unlink ADR with commits.

    Args:
        adr_id: ADR ID.
        commits: Commit SHAs to link/unlink.
        unlink: If True, remove links instead of adding.

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
        adr = notes_manager.get(adr_id)

        if adr is None:
            err_console.print(f"[red]Error:[/red] ADR not found: {adr_id}")
            raise typer.Exit(1)

        # Validate commits exist
        invalid_commits = []
        for commit in commits:
            if not git.commit_exists(commit):
                invalid_commits.append(commit)

        if invalid_commits:
            for commit in invalid_commits:
                err_console.print(
                    f"[yellow]Warning:[/yellow] Commit not found: {commit[:8]}"
                )

        # Update linked commits
        current = set(adr.metadata.linked_commits)
        changes = []

        for commit in commits:
            if unlink:
                if commit in current:
                    current.discard(commit)
                    changes.append(f"Unlinked: {commit[:8]}")
            elif commit not in current:
                current.add(commit)
                changes.append(f"Linked: {commit[:8]}")

        if not changes:
            console.print("[dim]No changes made[/dim]")
            return

        adr.metadata.linked_commits = list(current)
        notes_manager.update(adr)

        action = "Unlinked" if unlink else "Linked"
        console.print(
            f"[green]✓[/green] {action} commits for ADR: [cyan]{adr_id}[/cyan]"
        )
        for change in changes:
            console.print(f"  • {change}")

    except GitError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
