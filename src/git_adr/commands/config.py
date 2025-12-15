"""Implementation of `git adr config` command.

Manages git-adr configuration stored in git config.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from git_adr.core import ConfigManager, GitError, get_git
from git_adr.core.config import CONFIG_DOCS

console = Console()
err_console = Console(stderr=True)


def run_config(
    key: str | None = None,
    value: str | None = None,
    list_: bool = False,
    get: bool = False,
    set_: bool = False,
    unset: bool = False,
    global_: bool = False,
) -> None:
    """Manage git-adr configuration.

    Args:
        key: Configuration key.
        value: Value to set.
        list_: List all configuration.
        get: Get a value.
        set_: Set a value.
        unset: Unset a value.
        global_: Use global config.

    Raises:
        typer.Exit: On error.
    """
    try:
        git = get_git(cwd=Path.cwd())

        # For global config, we don't need to be in a repo
        if not global_ and not git.is_repository():
            err_console.print("[red]Error:[/red] Not a git repository")
            raise typer.Exit(1)

        config_manager = ConfigManager(git)

        # Handle --list
        if list_:
            _list_config(config_manager, global_=global_)
            return

        # Handle --get
        if get:
            if not key:
                err_console.print("[red]Error:[/red] --get requires a key")
                raise typer.Exit(1)
            _get_config(config_manager, key, global_=global_)
            return

        # Handle --set
        if set_:
            if not key or value is None:
                err_console.print("[red]Error:[/red] --set requires key and value")
                raise typer.Exit(1)
            _set_config(config_manager, key, value, global_=global_)
            return

        # Handle --unset
        if unset:
            if not key:
                err_console.print("[red]Error:[/red] --unset requires a key")
                raise typer.Exit(1)
            _unset_config(config_manager, key, global_=global_)
            return

        # No flag: infer from arguments
        if key and value is not None:
            # key value → set
            _set_config(config_manager, key, value, global_=global_)
        elif key:
            # key → get
            _get_config(config_manager, key, global_=global_)
        else:
            # nothing → list
            _list_config(config_manager, global_=global_)

    except GitError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def _list_config(config_manager: ConfigManager, global_: bool) -> None:
    """List all configuration.

    Args:
        config_manager: Config manager.
        global_: List global config only.
    """
    config = config_manager.list_all(global_=global_)

    if not config:
        scope = "global" if global_ else "local"
        console.print(f"[dim]No {scope} configuration set[/dim]")
        console.print()
        console.print("Available configuration keys:")
        _show_available_keys()
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Key", style="cyan")
    table.add_column("Value")
    table.add_column("Description", style="dim")

    for key, value in sorted(config.items()):
        short_key = key.replace("adr.", "")
        desc = CONFIG_DOCS.get(short_key, "")
        table.add_row(key, value, desc)

    console.print(table)


def _get_config(config_manager: ConfigManager, key: str, global_: bool) -> None:
    """Get a configuration value.

    Args:
        config_manager: Config manager.
        key: Key to get.
        global_: Get from global config.
    """
    value = config_manager.get(key, global_=global_)

    if value is None:
        # Show available keys suggestion
        short_key = key.replace("adr.", "")
        if short_key in CONFIG_DOCS:
            console.print(f"[dim]{key} is not set[/dim]")
        else:
            err_console.print(f"[red]Error:[/red] Unknown key: {key}")
            console.print()
            _show_available_keys()
            raise typer.Exit(1)
    else:
        console.print(value)


def _set_config(
    config_manager: ConfigManager,
    key: str,
    value: str,
    global_: bool,
) -> None:
    """Set a configuration value.

    Args:
        config_manager: Config manager.
        key: Key to set.
        value: Value to set.
        global_: Set in global config.
    """
    try:
        config_manager.set(key, value, global_=global_)
        scope = "global" if global_ else "local"
        console.print(f"[green]✓[/green] Set {key} = {value} ({scope})")
    except ValueError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def _unset_config(config_manager: ConfigManager, key: str, global_: bool) -> None:
    """Unset a configuration value.

    Args:
        config_manager: Config manager.
        key: Key to unset.
        global_: Unset from global config.
    """
    if config_manager.unset(key, global_=global_):
        scope = "global" if global_ else "local"
        console.print(f"[green]✓[/green] Unset {key} ({scope})")
    else:
        console.print(f"[dim]{key} was not set[/dim]")


def _show_available_keys() -> None:
    """Show available configuration keys."""
    table = Table(show_header=True, header_style="bold")
    table.add_column("Key", style="cyan")
    table.add_column("Description")

    for key, desc in sorted(CONFIG_DOCS.items()):
        table.add_row(f"adr.{key}", desc)

    console.print(table)
