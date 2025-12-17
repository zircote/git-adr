# git-adr

Architecture Decision Records (ADR) management for git repositories using git notes.

[![CI](https://github.com/zircote/git-adr/actions/workflows/ci.yml/badge.svg)](https://github.com/zircote/git-adr/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

`git-adr` is a command-line tool that integrates Architecture Decision Record management directly into your git workflow. Unlike file-based ADR tools, `git-adr` stores ADRs in **git notes**, making them:

- **Non-intrusive**: No files cluttering your repository
- **Portable**: Travel with your git history
- **Linkable**: Associate decisions with specific commits
- **Searchable**: Full-text search across all decisions
- **Syncable**: Push/pull ADRs like regular git content

## Installation

### Standalone Binary (Fastest)

Pre-built binaries are available for all platforms - no Python required:

```bash
# macOS/Linux (auto-detects platform)
curl -sSL https://raw.githubusercontent.com/zircote/git-adr/main/script/install-binary.sh | bash

# Or install to ~/.local/bin (no sudo)
curl -sSL https://raw.githubusercontent.com/zircote/git-adr/main/script/install-binary.sh | bash -s -- --local

# Specific version
curl -sSL https://raw.githubusercontent.com/zircote/git-adr/main/script/install-binary.sh | bash -s -- v0.1.0
```

Or download manually from [GitHub Releases](https://github.com/zircote/git-adr/releases):

| Platform | Download |
|----------|----------|
| macOS ARM64 (M1/M2/M3) | `git-adr-macos-arm64.tar.gz` |
| macOS Intel | `git-adr-macos-x86_64.tar.gz` |
| Linux x86_64 | `git-adr-linux-x86_64.tar.gz` |
| Windows x86_64 | `git-adr-windows-x86_64.zip` |

### Homebrew (macOS)

```bash
brew tap zircote/tap
brew install git-adr
```

This automatically installs shell completions and keeps git-adr updated with `brew upgrade`.

### pip / uv

```bash
pip install git-adr
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv tool install git-adr
```

### With Optional Features

```bash
# AI-powered features (drafting, suggestions, Q&A)
pip install "git-adr[ai]"

# Wiki synchronization (GitHub/GitLab)
pip install "git-adr[wiki]"

# Document export (DOCX format)
pip install "git-adr[export]"

# All features
pip install "git-adr[all]"
```

### Shell Completion

Enable tab completion for your shell:

```bash
# Automatic installation (detects your shell)
git-adr --install-completion

# Or manually for specific shells
git-adr --show-completion bash >> ~/.bashrc
git-adr --show-completion zsh >> ~/.zshrc
git-adr --show-completion fish > ~/.config/fish/completions/git-adr.fish
```

### Man Pages

Man pages are included in [GitHub releases](https://github.com/zircote/git-adr/releases).
Download and install:

```bash
# Download from release (replace VERSION)
curl -L https://github.com/zircote/git-adr/releases/download/vVERSION/git-adr-man-pages-VERSION.tar.gz | \
  sudo tar -xzf - -C /usr/local/share/man/

# Then use
man git-adr
man git-adr-new
```

Or build from source:

```bash
git clone https://github.com/zircote/git-adr.git
cd git-adr
make install-man  # Requires pandoc
```

## Quick Start

```bash
# Interactive setup (recommended) - prompts for template, hooks, and CI
git adr init

# Or non-interactive with specific options
git adr init --template madr --install-hooks --setup-github-ci

# Create a new ADR (opens editor)
git adr new "Use PostgreSQL for primary database"

# List all ADRs
git adr list

# Show a specific ADR
git adr show 20240115-use-postgresql

# Search ADRs
git adr search "database"

# ADRs sync automatically on push (if hooks installed)
# Or sync manually:
git adr sync push
```

### Init Options

| Option | Description |
|--------|-------------|
| `--template <format>` | Set ADR format (madr, nygard, y-statement, etc.) |
| `--install-hooks` | Install pre-push hooks for automatic sync |
| `--setup-github-ci` | Generate GitHub Actions workflows |
| `--no-input` | Skip all interactive prompts |

See [Hooks Guide](docs/HOOKS_GUIDE.md) for detailed hooks documentation.

## Commands

### Core Commands

| Command | Description |
|---------|-------------|
| `git adr init` | Initialize ADR tracking in repository |
| `git adr new <title>` | Create a new ADR |
| `git adr list` | List all ADRs with filtering options |
| `git adr show <id>` | Display an ADR with formatting |
| `git adr edit <id>` | Edit an existing ADR |
| `git adr search <query>` | Full-text search across ADRs |
| `git adr link <adr-id> <commit>` | Associate an ADR with commits |
| `git adr supersede <old-id> <title>` | Create ADR that supersedes another |
| `git adr log` | Show git log with ADR annotations |

### Artifact Management

| Command | Description |
|---------|-------------|
| `git adr attach <adr-id> <file>` | Attach diagram/image to an ADR |
| `git adr artifacts <adr-id>` | List artifacts attached to an ADR |
| `git adr artifact-get <sha256>` | Extract an artifact to a file |
| `git adr artifact-rm <adr-id> <sha256>` | Remove an artifact |

### Analytics & Reporting

| Command | Description |
|---------|-------------|
| `git adr stats` | Quick ADR statistics summary |
| `git adr report` | Generate detailed analytics report |
| `git adr metrics` | Export metrics for dashboards (JSON/Prometheus) |

### Export & Import

| Command | Description |
|---------|-------------|
| `git adr export` | Export ADRs to files (markdown, json, html, docx) |
| `git adr import` | Import ADRs from file-based storage |
| `git adr convert <id>` | Convert an ADR to different format |

### Synchronization

| Command | Description |
|---------|-------------|
| `git adr sync push` | Push ADR notes to remote |
| `git adr sync pull` | Pull ADR notes from remote |

### Configuration

| Command | Description |
|---------|-------------|
| `git adr config --list` | List all configuration |
| `git adr config <key> <value>` | Set configuration value |
| `git adr config --get <key>` | Get configuration value |

### Team Features

| Command | Description |
|---------|-------------|
| `git adr onboard` | Interactive onboarding wizard for new team members |

## AI Features

> Requires `pip install "git-adr[ai]"`

Configure your AI provider:

```bash
# Set provider (openai, anthropic, google, ollama)
git adr config adr.ai.provider openai

# Set API key (environment variable)
export OPENAI_API_KEY="your-key"
# or
export ANTHROPIC_API_KEY="your-key"
export GOOGLE_API_KEY="your-key"
```

### AI Commands

| Command | Description |
|---------|-------------|
| `git adr ai draft` | AI-guided ADR creation with interactive elicitation |
| `git adr ai suggest <id>` | Get AI suggestions to improve an ADR |
| `git adr ai summarize` | Generate natural language summary of decisions |
| `git adr ai ask "<question>"` | Ask questions about ADRs in natural language |

### Examples

```bash
# AI-assisted drafting
git adr ai draft "Choose a message queue"

# Get improvement suggestions
git adr ai suggest 20240115-use-postgresql

# Summarize recent decisions
git adr ai summarize --format slack

# Ask questions
git adr ai ask "Why did we choose PostgreSQL?"
```

## Wiki Synchronization

> Requires `pip install "git-adr[wiki]"`

Sync ADRs with GitHub or GitLab wikis:

```bash
# Initialize wiki sync
git adr wiki init --provider github --repo owner/repo

# Sync ADRs to wiki
git adr wiki sync
```

## Configuration Options

Configuration is stored in git config (local or global):

| Key | Description | Default |
|-----|-------------|---------|
| `adr.namespace` | Notes namespace | `adr` |
| `adr.template` | Default template format | `madr` |
| `adr.editor` | Editor command override | `$EDITOR` |
| `adr.ai.provider` | AI provider (openai, anthropic, google, ollama) | - |
| `adr.ai.model` | AI model name | Provider default |
| `adr.ai.temperature` | AI temperature (0.0-1.0) | `0.7` |

### Examples

```bash
# Set local config
git adr config adr.template madr

# Set global config
git adr config --global adr.editor "code --wait"

# List all config
git adr config --list
```

## ADR Format (MADR)

ADRs follow the [MADR](https://adr.github.io/madr/) format:

```markdown
---
id: 20240115-use-postgresql
title: Use PostgreSQL for primary database
date: 2024-01-15
status: accepted
tags: [database, infrastructure]
---

## Context and Problem Statement

We need to choose a database for our application...

## Decision Drivers

* Performance requirements
* Team expertise
* Operational complexity

## Considered Options

* PostgreSQL
* MySQL
* MongoDB

## Decision Outcome

Chosen option: "PostgreSQL", because...

### Consequences

#### Good
- ACID compliance
- Rich feature set

#### Bad
- Requires more operational expertise
```

## Git Notes Architecture

`git-adr` uses git notes to store ADRs, which provides:

- **No file pollution**: ADRs live in git's notes refs, not in your working tree
- **Full git integration**: Push, pull, merge like regular git content
- **Commit association**: Link decisions to the commits that implement them
- **History preservation**: ADR history is preserved in git

Notes are stored under:
- `refs/notes/adr` - ADR content
- `refs/notes/adr-index` - Search index
- `refs/notes/adr-artifacts` - Binary attachments

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/zircote/git-adr.git
cd git-adr

# Install dependencies with uv
uv sync --all-extras

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/git_adr --cov-report=term-missing
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint and fix
uv run ruff check . --fix

# Type check
uv run mypy src

# Security scan
uv run bandit -r src/

# Dependency audit
uv run pip-audit
```

### Project Structure

```
src/git_adr/
├── __init__.py          # Package exports
├── cli.py               # Main CLI entry point
├── core/                # Core functionality
│   ├── adr.py           # ADR data models
│   ├── config.py        # Configuration management
│   ├── git.py           # Git operations wrapper
│   ├── notes.py         # Git notes management
│   ├── index.py         # Search index
│   └── templates.py     # ADR templates
├── commands/            # CLI command implementations
│   ├── basic.py         # Core commands (new, list, show, etc.)
│   ├── ai_cmds.py       # AI-powered commands
│   ├── wiki.py          # Wiki sync commands
│   └── export.py        # Export/import commands
├── ai/                  # AI service integration
│   └── service.py       # LLM provider abstraction
├── wiki/                # Wiki providers
│   └── service.py       # GitHub/GitLab wiki sync
└── formats/             # Format converters
    └── docx.py          # DOCX export
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`uv run pytest && uv run ruff check .`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Claude Code Skill

A Claude Code skill for AI-assisted ADR management. Turn natural language into properly formatted ADRs.

### Why Use the Skill?

- **Instant ADR creation**: Describe a decision, get a formatted ADR
- **Six professional formats**: MADR, Nygard, Y-Statement, Alexandrian, Business Case, Planguage
- **Git-native storage**: ADRs in git notes, not files cluttering your repo
- **Direct execution**: Claude runs `git adr` commands, not just generates markdown

### Installation

```bash
# Method 1: Copy from repository
cp -r skills/git-adr ~/.claude/skills/

# Method 2: Download from release
curl -LO https://github.com/zircote/git-adr/releases/download/vX.Y.Z/git-adr-X.Y.Z.skill
unzip git-adr-X.Y.Z.skill -d ~/.claude/skills/
```

### Quick Example

```
You: "We decided to use PostgreSQL because it has better JSON support"

Claude: I'll create that ADR for you.
> git adr new "Use PostgreSQL for primary database"
Created ADR: 20251216-use-postgresql-for-primary-database
```

For full documentation, see **[docs/git-adr-skill.md](docs/git-adr-skill.md)**.

## Acknowledgments

- [MADR](https://adr.github.io/madr/) - Markdown ADR format
- [ADR Tools](https://github.com/npryce/adr-tools) - Original ADR tooling inspiration
