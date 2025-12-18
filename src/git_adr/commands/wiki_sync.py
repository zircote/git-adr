"""Implementation of `git adr wiki sync` command.

Synchronize ADRs with configured wiki.
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from git_adr.commands._shared import setup_command_context
from git_adr.core import GitError

console = Console()
err_console = Console(stderr=True)


def run_wiki_sync(
    direction: str = "push",
    adr: str | None = None,
    dry_run: bool = False,
) -> None:
    """Synchronize ADRs with the wiki.

    Args:
        direction: Sync direction (push, pull, both).
        adr: Sync only specific ADR.
        dry_run: Show what would be done.

    Raises:
        typer.Exit: On error.
    """
    try:
        # Initialize command context
        ctx = setup_command_context()

        # Check wiki configuration
        wiki_type = ctx.config_manager.get("wiki.type")
        if not wiki_type:
            err_console.print(
                "[red]Error:[/red] Wiki not configured.\nRun: git adr wiki init"
            )
            raise typer.Exit(1)

        # Validate direction
        if direction not in ("push", "pull", "both"):
            err_console.print(
                f"[red]Error:[/red] Invalid direction '{direction}'.\n"
                "Valid options: push, pull, both"
            )
            raise typer.Exit(1)

        # Get ADRs to sync
        if adr:
            adr_obj = ctx.notes_manager.get(adr)
            if not adr_obj:
                err_console.print(f"[red]Error:[/red] ADR not found: {adr}")
                raise typer.Exit(1)
            adrs = [adr_obj]
        else:
            adrs = ctx.notes_manager.list_all()

        if not adrs:
            console.print("[yellow]No ADRs to sync[/yellow]")
            return

        console.print(
            Panel(
                f"[bold]Wiki Synchronization[/bold]\n\n"
                f"Platform: [cyan]{wiki_type}[/cyan]\n"
                f"Direction: {direction}\n"
                f"ADRs: {len(adrs)}" + (" (dry run)" if dry_run else ""),
                title="Wiki Sync",
            )
        )

        # Perform sync
        from git_adr.wiki import WikiService, WikiServiceError

        wiki_service = WikiService(ctx.git, ctx.config)

        try:
            if dry_run:
                console.print()
                console.print("[bold]Would sync:[/bold]")
                for a in adrs[:15]:
                    console.print(
                        f"  • [cyan]{a.metadata.id}[/cyan]: {a.metadata.title}"
                    )
                if len(adrs) > 15:
                    console.print(f"  [dim]... and {len(adrs) - 15} more[/dim]")
                console.print()
                console.print("[dim]Run without --dry-run to sync[/dim]")
                return

            console.print()
            console.print("[dim]Syncing to wiki...[/dim]")

            result = wiki_service.sync(
                adrs=adrs,
                direction=direction,
                dry_run=False,
                platform=wiki_type,
            )

            # Display results
            console.print()

            if result.has_changes:
                table = Table(title="Sync Results")
                table.add_column("Action", style="bold")
                table.add_column("Count", justify="right")
                table.add_column("ADRs")

                if result.created:
                    table.add_row(
                        "[green]Created[/green]",
                        str(len(result.created)),
                        ", ".join(result.created[:5])
                        + ("..." if len(result.created) > 5 else ""),
                    )
                if result.updated:
                    table.add_row(
                        "[yellow]Updated[/yellow]",
                        str(len(result.updated)),
                        ", ".join(result.updated[:5])
                        + ("..." if len(result.updated) > 5 else ""),
                    )
                if result.deleted:
                    table.add_row(
                        "[red]Deleted[/red]",
                        str(len(result.deleted)),
                        ", ".join(result.deleted[:5])
                        + ("..." if len(result.deleted) > 5 else ""),
                    )

                console.print(table)
                console.print()
                console.print(
                    f"[green]✓[/green] Synced {result.total_synced} ADRs to wiki"
                )
            else:
                console.print("[dim]No changes to sync[/dim]")

            # Show errors if any
            if result.errors:
                console.print()
                console.print("[yellow]Warnings:[/yellow]")
                for error in result.errors[:5]:
                    console.print(f"  • {error}")

            # Show skipped
            if result.skipped:
                console.print()
                console.print("[dim]Skipped:[/dim]")
                for skip in result.skipped:
                    if skip == "pull:not-implemented":
                        console.print("  • [dim]Pull sync not yet implemented[/dim]")
                    else:
                        console.print(f"  • {skip}")

        except WikiServiceError as e:
            err_console.print(f"[red]Wiki Error:[/red] {e}")
            raise typer.Exit(1)

    except GitError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
