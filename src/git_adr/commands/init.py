"""Implementation of `git adr init` command.

Initializes ADR tracking in a git repository by:
- Creating the notes namespace
- Configuring fetch/push for notes sync
- Setting up rebase safety configuration
- Creating the initial ADR (ADR-0000: Use ADRs)
- Optionally installing pre-push hooks
- Optionally generating GitHub Actions CI workflows
"""

from __future__ import annotations

import sys
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
from git_adr.core.templates import TEMPLATE_DESCRIPTIONS, render_initial_adr

if TYPE_CHECKING:
    pass

# Default template format for ADRs
DEFAULT_TEMPLATE = "madr"

console = Console()
err_console = Console(stderr=True)


def _is_interactive() -> bool:
    """Check if running in an interactive terminal.

    Returns True only if both stdin and stdout are connected to a TTY,
    indicating a user is present and can respond to prompts.
    """
    return sys.stdin.isatty() and sys.stdout.isatty()


def _prompt_for_template() -> str:
    """Interactively prompt user to select a template format.

    Displays available templates with descriptions and accepts
    either a number (1-6) or template name as input.

    Returns:
        Selected template name (defaults to DEFAULT_TEMPLATE if invalid input).
    """
    console.print()
    console.print("[bold]Available ADR Templates:[/bold]")

    template_names = list(TEMPLATE_DESCRIPTIONS.keys())
    for i, (name, desc) in enumerate(TEMPLATE_DESCRIPTIONS.items(), 1):
        marker = " [dim](default)[/dim]" if name == DEFAULT_TEMPLATE else ""
        console.print(f"  {i}. [cyan]{name}[/cyan] - {desc}{marker}")

    console.print()
    choice = typer.prompt(
        "Select template format (number or name)",
        default=DEFAULT_TEMPLATE,
        show_default=True,
    )

    # Accept number or name
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(template_names):
            return template_names[idx]
        console.print(f"[yellow]Invalid selection, using '{DEFAULT_TEMPLATE}'[/yellow]")
        return DEFAULT_TEMPLATE

    if choice in template_names:
        return choice

    console.print(
        f"[yellow]Unknown template '{choice}', using '{DEFAULT_TEMPLATE}'[/yellow]"
    )
    return DEFAULT_TEMPLATE


def run_init(
    namespace: str = "adr",
    template: str | None = None,
    force: bool = False,
    no_input: bool = False,
    install_hooks: bool | None = None,
    setup_github_ci: bool | None = None,
) -> None:
    """Initialize git-adr in the current repository.

    Args:
        namespace: Notes namespace for ADRs.
        template: Default template format. If None, prompts interactively.
        force: If True, reinitialize even if already initialized.
        no_input: If True, skip all interactive prompts.
        install_hooks: If True, install hooks. If False, skip. If None, prompt.
        setup_github_ci: If True, generate CI. If False, skip. If None, prompt.

    Raises:
        typer.Exit: On error.
    """
    interactive = not no_input and _is_interactive()

    try:
        # Get git executor
        git = get_git(cwd=Path.cwd())

        # Verify we're in a git repository
        if not git.is_repository():
            err_console.print("[red]Error:[/red] Not a git repository")
            raise typer.Exit(1)

        # Create config manager and set initial config
        config_manager = ConfigManager(git)

        # Check if already initialized by looking for adr.initialized config
        # Note: We check via git config directly because ConfigManager.get returns defaults
        is_initialized = git.config_get("adr.initialized") == "true"
        if is_initialized and not force:
            existing_namespace = config_manager.get("namespace")
            err_console.print(
                f"[yellow]Warning:[/yellow] git-adr is already initialized "
                f"(namespace: {existing_namespace})"
            )
            err_console.print("Use --force to reinitialize")
            raise typer.Exit(1)

        # Determine template (interactive or default)
        if template is None:
            template = _prompt_for_template() if interactive else DEFAULT_TEMPLATE

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
        # When reinitializing with --force, first clear any existing multi-valued config
        if force:
            git.config_unset("notes.rewriteRef", all_values=True)
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

        # Track what was installed for contextual next steps
        hooks_installed = False
        ci_generated = False

        # Hooks installation
        hooks_installed = _handle_hooks_installation(
            install_hooks=install_hooks,
            interactive=interactive,
            force=force,
        )

        # GitHub CI generation
        ci_generated = _handle_github_ci_setup(
            setup_github_ci=setup_github_ci,
            interactive=interactive,
        )

        # Contextual next steps
        _print_next_steps(hooks_installed=hooks_installed, ci_generated=ci_generated)

    except NotARepositoryError:
        err_console.print("[red]Error:[/red] Not a git repository")
        raise typer.Exit(1)
    except GitError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def _handle_hooks_installation(
    install_hooks: bool | None,
    interactive: bool,
    force: bool,
) -> bool:
    """Handle pre-push hooks installation based on flags and interactivity.

    Args:
        install_hooks: Explicit flag (True/False) or None for prompt.
        interactive: Whether interactive prompts are enabled.
        force: Whether to force reinstall existing hooks.

    Returns:
        True if hooks were installed, False otherwise.
    """
    should_install = False

    if install_hooks is True:
        should_install = True
    elif install_hooks is False:
        should_install = False
    elif interactive:
        console.print()
        should_install = typer.confirm(
            "Install pre-push hooks for automatic ADR sync?",
            default=False,
        )

    if should_install:
        try:
            from git_adr.hooks import get_hooks_manager

            manager = get_hooks_manager()
            results = manager.install_all(force=force)
            console.print()
            console.print("[green]✓[/green] Git hooks installed:")
            for result in results:
                console.print(f"  • {result}")
            return True
        except Exception as e:
            err_console.print(f"[yellow]Warning:[/yellow] Could not install hooks: {e}")
            err_console.print(
                "[dim]You can install later with: git adr hooks install[/dim]"
            )
            return False

    return False


def _handle_github_ci_setup(
    setup_github_ci: bool | None,
    interactive: bool,
) -> bool:
    """Handle GitHub Actions CI workflow generation.

    Args:
        setup_github_ci: Explicit flag (True/False) or None for prompt.
        interactive: Whether interactive prompts are enabled.

    Returns:
        True if CI workflows were generated, False otherwise.
    """
    should_setup = False

    if setup_github_ci is True:
        should_setup = True
    elif setup_github_ci is False:
        should_setup = False
    elif interactive:
        console.print()
        should_setup = typer.confirm(
            "Generate GitHub Actions CI workflows?",
            default=False,
        )

    if should_setup:
        try:
            from git_adr.commands.ci import run_ci_github

            console.print()
            # Generate both sync and validate workflows
            run_ci_github(sync=True, validate=True)
            return True
        except Exception as e:
            err_console.print(
                f"[yellow]Warning:[/yellow] Could not generate CI workflows: {e}"
            )
            err_console.print(
                "[dim]You can generate later with: git adr ci github[/dim]"
            )
            return False

    return False


def _print_next_steps(hooks_installed: bool, ci_generated: bool) -> None:
    """Print contextual next steps based on what was configured.

    Args:
        hooks_installed: Whether hooks were installed.
        ci_generated: Whether CI workflows were generated.
    """
    console.print()
    console.print("Next steps:")
    console.print(
        '  • [cyan]git adr new "Your Decision Title"[/cyan] - Create a new ADR'
    )
    console.print("  • [cyan]git adr list[/cyan] - List all ADRs")

    if not hooks_installed:
        console.print(
            "  • [cyan]git adr hooks install[/cyan] - Enable auto-sync on push"
        )

    if not ci_generated:
        console.print("  • [cyan]git adr ci github[/cyan] - Generate CI workflows")

    console.print("  • [cyan]git adr --help[/cyan] - See all commands")


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
