"""Command-line interface for git-adr.

git-adr manages Architecture Decision Records using git notes,
keeping them invisible in the working tree but visible in history.
"""

from __future__ import annotations

import sys
from typing import Annotated

import typer
from rich.console import Console

from git_adr import __version__

# Create main application with rich integration
app = typer.Typer(
    name="git-adr",
    help="Architecture Decision Records management using git notes.",
    rich_markup_mode="rich",
    no_args_is_help=True,
    add_completion=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)

# Console for rich output
console = Console()
err_console = Console(stderr=True)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"git-adr version {__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-V",
            help="Show version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """Git ADR - Architecture Decision Records in git notes.

    Store ADRs invisibly in your repository's history, not in files.
    ADRs are associated with commits and sync with regular git operations.
    """


# =============================================================================
# Core Commands (P0)
# =============================================================================


@app.command()
def init(
    namespace: Annotated[
        str,
        typer.Option(
            "--namespace",
            "-n",
            help="Custom namespace for ADR notes (default: adr).",
        ),
    ] = "adr",
    template: Annotated[
        str,
        typer.Option(
            "--template",
            "-t",
            help="Default ADR format template.",
        ),
    ] = "madr",
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Reinitialize even if already initialized.",
        ),
    ] = False,
) -> None:
    """Initialize ADR tracking in this repository.

    Sets up the git notes namespace, configures fetch/push for notes,
    and creates the initial ADR (ADR-0000: Use ADRs).
    """
    from git_adr.commands.init import run_init

    run_init(namespace=namespace, template=template, force=force)


@app.command("new")
def new_adr(
    title: Annotated[str, typer.Argument(help="Title for the new ADR.")],
    status: Annotated[
        str,
        typer.Option(
            "--status",
            "-s",
            help="Initial status (proposed, accepted, deprecated, superseded).",
        ),
    ] = "proposed",
    tags: Annotated[
        list[str] | None,
        typer.Option(
            "--tag",
            "-t",
            help="Tags for categorization (can be repeated).",
        ),
    ] = None,
    deciders: Annotated[
        list[str] | None,
        typer.Option(
            "--deciders",
            "-d",
            help="Decision makers (comma-separated or repeated).",
        ),
    ] = None,
    link: Annotated[
        str | None,
        typer.Option(
            "--link",
            "-l",
            help="Link to a commit SHA.",
        ),
    ] = None,
    template: Annotated[
        str | None,
        typer.Option(
            "--template",
            help="Override default template format.",
        ),
    ] = None,
    file: Annotated[
        str | None,
        typer.Option(
            "--file",
            "-f",
            help="Read content from file instead of opening editor.",
        ),
    ] = None,
    no_edit: Annotated[
        bool,
        typer.Option(
            "--no-edit",
            help="Don't open editor (requires --file or stdin).",
        ),
    ] = False,
    preview: Annotated[
        bool,
        typer.Option(
            "--preview",
            help="Show template without creating ADR.",
        ),
    ] = False,
    draft: Annotated[
        bool,
        typer.Option(
            "--draft",
            help="Mark as draft (not ready for review).",
        ),
    ] = False,
) -> None:
    """Create a new Architecture Decision Record.

    Opens your configured editor with a template. The ADR is stored
    in git notes and automatically indexed for fast searching.

    [bold]Input modes:[/bold]
    - Editor (default): Opens $EDITOR with template
    - File: --file path/to/content.md
    - Stdin: echo "content" | git adr new "Title"
    - Preview: --preview shows template without creating
    """
    from git_adr.commands.new import run_new

    run_new(
        title=title,
        status=status,
        tags=tags or [],
        deciders=deciders,
        link=link,
        template=template,
        file=file,
        no_edit=no_edit,
        preview=preview,
        draft=draft,
    )


@app.command("list")
def list_adrs(
    status: Annotated[
        str | None,
        typer.Option(
            "--status",
            "-s",
            help="Filter by status.",
        ),
    ] = None,
    tag: Annotated[
        str | None,
        typer.Option(
            "--tag",
            "-t",
            help="Filter by tag.",
        ),
    ] = None,
    since: Annotated[
        str | None,
        typer.Option(
            "--since",
            help="Show ADRs since date (YYYY-MM-DD).",
        ),
    ] = None,
    until: Annotated[
        str | None,
        typer.Option(
            "--until",
            help="Show ADRs until date (YYYY-MM-DD).",
        ),
    ] = None,
    format_: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format (table, json, csv, oneline).",
        ),
    ] = "table",
    reverse: Annotated[
        bool,
        typer.Option(
            "--reverse",
            "-r",
            help="Reverse chronological order.",
        ),
    ] = False,
) -> None:
    """List all Architecture Decision Records.

    Shows a table of ADRs with their ID, status, date, and title.
    Use filters to narrow down the results.
    """
    from git_adr.commands.list import run_list

    run_list(
        status=status,
        tag=tag,
        since=since,
        until=until,
        format_=format_,
        reverse=reverse,
    )


@app.command()
def show(
    adr_id: Annotated[str, typer.Argument(help="ADR ID to display.")],
    format_: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format (markdown, yaml, json).",
        ),
    ] = "markdown",
    metadata_only: Annotated[
        bool,
        typer.Option(
            "--metadata-only",
            "-m",
            help="Show only metadata, not content.",
        ),
    ] = False,
    no_interactive: Annotated[
        bool,
        typer.Option(
            "--no-interactive",
            help="Suppress interactive prompts.",
        ),
    ] = False,
) -> None:
    """Display a single ADR with formatting.

    Renders the ADR with syntax highlighting and shows
    linked commits and supersession relationships.
    """
    from git_adr.commands.show import run_show

    run_show(
        adr_id=adr_id,
        format_=format_,
        metadata_only=metadata_only,
        interactive=not no_interactive,
    )


@app.command()
def edit(
    adr_id: Annotated[str, typer.Argument(help="ADR ID to edit.")],
    status: Annotated[
        str | None,
        typer.Option(
            "--status",
            "-s",
            help="Change status without opening editor.",
        ),
    ] = None,
    add_tag: Annotated[
        list[str] | None,
        typer.Option(
            "--add-tag",
            help="Add a tag (can be repeated).",
        ),
    ] = None,
    remove_tag: Annotated[
        list[str] | None,
        typer.Option(
            "--remove-tag",
            help="Remove a tag (can be repeated).",
        ),
    ] = None,
    link: Annotated[
        str | None,
        typer.Option(
            "--link",
            "-l",
            help="Link to a commit SHA.",
        ),
    ] = None,
    unlink: Annotated[
        str | None,
        typer.Option(
            "--unlink",
            help="Remove link to a commit SHA.",
        ),
    ] = None,
) -> None:
    """Edit an existing ADR.

    Opens the ADR in your editor, or use options for quick
    metadata changes without opening the editor.
    """
    from git_adr.commands.edit import run_edit

    run_edit(
        adr_id=adr_id,
        status=status,
        add_tag=add_tag or [],
        remove_tag=remove_tag or [],
        link=link,
        unlink=unlink,
    )


@app.command()
def rm(
    adr_id: Annotated[str, typer.Argument(help="ADR ID to remove.")],
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Skip confirmation prompt.",
        ),
    ] = False,
) -> None:
    """Remove an ADR from git notes.

    Permanently removes the specified ADR from storage. This action
    cannot be undone (though the ADR may be recoverable from git reflog).

    Use --force to skip the confirmation prompt.
    """
    from git_adr.commands.rm import run_rm

    run_rm(adr_id=adr_id, force=force)


@app.command()
def search(
    query: Annotated[str, typer.Argument(help="Search query.")],
    status: Annotated[
        str | None,
        typer.Option(
            "--status",
            "-s",
            help="Filter by status.",
        ),
    ] = None,
    tag: Annotated[
        str | None,
        typer.Option(
            "--tag",
            "-t",
            help="Filter by tag.",
        ),
    ] = None,
    context: Annotated[
        int,
        typer.Option(
            "--context",
            "-C",
            help="Lines of context around matches.",
        ),
    ] = 2,
    case_sensitive: Annotated[
        bool,
        typer.Option(
            "--case-sensitive",
            help="Case-sensitive search.",
        ),
    ] = False,
    regex: Annotated[
        bool,
        typer.Option(
            "--regex",
            "-E",
            help="Treat query as regular expression.",
        ),
    ] = False,
) -> None:
    """Search ADRs by content.

    Full-text search across all ADRs with highlighted snippets.
    """
    from git_adr.commands.search import run_search

    run_search(
        query=query,
        status=status,
        tag=tag,
        context=context,
        case_sensitive=case_sensitive,
        regex=regex,
    )


@app.command()
def link(
    adr_id: Annotated[str, typer.Argument(help="ADR ID to link.")],
    commits: Annotated[
        list[str],
        typer.Argument(help="Commit SHAs to link."),
    ],
    unlink: Annotated[
        bool,
        typer.Option(
            "--unlink",
            "-u",
            help="Remove links instead of adding.",
        ),
    ] = False,
) -> None:
    """Associate an ADR with commits.

    Links create bidirectional traceability between decisions
    and the code that implements them.
    """
    from git_adr.commands.link import run_link

    run_link(adr_id=adr_id, commits=commits, unlink=unlink)


@app.command()
def supersede(
    adr_id: Annotated[str, typer.Argument(help="ADR ID being superseded.")],
    title: Annotated[str, typer.Argument(help="Title for the new ADR.")],
    template: Annotated[
        str | None,
        typer.Option(
            "--template",
            help="Override template format.",
        ),
    ] = None,
) -> None:
    """Create a new ADR that supersedes an existing one.

    Creates a new ADR with a supersedes reference, and updates
    the original ADR's status to 'superseded'.
    """
    from git_adr.commands.supersede import run_supersede

    run_supersede(adr_id=adr_id, title=title, template=template)


@app.command()
def log(
    n: Annotated[
        int,
        typer.Option(
            "-n",
            help="Number of commits to show.",
        ),
    ] = 10,
    all_: Annotated[
        bool,
        typer.Option(
            "--all",
            "-a",
            help="Show all commits with ADR annotations.",
        ),
    ] = False,
) -> None:
    """Show git log with ADR annotations.

    Displays commit history with inline ADR summaries for commits
    that have associated architecture decisions.
    """
    from git_adr.commands.log import run_log

    run_log(n=n, all_=all_)


@app.command()
def sync(
    push: Annotated[
        bool,
        typer.Option(
            "--push",
            "-p",
            help="Push notes to remote.",
        ),
    ] = False,
    pull: Annotated[
        bool,
        typer.Option(
            "--pull",
            help="Pull notes from remote.",
        ),
    ] = False,
    remote: Annotated[
        str,
        typer.Option(
            "--remote",
            "-r",
            help="Remote name.",
        ),
    ] = "origin",
    merge_strategy: Annotated[
        str,
        typer.Option(
            "--merge-strategy",
            "-m",
            help="Merge strategy (union, ours, theirs).",
        ),
    ] = "union",
) -> None:
    """Synchronize ADR notes with remote repository.

    Push and pull ADR notes to/from the remote. By default,
    performs both push and pull.
    """
    from git_adr.commands.sync import run_sync

    # Default: do both if neither specified
    if not push and not pull:
        push = True
        pull = True

    run_sync(push=push, pull=pull, remote=remote, merge_strategy=merge_strategy)


@app.command()
def config(
    key: Annotated[
        str | None,
        typer.Argument(help="Configuration key."),
    ] = None,
    value: Annotated[
        str | None,
        typer.Argument(help="Value to set."),
    ] = None,
    list_: Annotated[
        bool,
        typer.Option(
            "--list",
            "-l",
            help="List all configuration.",
        ),
    ] = False,
    get: Annotated[
        bool,
        typer.Option(
            "--get",
            help="Get a configuration value.",
        ),
    ] = False,
    set_: Annotated[
        bool,
        typer.Option(
            "--set",
            help="Set a configuration value.",
        ),
    ] = False,
    unset: Annotated[
        bool,
        typer.Option(
            "--unset",
            help="Remove a configuration value.",
        ),
    ] = False,
    global_: Annotated[
        bool,
        typer.Option(
            "--global",
            "-g",
            help="Use global (user-level) configuration.",
        ),
    ] = False,
) -> None:
    """Manage git-adr configuration.

    Configuration is stored in git config and supports both
    local (repository) and global (user) levels.

    [bold]Keys:[/bold]
    - adr.namespace: Notes namespace (default: adr)
    - adr.template: Default template format
    - adr.editor: Editor command override
    - adr.ai.provider: AI provider name
    - adr.ai.model: AI model name
    """
    from git_adr.commands.config import run_config

    run_config(
        key=key,
        value=value,
        list_=list_,
        get=get,
        set_=set_,
        unset=unset,
        global_=global_,
    )


# =============================================================================
# Format Commands
# =============================================================================


@app.command()
def convert(
    adr_id: Annotated[str, typer.Argument(help="ADR ID to convert.")],
    to: Annotated[
        str,
        typer.Option(
            "--to",
            "-t",
            help="Target format.",
        ),
    ],
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-n",
            help="Show converted content without saving.",
        ),
    ] = False,
) -> None:
    """Convert an ADR to a different format.

    [bold]Formats:[/bold]
    - madr: MADR 4.0 (full template)
    - nygard: Original minimal format
    - y-statement: Single-sentence format
    - alexandrian: Pattern-language format
    - business: Business case format
    - planguage: Quality-focused format
    """
    from git_adr.commands.convert import run_convert

    run_convert(adr_id=adr_id, to=to, dry_run=dry_run)


# =============================================================================
# Artifact Commands
# =============================================================================


@app.command()
def attach(
    adr_id: Annotated[str, typer.Argument(help="ADR ID to attach to.")],
    file: Annotated[str, typer.Argument(help="File to attach.")],
    alt: Annotated[
        str | None,
        typer.Option(
            "--alt",
            "-a",
            help="Alt text for images.",
        ),
    ] = None,
    name: Annotated[
        str | None,
        typer.Option(
            "--name",
            "-n",
            help="Override attachment name.",
        ),
    ] = None,
) -> None:
    """Attach a file (diagram, image) to an ADR.

    Artifacts are stored in a separate git notes namespace
    and referenced by SHA256 hash for deduplication.
    """
    from git_adr.commands.attach import run_attach

    run_attach(adr_id=adr_id, file=file, alt=alt, name=name)


@app.command()
def artifacts(
    adr_id: Annotated[str, typer.Argument(help="ADR ID to list artifacts for.")],
) -> None:
    """List artifacts attached to an ADR."""
    from git_adr.commands.artifacts import run_artifacts

    run_artifacts(adr_id=adr_id)


@app.command("artifact-get")
def artifact_get(
    adr_id: Annotated[str, typer.Argument(help="ADR ID.")],
    name: Annotated[str, typer.Argument(help="Artifact name.")],
    output: Annotated[
        str | None,
        typer.Option(
            "--output",
            "-o",
            help="Output path (default: original filename).",
        ),
    ] = None,
) -> None:
    """Extract an artifact to a file."""
    from git_adr.commands.artifact_get import run_artifact_get

    run_artifact_get(adr_id=adr_id, name=name, output=output)


@app.command("artifact-rm")
def artifact_rm(
    adr_id: Annotated[str, typer.Argument(help="ADR ID.")],
    name: Annotated[str, typer.Argument(help="Artifact name to remove.")],
) -> None:
    """Remove an artifact from an ADR."""
    from git_adr.commands.artifact_rm import run_artifact_rm

    run_artifact_rm(adr_id=adr_id, name=name)


# =============================================================================
# AI Commands (P1)
# =============================================================================

ai_app = typer.Typer(
    name="ai",
    help="AI-assisted ADR operations.",
    no_args_is_help=True,
)
app.add_typer(ai_app, name="ai")


@ai_app.command("draft")
def ai_draft(
    title: Annotated[str, typer.Argument(help="Title for the new ADR.")],
    batch: Annotated[
        bool,
        typer.Option(
            "--batch",
            "-b",
            help="One-shot generation (no interactive prompts).",
        ),
    ] = False,
    from_commits: Annotated[
        str | None,
        typer.Option(
            "--from-commits",
            help="Analyze commits (e.g., 'HEAD~5..HEAD').",
        ),
    ] = None,
    context: Annotated[
        str | None,
        typer.Option(
            "--context",
            "-c",
            help="Additional context for the AI.",
        ),
    ] = None,
    template: Annotated[
        str | None,
        typer.Option(
            "--template",
            "-t",
            help="Override template format.",
        ),
    ] = None,
) -> None:
    """AI-guided ADR creation with interactive elicitation.

    By default, the AI asks Socratic questions to help you
    articulate the decision clearly:

    1. What problem are you solving?
    2. What options have you considered?
    3. What's driving this decision?
    4. What are the trade-offs/consequences?

    Use --batch for one-shot generation without prompts.
    """
    from git_adr.commands.ai_draft import run_ai_draft

    run_ai_draft(
        title=title,
        batch=batch,
        from_commits=from_commits,
        context=context,
        template=template,
    )


@ai_app.command("suggest")
def ai_suggest(
    adr_id: Annotated[str, typer.Argument(help="ADR ID to improve.")],
    aspect: Annotated[
        str,
        typer.Option(
            "--aspect",
            "-a",
            help="Focus area (context, options, consequences, all).",
        ),
    ] = "all",
) -> None:
    """Get AI suggestions to improve an ADR."""
    from git_adr.commands.ai_suggest import run_ai_suggest

    run_ai_suggest(adr_id=adr_id, aspect=aspect)


@ai_app.command("summarize")
def ai_summarize(
    period: Annotated[
        str,
        typer.Option(
            "--period",
            "-p",
            help="Time period (7d, 30d, 90d, etc.).",
        ),
    ] = "30d",
    format_: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format (markdown, slack, email, standup).",
        ),
    ] = "markdown",
) -> None:
    """Generate a natural language summary of recent decisions."""
    from git_adr.commands.ai_summarize import run_ai_summarize

    run_ai_summarize(period=period, format_=format_)


@ai_app.command("ask")
def ai_ask(
    question: Annotated[str, typer.Argument(help="Question to ask.")],
) -> None:
    """Ask questions about your ADRs in natural language.

    Example: git adr ai ask "Why did we choose PostgreSQL?"
    """
    from git_adr.commands.ai_ask import run_ai_ask

    run_ai_ask(question=question)


# =============================================================================
# Wiki Commands (P1)
# =============================================================================

wiki_app = typer.Typer(
    name="wiki",
    help="Wiki synchronization for ADRs.",
    no_args_is_help=True,
)
app.add_typer(wiki_app, name="wiki")


@wiki_app.command("init")
def wiki_init(
    platform: Annotated[
        str | None,
        typer.Option(
            "--platform",
            "-p",
            help="Force platform (github, gitlab).",
        ),
    ] = None,
) -> None:
    """Initialize wiki synchronization.

    Auto-detects GitHub or GitLab and sets up the wiki structure.
    """
    from git_adr.commands.wiki_init import run_wiki_init

    run_wiki_init(platform=platform)


@wiki_app.command("sync")
def wiki_sync(
    direction: Annotated[
        str,
        typer.Option(
            "--direction",
            "-d",
            help="Sync direction (push, pull, both).",
        ),
    ] = "push",
    adr: Annotated[
        str | None,
        typer.Option(
            "--adr",
            help="Sync only specific ADR.",
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-n",
            help="Show what would be done.",
        ),
    ] = False,
) -> None:
    """Synchronize ADRs with the wiki."""
    from git_adr.commands.wiki_sync import run_wiki_sync

    run_wiki_sync(direction=direction, adr=adr, dry_run=dry_run)


# =============================================================================
# Analytics Commands (P1)
# =============================================================================


@app.command()
def stats(
    velocity: Annotated[
        bool,
        typer.Option(
            "--velocity",
            "-v",
            help="Show decision velocity metrics and trends.",
        ),
    ] = False,
) -> None:
    """Show quick ADR statistics summary."""
    from git_adr.commands.stats import run_stats

    run_stats(velocity=velocity)


@app.command()
def report(
    format_: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format (terminal, html, json, markdown).",
        ),
    ] = "terminal",
    output: Annotated[
        str | None,
        typer.Option(
            "--output",
            "-o",
            help="Output file path.",
        ),
    ] = None,
    team: Annotated[
        bool,
        typer.Option(
            "--team",
            help="Include team collaboration metrics.",
        ),
    ] = False,
) -> None:
    """Generate an ADR analytics report/dashboard."""
    from git_adr.commands.report import run_report

    run_report(format_=format_, output=output, team=team)


@app.command()
def metrics(
    format_: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Export format (json, prometheus, csv).",
        ),
    ] = "json",
    output: Annotated[
        str | None,
        typer.Option(
            "--output",
            "-o",
            help="Output file path (default: stdout).",
        ),
    ] = None,
) -> None:
    """Export ADR metrics for dashboards."""
    from git_adr.commands.metrics import run_metrics

    run_metrics(format_=format_, output=output)


# =============================================================================
# Onboarding Commands (P2)
# =============================================================================


@app.command()
def onboard(
    role: Annotated[
        str,
        typer.Option(
            "--role",
            "-r",
            help="User role (developer, reviewer, architect).",
        ),
    ] = "developer",
    quick: Annotated[
        bool,
        typer.Option(
            "--quick",
            "-q",
            help="5-minute executive summary only.",
        ),
    ] = False,
    continue_: Annotated[
        bool,
        typer.Option(
            "--continue",
            "-c",
            help="Resume from last position.",
        ),
    ] = False,
    status_: Annotated[
        bool,
        typer.Option(
            "--status",
            "-s",
            help="Show onboarding progress.",
        ),
    ] = False,
) -> None:
    """Interactive onboarding wizard for new team members.

    Guides you through the most important ADRs for your role.
    """
    from git_adr.commands.onboard import run_onboard

    run_onboard(role=role, quick=quick, continue_=continue_, status_=status_)


# =============================================================================
# Export/Import Commands (P2)
# =============================================================================


@app.command("export")
def export_adrs(
    format_: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Export format (markdown, json, html, docx).",
        ),
    ] = "markdown",
    output: Annotated[
        str,
        typer.Option(
            "--output",
            "-o",
            help="Output directory or file.",
        ),
    ] = "./adr-export",
    adr: Annotated[
        str | None,
        typer.Option(
            "--adr",
            help="Export specific ADR only.",
        ),
    ] = None,
) -> None:
    """Export ADRs to files."""
    from git_adr.commands.export import run_export

    run_export(format_=format_, output=output, adr=adr)


@app.command("import")
def import_adrs(
    path: Annotated[str, typer.Argument(help="Path to ADRs to import.")],
    format_: Annotated[
        str | None,
        typer.Option(
            "--format",
            "-f",
            help="Source format (auto-detect if not specified).",
        ),
    ] = None,
    link_by_date: Annotated[
        bool,
        typer.Option(
            "--link-by-date",
            help="Associate ADRs with commits by date.",
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-n",
            help="Show what would be imported.",
        ),
    ] = False,
) -> None:
    """Import ADRs from file-based storage to git notes."""
    from git_adr.commands.import_ import run_import

    run_import(path=path, format_=format_, link_by_date=link_by_date, dry_run=dry_run)


# =============================================================================
# Aliases for common operations
# =============================================================================

# Register short aliases
app.command("n", hidden=True)(new_adr)
app.command("l", hidden=True)(list_adrs)
app.command("s", hidden=True)(search)
app.command("e", hidden=True)(edit)


# =============================================================================
# Shell Completion
# =============================================================================


@app.command("completion")
def completion(
    shell: Annotated[
        str,
        typer.Argument(help="Shell type: bash, zsh, fish, or powershell"),
    ],
    install: Annotated[
        bool,
        typer.Option("--install", "-i", help="Install completion to shell config"),
    ] = False,
) -> None:
    """Generate or install shell completion scripts.

    Examples:

        # Show bash completion script
        git adr completion bash

        # Install zsh completion
        git adr completion zsh --install

        # Save fish completion to file
        git adr completion fish > ~/.config/fish/completions/git-adr.fish
    """
    shell = shell.lower()
    valid_shells = ["bash", "zsh", "fish", "powershell"]

    if shell not in valid_shells:
        err_console.print(f"[red]Invalid shell: {shell}[/red]")
        err_console.print(f"Valid shells: {', '.join(valid_shells)}")
        raise typer.Exit(1)

    prog_name = "git-adr"
    env_var = "_GIT_ADR_COMPLETE"

    if shell == "bash":
        # Custom bash completion that supports both 'git-adr' and 'git adr'
        script = """# git-adr bash completion
_git_adr_completion() {
    local IFS=$'\\n'
    COMPREPLY=( $( env COMP_WORDS="${COMP_WORDS[*]}" \\
                   COMP_CWORD=$COMP_CWORD \\
                   _GIT_ADR_COMPLETE=complete_bash git-adr ) )
    return 0
}

# Register for direct command
complete -o default -F _git_adr_completion git-adr

# Register for git subcommand (git adr)
_git_adr() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    local commands="init new list show edit rm search link supersede log sync config convert attach artifacts artifact-get artifact-rm stats report metrics onboard export import completion ai wiki"

    if [[ ${COMP_CWORD} -eq 2 ]]; then
        COMPREPLY=( $(compgen -W "${commands}" -- "${cur}") )
    else
        local IFS=$'\\n'
        local words=("git-adr" "${COMP_WORDS[@]:2}")
        local cword=$((COMP_CWORD - 1))
        COMPREPLY=( $( env COMP_WORDS="${words[*]}" \\
                       COMP_CWORD=$cword \\
                       _GIT_ADR_COMPLETE=complete_bash git-adr ) )
    fi
}

# Hook into git completion for 'git adr'
if type __git_complete &>/dev/null; then
    __git_complete adr _git_adr
fi
"""
        config_file = "~/.bashrc"
    elif shell == "zsh":
        # Use Typer's built-in for zsh
        from typer.completion import get_completion_script

        script = get_completion_script(  # noqa: S604 # nosec B604 - shell specifies script type, not subprocess
            prog_name=prog_name, complete_var=env_var, shell="zsh"
        )
        config_file = "~/.zshrc"
    elif shell == "fish":
        from typer.completion import get_completion_script

        script = get_completion_script(  # noqa: S604 # nosec B604 - shell specifies script type, not subprocess
            prog_name=prog_name, complete_var=env_var, shell="fish"
        )
        config_file = "~/.config/fish/completions/git-adr.fish"
    else:  # powershell
        from typer.completion import get_completion_script

        script = get_completion_script(  # noqa: S604 # nosec B604 - shell specifies script type, not subprocess
            prog_name=prog_name, complete_var=env_var, shell="powershell"
        )
        config_file = "$PROFILE"

    if install:
        # Install the completion
        from pathlib import Path

        if shell == "fish":
            # Fish uses a dedicated completions directory
            fish_dir = Path.home() / ".config" / "fish" / "completions"
            fish_dir.mkdir(parents=True, exist_ok=True)
            completion_file = fish_dir / "git-adr.fish"
            completion_file.write_text(script)
            console.print(f"[green]✓[/green] Completion installed to {completion_file}")
        elif shell == "powershell":
            console.print(
                "[yellow]PowerShell completion requires manual setup.[/yellow]"
            )
            console.print(f"Add the following to your {config_file}:")
            console.print(script)
        else:
            # Bash/Zsh - append to config file
            config_path = Path(config_file).expanduser()
            marker = "# git-adr completion"

            if config_path.exists():
                content = config_path.read_text()
                if marker in content:
                    console.print(
                        f"[yellow]Completion already installed in {config_file}[/yellow]"
                    )
                    raise typer.Exit(0)

            with config_path.open("a") as f:
                f.write(f"\n{marker}\n{script}\n")

            console.print(f"[green]✓[/green] Completion installed to {config_file}")
            console.print(f"Run: [cyan]source {config_file}[/cyan] to activate")
    else:
        # Just print the script
        console.print(script, highlight=False)


def main() -> None:
    """Entry point for the git-adr CLI."""
    try:
        app()
    except KeyboardInterrupt:
        err_console.print("\n[yellow]Interrupted[/yellow]")
        sys.exit(130)


if __name__ == "__main__":
    main()
