"""Shared utilities for git-adr commands.

This module provides common functionality used across multiple commands,
reducing code duplication and ensuring consistency.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import typer
from rich.console import Console

from git_adr.core import ADRStatus, Config, ConfigManager, Git, NotesManager, get_git
from git_adr.core.index import IndexManager

# Status-to-style mapping for Rich console output
# Used by list, search, and show commands
STATUS_STYLES: dict[ADRStatus, str] = {
    ADRStatus.DRAFT: "dim",
    ADRStatus.PROPOSED: "yellow",
    ADRStatus.ACCEPTED: "green",
    ADRStatus.REJECTED: "red",
    ADRStatus.DEPRECATED: "dim red",
    ADRStatus.SUPERSEDED: "dim",
}


def get_status_style(status: ADRStatus) -> str:
    """Get the Rich style for an ADR status.

    Args:
        status: ADR status.

    Returns:
        Rich style name for the status.
    """
    return STATUS_STYLES.get(status, "default")


@dataclass
class CommandContext:
    """Context object containing initialized git-adr components.

    Attributes:
        git: Git instance for repository operations.
        config_manager: Configuration manager.
        config: Loaded configuration.
        notes_manager: Notes manager for ADR operations.
        index_manager: Optional index manager for search operations.
    """

    git: Git
    config_manager: ConfigManager
    config: Config
    notes_manager: NotesManager
    index_manager: IndexManager | None = None


def setup_command_context(
    cwd: Path | None = None,
    require_index: bool = False,
) -> CommandContext:
    """Initialize git-adr context for a command.

    This function handles the common initialization pattern used by most commands:
    1. Get git instance and verify it's a repository
    2. Load configuration and verify git-adr is initialized
    3. Create NotesManager and optionally IndexManager

    Args:
        cwd: Working directory (defaults to current directory).
        require_index: Whether to create IndexManager.

    Returns:
        CommandContext with initialized components.

    Raises:
        typer.Exit: If prerequisites are not met (not a git repo, not initialized).
    """
    err_console = Console(stderr=True)

    # Get git instance
    git = get_git(cwd=cwd or Path.cwd())

    # Check if git repository
    if not git.is_repository():
        err_console.print("[red]Error:[/red] Not a git repository")
        raise typer.Exit(1)

    # Load configuration
    config_manager = ConfigManager(git)
    config = config_manager.load()

    # Check if initialized
    if not config_manager.get("initialized"):
        err_console.print(
            "[red]Error:[/red] git-adr not initialized. Run `git adr init` first."
        )
        raise typer.Exit(1)

    # Create managers
    notes_manager = NotesManager(git, config)
    index_manager = IndexManager(notes_manager) if require_index else None

    return CommandContext(
        git=git,
        config_manager=config_manager,
        config=config,
        notes_manager=notes_manager,
        index_manager=index_manager,
    )
