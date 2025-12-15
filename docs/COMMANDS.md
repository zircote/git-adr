# git-adr Command Reference

Quick reference for all git-adr commands. For detailed information, see
the man pages: `git adr <command> --help` or read `docs/man/git-adr-*.1.md`.

## Getting Started

| Command | Description |
|---------|-------------|
| `git adr init` | Initialize ADR tracking in repository |
| `git adr onboard` | Interactive wizard for new team members |

## Creating & Managing ADRs

| Command | Description |
|---------|-------------|
| `git adr new <title>` | Create a new ADR |
| `git adr edit <id>` | Edit an existing ADR |
| `git adr rm <id>` | Remove an ADR |
| `git adr supersede <old-id> <title>` | Create ADR that supersedes another |

## Viewing ADRs

| Command | Description |
|---------|-------------|
| `git adr list` | List all ADRs |
| `git adr show <id>` | Display a single ADR |
| `git adr search <query>` | Search ADRs by content |
| `git adr log` | Show git log with ADR annotations |

## Linking & Traceability

| Command | Description |
|---------|-------------|
| `git adr link <id> <commit>` | Link ADR to a commit |
| `git adr edit <id> --unlink <commit>` | Remove commit link |

## Attachments

| Command | Description |
|---------|-------------|
| `git adr attach <id> <file>` | Attach file to ADR |
| `git adr artifacts <id>` | List attachments |
| `git adr artifact-get <id> <hash>` | Extract attachment |
| `git adr artifact-rm <id> <hash>` | Remove attachment |

## Synchronization

| Command | Description |
|---------|-------------|
| `git adr sync` | Sync ADRs with remote (push + pull) |
| `git adr sync push` | Push ADRs to remote |
| `git adr sync pull` | Pull ADRs from remote |

## Analytics & Reporting

| Command | Description |
|---------|-------------|
| `git adr stats` | Quick statistics summary |
| `git adr report` | Generate analytics report |
| `git adr metrics` | Export metrics (JSON) |

## Import & Export

| Command | Description |
|---------|-------------|
| `git adr export` | Export ADRs to files |
| `git adr import <path>` | Import from file-based ADRs |
| `git adr convert <id> --to <format>` | Convert ADR format |

## Configuration

| Command | Description |
|---------|-------------|
| `git adr config list` | Show all settings |
| `git adr config get <key>` | Get a setting value |
| `git adr config set <key> <value>` | Set a configuration value |

## AI Assistance (Optional)

Requires AI provider configuration. See `git adr config` for setup.

| Command | Description |
|---------|-------------|
| `git adr ai draft <title>` | AI-generated ADR draft |
| `git adr ai review <id>` | AI review suggestions |
| `git adr ai suggest` | AI-suggested ADRs from commits |

## Wiki Integration (Optional)

| Command | Description |
|---------|-------------|
| `git adr wiki init` | Configure wiki sync |
| `git adr wiki sync` | Sync ADRs to project wiki |

---

## Common Workflows

### Starting a New Project

```bash
git adr init
git adr new "Use git-adr for architecture decisions"
git adr sync push
```

### Team Collaboration

```bash
# Get latest ADRs
git adr sync pull

# Create new decision
git adr new "Adopt microservices architecture"

# Share with team
git adr sync push
```

### Linking Decisions to Implementation

```bash
# After implementing a decision
git adr link 20250115-use-postgresql abc1234

# View related commits
git adr show 20250115-use-postgresql
```

### Superseding a Decision

```bash
# When a decision is replaced
git adr supersede 20250101-use-mysql "Migrate to PostgreSQL"
```

### Onboarding New Team Members

```bash
# Interactive walkthrough of architecture
git adr onboard

# Or browse decisions
git adr list --status accepted
```

---

## Filtering & Output

### List Filters

```bash
git adr list --status accepted      # By status
git adr list --tags database        # By tag
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
git adr export --format docx        # Word documents (requires export extra)
```
