"""Implementation of `git adr sync` command.

Synchronizes ADR notes with remote repositories.
"""

from __future__ import annotations

import typer
from rich.console import Console

from git_adr.commands._shared import setup_command_context
from git_adr.core import GitError

console = Console()
err_console = Console(stderr=True)


def run_sync(
    push: bool = True,
    pull: bool = True,
    remote: str = "origin",
    merge_strategy: str = "union",
) -> None:
    """Synchronize ADR notes with remote.

    Args:
        push: Push notes to remote.
        pull: Pull notes from remote.
        remote: Remote name.
        merge_strategy: Strategy for merging conflicts.

    Raises:
        typer.Exit: On error.
    """
    try:
        # Initialize command context
        ctx = setup_command_context()

        # Verify remote exists
        remotes = ctx.git.get_remotes()
        if remote not in remotes:
            err_console.print(f"[red]Error:[/red] Remote not found: {remote}")
            err_console.print(f"Available remotes: {', '.join(remotes) or 'none'}")
            raise typer.Exit(1)

        # Pull first (to get latest changes)
        if pull:
            console.print(f"[dim]Fetching notes from {remote}...[/dim]")
            try:
                ctx.notes_manager.sync_pull(
                    remote=remote, merge_strategy=merge_strategy
                )
                console.print(f"[green]✓[/green] Pulled ADR notes from {remote}")
            except GitError as e:
                # Check for "remote ref not found" error - this is expected when
                # notes haven't been pushed to the remote yet. String matching is
                # used because git doesn't provide distinct exit codes for this case.
                # Prefer exit_code check if available, fallback to string match if not
                if getattr(e, "exit_code", None) == 128:
                    console.print(
                        f"[yellow]Note:[/yellow] No remote notes found on {remote}"
                    )
                elif "couldn't find remote ref" in str(e).lower():
                    # Fallback for legacy GitError without exit_code
                    console.print(
                        f"[yellow]Note:[/yellow] No remote notes found on {remote}"
                    )
                else:
                    raise

        # Push
        if push:
            console.print(f"[dim]Pushing notes to {remote}...[/dim]")
            try:
                ctx.notes_manager.sync_push(remote=remote)
                console.print(f"[green]✓[/green] Pushed ADR notes to {remote}")
            except GitError as e:
                if "failed to push" in str(e).lower():
                    err_console.print(
                        "[red]Error:[/red] Failed to push notes. "
                        "Try pulling first or use --force."
                    )
                    raise typer.Exit(1)
                raise

        console.print()
        console.print("[green]Sync complete![/green]")

    except GitError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
