# git-adr Command Reference

Complete reference for all git-adr commands.

## Core Commands

### init - Initialize ADR tracking

```bash
git adr init [OPTIONS]
```

- `--namespace <NAMESPACE>`: Notes namespace (default: adr)
- `-t, --template <TEMPLATE>`: Default ADR template format (default: madr)
- `--prefix <PREFIX>`: ADR ID prefix (default: ADR-)
- `--digits <DIGITS>`: Number of digits in ADR ID (default: 4)
- `-f, --force`: Force reinitialization

### new - Create a new ADR

```bash
git adr new [OPTIONS] <TITLE>
```

- `-s, --status <STATUS>`: Initial status (default: proposed)
- `-g, --tag <TAG>`: Tags (can be specified multiple times)
- `-d, --deciders <DECIDERS>`: Deciders (can be specified multiple times)
- `-l, --link <LINK>`: Link to commit SHA
- `--template <TEMPLATE>`: Template format to use
- `-f, --file <FILE>`: Read content from file
- `--no-edit`: Don't open editor
- `--preview`: Preview without saving

### edit - Edit an existing ADR

```bash
git adr edit [OPTIONS] <ADR_ID>
```

- `-s, --status <STATUS>`: Quick edit: change status
- `--add-tag <ADD_TAG>`: Quick edit: add tag
- `--remove-tag <REMOVE_TAG>`: Quick edit: remove tag
- `-t, --title <TITLE>`: Quick edit: change title
- `--add-decider <ADD_DECIDER>`: Quick edit: add decider
- `--remove-decider <REMOVE_DECIDER>`: Quick edit: remove decider

Without options, opens the ADR in your editor.

### list - List all ADRs

```bash
git adr list [OPTIONS]
```

- `-s, --status <STATUS>`: Filter by status
- `-g, --tag <TAG>`: Filter by tag
- `--since <SINCE>`: Filter by date (since)
- `--until <UNTIL>`: Filter by date (until)
- `-f, --format <FORMAT>`: Output format (table, json, csv, oneline) [default: table]
- `-r, --reverse`: Reverse sort order

### show - Display a single ADR

```bash
git adr show [OPTIONS] <ADR_ID>
```

- `-f, --format <FORMAT>`: Output format (markdown, yaml, json) [default: markdown]
- `--metadata-only`: Show only metadata

### search - Search ADRs by content

```bash
git adr search [OPTIONS] <QUERY>
```

- `-s, --status <STATUS>`: Filter by status
- `-g, --tag <TAG>`: Filter by tag
- `-c, --case-sensitive`: Case sensitive search
- `-E, --regex`: Use regex pattern
- `-C, --context <CONTEXT>`: Context lines to show (default: 2)
- `--limit <LIMIT>`: Maximum results

### rm - Remove an ADR

```bash
git adr rm [OPTIONS] <ADR_ID>
```

- `-f, --force`: Skip confirmation prompt

### supersede - Create ADR that supersedes another

```bash
git adr supersede [OPTIONS] <ADR_ID> <TITLE>
```

- `--template <TEMPLATE>`: Template format for new ADR

Creates a new ADR and marks the old one as superseded.

### link - Link ADR to commits

```bash
git adr link <ADR_ID> <COMMIT>
```

Links an ADR to a specific commit SHA.

### log - Show git log with ADR annotations

```bash
git adr log [OPTIONS] [REVISION]
```

- `-n <COUNT>`: Number of commits to show (default: 10)
- `--linked-only`: Show only commits with linked ADRs

## Sync Commands

### sync - Synchronize ADRs with remote

```bash
git adr sync [OPTIONS] [REMOTE]
```

Remote defaults to `origin`. Without flags, performs pull then push.

- `--pull`: Pull only
- `--push`: Push only
- `-f, --force`: Force push (use with caution)

## Artifact Commands

### attach - Attach file to ADR

```bash
git adr attach [OPTIONS] <ADR_ID> <FILE>
```

- `--name <NAME>`: Override filename
- `--description <DESCRIPTION>`: Description/alt text for the attachment

### artifacts - List and manage attachments

```bash
git adr artifacts [OPTIONS] <ADR_ID>
```

- `-f, --format <FORMAT>`: Output format (text, json) [default: text]
- `--extract <EXTRACT>`: Extract artifact to file
- `--remove`: Remove artifact from ADR

## Analytics Commands

### stats - Quick statistics summary

```bash
git adr stats [OPTIONS]
```

- `-f, --format <FORMAT>`: Output format (text, json) [default: text]

### report - Generate analytics report

```bash
git adr report [OPTIONS]
```

- `-f, --format <FORMAT>`: Output format (markdown, html, json) [default: markdown]
- `-o, --output <OUTPUT>`: Output file (stdout if not specified)
- `--detailed`: Include detailed status breakdown
- `--timeline`: Include timeline analysis

### metrics - Export metrics for dashboards

```bash
git adr metrics [OPTIONS]
```

- `-o, --output <OUTPUT>`: Output file (stdout if not specified)
- `--include-adrs`: Include individual ADR metrics
- `--pretty`: Pretty print JSON output

## Export/Import Commands

### export - Export ADRs to files

```bash
git adr export [OPTIONS]
```

- `-o, --output <OUTPUT>`: Output directory (default: ./adr-export)
- `-f, --format <FORMAT>`: Export format (markdown, json, html) [default: markdown]
- `--status <STATUS>`: Filter by status
- `--tag <TAG>`: Filter by tag
- `--index`: Generate index file

### import - Import from file-based ADRs

```bash
git adr import [OPTIONS] <PATH>
```

- `-f, --format <FORMAT>`: Import format (auto, markdown, json, adr-tools) [default: auto]
- `--link-by-date`: Link ADRs to commits by date
- `--dry-run`: Preview import without saving

### convert - Convert ADR to different format

```bash
git adr convert [OPTIONS] --to <TO> <ADR_ID>
```

- `-t, --to <TO>`: Target format (nygard, madr, y-statement, alexandrian)
- `--in-place`: Save in place (update the ADR)

## Config Commands

### config - Manage configuration

```bash
git adr config <COMMAND>
```

Subcommands: `get`, `set`, `unset`, `list`

### config get - Get a setting

```bash
git adr config get <KEY>
```

### config set - Set a configuration value

```bash
git adr config set <KEY> <VALUE>
```

### config unset - Remove a setting

```bash
git adr config unset <KEY>
```

### config list - Show all settings

```bash
git adr config list
```

### Key Configuration Options

| Key | Description |
|-----|-------------|
| `adr.template` | Default template: madr, nygard, y-statement |
| `adr.editor` | Editor command for ADRs |
| `adr.namespace` | Git notes namespace |
| `adr.sync.auto_push` | Auto-push after modifications |
| `adr.sync.auto_pull` | Auto-pull before reads |
| `adr.sync.merge_strategy` | Merge strategy: union, ours, theirs |
| `adr.artifact_warn_size` | Size warning threshold (bytes) |
| `adr.artifact_max_size` | Maximum artifact size |
| `adr.ai.provider` | AI provider: openai, anthropic, google, ollama |
| `adr.ai.model` | AI model name |
| `adr.wiki.platform` | Wiki platform: github, gitlab |
| `adr.wiki.auto_sync` | Auto-sync to wiki after changes |

## Hooks Commands

### hooks - Manage git hooks

```bash
git adr hooks <COMMAND>
```

Subcommands: `install`, `uninstall`, `status`

### hooks install - Install ADR git hooks

Installs pre-push hooks for automatic ADR synchronization.

### hooks uninstall - Uninstall ADR git hooks

Removes installed hooks and restores backups if present.

### hooks status - Show hook installation status

Displays current hook configuration and status.

## CI/CD Commands

### ci - Generate CI/CD workflows

```bash
git adr ci <COMMAND>
```

Subcommands: `github`, `gitlab`

### ci github - Generate GitHub Actions workflow

Creates `.github/workflows/adr-sync.yml` for ADR validation and sync.

### ci gitlab - Generate GitLab CI configuration

Creates GitLab CI snippet for ADR integration.

## Template Commands

### templates - Generate project templates

```bash
git adr templates <COMMAND>
```

Subcommands: `pr`, `issue`, `codeowners`, `all`

### templates pr - Generate pull request template

Creates `.github/pull_request_template.md` with ADR section.

### templates issue - Generate issue templates

Creates GitHub issue templates for ADR workflows.

### templates codeowners - Generate CODEOWNERS

Creates or updates CODEOWNERS file with ADR patterns.

### templates all - Generate all templates

Creates PR template, issue templates, and CODEOWNERS at once.

## Onboard Command

### onboard - Interactive onboarding wizard

```bash
git adr onboard [OPTIONS]
```

- `--accepted-only`: Show only accepted ADRs
- `--by-tag`: Show ADRs by category/tag
- `--non-interactive`: Skip interactive prompts
- `-l, --limit <LIMIT>`: Limit number of ADRs to show (default: 10)

## Common Workflows

### Start a new project

```bash
git adr init
git adr new "Use git-adr for architecture decisions"
git adr sync --push
```

### Team collaboration

```bash
git adr sync --pull                          # Get latest
git adr new "Adopt microservices"            # Create decision
git adr sync --push                          # Share with team
```

### Link decisions to implementation

```bash
git adr link ADR-0001-use-postgresql abc123
git adr show ADR-0001-use-postgresql
```

### Supersede a decision

```bash
git adr supersede ADR-0001-use-mysql "Migrate to PostgreSQL"
```

### Onboard new team member

```bash
git adr onboard                              # Interactive wizard
git adr list --status accepted               # Key decisions
git adr show <id>                            # Read specific ADR
```

## ADR ID Format

ADR IDs use the format: `ADR-NNNN-slug-from-title`

Example: `ADR-0001-use-postgresql-for-primary-database`

The prefix and number of digits are configurable via `git adr init`.

## Status Values

| Status | Description |
|--------|-------------|
| `draft` | Work in progress |
| `proposed` | Under review |
| `accepted` | Active decision |
| `rejected` | Not accepted |
| `deprecated` | No longer applies |
| `superseded` | Replaced by another ADR |
