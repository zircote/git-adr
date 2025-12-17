"""Governance template generation commands for git-adr.

This module provides commands to generate governance templates:
- PR templates with architecture impact checklists
- Issue templates for ADR proposals
- CODEOWNERS patterns for ADR review requirements
"""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

console = Console()
err_console = Console(stderr=True)


def run_templates_pr(
    output: str | None = None,
    require_adr: bool = False,
    reviewers: list[str] | None = None,
) -> None:
    """Generate a pull request template with ADR checklist.

    Args:
        output: Output path (default: .github/PULL_REQUEST_TEMPLATE.md)
        require_adr: Whether to require ADR for architectural changes
        reviewers: List of default reviewers to cc
    """
    from git_adr.templates import render_template

    content = render_template(
        "governance/pr-template.md.j2",
        require_adr=require_adr,
        reviewers=reviewers or [],
        title_placeholder="Decision Title",
    )

    # GitHub standard location
    output_path = Path(output) if output else Path(".github/PULL_REQUEST_TEMPLATE.md")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        console.print(
            f"[yellow]Warning:[/yellow] {output_path} already exists, overwriting"
        )

    output_path.write_text(content)
    console.print(f"[green]✓[/green] Generated {output_path}")
    console.print()
    console.print(
        "This template will be used automatically for new PRs in your repository."
    )


def run_templates_issue(
    output: str | None = None,
    labels: str = "architecture, adr-proposal",
    stakeholders: list[str] | None = None,
    assignees: str = "",
) -> None:
    """Generate an issue template for ADR proposals.

    Args:
        output: Output path (default: .github/ISSUE_TEMPLATE/adr-proposal.md)
        labels: Comma-separated labels to apply
        stakeholders: List of stakeholders to mention in the issue body
        assignees: Comma-separated GitHub usernames for auto-assignment
    """
    from git_adr.templates import render_template

    content = render_template(
        "governance/issue-template-adr.md.j2",
        labels=labels,
        stakeholders=stakeholders or [],
        assignees=assignees,
    )

    if output:
        output_path = Path(output)
    else:
        # GitHub standard location for issue templates
        output_path = Path(".github/ISSUE_TEMPLATE/adr-proposal.md")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        console.print(
            f"[yellow]Warning:[/yellow] {output_path} already exists, overwriting"
        )

    output_path.write_text(content)
    console.print(f"[green]✓[/green] Generated {output_path}")
    console.print()
    console.print(
        "This template will appear in the 'New Issue' dropdown in your repository."
    )


def run_templates_codeowners(
    output: str | None = None,
    team: str = "@architecture-team",
    adr_directory: str | None = None,
    protected_paths: list[str] | None = None,
    api_paths: list[str] | None = None,
    schema_paths: list[str] | None = None,
    infra_paths: list[str] | None = None,
) -> None:
    """Generate CODEOWNERS patterns for ADR governance.

    Args:
        output: Output path (default: prints to stdout for manual integration)
        team: GitHub team or user handle for architecture reviews
        adr_directory: Directory containing file-based ADRs (if any)
        protected_paths: Paths requiring architecture team review
        api_paths: API definition paths
        schema_paths: Database schema paths
        infra_paths: Infrastructure as Code paths
    """
    from git_adr.templates import render_template

    content = render_template(
        "governance/codeowners.j2",
        team=team,
        adr_directory=adr_directory,
        protected_paths=protected_paths or [],
        api_paths=api_paths or [],
        schema_paths=schema_paths or [],
        infra_paths=infra_paths or [],
    )

    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_path.exists():
            console.print(f"[yellow]Warning:[/yellow] {output_path} already exists")
            console.print(
                "Consider appending the relevant sections to your existing CODEOWNERS"
            )

        output_path.write_text(content)
        console.print(f"[green]✓[/green] Generated {output_path}")
    else:
        # Print to stdout for manual integration
        console.print("[bold]CODEOWNERS content:[/bold]\n")
        console.print(content, highlight=False)
        console.print()
        console.print(
            "[dim]Tip: Use --output CODEOWNERS to write to file, "
            "or copy the relevant sections above to your existing CODEOWNERS[/dim]"
        )


def run_templates_all(
    output_dir: str | None = None,
    team: str = "@architecture-team",
) -> None:
    """Generate all governance templates at once.

    Args:
        output_dir: Base output directory (default: .)
        team: GitHub team or user handle for reviews
    """
    base_dir = Path(output_dir) if output_dir else Path()

    console.print("[bold]Generating all governance templates...[/bold]\n")

    # Generate PR template
    run_templates_pr(
        output=str(base_dir / ".github/PULL_REQUEST_TEMPLATE.md"),
        require_adr=True,
        reviewers=[team],
    )
    console.print()

    # Generate issue template
    run_templates_issue(
        output=str(base_dir / ".github/ISSUE_TEMPLATE/adr-proposal.md"),
        stakeholders=[team],
    )
    console.print()

    # Generate CODEOWNERS
    run_templates_codeowners(
        output=str(base_dir / "CODEOWNERS.adr"),
        team=team,
        protected_paths=["src/", "lib/", "api/"],
    )

    console.print()
    console.print("[bold green]✓ All governance templates generated![/bold green]")
    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print("1. Review the generated templates in .github/")
    console.print("2. Merge CODEOWNERS.adr into your existing CODEOWNERS file")
    console.print("3. Commit and push to enable the templates")


def run_templates_list() -> None:
    """List available governance templates."""
    from git_adr.templates import list_templates

    console.print("[bold]Available Governance Templates:[/bold]\n")

    templates = list_templates("governance")
    for template in templates:
        name = (
            template.replace("governance/", "").replace(".md.j2", "").replace(".j2", "")
        )
        if "pr" in name:
            desc = "Pull Request template with ADR checklist"
        elif "issue" in name:
            desc = "Issue template for ADR proposals"
        elif "codeowners" in name:
            desc = "CODEOWNERS patterns for architecture review"
        else:
            desc = "Template"

        console.print(f"  • [cyan]{name}[/cyan] - {desc}")

    console.print()
    console.print(
        "Generate with: [cyan]git adr templates pr[/cyan], "
        "[cyan]git adr templates issue[/cyan], or "
        "[cyan]git adr templates codeowners[/cyan]"
    )
