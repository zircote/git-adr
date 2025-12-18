"""Implementation of `git adr artifact-rm` command.

Removes an artifact reference from an ADR.
"""

from __future__ import annotations

import typer
from rich.console import Console

from git_adr.commands._shared import setup_command_context
from git_adr.core import GitError

console = Console()
err_console = Console(stderr=True)


def run_artifact_rm(
    adr_id: str,
    name: str,
) -> None:
    """Remove an artifact from an ADR.

    Note: The artifact blob remains in git until garbage collected.

    Args:
        adr_id: ADR ID.
        name: Artifact name or SHA256 prefix.

    Raises:
        typer.Exit: On error.
    """
    try:
        # Initialize command context
        ctx = setup_command_context()

        # Verify ADR exists
        adr = ctx.notes_manager.get(adr_id)
        if adr is None:
            err_console.print(f"[red]Error:[/red] ADR not found: {adr_id}")
            raise typer.Exit(1)

        # Find the artifact
        artifacts = ctx.notes_manager.list_artifacts(adr_id)
        artifact_info = None

        for artifact in artifacts:
            if artifact.name == name or artifact.sha256.startswith(name):
                artifact_info = artifact
                break

        if artifact_info is None:
            err_console.print(f"[red]Error:[/red] Artifact not found: {name}")
            console.print()
            if artifacts:
                console.print("Available artifacts:")
                for a in artifacts:
                    console.print(f"  • {a.name}")
            raise typer.Exit(1)

        # Confirm removal
        if not typer.confirm(
            f"Remove artifact '{artifact_info.name}' from ADR {adr_id}?"
        ):
            console.print("[yellow]Aborted[/yellow]")
            return

        # Remove artifact reference
        if ctx.notes_manager.remove_artifact(adr_id, artifact_info.sha256):
            console.print(
                f"[green]✓[/green] Removed artifact [cyan]{artifact_info.name}[/cyan] "
                f"from ADR {adr_id}"
            )
            console.print(
                "[dim]Note: The artifact blob will be garbage collected later[/dim]"
            )
        else:
            err_console.print("[red]Error:[/red] Failed to remove artifact")
            raise typer.Exit(1)

    except GitError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
