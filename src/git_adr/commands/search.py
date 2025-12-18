"""Implementation of `git adr search` command.

Full-text search across ADRs with highlighted snippets.
"""

from __future__ import annotations

from typing import cast

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from git_adr.commands._shared import get_status_style, setup_command_context
from git_adr.core import ADRStatus, GitError
from git_adr.core.index import IndexManager

console = Console()
err_console = Console(stderr=True)


def run_search(
    query: str,
    status: str | None = None,
    tag: str | None = None,
    context: int = 2,
    case_sensitive: bool = False,
    regex: bool = False,
) -> None:
    """Search ADRs by content.

    Args:
        query: Search query.
        status: Filter by status.
        tag: Filter by tag.
        context: Lines of context around matches.
        case_sensitive: Case-sensitive search.
        regex: Treat query as regex.

    Raises:
        typer.Exit: On error.
    """
    try:
        # Initialize command context with index manager
        ctx = setup_command_context(require_index=True)
        index_manager = cast(IndexManager, ctx.index_manager)

        # Parse status filter
        parsed_status = None
        if status:
            try:
                parsed_status = ADRStatus.from_string(status)
            except ValueError:
                err_console.print(f"[red]Error:[/red] Invalid status: {status}")
                raise typer.Exit(1)

        # Perform search
        matches = index_manager.search(
            query=query,
            status=parsed_status,
            tag=tag,
            case_sensitive=case_sensitive,
            regex=regex,
            context_lines=context,
        )

        if not matches:
            console.print(f"[dim]No ADRs matching '{query}'[/dim]")
            return

        console.print(f"Found {len(matches)} matching ADR(s):\n")

        for match in matches:
            _display_match(match, query, case_sensitive)

    except GitError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def _display_match(match, query: str, case_sensitive: bool) -> None:
    """Display a search match with snippets.

    Args:
        match: SearchMatch object.
        query: Original search query.
        case_sensitive: Whether search was case-sensitive.
    """

    entry = match.entry

    # Header
    status_style = get_status_style(entry.status)
    header = Text()
    header.append(entry.id, style="cyan bold")
    header.append(" ")
    header.append(f"[{entry.status.value}]", style=status_style)
    header.append(" ")
    header.append(entry.title)

    console.print(header)
    console.print(f"  Date: {entry.date.isoformat()}", style="dim")

    if entry.tags:
        console.print(f"  Tags: {', '.join(entry.tags)}", style="dim")

    # Snippets
    if match.snippets:
        for snippet in match.snippets[:3]:  # Limit snippets
            highlighted = _highlight_snippet(snippet, query, case_sensitive)
            console.print()
            console.print(Panel(highlighted, border_style="dim"))

    console.print()


def _highlight_snippet(snippet: str, query: str, case_sensitive: bool) -> Text:
    """Highlight search terms in snippet.

    Args:
        snippet: Snippet text.
        query: Search query.
        case_sensitive: Whether search was case-sensitive.

    Returns:
        Rich Text with highlighting.
    """
    import re

    flags = 0 if case_sensitive else re.IGNORECASE
    pattern = re.compile(re.escape(query), flags)

    text = Text()
    last_end = 0

    for match in pattern.finditer(snippet):
        # Add text before match
        text.append(snippet[last_end : match.start()])
        # Add highlighted match
        text.append(match.group(), style="bold yellow")
        last_end = match.end()

    # Add remaining text
    text.append(snippet[last_end:])

    return text
