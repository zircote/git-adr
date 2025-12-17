# GitHub Copilot Instructions for git-adr

## Project Overview

git-adr is a CLI tool for managing Architecture Decision Records (ADRs) stored in **git notes** (not files), making ADRs non-intrusive and portable with git history.

### Storage Model

- `refs/notes/adr` - ADR content (markdown with YAML frontmatter)
- `refs/notes/adr-index` - Search index for fast full-text lookup
- `refs/notes/adr-artifacts` - Binary attachments (base64 encoded)

### Layer Architecture

```
CLI (cli.py)
    ↓
Commands (commands/*.py) - Typer commands using core services
    ↓
Core (core/*.py)
├── NotesManager - CRUD for ADRs in git notes
├── IndexManager - Search index operations
├── Git - Low-level git subprocess wrapper
├── ConfigManager - adr.* git config settings
└── ADR dataclass - Metadata + content model
    ↓
Optional Services
├── ai/service.py - LLM abstraction (OpenAI/Anthropic/Google/Ollama via LangChain)
├── wiki/service.py - GitHub/GitLab wiki sync
└── formats/docx.py - DOCX export
```

## Code Style

- Python 3.11+ with full type annotations
- Use `typer` for CLI commands (not click)
- Follow Google-style docstrings
- Use `pathlib.Path` over `os.path`
- Prefer dataclasses for structured data

## Testing

- Use pytest with fixtures in `tests/conftest.py`
- Test files mirror source structure: `src/git_adr/foo.py` -> `tests/test_foo.py`
- Use `initialized_adr_repo` fixture for tests requiring ADR operations
- Test naming: `test_<function>_<scenario>_<expected>`

**Available fixtures:**
- `temp_git_repo` - Empty git repository
- `temp_git_repo_with_commit` - Git repo with initial commit
- `initialized_adr_repo` - Git repo with ADR initialized (most common)

## Common Patterns

### CLI Commands (Typer-based)

```python
from typing import Annotated
import typer

@app.command()
def my_command(
    arg: Annotated[str, typer.Argument(help="Description")],
    option: Annotated[str, typer.Option("--option", "-o")] = "default",
) -> None:
    """Command description for help text."""
    git = Git()
    config = ConfigManager(git).load()
    notes = NotesManager(git, config)
    # ... implementation
```

### File Operations

```python
from pathlib import Path

def read_adr(path: Path) -> str:
    return path.read_text(encoding="utf-8")
```

### Rich Console Output

Escape brackets in package names like `pip install 'git-adr[ai]'` as `'git-adr\\[ai]'` to prevent Rich from interpreting `[ai]` as markup.

## ADR Format

ADRs use YAML frontmatter with markdown body:
- **Status**: Proposed, Accepted, Deprecated, Superseded
- **Sections**: Context, Decision, Consequences

## Optional Dependencies

- `[ai]` - LangChain providers for AI commands
- `[wiki]` - PyGithub/python-gitlab for wiki sync
- `[export]` - python-docx for DOCX export
- `[all]` - Everything

## Development Commands

```bash
uv sync --all-extras        # Install all dependencies
uv run pytest               # Run tests
uv run ruff format .        # Format code
uv run ruff check . --fix   # Lint and auto-fix
uv run mypy src             # Type check
uv run bandit -r src/       # Security scan
```
