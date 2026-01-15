# git-adr Command Reference

Quick reference for all git-adr commands. For detailed information, run
`git adr <command> --help`.

## Getting Started

| Command | Description |
|---------|-------------|
| `git adr init` | Initialize ADR tracking |
| `git adr init --force` | Reinitialize (overwrites existing config) |
| `git adr init --prefix PREFIX` | Set ADR ID prefix (default: ADR-) |
| `git adr init --digits N` | Set ID digit count (default: 4) |
| `git adr onboard` | Interactive wizard for new team members |

### Init Options

| Option | Description |
|--------|-------------|
| `-t, --template <format>` | Set ADR format (madr, nygard, y-statement, alexandrian) |
| `--namespace <name>` | Custom notes namespace (default: adr) |
| `--prefix <prefix>` | ADR ID prefix (default: ADR-) |
| `--digits <n>` | Number of digits in ADR ID (default: 4) |
| `-f, --force` | Reinitialize even if already initialized |

## Creating & Managing ADRs

| Command | Description |
|---------|-------------|
| `git adr new <title>` | Create a new ADR |
| `git adr edit <id>` | Edit an existing ADR |
| `git adr rm <id>` | Remove an ADR |
| `git adr supersede <old-id> <title>` | Create ADR that supersedes another |

### New ADR Options

| Option | Description |
|--------|-------------|
| `-s, --status <status>` | Initial status (default: proposed) |
| `-g, --tag <tag>` | Add tag (can be repeated) |
| `-d, --deciders <name>` | Add decider (can be repeated) |
| `-l, --link <commit>` | Link to commit SHA |
| `--template <format>` | Template format to use |
| `-f, --file <path>` | Read content from file |
| `--no-edit` | Don't open editor |
| `--preview` | Preview without saving |

### Edit Options

| Option | Description |
|--------|-------------|
| `-s, --status <status>` | Quick edit: change status |
| `--add-tag <tag>` | Quick edit: add tag |
| `--remove-tag <tag>` | Quick edit: remove tag |
| `-t, --title <title>` | Quick edit: change title |
| `--add-decider <name>` | Quick edit: add decider |
| `--remove-decider <name>` | Quick edit: remove decider |

## Viewing ADRs

| Command | Description |
|---------|-------------|
| `git adr list` | List all ADRs |
| `git adr show <id>` | Display a single ADR |
| `git adr search <query>` | Search ADRs by content |
| `git adr log` | Show git log with ADR annotations |

### List Options

| Option | Description |
|--------|-------------|
| `-s, --status <status>` | Filter by status |
| `-g, --tag <tag>` | Filter by tag |
| `--since <date>` | Filter by date (since YYYY-MM-DD) |
| `--until <date>` | Filter by date (until YYYY-MM-DD) |
| `-f, --format <fmt>` | Output format (table, json, csv, oneline) |
| `-r, --reverse` | Reverse sort order |

### Search Options

| Option | Description |
|--------|-------------|
| `-s, --status <status>` | Filter by status |
| `-g, --tag <tag>` | Filter by tag |
| `-c, --case-sensitive` | Case sensitive search |
| `-E, --regex` | Use regex pattern |
| `-C, --context <n>` | Context lines to show (default: 2) |
| `--limit <n>` | Maximum results |

### Log Options

| Option | Description |
|--------|-------------|
| `-n <count>` | Number of commits to show (default: 10) |
| `--linked-only` | Show only commits with linked ADRs |

## Linking & Traceability

| Command | Description |
|---------|-------------|
| `git adr link <id> <commit>` | Link ADR to a commit |

## Attachments

| Command | Description |
|---------|-------------|
| `git adr attach <id> <file>` | Attach file to ADR |
| `git adr artifacts <id>` | List attachments |
| `git adr artifacts <id> --extract <file>` | Extract attachment to file |
| `git adr artifacts <id> --remove` | Remove attachment |

### Attach Options

| Option | Description |
|--------|-------------|
| `--name <name>` | Override filename |
| `--description <text>` | Description/alt text for the attachment |

## Synchronization

| Command | Description |
|---------|-------------|
| `git adr sync` | Sync ADRs with remote (pull then push) |
| `git adr sync --push` | Push ADRs to remote only |
| `git adr sync --pull` | Pull ADRs from remote only |
| `git adr sync <remote>` | Sync with specific remote (default: origin) |

### Sync Options

| Option | Description |
|--------|-------------|
| `--push` | Push only |
| `--pull` | Pull only |
| `-f, --force` | Force push (use with caution) |

## Git Hooks

| Command | Description |
|---------|-------------|
| `git adr hooks install` | Install ADR git hooks |
| `git adr hooks uninstall` | Remove ADR hooks |
| `git adr hooks status` | Show hook installation status |

## CI/CD Integration

| Command | Description |
|---------|-------------|
| `git adr ci github` | Generate GitHub Actions workflow |
| `git adr ci gitlab` | Generate GitLab CI configuration |

## Templates Generation

| Command | Description |
|---------|-------------|
| `git adr templates pr` | Generate PR template with ADR section |
| `git adr templates issue` | Generate GitHub issue templates |
| `git adr templates codeowners` | Generate CODEOWNERS file |
| `git adr templates all` | Generate all templates |

## Analytics & Reporting

| Command | Description |
|---------|-------------|
| `git adr stats` | Quick statistics summary |
| `git adr report` | Generate comprehensive analytics report |
| `git adr metrics` | Export metrics as JSON |

### Stats Options

| Option | Description |
|--------|-------------|
| `-f, --format <fmt>` | Output format (text, json) |

### Report Options

| Option | Description |
|--------|-------------|
| `-f, --format <fmt>` | Output format (markdown, html, json) |
| `-o, --output <file>` | Output to file |
| `--detailed` | Include detailed status breakdown |
| `--timeline` | Include timeline analysis |

### Metrics Options

| Option | Description |
|--------|-------------|
| `-o, --output <file>` | Output to file |
| `--include-adrs` | Include individual ADR data |
| `--pretty` | Pretty print JSON |

## Import & Export

| Command | Description |
|---------|-------------|
| `git adr export` | Export ADRs to files (markdown, json, html) |
| `git adr import <path>` | Import from file-based ADRs |
| `git adr convert <id> --to <format>` | Convert ADR format |

### Export Options

| Option | Description |
|--------|-------------|
| `-o, --output <dir>` | Output directory (default: ./adr-export) |
| `-f, --format <fmt>` | Export format (markdown, json, html) |
| `--status <status>` | Filter by status |
| `--tag <tag>` | Filter by tag |
| `--index` | Generate index file |

### Import Options

| Option | Description |
|--------|-------------|
| `-f, --format <fmt>` | Import format (auto, markdown, json, adr-tools) |
| `--link-by-date` | Link ADRs to commits by date |
| `--dry-run` | Preview import without saving |

### Convert Options

| Option | Description |
|--------|-------------|
| `-t, --to <format>` | Target format (nygard, madr, y-statement, alexandrian) |
| `--in-place` | Save in place (update the ADR) |

## Configuration

| Command | Description |
|---------|-------------|
| `git adr config list` | Show all settings |
| `git adr config get <key>` | Get a setting value |
| `git adr config set <key> <value>` | Set a configuration value |
| `git adr config unset <key>` | Remove a configuration value |

### Key Configuration Options

| Key | Description |
|-----|-------------|
| `adr.template` | Default template: madr, nygard, y-statement |
| `adr.editor` | Editor command for ADRs |
| `adr.namespace` | Git notes namespace |
| `adr.prefix` | ADR ID prefix |
| `adr.digits` | Number of digits in ADR ID |

## Onboarding

| Command | Description |
|---------|-------------|
| `git adr onboard` | Interactive onboarding wizard |
| `git adr onboard --accepted-only` | Show only accepted ADRs |
| `git adr onboard --by-tag` | Show ADRs by category/tag |
| `git adr onboard --non-interactive` | Skip interactive prompts |

### Onboard Options

| Option | Description |
|--------|-------------|
| `--accepted-only` | Show only accepted ADRs |
| `--by-tag` | Show ADRs by category/tag |
| `--non-interactive` | Skip interactive prompts |
| `-l, --limit <n>` | Limit number of ADRs to show (default: 10) |

---

## Common Workflows

### Starting a New Project

```bash
# Initialize ADR tracking
git adr init

# Set up CI/CD and templates
git adr ci github
git adr templates all
git adr hooks install

# Create your first decision
git adr new "Use git-adr for architecture decisions"

# Push to remote
git adr sync --push
```

### Team Collaboration

```bash
# Get latest ADRs
git adr sync --pull

# Create new decision
git adr new "Adopt microservices architecture"

# Share with team
git adr sync --push
```

### Linking Decisions to Implementation

```bash
# After implementing a decision
git adr link ADR-0001 abc1234

# View related commits
git adr show ADR-0001
```

### Superseding a Decision

```bash
# When a decision is replaced
git adr supersede ADR-0001 "Migrate to PostgreSQL"
```

### Onboarding New Team Members

```bash
# Interactive walkthrough of architecture
git adr onboard

# Or browse decisions
git adr list --status accepted
```

### Importing Existing ADRs

```bash
# Import from adr-tools directory
git adr import ./doc/adr --format adr-tools

# Preview before importing
git adr import ./adrs --dry-run
```

### Generating Reports

```bash
# Generate HTML report
git adr report --format html --output adr-report.html --detailed --timeline

# Export metrics for dashboards
git adr metrics --pretty --output metrics.json
```

---

## Filtering & Output

### List Filters

```bash
git adr list --status accepted      # By status
git adr list -g database            # By tag
git adr list --since 2025-01-01     # By date
git adr list --format json          # JSON output
```

### Report Formats

```bash
git adr report --format markdown    # Markdown report
git adr report --format html        # HTML report
git adr report --format json        # JSON data
```

### Export Options

```bash
git adr export --output ./adrs      # Export to directory
git adr export --format html        # HTML documents
```

---

## Optional Features

Some features require building with additional feature flags:

```bash
# Build with AI features
cargo build --release --features ai

# Build with wiki sync
cargo build --release --features wiki

# Build with all features
cargo build --release --features all
```

### AI Assistance (requires `--features ai`)

| Command | Description |
|---------|-------------|
| `git adr ai draft <topic>` | Generate ADR draft using AI |
| `git adr ai suggest <id>` | Get AI suggestions for improving ADR |
| `git adr ai summarize <id>` | Summarize an ADR using AI |

### Wiki Integration (requires `--features wiki`)

| Command | Description |
|---------|-------------|
| `git adr wiki push` | Push ADRs to wiki |
| `git adr wiki pull` | Pull ADRs from wiki |
| `git adr wiki status` | Show wiki sync status |
