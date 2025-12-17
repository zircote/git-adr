"""CI/CD workflow generation commands for git-adr.

This module provides commands to generate CI/CD workflow configurations
for various platforms (GitHub Actions, GitLab CI) that integrate ADR
operations into the development pipeline.
"""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from git_adr import __version__

console = Console()
err_console = Console(stderr=True)


def run_ci_github(
    sync: bool = False,
    validate: bool = False,
    output: str | None = None,
    main_branch: str = "main",
    wiki_sync: bool = False,
    wiki_provider: str = "github",
    python_version: str = "3.11",
    export_format: str | None = None,
) -> None:
    """Generate GitHub Actions workflow for ADR operations.

    Args:
        sync: Generate sync workflow (push ADRs to wiki on merge)
        validate: Generate validation workflow (check ADRs on PR)
        output: Output directory (default: .github/workflows)
        main_branch: Main branch name for triggers
        wiki_sync: Enable wiki synchronization in sync workflow
        wiki_provider: Wiki provider (github, confluence)
        python_version: Python version for workflows
        export_format: Export format (markdown, json, html)
    """
    from git_adr.templates import render_template

    # Default to both if neither specified
    if not sync and not validate:
        sync = True
        validate = True

    output_dir = Path(output) if output else Path(".github/workflows")

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_files: list[Path] = []

    if sync:
        content = render_template(
            "ci/github-actions-sync.yml.j2",
            main_branch=main_branch,
            wiki_sync=wiki_sync,
            wiki_provider=wiki_provider,
            python_version=python_version,
            export_format=export_format,
            validate_adrs=validate,  # Include validation step in sync
            git_adr_version=__version__,  # Pin to current version for supply-chain security
        )

        output_file = output_dir / "adr-sync.yml"
        if output_file.exists():
            console.print(
                f"[yellow]Warning:[/yellow] {output_file} already exists, overwriting"
            )

        output_file.write_text(content)
        generated_files.append(output_file)
        console.print(f"[green]✓[/green] Generated {output_file}")

    if validate:
        content = render_template(
            "ci/github-actions-validate.yml.j2",
            main_branch=main_branch,
            python_version=python_version,
            require_adr_for_changes=False,  # Default: advisory only
            git_adr_version=__version__,  # Pin to current version for supply-chain security
        )

        output_file = output_dir / "adr-validate.yml"
        if output_file.exists():
            console.print(
                f"[yellow]Warning:[/yellow] {output_file} already exists, overwriting"
            )

        output_file.write_text(content)
        generated_files.append(output_file)
        console.print(f"[green]✓[/green] Generated {output_file}")

    if generated_files:
        console.print()
        console.print("[bold]Next steps:[/bold]")
        console.print("1. Review the generated workflow files")
        console.print("2. Customize triggers and options as needed")
        console.print("3. Commit and push to enable the workflows")
        if wiki_sync:
            console.print(
                "4. Ensure GITHUB_TOKEN has wiki write permissions (or use a PAT)"
            )


def run_ci_gitlab(
    sync: bool = False,
    validate: bool = False,
    output: str | None = None,
    main_branch: str = "main",
    wiki_sync: bool = False,
    wiki_provider: str = "gitlab",
    python_version: str = "3.11",
    export_format: str | None = None,
) -> None:
    """Generate GitLab CI pipeline for ADR operations.

    Args:
        sync: Generate sync stage (push ADRs to wiki on merge)
        validate: Generate validation stage (check ADRs on MR)
        output: Output file (default: .gitlab-ci.yml or gitlab-ci-adr.yml)
        main_branch: Main branch name for triggers
        wiki_sync: Enable wiki synchronization
        wiki_provider: Wiki provider (gitlab, confluence)
        python_version: Python version for jobs
        export_format: Export format (markdown, json, html)
    """
    from git_adr.templates import render_template

    # Default to both if neither specified
    if not sync and not validate:
        sync = True
        validate = True

    # Determine output path
    if output:
        output_file = Path(output)
    else:
        # Check if .gitlab-ci.yml exists
        existing_ci = Path(".gitlab-ci.yml")
        if existing_ci.exists():
            # Create separate file to be included
            output_file = Path("gitlab-ci-adr.yml")
            console.print(
                "[yellow]Note:[/yellow] Existing .gitlab-ci.yml found. "
                f"Creating {output_file} for manual inclusion."
            )
            console.print(
                "Add to your .gitlab-ci.yml: [cyan]include: gitlab-ci-adr.yml[/cyan]"
            )
        else:
            output_file = existing_ci

    content = render_template(
        "ci/gitlab-ci-sync.yml.j2",
        main_branch=main_branch,
        validate_adrs=validate,
        wiki_sync=wiki_sync,
        wiki_provider=wiki_provider,
        python_version=python_version,
        export_format=export_format,
        git_adr_version=__version__,  # Pin to current version for supply-chain security
    )

    if output_file.exists() and output_file.name == ".gitlab-ci.yml":
        console.print(
            f"[yellow]Warning:[/yellow] {output_file} already exists, overwriting"
        )

    output_file.write_text(content)
    console.print(f"[green]✓[/green] Generated {output_file}")

    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print("1. Review the generated pipeline configuration")
    console.print("2. Customize stages and jobs as needed")
    if output_file.name != ".gitlab-ci.yml":
        console.print(
            f"3. Include in your .gitlab-ci.yml: [cyan]include: {output_file}[/cyan]"
        )
    else:
        console.print("3. Commit and push to enable the pipeline")
    if wiki_sync:
        console.print(
            f"4. Configure CI/CD variables for wiki access "
            f"({'GITLAB_TOKEN' if wiki_provider == 'gitlab' else 'CONFLUENCE_*'})"
        )


def run_ci_list() -> None:
    """List available CI/CD templates."""
    from git_adr.templates import list_templates

    console.print("[bold]Available CI/CD Templates:[/bold]\n")

    templates = list_templates("ci")
    for template in templates:
        name = template.replace("ci/", "").replace(".yml.j2", "")
        if "github" in name:
            platform = "GitHub Actions"
        elif "gitlab" in name:
            platform = "GitLab CI"
        else:
            platform = "Generic"

        console.print(f"  • [cyan]{name}[/cyan] ({platform})")

    console.print()
    console.print(
        "Generate with: [cyan]git adr ci github[/cyan] or "
        "[cyan]git adr ci gitlab[/cyan]"
    )
