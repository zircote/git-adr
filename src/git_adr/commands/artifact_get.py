"""Implementation of `git adr artifact-get` command.

Extracts an artifact from an ADR to a file.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from git_adr.commands._shared import setup_command_context
from git_adr.core import GitError

console = Console()
err_console = Console(stderr=True)


def _validate_output_path(output: str | None, default_name: str) -> Path:
    """Validate and resolve output path, preventing path traversal.

    Args:
        output: User-provided output path (may be None).
        default_name: Default filename to use if output is None.

    Returns:
        Validated and resolved output path within cwd.

    Raises:
        typer.Exit: If path traversal is detected.
    """
    cwd = Path.cwd().resolve()

    if output:
        # Resolve the user-provided path
        output_path = Path(output).resolve()

        # Security: prevent path traversal by ensuring output is within cwd
        try:
            output_path.relative_to(cwd)
        except ValueError:
            err_console.print(
                "[red]Error:[/red] Output path must be within current directory"
            )
            raise typer.Exit(1)
    else:
        # Default: use artifact name in current directory
        output_path = cwd / default_name

    return output_path


def run_artifact_get(
    adr_id: str,
    name: str,
    output: str | None = None,
) -> None:
    """Extract an artifact to a file.

    Args:
        adr_id: ADR ID.
        name: Artifact name.
        output: Output path (default: original filename).

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
            console.print("Available artifacts:")
            for a in artifacts:
                console.print(f"  - {a.name}")
            raise typer.Exit(1)

        # Get artifact content
        result = ctx.notes_manager.get_artifact(artifact_info.sha256)
        if result is None:
            err_console.print("[red]Error:[/red] Could not retrieve artifact content")
            raise typer.Exit(1)

        artifact_info, content = result

        # Validate output path (SEC-001: prevent path traversal)
        output_path = _validate_output_path(output, artifact_info.name)

        # Check if output exists
        if output_path.exists():
            if not typer.confirm(f"Overwrite {output_path}?"):
                console.print("[yellow]Aborted[/yellow]")
                return

        # Write content
        output_path.write_bytes(content)

        console.print(
            f"[green]Extracted[/green] [cyan]{artifact_info.name}[/cyan] "
            f"to {output_path}"
        )

    except GitError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
