"""Implementation of `git adr wiki init` command.

Initialize wiki synchronization for ADRs.
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel

from git_adr.commands._shared import setup_command_context
from git_adr.core import GitError

console = Console()
err_console = Console(stderr=True)


def run_wiki_init(
    platform: str | None = None,
) -> None:
    """Initialize wiki synchronization.

    Auto-detects GitHub or GitLab and sets up the wiki structure.

    Args:
        platform: Force platform (github, gitlab).

    Raises:
        typer.Exit: On error.
    """
    try:
        # Initialize command context
        ctx = setup_command_context()

        # Initialize wiki service
        from git_adr.wiki import WikiService, WikiServiceError

        wiki_service = WikiService(ctx.git, ctx.config)

        try:
            result = wiki_service.init(platform)
            detected_platform = result["platform"]
            wiki_url = result["wiki_url"]

            # Store wiki config
            ctx.config_manager.set("wiki.type", detected_platform)
            ctx.config_manager.set("wiki.url", wiki_url)

            console.print(
                Panel(
                    f"[bold green]Wiki Sync Initialized[/bold green]\n\n"
                    f"Platform: [cyan]{detected_platform}[/cyan]\n"
                    f"Wiki URL: [dim]{wiki_url}[/dim]",
                    title="Wiki Init",
                )
            )

            console.print()
            console.print("[bold]Next steps:[/bold]")
            console.print("  1. Ensure wiki is enabled in repository settings")
            console.print("  2. Run [cyan]git adr wiki sync[/cyan] to publish ADRs")
            console.print()
            console.print("[dim]Tip: Use --dry-run to preview changes[/dim]")

        except WikiServiceError as e:
            # Fallback to showing available platforms
            err_console.print(f"[yellow]Warning:[/yellow] {e}")
            console.print()
            console.print("[bold]Supported wiki platforms:[/bold]")
            console.print()
            console.print("  [cyan]github[/cyan]")
            console.print("    Sync to GitHub Wiki (repo.wiki.git)")
            console.print("    Auto-generates navigation sidebar")
            console.print()
            console.print("  [cyan]gitlab[/cyan]")
            console.print("    Sync to GitLab Wiki")
            console.print("    Auto-generates navigation pages")
            console.print()
            console.print("Usage: [cyan]git adr wiki init --platform github[/cyan]")

    except GitError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
