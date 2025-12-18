"""Implementation of `git adr convert` command.

Converts an ADR to a different format.
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.markdown import Markdown

from git_adr.commands._shared import setup_command_context
from git_adr.core import GitError
from git_adr.core.templates import TEMPLATE_DESCRIPTIONS, TemplateEngine

console = Console()
err_console = Console(stderr=True)


def run_convert(
    adr_id: str,
    to: str,
    dry_run: bool = False,
) -> None:
    """Convert an ADR to a different format.

    Args:
        adr_id: ADR ID to convert.
        to: Target format.
        dry_run: Show result without saving.

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

        # Create template engine
        template_engine = TemplateEngine(ctx.config.custom_templates_dir)

        # Validate target format
        available_formats = template_engine.list_formats()
        if to not in available_formats:
            err_console.print(f"[red]Error:[/red] Unknown format: {to}")
            console.print()
            console.print("Available formats:")
            for fmt, desc in TEMPLATE_DESCRIPTIONS.items():
                console.print(f"  • [cyan]{fmt}[/cyan]: {desc}")
            raise typer.Exit(1)

        # Check if already in target format
        if adr.metadata.format == to:
            console.print(f"[dim]ADR is already in {to} format[/dim]")
            return

        # Convert
        try:
            converted_content = template_engine.convert(adr, to)
        except ValueError as e:
            err_console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

        if dry_run:
            console.print(f"[bold]Preview: {adr_id} → {to} format[/bold]")
            console.print()
            console.print(Markdown(converted_content))
            console.print()
            console.print("[dim]Use without --dry-run to save changes[/dim]")
            return

        # Update ADR
        from git_adr.core import ADR

        updated_adr = ADR(
            metadata=adr.metadata,
            content=converted_content,
        )
        updated_adr.metadata.format = to

        ctx.notes_manager.update(updated_adr)

        console.print(
            f"[green]✓[/green] Converted ADR [cyan]{adr_id}[/cyan] "
            f"from {adr.metadata.format} to {to}"
        )

    except GitError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
