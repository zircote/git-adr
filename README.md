# git-adr

Architecture Decision Records (ADR) management for git repositories using git notes.

[![CI](https://github.com/zircote/git-adr/actions/workflows/ci.yml/badge.svg)](https://github.com/zircote/git-adr/actions/workflows/ci.yml)
[![Crates.io](https://img.shields.io/crates/v/git-adr.svg)](https://crates.io/crates/git-adr)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

`git-adr` is a command-line tool that integrates Architecture Decision Record management directly into your git workflow. Unlike file-based ADR tools, `git-adr` stores ADRs in **git notes**, making them:

- **Non-intrusive**: No files cluttering your repository
- **Portable**: Travel with your git history
- **Linkable**: Associate decisions with specific commits
- **Searchable**: Full-text search across all decisions
- **Syncable**: Push/pull ADRs like regular git content

## Installation

### Pre-built Binaries

Download from [GitHub Releases](https://github.com/zircote/git-adr/releases):

| Platform | Download |
|----------|----------|
| macOS ARM64 (M1/M2/M3/M4) | `git-adr-aarch64-apple-darwin.tar.gz` |
| macOS Intel | `git-adr-x86_64-apple-darwin.tar.gz` |
| Linux x86_64 | `git-adr-x86_64-unknown-linux-gnu.tar.gz` |
| Linux x86_64 (musl) | `git-adr-x86_64-unknown-linux-musl.tar.gz` |
| Linux ARM64 | `git-adr-aarch64-unknown-linux-gnu.tar.gz` |
| Windows x86_64 | `git-adr-x86_64-pc-windows-msvc.zip` |

### Homebrew (macOS)

```bash
brew tap zircote/tap
brew install git-adr
```

### Cargo (Rust)

```bash
cargo install git-adr
```

### With Optional Features

```bash
# AI-powered features (drafting, suggestions)
cargo install git-adr --features ai

# Wiki synchronization (GitHub/GitLab)
cargo install git-adr --features wiki

# Document export (DOCX format)
cargo install git-adr --features export

# All features
cargo install git-adr --features all
```

### From Source

```bash
git clone https://github.com/zircote/git-adr.git
cd git-adr
cargo build --release
# Binary at target/release/git-adr
```

## Quick Start

```bash
# Initialize ADR tracking in your repository
git adr init

# Create a new ADR (opens editor)
git adr new "Use PostgreSQL for primary database"

# List all ADRs
git adr list

# Show a specific ADR
git adr show ADR-0001

# Search ADRs
git adr search "database"

# Sync ADRs with remote
git adr sync --push
```

## Commands

### Core Commands

| Command | Description |
|---------|-------------|
| `git adr init` | Initialize ADR tracking in repository |
| `git adr new <title>` | Create a new ADR |
| `git adr list` | List all ADRs with filtering options |
| `git adr show <id>` | Display an ADR with formatting |
| `git adr edit <id>` | Edit an existing ADR |
| `git adr rm <id>` | Remove an ADR |
| `git adr search <query>` | Full-text search across ADRs |
| `git adr link <adr-id> <commit>` | Associate an ADR with commits |
| `git adr supersede <old-id> <title>` | Create ADR that supersedes another |
| `git adr log` | Show git log with ADR annotations |

### Artifact Management

| Command | Description |
|---------|-------------|
| `git adr attach <adr-id> <file>` | Attach diagram/image to an ADR |
| `git adr artifacts <adr-id>` | List artifacts attached to an ADR |

### Analytics & Export

| Command | Description |
|---------|-------------|
| `git adr stats` | Quick ADR statistics summary |
| `git adr export` | Export ADRs to files (markdown, json, html, docx) |
| `git adr convert <id>` | Convert an ADR to different format |

### Synchronization

| Command | Description |
|---------|-------------|
| `git adr sync` | Sync ADRs with remote (push & fetch) |
| `git adr sync --push` | Push ADR notes to remote only |
| `git adr sync --pull` | Fetch ADR notes from remote only |

### Configuration

| Command | Description |
|---------|-------------|
| `git adr config list` | List all configuration |
| `git adr config set <key> <value>` | Set configuration value |
| `git adr config get <key>` | Get configuration value |

## Configuration Options

Configuration is stored in git config (local or global):

| Key | Description | Default |
|-----|-------------|---------|
| `adr.prefix` | ADR ID prefix | `ADR-` |
| `adr.digits` | Number of digits in ADR ID | `4` |
| `adr.template` | Default template format | `madr` |
| `adr.format` | ADR format (nygard, madr, etc.) | `nygard` |

### Examples

```bash
# Set configuration
git adr config set template madr

# Get configuration
git adr config get template

# List all config
git adr config list
```

## ADR Formats

git-adr supports multiple ADR formats:

### Nygard (Default)

The original ADR format by Michael Nygard.

```markdown
# Use PostgreSQL for primary database

## Status

Accepted

## Context

We need to choose a database...

## Decision

We will use PostgreSQL...

## Consequences

- ACID compliance
- Rich feature set
```

### MADR

Markdown Architectural Decision Records format.

```markdown
# Use PostgreSQL for primary database

## Status

Accepted

## Context and Problem Statement

We need to choose a database...

## Decision Drivers

* Performance requirements
* Team expertise

## Considered Options

* PostgreSQL
* MySQL
* MongoDB

## Decision Outcome

Chosen option: "PostgreSQL", because...
```

### Other Formats

- **Y-Statement**: Concise one-sentence decision format
- **Alexandrian**: Pattern-based format with forces
- **Business Case**: MBA-style with cost-benefit analysis

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

## AI Features (Planned)

> Requires installation with `--features ai`
>
> **Note:** AI features are not yet implemented in the Rust version. They are planned for a future release.

## Wiki Synchronization (Planned)

> Requires installation with `--features wiki`
>
> **Note:** Wiki synchronization is not yet implemented in the Rust version. It is planned for a future release.

## Development

### Setup

```bash
git clone https://github.com/zircote/git-adr.git
cd git-adr

# Build
cargo build

# Run tests
cargo test

# Run with all features
cargo test --all-features

# Check lints
cargo clippy --all-targets --all-features

# Format
cargo fmt
```

### Project Structure

```
src/
├── lib.rs           # Library entry point
├── main.rs          # Binary entry point
├── cli/             # CLI command implementations
│   ├── mod.rs       # CLI definition
│   ├── init.rs      # Initialize command
│   ├── new.rs       # New ADR command
│   └── ...          # Other commands
├── core/            # Core business logic
│   ├── adr.rs       # ADR data model
│   ├── git.rs       # Git operations
│   ├── notes.rs     # Git notes management
│   ├── config.rs    # Configuration
│   ├── index.rs     # Search index
│   └── templates.rs # ADR templates
├── ai/              # AI features (optional)
├── wiki/            # Wiki sync (optional)
└── export/          # Export formats (optional)
```

## Migration from v0.x (Python)

Version 1.0 is a complete rewrite in Rust. The data format (git notes) is fully compatible, so your existing ADRs will work without changes. Some CLI flags may have changed - use `git adr --help` for current options.

To access the Python version:

```bash
# Checkout the Python version
git checkout python-final

# Or install the last Python release
pip install git-adr==0.3.0
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`cargo test && cargo clippy`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [MADR](https://adr.github.io/madr/) - Markdown ADR format
- [ADR Tools](https://github.com/npryce/adr-tools) - Original ADR tooling inspiration
