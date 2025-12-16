# git-adr Command Reference

Quick reference for all git-adr commands. For detailed information, see
the man pages: `git adr <command> --help` or read `docs/man/git-adr-*.1.md`.

## Getting Started

| Command | Description |
|---------|-------------|
| `git adr init` | Initialize ADR tracking (interactive prompts) |
| `git adr init --no-input` | Initialize with defaults (non-interactive) |
| `git adr init --install-hooks` | Initialize with pre-push hooks |
| `git adr init --setup-github-ci` | Initialize with GitHub Actions |
| `git adr onboard` | Interactive wizard for new team members |

### Init Options

| Option | Description |
|--------|-------------|
| `--template <format>` | Set ADR format (madr, nygard, y-statement, alexandrian, business, planguage) |
| `--namespace <name>` | Custom notes namespace (default: adr) |
| `--install-hooks` | Install pre-push hooks for automatic sync |
| `--no-install-hooks` | Skip hooks installation |
| `--setup-github-ci` | Generate GitHub Actions workflows |
| `--no-setup-github-ci` | Skip CI workflow generation |
| `--no-input` | Skip all interactive prompts |
| `--force` | Reinitialize even if already initialized |

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

## Git Hooks

Pre-push hooks for automatic ADR synchronization. See [Hooks Guide](./HOOKS_GUIDE.md) for details.

| Command | Description |
|---------|-------------|
| `git adr hooks install` | Install pre-push hooks |
| `git adr hooks install --force` | Force reinstall (backs up existing hooks) |
| `git adr hooks install --manual` | Show manual integration instructions |
| `git adr hooks uninstall` | Remove hooks and restore backups |
| `git adr hooks status` | Check hook installation status |
| `git adr hooks config --show` | View current hook configuration |
| `git adr hooks config --block-on-failure` | Block push if sync fails |
| `git adr hooks config --no-block-on-failure` | Allow push even if sync fails |

### Skip Hooks

```bash
# Skip once
GIT_ADR_SKIP=1 git push

# Skip permanently
git config adr.hooks.skip true
```

## CI/CD Integration

Generate CI/CD workflow configurations. See [SDLC Integration Guide](./SDLC_INTEGRATION.md) for details.

| Command | Description |
|---------|-------------|
| `git adr ci github` | Generate GitHub Actions (sync + validate) |
| `git adr ci github --sync` | Generate sync workflow only |
| `git adr ci github --validate` | Generate validation workflow only |
| `git adr ci gitlab` | Generate GitLab CI pipeline |
| `git adr ci list` | List available CI templates |

### Governance Templates

| Command | Description |
|---------|-------------|
| `git adr templates all` | Generate all governance templates |
| `git adr templates pr` | Generate PR template with ADR checklist |
| `git adr templates issue` | Generate issue template for ADR proposals |
| `git adr templates codeowners` | Generate CODEOWNERS for ADR review |
| `git adr templates list` | List available templates |

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
# Interactive setup (prompts for template, hooks, CI)
git adr init

# Or non-interactive with all features
git adr init --no-input --install-hooks --setup-github-ci

# Create your first decision
git adr new "Use git-adr for architecture decisions"

# Push to remote (automatic if hooks installed)
git push
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
