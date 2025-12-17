"""Implementation of `git adr log` command.

Shows git log with ADR annotations inline.
"""

from __future__ import annotations

import typer
from rich.console import Console

from git_adr.commands._shared import setup_command_context
from git_adr.core import GitError

console = Console()
err_console = Console(stderr=True)


def run_log(
    n: int = 10,
    all_: bool = False,
) -> None:
    """Show git log with ADR annotations.

    Args:
        n: Number of commits to show.
        all_: Show all commits with annotations.

    Raises:
        typer.Exit: On error.
    """
    try:
        # Initialize command context
        ctx = setup_command_context()

        # Build git log command
        args = [
            "log",
            f"--show-notes={ctx.config.notes_ref}",
            "--format=format:%C(yellow)%h%C(reset) %C(cyan)%ad%C(reset) %s%n%C(dim)%an%C(reset)%n%N",
            "--date=short",
        ]

        if not all_:
            args.append(f"-{n}")

        result = ctx.git.run(args, check=False)

        if result.success:
            # Parse and format the output
            _format_log_output(result.stdout)
        else:
            err_console.print(f"[red]Error:[/red] {result.stderr}")
            raise typer.Exit(1)

    except GitError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def _format_log_output(output: str) -> None:
    """Format git log output with ADR highlighting.

    Args:
        output: Raw git log output.
    """

    entries = output.strip().split("\n\n")

    for entry in entries:
        if not entry.strip():
            continue

        lines = entry.split("\n")
        if len(lines) < 2:
            console.print(entry)
            continue

        # First line is commit info
        commit_line = lines[0]

        # Remaining lines are notes (if any)
        notes = "\n".join(lines[2:]).strip() if len(lines) > 2 else ""

        # Print commit info
        console.print(commit_line)

        if notes and "---" in notes:
            # This looks like an ADR note (has YAML frontmatter)
            _format_adr_note(notes)
        elif notes:
            # Just regular notes text
            console.print(f"    [dim]{notes}[/dim]")

        console.print()


def _format_adr_note(note_content: str) -> None:
    """Format an ADR note for display.

    Args:
        note_content: Note content (YAML frontmatter + markdown).
    """
    import yaml

    try:
        # Try to parse as ADR
        if note_content.startswith("---"):
            parts = note_content.split("---", 2)
            if len(parts) >= 3:
                metadata = yaml.safe_load(parts[1])
                if metadata and "id" in metadata:
                    # Format as ADR reference
                    adr_id = metadata.get("id", "unknown")
                    title = metadata.get("title", "")
                    status = metadata.get("status", "")

                    console.print(
                        f"    [green]ADR:[/green] [cyan]{adr_id}[/cyan] "
                        f"[{status}] {title}"
                    )
                    return
    except (yaml.YAMLError, KeyError):
        pass

    # Fallback: just print the note
    console.print(f"    [dim]{note_content[:100]}...[/dim]")
