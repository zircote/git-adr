"""Implementation of `git adr artifacts` command.

Lists artifacts attached to an ADR.
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from git_adr.commands._shared import setup_command_context
from git_adr.core import GitError

console = Console()
err_console = Console(stderr=True)


def run_artifacts(adr_id: str) -> None:
    """List artifacts attached to an ADR.

    Args:
        adr_id: ADR ID.

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

        # List artifacts
        artifacts = ctx.notes_manager.list_artifacts(adr_id)

        if not artifacts:
            console.print(f"[dim]No artifacts attached to {adr_id}[/dim]")
            return

        table = Table(show_header=True, header_style="bold")
        table.add_column("Name", style="cyan")
        table.add_column("Size")
        table.add_column("Type", style="dim")
        table.add_column("SHA256", style="dim")

        for artifact in artifacts:
            table.add_row(
                artifact.name,
                _format_size(artifact.size),
                artifact.mime_type,
                artifact.sha256[:16] + "...",
            )

        console.print(f"Artifacts for ADR [cyan]{adr_id}[/cyan]:")
        console.print()
        console.print(table)

    except GitError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def _format_size(size: int) -> str:
    """Format file size for display.

    Args:
        size: Size in bytes.

    Returns:
        Formatted size string.
    """
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    else:
        return f"{size / (1024 * 1024):.1f} MB"
