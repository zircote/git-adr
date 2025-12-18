"""Implementation of `git adr new` command.

Creates a new Architecture Decision Record with multiple input modes:
- Editor mode (default): Opens configured editor with template
- File input: --file path/to/content.md
- Stdin input: cat file.md | git adr new "Title"
- Preview mode: --preview shows template without creating
"""

from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown

from git_adr.commands._editor import open_editor
from git_adr.commands._shared import setup_command_context
from git_adr.core import (
    ADR,
    ADRMetadata,
    ADRStatus,
    Config,
    GitError,
    ensure_list,
    generate_adr_id,
    validate_adr,
)
from git_adr.core.templates import TemplateEngine

console = Console()
err_console = Console(stderr=True)


def run_new(
    title: str,
    status: str = "proposed",
    tags: list[str] | None = None,
    deciders: list[str] | None = None,
    link: str | None = None,
    template: str | None = None,
    file: str | None = None,
    no_edit: bool = False,
    preview: bool = False,
    draft: bool = False,
) -> None:
    """Create a new ADR.

    Args:
        title: ADR title.
        status: Initial status.
        tags: Tags for the ADR.
        deciders: Decision makers for the ADR.
        link: Commit SHA to link.
        template: Template format override.
        file: Read content from file.
        no_edit: Skip editor (requires --file or stdin).
        preview: Show template without creating.
        draft: Mark as draft.

    Raises:
        typer.Exit: On error.
    """
    try:
        # Initialize command context
        ctx = setup_command_context()

        # Get template format
        format_name = template or ctx.config.template

        # Generate ADR ID
        existing_ids = {adr.id for adr in ctx.notes_manager.list_all()}
        adr_id = generate_adr_id(title, existing_ids)

        # Parse status
        if draft:
            adr_status = ADRStatus.DRAFT
        else:
            try:
                adr_status = ADRStatus.from_string(status)
            except ValueError:
                err_console.print(f"[red]Error:[/red] Invalid status: {status}")
                valid = ", ".join(s.value for s in ADRStatus)
                err_console.print(f"Valid statuses: {valid}")
                raise typer.Exit(1)

        # Create template engine
        template_engine = TemplateEngine(ctx.config.custom_templates_dir)

        # Render template
        try:
            content = template_engine.render_for_new(
                format_name=format_name,
                title=title,
                adr_id=adr_id,
                status=str(adr_status),
                tags=tags,
            )
        except ValueError as e:
            err_console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

        # Handle preview mode
        if preview:
            _show_preview(content, format_name)
            return

        # Get content from various sources
        final_content = _get_content(
            template_content=content,
            file_path=file,
            no_edit=no_edit,
            config=ctx.config,
        )

        if final_content is None:
            console.print("[yellow]Aborted[/yellow]")
            raise typer.Exit(0)

        # Parse frontmatter from content and merge with CLI args
        from datetime import date as date_type

        import frontmatter

        try:
            post = frontmatter.loads(final_content)
            fm = dict(post.metadata) if post.metadata else {}
            body_content = post.content
        except Exception:
            # If frontmatter parsing fails, use content as-is
            fm = {}
            body_content = final_content

        # CLI args take precedence over frontmatter
        # Support both 'deciders' and 'decision-makers' (MADR 4.0) in frontmatter
        fm_deciders = ensure_list(
            fm.get("deciders") if "deciders" in fm else fm.get("decision-makers", [])
        )
        fm_consulted = ensure_list(fm.get("consulted"))
        fm_informed = ensure_list(fm.get("informed"))

        # Deciders: CLI takes precedence, fallback to frontmatter
        merged_deciders = deciders if deciders else fm_deciders

        # Parse comma-separated values if provided as single string entries
        if merged_deciders:
            parsed_deciders = []
            for d in merged_deciders:
                # Split on comma if present, strip whitespace
                parsed_deciders.extend([x.strip() for x in d.split(",") if x.strip()])
            merged_deciders = parsed_deciders

        # Interactive prompt for deciders if empty and TTY available
        if not merged_deciders and sys.stdin.isatty() and not no_edit:
            deciders_input = typer.prompt(
                "Enter deciders (comma-separated, or press Enter to skip)",
                default="",
            )
            if deciders_input:
                merged_deciders = [
                    d.strip() for d in deciders_input.split(",") if d.strip()
                ]

        # Validate: deciders are required for new ADRs
        if not merged_deciders:
            err_console.print(
                "[red]Error:[/red] Deciders are required. "
                "Use --deciders or specify in frontmatter."
            )
            raise typer.Exit(1)

        # Tags: CLI takes precedence, but merge if CLI is empty
        merged_tags = tags if tags else ensure_list(fm.get("tags"))

        # Date: use CLI-provided date (today) unless frontmatter has one
        adr_date = date_type.today()
        if "date" in fm:
            try:
                fm_date = fm["date"]
                if isinstance(fm_date, date_type):
                    adr_date = fm_date
                elif isinstance(fm_date, str):
                    adr_date = date_type.fromisoformat(fm_date[:10])
            except (ValueError, TypeError):
                pass  # Keep today's date

        # Create metadata
        metadata = ADRMetadata(
            id=adr_id,
            title=title,
            date=adr_date,
            status=adr_status,
            tags=merged_tags or [],
            deciders=merged_deciders,
            consulted=fm_consulted,
            informed=fm_informed,
            format=format_name,
            linked_commits=[link] if link else [],
        )

        # Validate linked commit
        if link:
            if not ctx.git.commit_exists(link):
                err_console.print(
                    f"[yellow]Warning:[/yellow] Commit {link[:8]} not found"
                )

        # Create ADR (use body_content without frontmatter)
        adr = ADR(metadata=metadata, content=body_content)

        # Validate
        issues = validate_adr(adr)
        if issues:
            err_console.print("[yellow]Validation warnings:[/yellow]")
            for issue in issues:
                err_console.print(f"  • {issue}")

        # Store ADR
        ctx.notes_manager.add(adr)

        # Success
        console.print()
        console.print(f"[green]✓[/green] Created ADR: [cyan]{adr_id}[/cyan]")
        console.print(f"  Title: {title}")
        console.print(f"  Status: {adr_status}")
        if tags:
            console.print(f"  Tags: {', '.join(tags)}")
        if link:
            console.print(f"  Linked: {link[:8]}")

    except GitError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def _show_preview(content: str, format_name: str) -> None:
    """Show template preview.

    Args:
        content: Template content.
        format_name: Format name.
    """
    console.print()
    console.print(f"[bold]Template Preview[/bold] ({format_name} format)")
    console.print()
    console.print(Markdown(content))


def _get_content(
    template_content: str,
    file_path: str | None,
    no_edit: bool,
    config: Config,
) -> str | None:
    """Get ADR content from file, stdin, or editor.

    Args:
        template_content: Rendered template.
        file_path: Optional file to read from.
        no_edit: If True, don't open editor.
        config: Configuration.

    Returns:
        Final content, or None if aborted.
    """

    # Check for file input first (explicit file takes precedence)
    if file_path:
        path = Path(file_path)
        if not path.exists():
            err_console.print(f"[red]Error:[/red] File not found: {file_path}")
            raise typer.Exit(1)

        content = path.read_text()
        console.print(f"[dim]Read content from {file_path}[/dim]")
        return content

    # Check for stdin input (only if no file specified)
    if not sys.stdin.isatty():
        console.print("[dim]Reading content from stdin...[/dim]")
        stdin_content = sys.stdin.read()
        if stdin_content.strip():
            return stdin_content
        if no_edit:
            err_console.print(
                "[red]Error:[/red] No content from stdin and --no-edit specified"
            )
            raise typer.Exit(1)

    # If no_edit and no file/stdin, error
    if no_edit:
        err_console.print("[red]Error:[/red] --no-edit requires --file or stdin input")
        raise typer.Exit(1)

    # Open editor
    return open_editor(template_content, config)
