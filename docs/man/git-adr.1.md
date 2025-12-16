# git-adr(1) -- Architecture Decision Records management using git notes

## SYNOPSIS

`git adr` [OPTIONS] COMMAND [ARGS]...

## DESCRIPTION

**git-adr** is a command-line tool for managing Architecture Decision Records (ADRs)
using git notes. Unlike traditional file-based ADR tools, git-adr stores ADRs as
git notes attached to the repository, providing:

- **Rebase-safe storage**: ADRs survive rebases and amends
- **No file conflicts**: ADRs don't clutter the working tree
- **Distributed sync**: ADRs sync with `git fetch`/`git push`
- **Commit linkage**: Connect decisions to implementation commits

## OPTIONS

`-V`, `--version`
: Show version and exit.

`-h`, `--help`
: Show help message and exit.

`--install-completion`
: Install shell completion for the current shell.

`--show-completion`
: Show completion script for the current shell.

## COMMANDS

### Core Commands

`git adr init`
: Initialize ADR tracking in the current repository. Sets up git notes
  namespace and configures remotes for ADR synchronization.

`git adr new` TITLE
: Create a new Architecture Decision Record. Opens your configured editor
  with a template for the ADR content.

`git adr list` [OPTIONS]
: List all Architecture Decision Records. Supports filtering by status,
  tags, and date range.

`git adr show` ADR_ID
: Display a single ADR with rich formatting.

`git adr edit` ADR_ID
: Edit an existing ADR. Supports quick metadata changes (--status, --add-tag)
  or full editor mode.

`git adr rm` ADR_ID [--force]
: Remove an ADR from git notes. Use --force to skip confirmation.

`git adr search` QUERY
: Search ADRs by content using full-text search.

### Lifecycle Commands

`git adr link` ADR_ID COMMIT
: Associate an ADR with one or more commits, creating traceability
  between decisions and their implementation.

`git adr supersede` OLD_ADR_ID TITLE
: Create a new ADR that supersedes an existing one. The old ADR is
  automatically marked as superseded.

### Synchronization

`git adr sync` [push|pull|both]
: Synchronize ADR notes with a remote repository.

### Analysis & Reporting

`git adr stats`
: Show quick ADR statistics summary.

`git adr report` [--format=FORMAT]
: Generate an ADR analytics report. Supports markdown, html, and json formats.

`git adr metrics` [--format=FORMAT]
: Export ADR metrics for dashboards (json format).

`git adr log`
: Show git log annotated with related ADRs.

### Content Management

`git adr convert` ADR_ID --to=FORMAT
: Convert an ADR to a different template format.

`git adr attach` ADR_ID FILE
: Attach a file (diagram, image, etc.) to an ADR.

`git adr artifacts` ADR_ID
: List artifacts attached to an ADR.

`git adr artifact-get` ADR_ID HASH [--output=FILE]
: Extract an artifact to a file.

`git adr artifact-rm` ADR_ID HASH
: Remove an artifact from an ADR.

### Import/Export

`git adr export` [--output=DIR] [--format=FORMAT]
: Export ADRs to files for external consumption.

`git adr import` PATH
: Import ADRs from file-based storage (e.g., docs/adr/) to git notes.

### Configuration

`git adr config` [get|set|list] KEY [VALUE]
: Manage git-adr configuration settings.

### AI Assistance (Optional)

`git adr ai draft` TITLE
: Generate an ADR draft using AI assistance. Requires AI provider
  configuration (OpenAI, Anthropic, Google, or Ollama).

`git adr ai review` ADR_ID
: Get AI-powered review suggestions for an ADR.

`git adr ai suggest`
: Get AI suggestions for potential ADRs based on recent commits.

### Wiki Integration (Optional)

`git adr wiki init` [--platform=PLATFORM]
: Initialize wiki synchronization for GitHub or GitLab.

`git adr wiki sync` [--direction=push|pull|both]
: Synchronize ADRs with the project wiki.

### Onboarding

`git adr onboard`
: Interactive onboarding wizard for new team members to learn about
  the project's architecture decisions.

## CONFIGURATION

git-adr stores its configuration in git config. Key settings include:

`adr.namespace`
: Git notes namespace for ADRs (default: `adr`)

`adr.artifacts_namespace`
: Git notes namespace for artifacts (default: `adr-artifacts`)

`adr.template`
: Default template format: madr, nygard, y-statement, alexandrian, business, planguage

`adr.editor`
: Editor command for creating/editing ADRs

`adr.artifact_warn_size`
: Size threshold (bytes) for attachment warnings (default: 1048576)

`adr.artifact_max_size`
: Maximum attachment size in bytes (default: 10485760)

`adr.sync.auto_push`
: Auto-push after modifications (default: false)

`adr.sync.auto_pull`
: Auto-pull before reads (default: true)

`adr.sync.merge_strategy`
: Merge strategy: union, ours, theirs, cat_sort_uniq (default: union)

`adr.ai.provider`
: AI provider: openai, anthropic, google, bedrock, azure, ollama, openrouter

`adr.ai.model`
: AI model name (provider-specific)

`adr.ai.temperature`
: AI temperature 0.0-1.0 (default: 0.7)

`adr.wiki.platform`
: Wiki platform: github, gitlab, auto

`adr.wiki.auto_sync`
: Auto-sync to wiki after changes (default: false)

Use `git adr config list` to see all settings. For complete documentation
with examples and recipes, see docs/CONFIGURATION.md in the repository.

## EXAMPLES

Initialize git-adr in a repository:

    $ git adr init

Create a new ADR:

    $ git adr new "Use PostgreSQL for primary database"

List all ADRs:

    $ git adr list

List only accepted ADRs:

    $ git adr list --status accepted

Show a specific ADR:

    $ git adr show 20250115-use-postgresql

Link an ADR to a commit:

    $ git adr link 20250115-use-postgresql abc123

Search ADRs:

    $ git adr search "database"

Sync ADRs with remote:

    $ git adr sync push

## TEMPLATE FORMATS

git-adr supports multiple ADR template formats:

**madr** (Markdown Any Decision Records)
: Full-featured format with context, decision drivers, options, and consequences.

**nygard** (Michael Nygard's original format)
: Simple format with status, context, decision, and consequences.

**y-statement**
: Compact format using "In the context of... we decided..." structure.

**custom**
: User-defined templates in the repository.

## FILES

`~/.gitconfig`, `.git/config`
: Git configuration files where git-adr stores its settings.

`refs/notes/adr`
: Git notes reference where ADRs are stored.

`refs/notes/adr-artifacts`
: Git notes reference where ADR artifacts (attachments) are stored.

## ENVIRONMENT

`EDITOR`, `VISUAL`
: Default editor for creating and editing ADRs.

`OPENAI_API_KEY`
: API key for OpenAI AI assistance.

`ANTHROPIC_API_KEY`
: API key for Anthropic AI assistance.

`GOOGLE_API_KEY`
: API key for Google AI assistance.

## SEE ALSO

git-notes(1), git-config(1)

**Online Documentation:**

- docs/CONFIGURATION.md - Complete configuration reference with examples
- docs/ADR_FORMATS.md - All template formats with full examples
- docs/ADR_PRIMER.md - Introduction to ADRs for beginners
- docs/COMMANDS.md - Complete command reference

## AUTHOR

Written by zircote.

## REPORTING BUGS

Report bugs at <https://github.com/zircote/git-adr/issues>

## COPYRIGHT

Copyright (C) 2025 zircote. License MIT.
