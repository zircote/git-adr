"""Implementation of `git adr init` command.

Initializes ADR tracking in a git repository by:
- Creating the notes namespace
- Configuring fetch/push for notes sync
- Setting up rebase safety configuration
- Creating the initial ADR (ADR-0000: Use ADRs)
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import typer
from rich.console import Console

from git_adr.core import (
    ADR,
    ADRMetadata,
    ADRStatus,
    ConfigManager,
    GitError,
    NotARepositoryError,
    NotesManager,
    get_git,
)
from git_adr.core.templates import render_initial_adr

if TYPE_CHECKING:
    pass

console = Console()
err_console = Console(stderr=True)


def run_init(
    namespace: str = "adr",
    template: str = "madr",
    force: bool = False,
) -> None:
    """Initialize git-adr in the current repository.

    Args:
        namespace: Notes namespace for ADRs.
        template: Default template format.
        force: If True, reinitialize even if already initialized.

    Raises:
        typer.Exit: On error.
    """
    try:
        # Get git executor
        git = get_git(cwd=Path.cwd())

        # Verify we're in a git repository
        if not git.is_repository():
            err_console.print("[red]Error:[/red] Not a git repository")
            raise typer.Exit(1)

        # Create config manager and set initial config
        config_manager = ConfigManager(git)

        # Check if already initialized
        existing_namespace = config_manager.get("namespace")
        if existing_namespace and not force:
            err_console.print(
                f"[yellow]Warning:[/yellow] git-adr is already initialized "
                f"(namespace: {existing_namespace})"
            )
            err_console.print("Use --force to reinitialize")
            raise typer.Exit(1)

        # Set configuration
        config_manager.set("namespace", namespace)
        config_manager.set("template", template)

        # Load config
        config = config_manager.load()

        # Initialize notes manager
        notes_manager = NotesManager(git, config)

        # Configure remotes for notes sync
        remotes = git.get_remotes()
        if remotes:
            console.print(f"Configuring notes sync for remote(s): {', '.join(remotes)}")
            notes_manager.initialize(force=force)
        else:
            console.print(
                "[yellow]Note:[/yellow] No remotes configured. "
                "ADRs will be stored locally until you add a remote."
            )
            # Still set the initialized flag
            git.config_set("adr.initialized", "true")

        # Configure notes rewrite for rebase safety
        # This ensures notes are preserved during rebase/amend operations
        git.config_set("notes.rewriteRef", config.notes_ref)
        git.config_set("notes.rewriteRef", config.artifacts_ref, append=True)
        git.config_set("notes.rewrite.rebase", "true")
        git.config_set("notes.rewrite.amend", "true")

        # Create initial ADR
        _create_initial_adr(notes_manager, namespace)

        # Success message
        console.print()
        console.print("[green]✓[/green] git-adr initialized successfully!")
        console.print()
        console.print("Configuration:")
        console.print(f"  • Namespace: [cyan]{namespace}[/cyan]")
        console.print(f"  • Template: [cyan]{template}[/cyan]")
        console.print(f"  • Notes ref: [cyan]{config.notes_ref}[/cyan]")
        console.print()
        console.print("Next steps:")
        console.print(
            '  • [cyan]git adr new "Your Decision Title"[/cyan] - Create a new ADR'
        )
        console.print("  • [cyan]git adr list[/cyan] - List all ADRs")
        console.print("  • [cyan]git adr --help[/cyan] - See all commands")

    except NotARepositoryError:
        err_console.print("[red]Error:[/red] Not a git repository")
        raise typer.Exit(1)
    except GitError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def _create_initial_adr(notes_manager: NotesManager, namespace: str) -> None:
    """Create the initial ADR documenting the decision to use ADRs.

    Args:
        notes_manager: Notes manager instance.
        namespace: Notes namespace.
    """
    from datetime import date

    # Check if initial ADR already exists
    initial_id = "00000000-use-adrs"
    if notes_manager.exists(initial_id):
        console.print(f"[dim]Initial ADR ({initial_id}) already exists, skipping[/dim]")
        return

    # Create initial ADR
    content = render_initial_adr(
        adr_id=initial_id,
        title="Use Architecture Decision Records",
    )

    metadata = ADRMetadata(
        id=initial_id,
        title="Use Architecture Decision Records",
        date=date.today(),
        status=ADRStatus.ACCEPTED,
        tags=["documentation", "process"],
        format="nygard",
    )

    adr = ADR(metadata=metadata, content=content)

    try:
        notes_manager.add(adr)
        console.print(f"[dim]Created initial ADR: {initial_id}[/dim]")
    except GitError as e:
        console.print(f"[yellow]Warning:[/yellow] Could not create initial ADR: {e}")
