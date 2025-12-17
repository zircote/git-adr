"""Editor utilities for git-adr commands.

Provides shared functionality for opening external editors across commands
(new, edit, supersede).
"""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess  # nosec B404 - subprocess needed to launch user's editor
import tempfile
from pathlib import Path

from rich.console import Console

from git_adr.core import Config

console = Console()
err_console = Console(stderr=True)

# Editor fallback chain
EDITOR_FALLBACKS = ["vim", "nano", "vi"]

# GUI editors that need --wait flag
GUI_EDITORS = {
    "code": "--wait",
    "subl": "--wait",
    "sublime_text": "--wait",
    "atom": "--wait",
    "zed": "--wait",
    "cursor": "--wait",
    "idea": "--wait",
    "pycharm": "--wait",
    "webstorm": "--wait",
}


def find_editor(config: Config) -> str | None:
    """Find the editor to use.

    Fallback chain:
    1. adr.editor config
    2. $EDITOR
    3. $VISUAL
    4. vim
    5. nano
    6. vi

    Args:
        config: Configuration.

    Returns:
        Editor command, or None if not found.
    """
    # Check config
    if config.editor:
        try:
            parts = shlex.split(config.editor)
            if parts and shutil.which(parts[0]):
                return config.editor
        except ValueError:
            # Malformed editor string (e.g., unmatched quotes)
            err_console.print(
                f"[yellow]Warning:[/yellow] Invalid editor config: {config.editor}"
            )

    # Check environment
    for env_var in ["EDITOR", "VISUAL"]:
        editor = os.environ.get(env_var)
        if editor:
            try:
                parts = shlex.split(editor)
                if parts and shutil.which(parts[0]):
                    return editor
            except ValueError:
                # Malformed editor string (e.g., unmatched quotes)
                err_console.print(
                    f"[yellow]Warning:[/yellow] Invalid ${env_var}: {editor}"
                )

    # Check fallbacks
    for editor in EDITOR_FALLBACKS:
        if shutil.which(editor):
            return editor

    return None


def build_editor_command(editor: str, file_path: str) -> list[str]:
    """Build the editor command with appropriate flags.

    Adds --wait flag for GUI editors that need it.

    Args:
        editor: Editor command (may contain quoted paths with spaces).
        file_path: Path to file to edit.

    Returns:
        Command list for subprocess.
    """
    # Use shlex.split() for proper shell-style parsing of editor string
    # This correctly handles paths with spaces, quoted arguments, etc.
    try:
        parts = shlex.split(editor)
        cmd = parts[0]
        args = parts[1:]
    except ValueError:
        # Fallback: treat entire string as command (already validated by find_editor)
        cmd = editor
        args = []

    # Check if this is a GUI editor that needs --wait
    cmd_name = Path(cmd).stem.lower()
    if cmd_name in GUI_EDITORS:
        wait_flag = GUI_EDITORS[cmd_name]
        if wait_flag not in args:
            args.append(wait_flag)

    return [cmd, *args, file_path]


def open_editor(content: str, config: Config) -> str | None:
    """Open the user's editor with content.

    Args:
        content: Initial content.
        config: Configuration.

    Returns:
        Edited content, or None if aborted.

    Raises:
        SystemExit: If no editor found (via typer.Exit).
    """
    import typer

    # Find editor
    editor_cmd = find_editor(config)
    if editor_cmd is None:
        err_console.print(
            "[red]Error:[/red] No editor found. Set $EDITOR or use --file"
        )
        raise typer.Exit(1)

    # Create temp file
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".md",
        prefix="git-adr-",
        delete=False,
    ) as f:
        f.write(content)
        temp_path = f.name

    try:
        # Build editor command
        cmd = build_editor_command(editor_cmd, temp_path)

        console.print(f"[dim]Opening editor: {editor_cmd}[/dim]")

        # Run editor - cmd is built from user's $EDITOR (trusted) + temp file path we control
        result = subprocess.run(cmd, check=False)  # nosec B603

        if result.returncode != 0:
            err_console.print(
                f"[yellow]Warning:[/yellow] Editor exited with code {result.returncode}"
            )

        # Read edited content
        edited_content = Path(temp_path).read_text()

        # Check if content was changed
        if edited_content.strip() == content.strip():
            console.print("[dim]No changes made[/dim]")
            return None

        # Check for empty content
        if not edited_content.strip():
            console.print("[dim]Empty content[/dim]")
            return None

        return edited_content

    finally:
        # Clean up temp file
        Path(temp_path).unlink(missing_ok=True)
