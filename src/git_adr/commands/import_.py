"""Implementation of `git adr import` command.

Imports ADRs from external sources (files, directories, other tools).
"""

from __future__ import annotations

import json
import re
from datetime import date as date_type
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console

from git_adr.commands._shared import setup_command_context
from git_adr.core import (
    ADR,
    ADRMetadata,
    GitError,
    ensure_list,
    generate_adr_id,
)
from git_adr.core.adr import ADRStatus

console = Console()
err_console = Console(stderr=True)


def _validate_source_path(path: str) -> Path:
    """Validate source path for import.

    For import command, we allow reading from anywhere on the filesystem
    since the user explicitly provides the path. This is a read-only operation.

    Args:
        path: User-provided source path.

    Returns:
        Validated and resolved source path.

    Raises:
        typer.Exit: If source doesn't exist.
    """
    # Resolve the user-provided path
    source_path = Path(path).expanduser().resolve()

    # Verify source exists
    if not source_path.exists():
        err_console.print(f"[red]Error:[/red] Source not found: {path}")
        raise typer.Exit(1)

    return source_path


def run_import(
    path: str,
    format_: str | None = None,
    link_by_date: bool = False,
    dry_run: bool = False,
) -> None:
    """Import ADRs from file-based storage to git notes.

    Args:
        path: Path to ADRs to import.
        format_: Source format (auto-detect if not specified).
        link_by_date: Associate ADRs with commits by date.
        dry_run: Show what would be imported.

    Raises:
        typer.Exit: On error.
    """
    try:
        # Initialize command context
        ctx = setup_command_context()

        # Validate source path
        source_path = _validate_source_path(path)

        # Detect format
        source_format = format_ or "auto"
        if source_format == "auto":
            source_format = _detect_format(source_path)
            console.print(f"[dim]Detected format: {source_format}[/dim]")

        # Parse source
        if source_format == "json":
            adrs = _import_json(source_path)
        elif source_format == "adr-tools":
            adrs = _import_adr_tools(source_path)
        else:
            adrs = _import_markdown(source_path)

        if not adrs:
            console.print("[yellow]No ADRs found to import[/yellow]")
            return

        # Link by date if requested
        if link_by_date:
            console.print("[dim]Linking ADRs to commits by date...[/dim]")
            # TODO: Implement date-based linking

        # Preview or import
        if dry_run:
            console.print(f"[bold]Would import {len(adrs)} ADRs:[/bold]")
            for adr in adrs:
                console.print(f"  - {adr.metadata.id}: {adr.metadata.title}")
            console.print()
            console.print("[dim]Use without --dry-run to import[/dim]")
        else:
            imported = 0
            for adr in adrs:
                # Check if already exists
                existing = ctx.notes_manager.get(adr.metadata.id)
                if existing:
                    console.print(
                        f"[yellow]Skipping[/yellow] {adr.metadata.id}: already exists"
                    )
                    continue

                ctx.notes_manager.add(adr)
                console.print(f"[green]Imported[/green] {adr.metadata.id}")
                imported += 1

            console.print()
            console.print(f"[green]Imported[/green] {imported} ADRs")

    except GitError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def _detect_format(path: Path) -> str:
    """Auto-detect source format."""
    if path.is_file():
        if path.suffix == ".json":
            return "json"
        return "markdown"

    # Directory - check for adr-tools pattern
    files = list(path.glob("*.md"))
    if files:
        files[0].read_text()
        if re.search(r"^\d{4}-", files[0].name):
            return "adr-tools"
    return "markdown"


def _import_markdown(path: Path) -> list[ADR]:
    """Import from Markdown files."""
    import frontmatter

    adrs = []

    files = [path] if path.is_file() else list(path.glob("**/*.md"))

    for file in files:
        try:
            post = frontmatter.load(file)
            metadata = post.metadata

            title = metadata.get("title") or file.stem
            adr_id = metadata.get("id") or _generate_id_from_filename(file.name, title)

            # Parse date
            date_val = metadata.get("date") or metadata.get("created")
            if isinstance(date_val, str):
                adr_date = date_type.fromisoformat(date_val[:10])
            elif isinstance(date_val, (date_type, datetime)):
                adr_date = (
                    date_val if isinstance(date_val, date_type) else date_val.date()
                )
            else:
                adr_date = date_type.today()

            # Parse status
            status_val = metadata.get("status", "draft")
            try:
                adr_status = (
                    ADRStatus(status_val)
                    if status_val in [s.value for s in ADRStatus]
                    else ADRStatus.DRAFT
                )
            except ValueError:
                adr_status = ADRStatus.DRAFT

            adr_metadata = ADRMetadata(
                id=adr_id,
                title=title,
                date=adr_date,
                status=adr_status,
                deciders=ensure_list(metadata.get("deciders")),
                consulted=ensure_list(metadata.get("consulted")),
                informed=ensure_list(metadata.get("informed")),
                tags=ensure_list(metadata.get("tags")),
                format=metadata.get("format", "madr"),
            )

            adrs.append(ADR(metadata=adr_metadata, content=post.content))

        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Failed to parse {file}: {e}")

    return adrs


def _import_json(path: Path) -> list[ADR]:
    """Import from JSON file."""
    data = json.loads(path.read_text())

    adrs = []
    items = data.get("adrs", [data] if "id" in data else [])

    for item in items:
        # Parse date
        date_val = item.get("date") or item.get("created")
        if isinstance(date_val, str):
            adr_date = date_type.fromisoformat(date_val[:10])
        else:
            adr_date = date_type.today()

        # Parse status
        status_val = item.get("status", "draft")
        try:
            adr_status = (
                ADRStatus(status_val)
                if status_val in [s.value for s in ADRStatus]
                else ADRStatus.DRAFT
            )
        except ValueError:
            adr_status = ADRStatus.DRAFT

        adr_metadata = ADRMetadata(
            id=item["id"],
            title=item["title"],
            date=adr_date,
            status=adr_status,
            deciders=ensure_list(item.get("deciders")),
            consulted=ensure_list(item.get("consulted")),
            informed=ensure_list(item.get("informed")),
            tags=ensure_list(item.get("tags")),
            format=item.get("format", "madr"),
            linked_commits=ensure_list(item.get("linked_commits")),
            supersedes=item.get("supersedes"),
            superseded_by=item.get("superseded_by"),
        )

        adrs.append(ADR(metadata=adr_metadata, content=item.get("content", "")))

    return adrs


def _import_adr_tools(path: Path) -> list[ADR]:
    """Import from adr-tools format (NNNN-title.md)."""
    adrs = []
    pattern = re.compile(r"^(\d{4})-(.+)\.md$")

    for file in sorted(path.glob("*.md")):
        match = pattern.match(file.name)
        if not match:
            continue

        _num, slug = match.groups()
        content = file.read_text()

        # Parse adr-tools format
        title = slug.replace("-", " ").title()
        status = "accepted"
        date_str = date_type.today().isoformat()

        # Try to extract title from content
        title_match = re.search(r"^#\s*\d+\.\s*(.+)$", content, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()

        # Try to extract status
        status_match = re.search(r"^##\s*Status\s*\n+(\w+)", content, re.MULTILINE)
        if status_match:
            status = status_match.group(1).lower()

        # Try to extract date
        date_match = re.search(
            r"^##\s*Date\s*\n+(\d{4}-\d{2}-\d{2})", content, re.MULTILINE
        )
        if date_match:
            date_str = date_match.group(1)

        adr_id = generate_adr_id(title)
        adr_date = date_type.fromisoformat(date_str)

        # Parse status
        try:
            adr_status = (
                ADRStatus(status)
                if status in [s.value for s in ADRStatus]
                else ADRStatus.DRAFT
            )
        except ValueError:
            adr_status = ADRStatus.DRAFT

        adr_metadata = ADRMetadata(
            id=adr_id,
            title=title,
            date=adr_date,
            status=adr_status,
            deciders=["imported"],
            format="nygard",  # adr-tools uses Nygard format
        )

        adrs.append(ADR(metadata=adr_metadata, content=content))

    return adrs


def _generate_id_from_filename(filename: str, title: str) -> str:
    """Generate ADR ID from filename."""
    stem = Path(filename).stem
    # Remove common prefixes
    stem = re.sub(r"^(adr[-_]?)?(\d+[-_])?", "", stem, flags=re.IGNORECASE)
    return generate_adr_id(title or stem)
