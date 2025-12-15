# GitHub Copilot Instructions for git-adr

## Project Overview

git-adr is a CLI tool for managing Architecture Decision Records (ADRs) in git repositories.

## Code Style

- Python 3.12+ with full type annotations
- Use `click` for CLI commands
- Follow Google-style docstrings
- Use `pathlib.Path` over `os.path`
- Prefer dataclasses or Pydantic models for structured data

## Testing

- Use pytest with fixtures in `conftest.py`
- Test files should mirror source structure: `src/git_adr/foo.py` -> `tests/test_foo.py`
- Use `temp_git_repo` fixture for tests requiring git operations

## Common Patterns

### CLI Commands

```python
import click

@click.command()
@click.argument("name")
@click.option("--force", "-f", is_flag=True, help="Force operation")
def my_command(name: str, force: bool) -> None:
    """Short description of command."""
    ...
```

### File Operations

```python
from pathlib import Path

def read_adr(path: Path) -> str:
    return path.read_text(encoding="utf-8")
```

## ADR Format

ADRs follow the standard format:
- Title with sequence number (e.g., "0001-use-postgresql.md")
- Status: Proposed, Accepted, Deprecated, Superseded
- Context, Decision, Consequences sections
