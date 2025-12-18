"""Implementation of `git adr show` command.

Displays a single ADR with formatting and syntax highlighting.
"""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING

import typer
import yaml
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from git_adr.commands._shared import get_status_style, setup_command_context
from git_adr.core import ADRStatus, GitError

if TYPE_CHECKING:
    from git_adr.core.notes import NotesManager

console = Console()
err_console = Console(stderr=True)


def run_show(
    adr_id: str,
    format_: str = "markdown",
    metadata_only: bool = False,
    interactive: bool = True,
) -> None:
    """Display a single ADR.

    Args:
        adr_id: ADR ID to display.
        format_: Output format (markdown, yaml, json).
        metadata_only: Show only metadata.
        interactive: Allow interactive prompts (e.g., to add missing deciders).

    Raises:
        typer.Exit: On error.
    """
    try:
        # Initialize command context
        ctx = setup_command_context()

        # Get ADR
        adr = ctx.notes_manager.get(adr_id)

        if adr is None:
            err_console.print(f"[red]Error:[/red] ADR not found: {adr_id}")
            raise typer.Exit(1)

        # Check for missing deciders and prompt if interactive
        if (
            interactive
            and format_ == "markdown"
            and not adr.metadata.deciders
            and sys.stdin.isatty()
        ):
            adr = _prompt_for_deciders(adr, ctx.notes_manager)

        # Output based on format
        if format_ == "markdown":
            _output_markdown(adr, metadata_only)
        elif format_ == "yaml":
            _output_yaml(adr, metadata_only)
        elif format_ == "json":
            _output_json(adr, metadata_only)
        else:
            err_console.print(f"[red]Error:[/red] Unknown format: {format_}")
            raise typer.Exit(1)

    except GitError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def _output_markdown(adr, metadata_only: bool) -> None:
    """Output ADR as formatted markdown.

    Args:
        adr: ADR to display.
        metadata_only: Show only metadata.
    """
    # Create header panel
    header_content = [
        f"[bold]{adr.metadata.title}[/bold]",
        "",
        f"ID: [cyan]{adr.metadata.id}[/cyan]",
        f"Date: {adr.metadata.date.isoformat()}",
        f"Status: {_format_status(adr.metadata.status)}",
    ]

    # Stakeholder metadata (RACI-inspired)
    if adr.metadata.deciders:
        header_content.append(f"Deciders: {', '.join(adr.metadata.deciders)}")
    if adr.metadata.consulted:
        header_content.append(f"Consulted: {', '.join(adr.metadata.consulted)}")
    if adr.metadata.informed:
        header_content.append(f"Informed: {', '.join(adr.metadata.informed)}")

    if adr.metadata.tags:
        header_content.append(f"Tags: {', '.join(adr.metadata.tags)}")

    if adr.metadata.linked_commits:
        commits = ", ".join(c[:8] for c in adr.metadata.linked_commits)
        header_content.append(f"Linked commits: [dim]{commits}[/dim]")

    if adr.metadata.supersedes:
        header_content.append(f"Supersedes: [yellow]{adr.metadata.supersedes}[/yellow]")

    if adr.metadata.superseded_by:
        header_content.append(
            f"Superseded by: [yellow]{adr.metadata.superseded_by}[/yellow]"
        )

    console.print(Panel("\n".join(header_content), title="ADR", border_style="blue"))

    if not metadata_only:
        console.print()
        console.print(Markdown(adr.content))


def _output_yaml(adr, metadata_only: bool) -> None:
    """Output ADR as YAML.

    Args:
        adr: ADR to display.
        metadata_only: Show only metadata.
    """
    data = adr.metadata.to_dict()

    if not metadata_only:
        data["content"] = adr.content

    console.print(yaml.dump(data, default_flow_style=False, sort_keys=False))


def _output_json(adr, metadata_only: bool) -> None:
    """Output ADR as JSON.

    Args:
        adr: ADR to display.
        metadata_only: Show only metadata.
    """
    data = adr.metadata.to_dict()

    if not metadata_only:
        data["content"] = adr.content

    console.print(json.dumps(data, indent=2))


def _format_status(status: ADRStatus) -> str:
    """Format status with color.

    Args:
        status: ADR status.

    Returns:
        Formatted status string.
    """
    style = get_status_style(status)
    return f"[{style}]{status.value}[/{style}]"


def _prompt_for_deciders(adr, notes_manager: NotesManager):
    """Prompt user to add deciders to an ADR missing them.

    Args:
        adr: ADR with missing deciders.
        notes_manager: NotesManager for saving updates.

    Returns:
        Updated ADR (or original if user declines).
    """
    from dataclasses import replace

    from git_adr.core import ADR

    console.print()
    console.print("[yellow]⚠ This ADR has no deciders recorded.[/yellow]")

    if not typer.confirm("Would you like to add deciders now?", default=False):
        return adr

    deciders_input = typer.prompt(
        "Enter deciders (comma-separated)",
        default="",
    )

    if not deciders_input.strip():
        console.print("[dim]No deciders added.[/dim]")
        return adr

    # Parse comma-separated deciders
    deciders = [d.strip() for d in deciders_input.split(",") if d.strip()]

    if not deciders:
        console.print("[dim]No valid deciders provided.[/dim]")
        return adr

    # Update ADR metadata
    updated_metadata = replace(adr.metadata, deciders=deciders)
    updated_adr = ADR(metadata=updated_metadata, content=adr.content)

    # Save to git notes
    notes_manager.update(updated_adr)

    console.print(f"[green]✓[/green] Added deciders: {', '.join(deciders)}")
    console.print()

    return updated_adr
