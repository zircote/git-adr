"""Hook management CLI commands for git-adr.

This module provides user-facing commands for managing git hooks:
- install: Install git-adr hooks
- uninstall: Remove git-adr hooks
- status: Show hook installation status
- config: Configure hook behavior
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from git_adr.hooks import HookStatus, get_hooks_manager

console = Console()
err_console = Console(stderr=True)


def run_hooks_install(force: bool = False, manual: bool = False) -> None:
    """Install git-adr hooks.

    Args:
        force: Overwrite existing hooks (backs up first)
        manual: Show manual integration instructions instead of installing
    """
    try:
        manager = get_hooks_manager()
    except FileNotFoundError:
        err_console.print("[red]Error:[/red] Not in a git repository")
        return

    if manual:
        # Show manual integration instructions
        instructions = manager.get_manual_instructions()
        console.print(
            Panel(
                instructions,
                title="Manual Hook Integration",
                subtitle="Add to your existing hooks",
            )
        )
        return

    # Install hooks
    console.print("[bold]Installing git-adr hooks...[/bold]\n")

    results = manager.install_all(force=force)
    for result in results:
        if "installed" in result.lower():
            console.print(f"  [green]✓[/green] {result}")
        elif "skipped" in result.lower() or "already" in result.lower():
            console.print(f"  [yellow]○[/yellow] {result}")
        else:
            console.print(f"  [dim]•[/dim] {result}")

    console.print()
    console.print("[bold]Hooks installed![/bold]")
    console.print()
    console.print("[dim]Notes will be synced automatically on git push.[/dim]")
    console.print("[dim]To skip once: GIT_ADR_SKIP=1 git push[/dim]")
    console.print("[dim]To uninstall: git adr hooks uninstall[/dim]")


def run_hooks_uninstall() -> None:
    """Uninstall git-adr hooks."""
    try:
        manager = get_hooks_manager()
    except FileNotFoundError:
        err_console.print("[red]Error:[/red] Not in a git repository")
        return

    console.print("[bold]Uninstalling git-adr hooks...[/bold]\n")

    results = manager.uninstall_all()
    for result in results:
        if "uninstalled" in result.lower() or "restored" in result.lower():
            console.print(f"  [green]✓[/green] {result}")
        else:
            console.print(f"  [dim]•[/dim] {result}")

    console.print()
    console.print("[bold]Hooks removed.[/bold]")
    console.print("[dim]Run 'git adr hooks install' to reinstall.[/dim]")


def run_hooks_status() -> None:
    """Show hook installation status."""
    try:
        manager = get_hooks_manager()
    except FileNotFoundError:
        err_console.print("[red]Error:[/red] Not in a git repository")
        return

    status = manager.get_status()

    table = Table(title="Git-ADR Hook Status")
    table.add_column("Hook", style="cyan")
    table.add_column("Status")
    table.add_column("Details", style="dim")

    for hook_type, hook_status in status.items():
        if hook_status == HookStatus.INSTALLED:
            status_str = "[green]✓ Installed[/green]"
            details = "Active"
        elif hook_status == HookStatus.NOT_INSTALLED:
            status_str = "[yellow]○ Not installed[/yellow]"
            details = "Run: git adr hooks install"
        elif hook_status == HookStatus.OUTDATED:
            status_str = "[yellow]↑ Outdated[/yellow]"
            details = "Run: git adr hooks install --force"
        elif hook_status == HookStatus.FOREIGN:
            status_str = "[blue]? Foreign[/blue]"
            details = "Existing hook (not ours)"
        else:
            status_str = "[red]? Unknown[/red]"
            details = ""

        table.add_row(hook_type, status_str, details)

    console.print(table)

    # Show config status
    console.print()
    _show_config_status()


def _show_config_status() -> None:
    """Show hook-related configuration."""
    from pathlib import Path

    from git_adr.core.git import get_git

    try:
        git = get_git(cwd=Path.cwd())
    except Exception:
        return

    console.print("[bold]Hook Configuration:[/bold]")

    # Check blockOnFailure
    block = git.config_get("adr.hooks.blockOnFailure")
    if block == "true":
        console.print(
            "  • Block on failure: [yellow]enabled[/yellow] (push fails if sync fails)"
        )
    else:
        console.print("  • Block on failure: [green]disabled[/green] (default)")

    # Check skip
    skip = git.config_get("adr.hooks.skip")
    if skip == "true":
        console.print("  • Hooks skipped: [yellow]yes[/yellow] (via config)")
    else:
        console.print("  • Hooks skipped: [green]no[/green]")


def run_hooks_config(
    block_on_failure: bool | None = None,
    no_block_on_failure: bool = False,
    show: bool = False,
) -> None:
    """Configure hook behavior.

    Args:
        block_on_failure: Enable blocking on sync failure
        no_block_on_failure: Disable blocking on sync failure
        show: Show current configuration
    """
    from pathlib import Path

    from git_adr.core.git import get_git

    try:
        git = get_git(cwd=Path.cwd())
    except Exception:
        err_console.print("[red]Error:[/red] Not in a git repository")
        return

    if show or (block_on_failure is None and not no_block_on_failure):
        # Show current config
        _show_config_status()
        return

    if block_on_failure:
        git.config_set("adr.hooks.blockOnFailure", "true")
        console.print("[green]✓[/green] Block on failure: enabled")
        console.print("[dim]Push will fail if notes sync fails[/dim]")

    if no_block_on_failure:
        git.config_set("adr.hooks.blockOnFailure", "false")
        console.print("[green]✓[/green] Block on failure: disabled")
        console.print("[dim]Push continues even if notes sync fails[/dim]")
