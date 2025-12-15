"""Implementation of `git adr show` command.

Displays a single ADR with formatting and syntax highlighting.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from git_adr.core import (
    ConfigManager,
    GitError,
    NotesManager,
    get_git,
)

console = Console()
err_console = Console(stderr=True)


def run_show(
    adr_id: str,
    format_: str = "markdown",
    metadata_only: bool = False,
) -> None:
    """Display a single ADR.

    Args:
        adr_id: ADR ID to display.
        format_: Output format (markdown, yaml, json).
        metadata_only: Show only metadata.

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

        # Get ADR
        notes_manager = NotesManager(git, config)
        adr = notes_manager.get(adr_id)

        if adr is None:
            err_console.print(f"[red]Error:[/red] ADR not found: {adr_id}")
            raise typer.Exit(1)

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


def _format_status(status) -> str:
    """Format status with color.

    Args:
        status: ADR status.

    Returns:
        Formatted status string.
    """
    from git_adr.core import ADRStatus

    styles = {
        ADRStatus.DRAFT: "dim",
        ADRStatus.PROPOSED: "yellow",
        ADRStatus.ACCEPTED: "green",
        ADRStatus.REJECTED: "red",
        ADRStatus.DEPRECATED: "dim red",
        ADRStatus.SUPERSEDED: "dim",
    }
    style = styles.get(status, "default")
    return f"[{style}]{status.value}[/{style}]"
