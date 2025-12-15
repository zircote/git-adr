# git-adr

Architecture Decision Records (ADR) management for git repositories.

[![CI](https://github.com/zircote/git-adr/actions/workflows/ci.yml/badge.svg)](https://github.com/zircote/git-adr/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

`git-adr` is a command-line tool that integrates Architecture Decision Record management directly into your git workflow. Track architectural decisions alongside your code with first-class git integration.

## Installation

```bash
pip install git-adr
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv tool install git-adr
```

## Quick Start

```bash
# Initialize ADR directory in your repository
git adr init

# Create a new ADR
git adr new "Use PostgreSQL for primary database"

# List all ADRs
git adr list

# Show a specific ADR
git adr show 0001
```

## Commands

| Command | Description |
|---------|-------------|
| `git adr init` | Initialize ADR directory in repository |
| `git adr new <title>` | Create a new ADR |
| `git adr list` | List all ADRs |
| `git adr show <number>` | Show an ADR |
| `git adr link <from> <to>` | Link ADRs together |
| `git adr generate` | Generate documentation from ADRs |

## ADR Format

ADRs follow a standard format:

```markdown
# 1. Use PostgreSQL for primary database

Date: 2024-01-15

## Status

Accepted

## Context

We need to choose a database for our application...

## Decision

We will use PostgreSQL because...

## Consequences

- Positive: ACID compliance, rich feature set
- Negative: Requires more operational expertise
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/zircote/git-adr.git
cd git-adr

# Install dependencies with uv
uv sync --all-extras --dev

# Run tests
uv run pytest

# Run linting
uv run ruff check .
uv run mypy .
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint and fix
uv run ruff check . --fix

# Type check
uv run mypy .

# Security scan
uv run bandit -r src/
```

## License

MIT License - see [LICENSE](LICENSE) for details.
