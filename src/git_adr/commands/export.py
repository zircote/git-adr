"""Implementation of `git adr export` command.

Exports ADRs to various formats and locations.
"""

from __future__ import annotations

import html
import json
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, cast

import typer
from rich.console import Console

from git_adr.commands._shared import setup_command_context
from git_adr.core import ADR, GitError
from git_adr.core.index import IndexManager

if TYPE_CHECKING:
    from git_adr.core.notes import NotesManager

console = Console()
err_console = Console(stderr=True)


def _get_author(adr: ADR) -> str:
    """Get the primary author from ADR deciders."""
    if adr.metadata.deciders:
        return adr.metadata.deciders[0]
    return "unknown"


def run_export(
    format_: str = "markdown",
    output: str = "./adr-export",
    adr: str | None = None,
) -> None:
    """Export ADRs to files.

    Args:
        format_: Export format (markdown, json, html, docx).
        output: Output directory or file.
        adr: Export specific ADR only.

    Raises:
        typer.Exit: On error.
    """
    try:
        # Initialize command context with index manager
        ctx = setup_command_context(require_index=True)
        index_manager = cast(IndexManager, ctx.index_manager)

        # Rebuild index
        index_manager.rebuild()

        # Get ADRs
        if adr:
            adr_obj = ctx.notes_manager.get(adr)
            if not adr_obj:
                err_console.print(f"[red]Error:[/red] ADR not found: {adr}")
                raise typer.Exit(1)
            all_adrs = [adr_obj]
        else:
            all_adrs = ctx.notes_manager.list_all()

        if not all_adrs:
            console.print("[yellow]No ADRs to export[/yellow]")
            return

        # Create output directory
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)

        # Export based on format
        if format_ == "json":
            _export_json(all_adrs, output_path, ctx.notes_manager)
        elif format_ == "html":
            _export_html(all_adrs, output_path, ctx.notes_manager)
        elif format_ == "docx":
            console.print("[yellow]DOCX export coming soon[/yellow]")
            console.print("[dim]Install: pip install 'git-adr\\[export]'[/dim]")
            return
        else:
            _export_markdown(all_adrs, output_path, ctx.notes_manager)

        console.print(
            f"[green]✓[/green] Exported {len(all_adrs)} ADRs to {output_path}"
        )

    except GitError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def _export_markdown(
    adrs: list[ADR], output_path: Path, notes_manager: NotesManager
) -> None:
    """Export ADRs as Markdown files."""
    for adr in adrs:
        filename = f"{adr.metadata.id}.md"
        file_path = output_path / filename

        # Write with frontmatter
        content = _format_adr_markdown(adr)
        file_path.write_text(content)

    # Create index file
    index_content = ["# Architecture Decision Records", ""]
    for adr in sorted(adrs, key=lambda a: a.metadata.id):
        index_content.append(
            f"- [{adr.metadata.id}]({adr.metadata.id}.md): {adr.metadata.title}"
        )
    (output_path / "README.md").write_text("\n".join(index_content))


def _export_json(
    adrs: list[ADR], output_path: Path, notes_manager: NotesManager
) -> None:
    """Export ADRs as JSON."""
    data = {
        "adrs": [
            {
                "id": adr.metadata.id,
                "title": adr.metadata.title,
                "status": adr.metadata.status.value,
                "deciders": adr.metadata.deciders,
                "date": str(adr.metadata.date),
                "tags": adr.metadata.tags,
                "format": adr.metadata.format,
                "content": adr.content,
                "linked_commits": adr.metadata.linked_commits,
                "supersedes": adr.metadata.supersedes,
                "superseded_by": adr.metadata.superseded_by,
            }
            for adr in adrs
        ]
    }

    (output_path / "adrs.json").write_text(json.dumps(data, indent=2))


def _export_html(
    adrs: list[ADR], output_path: Path, notes_manager: NotesManager
) -> None:
    """Export ADRs as HTML files."""
    # Try to use mistune for markdown conversion
    md: Callable[[str], str]
    try:
        import mistune

        md = mistune.html  # type: ignore[assignment]
    except ImportError:
        # Fallback: just wrap in pre tags
        def md(x: str) -> str:
            return f"<pre>{x}</pre>"

    for adr in adrs:
        filename = f"{adr.metadata.id}.html"
        file_path = output_path / filename

        html_content = _format_adr_html(adr, md)
        file_path.write_text(html_content)

    # Create index
    index_html = [
        "<!DOCTYPE html>",
        "<html><head><title>ADR Index</title>",
        "<style>body{font-family:system-ui,sans-serif;max-width:800px;margin:0 auto;padding:20px;}</style>",
        "</head><body>",
        "<h1>Architecture Decision Records</h1>",
        "<ul>",
    ]

    for adr in sorted(adrs, key=lambda a: a.metadata.id):
        safe_id = html.escape(adr.metadata.id)
        safe_title = html.escape(adr.metadata.title)
        index_html.append(
            f'<li><a href="{safe_id}.html">{safe_id}</a>: {safe_title}</li>'
        )

    index_html.extend(["</ul>", "</body></html>"])
    (output_path / "index.html").write_text("\n".join(index_html))


def _format_adr_markdown(adr: ADR) -> str:
    """Format ADR as Markdown with frontmatter."""
    lines = [
        "---",
        f"id: {adr.metadata.id}",
        f"title: {adr.metadata.title}",
        f"status: {adr.metadata.status.value}",
        f"deciders: [{_get_author(adr)}]",
        f"date: {adr.metadata.date}",
    ]
    if adr.metadata.tags:
        lines.append(f"tags: [{', '.join(adr.metadata.tags)}]")
    lines.extend(["---", "", adr.content])
    return "\n".join(lines)


def _format_adr_html(adr: ADR, md_converter) -> str:
    """Format ADR as HTML.

    All user-controlled values are HTML-escaped to prevent XSS attacks.
    """
    # Escape all user-controlled values
    safe_id = html.escape(adr.metadata.id)
    safe_title = html.escape(adr.metadata.title)
    safe_status = html.escape(adr.metadata.status.value)
    safe_author = html.escape(_get_author(adr))
    safe_date = html.escape(str(adr.metadata.date))

    # Convert markdown content to HTML (mistune handles its own escaping)
    content_html = md_converter(adr.content)

    return f"""<!DOCTYPE html>
<html>
<head>
<title>{safe_id}: {safe_title}</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
.meta {{ background: #f5f5f5; padding: 10px; border-radius: 4px; margin-bottom: 20px; }}
.meta dt {{ font-weight: bold; }}
</style>
</head>
<body>
<h1>{safe_id}: {safe_title}</h1>
<dl class="meta">
<dt>Status</dt><dd>{safe_status}</dd>
<dt>Decider</dt><dd>{safe_author}</dd>
<dt>Date</dt><dd>{safe_date}</dd>
</dl>
{content_html}
</body>
</html>"""
