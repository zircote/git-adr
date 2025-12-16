# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Development Commands

```bash
# Install dependencies
uv sync --all-extras

# Run all tests
uv run pytest

# Run single test file
uv run pytest tests/test_core.py

# Run tests matching pattern
uv run pytest -k "test_new"

# Run with coverage
uv run pytest --cov=src/git_adr --cov-report=term-missing

# Format code
uv run ruff format .

# Lint and auto-fix
uv run ruff check . --fix

# Type check
uv run mypy src

# Security scan
uv run bandit -r src/

# Run the CLI
uv run git-adr --help
```

## Architecture Overview

git-adr stores Architecture Decision Records in **git notes** (not files), making ADRs non-intrusive and portable with git history.

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

### Key Patterns

**Command structure** (Typer-based):
```python
@app.command()
def mycommand(
    arg: Annotated[str, typer.Argument(help="Description")],
    option: Annotated[str, typer.Option("--option", "-o")] = "default",
):
    """Command description for help text."""
    git = Git()
    config = ConfigManager(git).load()
    notes = NotesManager(git, config)
    # ... implementation
```

**Error messages with Rich console**: Escape brackets in `pip install 'git-adr[ai]'` as `'git-adr\\[ai]'` to prevent Rich from interpreting `[ai]` as markup.

## Code Style

- Python 3.11+ with full type annotations
- Use `typer` for CLI (not `click` as in older docs)
- Google-style docstrings
- Use `pathlib.Path` over `os.path`
- Prefer dataclasses for structured data

## Testing

Test files mirror source: `src/git_adr/foo.py` → `tests/test_foo.py`

**Available fixtures** (from `tests/conftest.py`):
- `temp_git_repo` - Empty git repository
- `temp_git_repo_with_commit` - Git repo with initial commit
- `initialized_adr_repo` - Git repo with ADR initialized (most common)

**Test naming**: `test_<function>_<scenario>_<expected>`

## Version Management

Version is defined in two places that CI syncs automatically:
- `pyproject.toml` (source of truth)
- `src/git_adr/__init__.py` (`__version__`)

To release: push a tag like `v0.1.4` - CI handles PyPI publish and Homebrew formula update.

## Optional Dependencies

Core package is minimal. Extras for specific features:
- `[ai]` - LangChain providers for AI commands
- `[wiki]` - PyGithub/python-gitlab for wiki sync
- `[export]` - python-docx for DOCX export
- `[all]` - Everything
