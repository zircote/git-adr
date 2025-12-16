"""Implementation of `git adr issue` command.

Creates GitHub issues from the command line using issue templates.
Supports hybrid input (flags + interactive prompts), preview before
submission, and local file fallback when gh CLI is unavailable.
"""

from __future__ import annotations

import os
import subprocess  # nosec B404 - subprocess needed to launch user's editor
import tempfile
from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from git_adr.core.gh_client import GitHubIssueClient, check_gh_status
from git_adr.core.issue import Issue, IssueBuilder, save_local_issue
from git_adr.core.issue_template import (
    FormElement,
    FormElementType,
    IssueTemplate,
    TemplateManager,
    TemplateSection,
)

console = Console()
err_console = Console(stderr=True)


def run_issue(
    type_: str | None = None,
    title: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    assignees: list[str] | None = None,
    repo: str | None = None,
    dry_run: bool = False,
    local_only: bool = False,
    no_edit: bool = False,
) -> None:
    """Create a GitHub issue from a template.

    Args:
        type_: Issue type (bug, feat, docs) or template name.
        title: Issue title (if not provided, will prompt).
        description: Issue description (if not provided, will prompt).
        labels: Additional labels (added to template labels).
        assignees: Override template assignees.
        repo: Target repository in owner/repo format.
        dry_run: Show what would be created without submitting.
        local_only: Save locally instead of submitting to GitHub.
        no_edit: Skip preview/edit step.

    Raises:
        typer.Exit: On error.
    """
    # Initialize template manager
    project_root = _find_project_root()
    manager = TemplateManager(project_root)

    # Resolve template type
    if type_ is None:
        # Show available types and prompt
        available = manager.get_available_types()
        if not available:
            err_console.print("[red]Error:[/red] No issue templates found")
            raise typer.Exit(1)

        console.print("\n[bold]Available issue types:[/bold]")
        for name in available:
            template = manager.get_template(name)
            aliases = manager.get_aliases_for_type(name)
            if template:
                alias_str = f" (aliases: {', '.join(aliases)})" if aliases else ""
                console.print(f"  [cyan]{name}[/cyan]{alias_str}")
                if template.about:
                    console.print(f"    {template.about}")

        type_ = Prompt.ask(
            "\nSelect issue type",
            choices=available,
            default=available[0] if available else None,
        )

    # Get template - type_ is guaranteed to be str at this point by Prompt.ask
    if type_ is None:
        err_console.print("[red]Error:[/red] No issue type selected")
        raise typer.Exit(1)
    template = manager.get_template(type_)
    if template is None:
        err_console.print(f"[red]Error:[/red] Unknown issue type: {type_}")
        console.print(manager.format_available_types_message())
        raise typer.Exit(1)

    console.print(f"\n[bold]Creating {template.name}[/bold]")
    if template.about:
        console.print(f"[dim]{template.about}[/dim]\n")

    # Initialize builder with template
    builder = IssueBuilder(template)

    # Set title from flag or prompt
    if title:
        # Merge template prefix with provided title if needed
        if template.title and not title.startswith(template.title):
            builder.set_title(template.title + title)
        else:
            builder.set_title(title)
    else:
        # Prompt for title with template prefix hint
        default_title = template.title or ""
        prompted_title = Prompt.ask(
            "Issue title",
            default=default_title if default_title else None,
        )
        builder.set_title(prompted_title or "")

    # Add extra labels from flags
    if labels:
        for label in labels:
            builder.add_label(label)

    # Override assignees if provided
    if assignees:
        builder.set_assignees(assignees)

    # Prompt for template fields
    _prompt_for_fields(builder, template, description)

    # Preview and confirmation flow
    if not no_edit:
        action = _preview_and_confirm(builder, dry_run)
        if action == "cancel":
            console.print("[yellow]Issue creation cancelled.[/yellow]")
            raise typer.Exit(0)
        if action == "edit":
            _edit_in_editor(builder)

    # Check for dry run
    if dry_run:
        console.print("\n[cyan]Dry run - no issue created[/cyan]")
        console.print(
            Panel(builder.preview(), title="Issue Preview", border_style="cyan")
        )
        return

    # Build the issue
    try:
        issue = builder.build()
    except ValueError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    # Submit or save locally
    if local_only:
        _save_locally(issue)
    else:
        _submit_or_save(issue, repo)


def _find_project_root() -> Path:
    """Find the project root directory (containing .git)."""
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / ".git").exists():
            return parent
    return cwd


def _prompt_for_fields(
    builder: IssueBuilder,
    template: IssueTemplate,
    description: str | None = None,
) -> None:
    """Prompt user for template fields.

    Args:
        builder: IssueBuilder to populate.
        template: Template with field definitions.
        description: Optional pre-provided description (used for first field).
    """
    fields = template.promptable_fields
    description_used = False

    for _i, field in enumerate(fields):
        if isinstance(field, TemplateSection):
            # For markdown templates, prompt for each section
            field_id = field.id

            # Use provided description for first text field
            if not description_used and description:
                builder.set_field(field_id, description)
                description_used = True
                console.print(f"[dim]Using provided value for {field.header}[/dim]")
                continue

            console.print(f"\n[bold]{field.header}[/bold]")
            if field.hint:
                console.print(f"[dim]{field.hint}[/dim]")

            value = _prompt_multiline(f"Enter {field.header}")
            builder.set_field(field_id, value)

        elif isinstance(field, FormElement):
            # For YAML forms, handle different element types
            field_id = field.id or ""

            # Use provided description for first text field
            if (
                not description_used
                and description
                and field.type
                in (
                    FormElementType.INPUT,
                    FormElementType.TEXTAREA,
                )
            ):
                builder.set_field(field_id, description)
                description_used = True
                console.print(f"[dim]Using provided value for {field.label}[/dim]")
                continue

            console.print(f"\n[bold]{field.label}[/bold]")
            if field.description:
                console.print(f"[dim]{field.description}[/dim]")

            if field.type == FormElementType.INPUT:
                value = Prompt.ask(
                    "Value",
                    default=field.default_value or "",
                )
                builder.set_field(field_id, value)

            elif field.type == FormElementType.TEXTAREA:
                value = _prompt_multiline(f"Enter {field.label}")
                builder.set_field(field_id, value)

            elif field.type == FormElementType.DROPDOWN:
                options = field.options
                if options:
                    console.print("Options:")
                    for j, opt in enumerate(options, 1):
                        console.print(f"  {j}. {opt}")
                    choice = Prompt.ask(
                        "Select option",
                        choices=[str(j) for j in range(1, len(options) + 1)],
                    )
                    value = options[int(choice) - 1]
                    builder.set_field(field_id, value)

            elif field.type == FormElementType.CHECKBOXES:
                options = field.options
                selected: list[str] = []
                if options:
                    console.print("Select options (y/n for each):")
                    for opt in options:
                        if Confirm.ask(f"  {opt}", default=False):
                            selected.append(opt)
                    builder.set_field(
                        field_id, "\n".join(f"- [x] {s}" for s in selected)
                    )


def _prompt_multiline(prompt: str) -> str:
    """Prompt for multiline input.

    Args:
        prompt: Prompt message.

    Returns:
        User input as string.
    """
    console.print(
        f"[dim]({prompt}. Enter text, then press Enter twice to finish)[/dim]"
    )

    lines: list[str] = []
    empty_count = 0

    while True:
        try:
            line = input()
            if line == "":
                empty_count += 1
                if empty_count >= 2:
                    break
                lines.append("")
            else:
                empty_count = 0
                lines.append(line)
        except EOFError:
            break

    # Remove trailing empty lines for cleaner output
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines).strip()


def _preview_and_confirm(builder: IssueBuilder, dry_run: bool) -> str:
    """Show preview and get user confirmation.

    Args:
        builder: IssueBuilder with current state.
        dry_run: Whether this is a dry run.

    Returns:
        Action to take: "submit", "edit", or "cancel".
    """
    console.print("\n")
    console.print(
        Panel(
            Markdown(builder.preview()),
            title="Issue Preview",
            border_style="blue",
        )
    )

    if dry_run:
        return "submit"  # Will be handled as dry run later

    # Prompt for action
    action = Prompt.ask(
        "\nAction",
        choices=["submit", "edit", "cancel"],
        default="submit",
    )

    return action


def _edit_in_editor(builder: IssueBuilder) -> None:
    """Open issue in external editor for editing.

    Args:
        builder: IssueBuilder to edit.
    """
    # Get editor
    editor = os.environ.get("EDITOR", os.environ.get("VISUAL", "vim"))

    # Create temp file with current content
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".md",
        delete=False,
    ) as f:
        # Write preview content
        f.write(f"# {builder.title}\n\n")
        for field in builder.template.promptable_fields:
            if isinstance(field, TemplateSection):
                value = builder.get_field(field.id) or ""
                f.write(f"## {field.header}\n\n{value}\n\n")
            elif isinstance(field, FormElement) and field.id:
                value = builder.get_field(field.id) or ""
                f.write(f"## {field.label}\n\n{value}\n\n")
        temp_path = f.name

    try:
        # Open editor
        subprocess.run([editor, temp_path], check=True)  # nosec B603

        # Read back edited content and update builder
        edited = Path(temp_path).read_text()
        _parse_edited_content(builder, edited)

        console.print("[green]Content updated from editor.[/green]")
    except subprocess.CalledProcessError:
        console.print(
            "[yellow]Editor closed without saving or error occurred.[/yellow]"
        )
    finally:
        # Clean up temp file
        Path(temp_path).unlink(missing_ok=True)


def _parse_edited_content(builder: IssueBuilder, content: str) -> None:
    """Parse edited markdown content back into builder.

    Args:
        builder: IssueBuilder to update.
        content: Edited markdown content.
    """
    import re

    lines = content.split("\n")
    current_section: str | None = None
    section_content: list[str] = []

    # Extract title from # heading
    for line in lines:
        title_match = re.match(r"^#\s+(.+)$", line)
        if title_match:
            builder.set_title(title_match.group(1).strip())
            break

    # Extract sections
    for line in lines:
        section_match = re.match(r"^##\s+(.+)$", line)
        if section_match:
            # Save previous section
            if current_section is not None:
                _save_section(builder, current_section, section_content)
            current_section = section_match.group(1).strip()
            section_content = []
        elif current_section is not None:
            section_content.append(line)

    # Save last section
    if current_section is not None:
        _save_section(builder, current_section, section_content)


def _save_section(builder: IssueBuilder, header: str, content_lines: list[str]) -> None:
    """Save a section to the builder.

    Args:
        builder: IssueBuilder to update.
        header: Section header.
        content_lines: Section content lines.
    """
    content = "\n".join(content_lines).strip()

    # Try to match by header to field
    for field in builder.template.promptable_fields:
        if isinstance(field, TemplateSection):
            if field.header.lower() == header.lower():
                builder.set_field(field.id, content)
                return
        elif isinstance(field, FormElement) and field.id:
            if field.label.lower() == header.lower():
                builder.set_field(field.id, content)
                return


def _save_locally(issue: Issue) -> None:
    """Save issue to local file.

    Args:
        issue: Issue to save.
    """
    try:
        path = save_local_issue(issue)
        console.print(f"\n[green]Issue saved locally:[/green] {path}")
        console.print(
            "[dim]You can submit this later manually or copy the content to GitHub.[/dim]"
        )
    except OSError as e:
        err_console.print(f"[red]Error saving file:[/red] {e}")
        raise typer.Exit(1)


def _submit_or_save(issue: Issue, repo: str | None = None) -> None:
    """Submit to GitHub or save locally if unavailable.

    Args:
        issue: Issue to submit.
        repo: Optional repository override.
    """
    # Check gh CLI status
    is_ready, message = check_gh_status()

    if not is_ready:
        console.print(f"\n[yellow]{message}[/yellow]")
        console.print("\n[dim]Saving locally instead...[/dim]")
        _save_locally(issue)
        return

    # Submit via gh CLI
    console.print("\n[dim]Submitting to GitHub...[/dim]")
    client = GitHubIssueClient(repo=repo)
    result = client.create_issue(issue)

    if result.success:
        console.print("\n[green]Issue created successfully![/green]")
        console.print(f"[link={result.url}]{result.url}[/link]")
    else:
        err_console.print(f"\n[red]Error:[/red] {result.error}")
        console.print("\n[dim]Saving locally as fallback...[/dim]")
        _save_locally(issue)
