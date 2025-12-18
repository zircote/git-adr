"""Implementation of `git adr attach` command.

Attaches files (diagrams, images) to ADRs.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from git_adr.commands._shared import setup_command_context
from git_adr.core import GitError

console = Console()
err_console = Console(stderr=True)


def _validate_input_path(file: str) -> Path:
    """Validate input file path.

    For attach command, we allow reading files from anywhere on the filesystem
    since the user explicitly provides the path. This is a read-only operation.

    Args:
        file: User-provided file path.

    Returns:
        Validated and resolved file path.

    Raises:
        typer.Exit: If file doesn't exist or is not a regular file.
    """
    # Resolve the user-provided path
    file_path = Path(file).expanduser().resolve()

    # Verify file exists
    if not file_path.exists():
        err_console.print(f"[red]Error:[/red] File not found: {file}")
        raise typer.Exit(1)

    if not file_path.is_file():
        err_console.print(f"[red]Error:[/red] Not a file: {file}")
        raise typer.Exit(1)

    return file_path


def run_attach(
    adr_id: str,
    file: str,
    alt: str | None = None,
    name: str | None = None,
) -> None:
    """Attach a file to an ADR.

    Args:
        adr_id: ADR ID to attach to.
        file: Path to file.
        alt: Alt text for images.
        name: Override filename.

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

        # Validate file path
        file_path = _validate_input_path(file)

        # Check size warning
        size = file_path.stat().st_size
        if size > ctx.config.artifact_warn_size:
            size_mb = size / (1024 * 1024)
            console.print(
                f"[yellow]Warning:[/yellow] File is {size_mb:.1f}MB. "
                "Large attachments may slow down repository sync."
            )

        # Attach file
        try:
            artifact = ctx.notes_manager.attach_artifact(
                adr_id=adr_id,
                file_path=file_path,
                name=name,
                alt_text=alt or "",
            )

            console.print(
                f"[green]Attached[/green] [cyan]{artifact.name}[/cyan] to ADR {adr_id}"
            )
            console.print(f"  SHA256: {artifact.sha256[:16]}...")
            console.print(f"  Size: {_format_size(artifact.size)}")
            console.print(f"  Type: {artifact.mime_type}")

        except ValueError as e:
            err_console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

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
        return f"{size} bytes"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    else:
        return f"{size / (1024 * 1024):.1f} MB"
