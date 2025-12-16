"""Hook command handler for git-adr.

This module handles callbacks from git hook scripts. The actual hook scripts
delegate to `git adr hook <type>` which invokes these handlers.

This is an internal command not intended for direct user invocation.
"""

from __future__ import annotations

import sys
from pathlib import Path

from rich.console import Console

err_console = Console(stderr=True)


def run_hook(hook_type: str, *args: str) -> None:
    """Execute hook logic for the given hook type.

    Called by git hook scripts via `git adr hook <type> [args...]`.

    Args:
        hook_type: The type of hook (e.g., "pre-push")
        *args: Additional arguments passed by the hook

    Raises:
        SystemExit: On error (exit code 1)
    """
    try:
        match hook_type:
            case "pre-push":
                if not args:
                    err_console.print("[red]Error:[/red] pre-push requires remote name")
                    sys.exit(1)
                _handle_pre_push(args[0])
            case _:
                err_console.print(f"[red]Error:[/red] Unknown hook type: {hook_type}")
                sys.exit(1)
    except Exception as e:
        err_console.print(f"[red]Hook error:[/red] {e}")
        sys.exit(1)


def _handle_pre_push(remote: str) -> None:
    """Handle pre-push hook - sync notes to remote.

    Args:
        remote: Name of the remote being pushed to
    """
    from git_adr.core.config import ConfigManager
    from git_adr.core.git import get_git
    from git_adr.core.notes import NotesManager

    # Get git instance
    git = get_git(cwd=Path.cwd())

    # Load config
    config = ConfigManager(git).load()

    # Get timeout from git config (default 5 seconds)
    timeout_str = git.config_get("adr.sync.timeout")
    timeout: int | None = None
    if timeout_str:
        try:
            timeout = int(timeout_str)
        except ValueError:
            timeout = 5
    else:
        timeout = 5

    # Create notes manager and sync
    notes_manager = NotesManager(git, config)

    try:
        # Push notes to remote
        notes_manager.sync_push(remote=remote, timeout=timeout)
    except Exception as e:
        # Re-raise so caller can handle based on blockOnFailure config
        raise RuntimeError(f"Failed to sync notes to {remote}: {e}") from e
