"""Implementation of `git adr supersede` command.

Creates a new ADR that supersedes an existing one.
"""

from __future__ import annotations

from datetime import date

import typer
from rich.console import Console

from git_adr.commands._shared import setup_command_context
from git_adr.core import (
    ADR,
    ADRMetadata,
    ADRStatus,
    GitError,
    generate_adr_id,
)
from git_adr.core.templates import TemplateEngine

console = Console()
err_console = Console(stderr=True)


def run_supersede(
    adr_id: str,
    title: str,
    template: str | None = None,
) -> None:
    """Create a new ADR that supersedes an existing one.

    Args:
        adr_id: ID of ADR being superseded.
        title: Title for the new ADR.
        template: Template format override.

    Raises:
        typer.Exit: On error.
    """
    try:
        # Initialize command context
        ctx = setup_command_context()

        # Get the original ADR
        original = ctx.notes_manager.get(adr_id)
        if original is None:
            err_console.print(f"[red]Error:[/red] ADR not found: {adr_id}")
            raise typer.Exit(1)

        # Check if already superseded
        if original.metadata.status == ADRStatus.SUPERSEDED:
            err_console.print(
                f"[yellow]Warning:[/yellow] ADR {adr_id} is already superseded"
            )
            if original.metadata.superseded_by:
                err_console.print(f"  Superseded by: {original.metadata.superseded_by}")

        # Generate new ADR ID
        existing_ids = {adr.id for adr in ctx.notes_manager.list_all()}
        new_id = generate_adr_id(title, existing_ids)

        # Get template format
        format_name = template or ctx.config.template

        # Create template engine and render
        template_engine = TemplateEngine(ctx.config.custom_templates_dir)

        try:
            content = template_engine.render_for_new(
                format_name=format_name,
                title=title,
                adr_id=new_id,
                status="proposed",
                tags=list(original.metadata.tags),  # Inherit tags
                supersedes=adr_id,
            )
        except ValueError as e:
            err_console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

        # Add supersession reference to content
        supersession_note = (
            f"\n\n> **Note:** This ADR supersedes [{adr_id}].\n"
            f"> Previous decision: {original.metadata.title}\n"
        )
        content = content.replace(
            "## More Information",
            f"## Supersession{supersession_note}\n## More Information",
        )

        # Open editor for new ADR
        from git_adr.commands._editor import open_editor

        final_content = open_editor(content, ctx.config)

        if final_content is None:
            console.print("[yellow]Aborted[/yellow]")
            return

        # Create new ADR metadata
        metadata = ADRMetadata(
            id=new_id,
            title=title,
            date=date.today(),
            status=ADRStatus.PROPOSED,
            tags=list(original.metadata.tags),
            format=format_name,
            supersedes=adr_id,
        )

        new_adr = ADR(metadata=metadata, content=final_content)

        # Update original ADR
        original.metadata.status = ADRStatus.SUPERSEDED
        original.metadata.superseded_by = new_id

        # Save both
        ctx.notes_manager.add(new_adr)
        ctx.notes_manager.update(original)

        console.print()
        console.print(
            f"[green]✓[/green] Created superseding ADR: [cyan]{new_id}[/cyan]"
        )
        console.print(f"  Title: {title}")
        console.print(f"  Supersedes: {adr_id}")
        console.print()
        console.print(f"[dim]Original ADR ({adr_id}) marked as superseded[/dim]")

    except GitError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
