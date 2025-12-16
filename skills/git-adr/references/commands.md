# git-adr Command Reference

Complete reference for all git-adr commands.

## Core Commands

### init - Initialize ADR tracking

```bash
git adr init [--force] [--namespace TEXT] [--template madr|nygard|y-statement]
```

- `--force`, `-f`: Reinitialize even if already initialized
- `--namespace`: Custom git notes namespace (default: refs/notes/adr)
- `--template`: Default template format (default: madr)

### new - Create a new ADR

```bash
git adr new TITLE [OPTIONS]
```

- `--status proposed|accepted|deprecated|superseded|draft`: Initial status
- `--tags`, `-t TEXT`: Tags (repeatable)
- `--link TEXT`: Commit SHA to link
- `--template`: Template format override
- `--file`, `-f PATH`: Read content from file
- `--no-edit`: Skip editor (requires --file or stdin)
- `--preview`: Show template without creating
- `--draft`: Shortcut for --status draft

### edit - Edit an existing ADR

```bash
git adr edit ADR_ID [OPTIONS]
```

- `--status TEXT`: Change status without editor
- `--add-tag TEXT`: Add tag (repeatable)
- `--remove-tag TEXT`: Remove tag (repeatable)
- `--link TEXT`: Link to commit
- `--unlink TEXT`: Remove commit link

Without options, opens the ADR in your editor.

### list - List all ADRs

```bash
git adr list [OPTIONS]
```

- `--status TEXT`: Filter by status
- `--tag TEXT`: Filter by tag
- `--since YYYY-MM-DD`: Filter by start date
- `--until YYYY-MM-DD`: Filter by end date
- `--format table|json|csv|oneline`: Output format
- `--reverse`: Reverse chronological order

### show - Display a single ADR

```bash
git adr show ADR_ID [OPTIONS]
```

- `--format markdown|yaml|json`: Output format
- `--metadata-only`: Show only metadata
- `--no-interactive`: Disable interactive prompts

### search - Search ADRs by content

```bash
git adr search QUERY [OPTIONS]
```

- `--status TEXT`: Filter by status
- `--tag TEXT`: Filter by tag
- `--context INT`: Lines of context (default: 2)
- `--case-sensitive`: Case-sensitive search
- `--regex`: Treat query as regex

### rm - Remove an ADR

```bash
git adr rm ADR_ID [--force]
```

- `--force`, `-f`: Skip confirmation prompt

### supersede - Create ADR that supersedes another

```bash
git adr supersede OLD_ADR_ID TITLE [--template TEXT]
```

Creates a new ADR and marks the old one as superseded.

### link - Link ADR to commits

```bash
git adr link ADR_ID COMMIT... [--unlink]
```

- `--unlink`: Remove links instead of adding

### log - Show git log with ADR annotations

```bash
git adr log [-n INT] [--all]
```

- `-n INT`: Number of commits (default: 10)
- `--all`: Show all annotated commits

## Sync Commands

### sync - Synchronize ADRs with remote

```bash
git adr sync [push|pull|both] [OPTIONS]
```

Direction defaults to `both` (pull then push).

- `--remote`, `-r TEXT`: Remote name (default: origin)
- `--force`, `-f`: Force push/pull
- `--dry-run`: Show what would be done

### sync push - Push ADRs to remote

```bash
git adr sync push [--remote TEXT] [--force]
```

### sync pull - Pull ADRs from remote

```bash
git adr sync pull [--remote TEXT] [--force]
```

## Artifact Commands

### attach - Attach file to ADR

```bash
git adr attach ADR_ID FILE [--alt TEXT] [--name TEXT]
```

- `--alt`: Alt text for images
- `--name`: Override filename

### artifacts - List attachments

```bash
git adr artifacts ADR_ID
```

### artifact-get - Extract attachment

```bash
git adr artifact-get ADR_ID NAME [--output PATH]
```

NAME can be filename or SHA256 prefix.

### artifact-rm - Remove attachment

```bash
git adr artifact-rm ADR_ID NAME
```

## Analytics Commands

### stats - Quick statistics summary

```bash
git adr stats [--velocity]
```

- `--velocity`: Show decision velocity metrics

### report - Generate analytics report

```bash
git adr report [OPTIONS]
```

- `--format terminal|html|json|markdown`: Output format
- `--output PATH`: Output file path
- `--team`: Include team metrics

### metrics - Export metrics for dashboards

```bash
git adr metrics [OPTIONS]
```

- `--format json|prometheus|csv`: Export format
- `--output PATH`: Output file path

## Export/Import Commands

### export - Export ADRs to files

```bash
git adr export [OPTIONS]
```

- `--format markdown|json|html|docx`: Export format
- `--output PATH`: Output directory (default: ./adr-export)
- `--adr TEXT`: Export specific ADR only

### import - Import from file-based ADRs

```bash
git adr import PATH [OPTIONS]
```

- `--format auto|markdown|json|adr-tools`: Source format
- `--link-by-date`: Associate ADRs with commits by date
- `--dry-run`: Preview import

### convert - Convert ADR to different format

```bash
git adr convert ADR_ID --to FORMAT [--dry-run]
```

Available formats: madr, nygard, y-statement, alexandrian, business, planguage

## Config Commands

### config list - Show all settings

```bash
git adr config --list [--global]
```

### config get - Get a setting

```bash
git adr config KEY
git adr config --get KEY [--global]
```

### config set - Set a configuration value

```bash
git adr config KEY VALUE
git adr config --set KEY VALUE [--global]
```

### config unset - Remove a setting

```bash
git adr config --unset KEY [--global]
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

## Wiki Commands

### wiki init - Configure wiki sync

```bash
git adr wiki init [--platform github|gitlab]
```

Auto-detects platform if not specified.

### wiki sync - Sync ADRs to project wiki

```bash
git adr wiki sync [OPTIONS]
```

- `--direction push|pull|both`: Sync direction (default: push)
- `--adr TEXT`: Sync only specific ADR
- `--dry-run`: Preview changes

## Onboard Command

### onboard - Interactive onboarding wizard

```bash
git adr onboard [OPTIONS]
```

- `--role developer|reviewer|architect`: User role
- `--quick`: 5-minute executive summary
- `--continue`: Resume from last position
- `--status`: Show onboarding progress

## Common Workflows

### Start a new project

```bash
git adr init
git adr new "Use git-adr for architecture decisions"
git adr sync push
```

### Team collaboration

```bash
git adr sync pull                           # Get latest
git adr new "Adopt microservices"          # Create decision
git adr sync push                          # Share with team
```

### Link decisions to implementation

```bash
git adr link 20250115-use-postgresql abc123
git adr show 20250115-use-postgresql
```

### Supersede a decision

```bash
git adr supersede 20250101-use-mysql "Migrate to PostgreSQL"
```

### Onboard new team member

```bash
git adr onboard --quick                    # Quick overview
git adr list --status accepted             # Key decisions
git adr show <id>                          # Read specific ADR
```

## ADR ID Format

ADR IDs use the format: `YYYYMMDD-slug-from-title`

Example: `20250115-use-postgresql-for-primary-database`

## Status Values

| Status | Description |
|--------|-------------|
| `draft` | Work in progress |
| `proposed` | Under review |
| `accepted` | Active decision |
| `rejected` | Not accepted |
| `deprecated` | No longer applies |
| `superseded` | Replaced by another ADR |
