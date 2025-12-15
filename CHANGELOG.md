# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-12-15

Initial release of git-adr - Architecture Decision Records management for git repositories using git notes.

### Added

- **Core ADR Management**
  - `init` - Initialize ADR configuration with customizable templates
  - `new` - Create new ADRs with frontmatter support (title, status, deciders, consulted, informed)
  - `show` - Display ADR content with rich formatting and DACI metadata
  - `list` - List all ADRs with filtering and sorting options
  - `search` - Full-text search across ADR content
  - `sync` - Sync ADRs between git notes and filesystem
  - `rm` - Remove ADRs from git notes storage

- **Status Management**
  - `accept`, `supersede`, `deprecate`, `amend` - ADR lifecycle commands
  - Status tracking with timestamps and linked decisions

- **Graph & Visualization**
  - `graph` - Generate dependency graphs showing ADR relationships
  - Support for Mermaid diagram output

- **Export Capabilities**
  - `export` - Export ADRs to multiple formats (markdown, HTML, JSON)
  - Optional DOCX export with `[export]` extra

- **AI Integration** (optional `[ai]` extra)
  - AI-powered ADR generation and suggestions
  - Support for OpenAI, Anthropic, Google, and Ollama providers

- **Wiki Integration** (optional `[wiki]` extra)
  - Publish ADRs to GitHub Wiki
  - Publish ADRs to GitLab Wiki

- **Developer Experience**
  - Shell completion for Bash, Zsh, and Fish
  - Comprehensive man pages
  - Install script following git-lfs conventions
  - Git subcommand integration (`git adr` works alongside `git-adr`)

- **CI/CD**
  - GitHub Actions workflows for testing, linting, and releases
  - Automated binary releases for Linux, macOS, and Windows
  - Homebrew tap support for macOS installation

### Technical Details

- Built with Python 3.11+ using Typer for CLI
- Uses git notes for storage (non-intrusive, separate from code commits)
- Supports frontmatter-based metadata in Markdown files
- 78%+ test coverage with pytest

[0.1.0]: https://github.com/zircote/git-adr/releases/tag/v0.1.0
