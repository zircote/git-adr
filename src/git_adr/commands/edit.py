"""Implementation of `git adr edit` command.

Modifies an existing ADR - opens in editor or makes quick metadata changes.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import typer
from rich.console import Console

from git_adr.commands._shared import setup_command_context
from git_adr.core import ADR, ADRStatus, GitError

if TYPE_CHECKING:
    from git_adr.core.notes import NotesManager

console = Console()
err_console = Console(stderr=True)


def run_edit(
    adr_id: str,
    status: str | None = None,
    add_tag: list[str] | None = None,
    remove_tag: list[str] | None = None,
    link: str | None = None,
    unlink: str | None = None,
) -> None:
    """Edit an existing ADR.

    Args:
        adr_id: ADR ID to edit.
        status: Change status without editor.
        add_tag: Tags to add.
        remove_tag: Tags to remove.
        link: Commit to link.
        unlink: Commit to unlink.

    Raises:
        typer.Exit: On error.
    """
    try:
        # Initialize command context
        ctx = setup_command_context()

        adr = ctx.notes_manager.get(adr_id)

        if adr is None:
            err_console.print(f"[red]Error:[/red] ADR not found: {adr_id}")
            raise typer.Exit(1)

        # Check if quick edit (no editor)
        quick_edit = any([status, add_tag, remove_tag, link, unlink])

        if quick_edit:
            _quick_edit(
                ctx.notes_manager,
                adr,
                status=status,
                add_tag=add_tag or [],
                remove_tag=remove_tag or [],
                link=link,
                unlink=unlink,
            )
        else:
            _full_edit(ctx.notes_manager, adr, ctx.config)

    except GitError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def _quick_edit(
    notes_manager: NotesManager,
    adr: ADR,
    status: str | None,
    add_tag: list[str],
    remove_tag: list[str],
    link: str | None,
    unlink: str | None,
) -> None:
    """Make quick metadata changes without opening editor.

    Args:
        notes_manager: Notes manager.
        adr: ADR to edit.
        status: New status.
        add_tag: Tags to add.
        remove_tag: Tags to remove.
        link: Commit to link.
        unlink: Commit to unlink.
    """
    changes: list[str] = []

    # Update status
    if status:
        try:
            new_status = ADRStatus.from_string(status)
            adr.metadata.status = new_status
            changes.append(f"Status → {new_status.value}")
        except ValueError:
            err_console.print(f"[red]Error:[/red] Invalid status: {status}")
            valid = ", ".join(s.value for s in ADRStatus)
            err_console.print(f"Valid statuses: {valid}")
            raise typer.Exit(1)

    # Update tags
    current_tags = set(adr.metadata.tags)
    for tag in add_tag:
        if tag not in current_tags:
            current_tags.add(tag)
            changes.append(f"Added tag: {tag}")

    for tag in remove_tag:
        if tag in current_tags:
            current_tags.discard(tag)
            changes.append(f"Removed tag: {tag}")

    adr.metadata.tags = sorted(current_tags)

    # Update linked commits
    current_commits = set(adr.metadata.linked_commits)
    if link:
        if link not in current_commits:
            current_commits.add(link)
            changes.append(f"Linked commit: {link[:8]}")

    if unlink:
        if unlink in current_commits:
            current_commits.discard(unlink)
            changes.append(f"Unlinked commit: {unlink[:8]}")

    adr.metadata.linked_commits = list(current_commits)

    if not changes:
        console.print("[dim]No changes made[/dim]")
        return

    # Save changes
    notes_manager.update(adr)

    console.print(f"[green]✓[/green] Updated ADR: [cyan]{adr.id}[/cyan]")
    for change in changes:
        console.print(f"  • {change}")


def _full_edit(notes_manager: NotesManager, adr: ADR, config) -> None:
    """Open ADR in editor for full editing.

    Args:
        notes_manager: Notes manager.
        adr: ADR to edit.
        config: Configuration.
    """
    import subprocess  # nosec B404 - subprocess needed to launch user's editor
    import tempfile

    from git_adr.commands._editor import build_editor_command, find_editor

    # Find editor
    editor_cmd = find_editor(config)
    if editor_cmd is None:
        err_console.print(
            "[red]Error:[/red] No editor found. Set $EDITOR or use quick edit options."
        )
        raise typer.Exit(1)

    # Write ADR to temp file
    original_content = adr.to_markdown()

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".md",
        prefix=f"git-adr-{adr.id}-",
        delete=False,
    ) as f:
        f.write(original_content)
        temp_path = f.name

    try:
        # Open editor
        cmd = build_editor_command(editor_cmd, temp_path)
        console.print(f"[dim]Opening editor: {editor_cmd}[/dim]")

        # cmd is built from user's $EDITOR (trusted) + temp file path we control
        result = subprocess.run(cmd, check=False)  # nosec B603

        if result.returncode != 0:
            err_console.print(
                f"[yellow]Warning:[/yellow] Editor exited with code {result.returncode}"
            )

        # Read edited content
        edited_content = Path(temp_path).read_text()

        # Check for changes
        if edited_content.strip() == original_content.strip():
            console.print("[dim]No changes made[/dim]")
            return

        # Parse updated ADR
        try:
            updated_adr = ADR.from_markdown(edited_content)
            # Preserve the original ID
            updated_adr.metadata.id = adr.id
        except ValueError as e:
            err_console.print(f"[red]Error:[/red] Invalid ADR format: {e}")
            raise typer.Exit(1)

        # Save changes
        notes_manager.update(updated_adr)

        console.print(f"[green]✓[/green] Updated ADR: [cyan]{adr.id}[/cyan]")

    finally:
        Path(temp_path).unlink(missing_ok=True)
