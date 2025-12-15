# Contributing to git-adr

Thank you for your interest in contributing to git-adr! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Git

### Setting Up Your Development Environment

```bash
# Clone the repository
git clone https://github.com/zircote/git-adr.git
cd git-adr

# Create virtual environment and install dependencies
uv sync --all-extras

# Verify installation
uv run git-adr --version
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/git_adr --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_core.py

# Run tests matching a pattern
uv run pytest -k "test_new"
```

### Code Quality Checks

Before submitting a PR, ensure all checks pass:

```bash
# Format code
uv run ruff format .

# Lint (with auto-fix)
uv run ruff check . --fix

# Type check
uv run mypy src

# Security scan
uv run bandit -r src/

# Dependency audit
uv run pip-audit

# Run all checks (as CI does)
uv run ruff format --check . && \
uv run ruff check . && \
uv run mypy src && \
uv run pytest
```

## Project Architecture

### Directory Structure

```
src/git_adr/
├── __init__.py          # Package exports and version
├── cli.py               # Typer CLI application setup
├── core/                # Core business logic
│   ├── __init__.py      # Core module exports
│   ├── adr.py           # ADR dataclass and status enum
│   ├── config.py        # Configuration management
│   ├── git.py           # Git operations wrapper
│   ├── notes.py         # Git notes CRUD operations
│   ├── index.py         # Search index management
│   └── templates.py     # ADR templates (MADR, etc.)
├── commands/            # CLI command implementations
│   ├── __init__.py
│   ├── basic.py         # Core commands (new, list, show, edit, etc.)
│   ├── ai_cmds.py       # AI-powered commands
│   ├── wiki.py          # Wiki synchronization
│   └── export.py        # Export/import functionality
├── ai/                  # AI service layer
│   └── service.py       # LLM provider abstraction
├── wiki/                # Wiki providers
│   └── service.py       # GitHub/GitLab wiki sync
└── formats/             # Format converters
    └── docx.py          # DOCX export
```

### Key Components

#### Core Layer (`core/`)

- **Git**: Low-level git operations wrapper
- **NotesManager**: CRUD operations for ADRs stored in git notes
- **IndexManager**: Search index for fast full-text search
- **ConfigManager**: Git config-based configuration
- **ADR**: Dataclass representing an ADR with metadata

#### Command Layer (`commands/`)

Commands are implemented as Typer commands that use core services:

```python
@app.command()
def new(
    title: Annotated[str, typer.Argument(help="ADR title")],
    status: Annotated[str, typer.Option("--status", "-s")] = "proposed",
):
    """Create a new ADR."""
    git = get_git()
    config = ConfigManager(git).load()
    notes = NotesManager(git, config)
    # ... implementation
```

#### AI Layer (`ai/`)

Abstracts LLM providers using LangChain:

- OpenAI (GPT-4, GPT-4-mini)
- Anthropic (Claude)
- Google (Gemini)
- Ollama (local models)

## Making Changes

### Workflow

1. **Fork and clone** the repository
2. **Create a feature branch**: `git checkout -b feature/my-feature`
3. **Make changes** following the coding standards
4. **Write tests** for new functionality
5. **Run checks** to ensure quality
6. **Commit** with conventional commit messages
7. **Push** and open a Pull Request

### Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add wiki sync for GitLab
fix: handle empty ADR content gracefully
docs: update README with AI examples
test: add coverage for artifact operations
refactor: extract common validation logic
chore: update dependencies
```

### Code Style

- Follow PEP 8 (enforced by ruff)
- Use type hints for all function signatures
- Write docstrings for public functions
- Keep functions focused and small
- Prefer composition over inheritance

### Testing Guidelines

- Write tests for all new functionality
- Use pytest fixtures from `conftest.py`
- Test both success and error cases
- Use meaningful test names: `test_<function>_<scenario>_<expected>`

Example test structure:

```python
class TestNotesManager:
    """Tests for NotesManager operations."""

    def test_add_creates_note(self, initialized_adr_repo: Path) -> None:
        """Test that add() creates a git note for the ADR."""
        git = Git(cwd=initialized_adr_repo)
        config = ConfigManager(git).load()
        notes = NotesManager(git, config)

        adr = ADR(
            metadata=ADRMetadata(
                id="test-adr",
                title="Test",
                date=date.today(),
                status=ADRStatus.PROPOSED,
            ),
            content="## Context\n\nTest content.",
        )

        notes.add(adr)
        result = notes.get("test-adr")

        assert result is not None
        assert result.metadata.title == "Test"
```

### Available Fixtures

From `tests/conftest.py`:

- `temp_git_repo`: Empty git repository
- `temp_git_repo_with_commit`: Git repo with initial commit
- `initialized_adr_repo`: Git repo with ADR initialized

## Adding New Features

### Adding a New Command

1. Add the command in appropriate file under `commands/`:

```python
# commands/basic.py
@app.command()
def mycommand(
    arg: Annotated[str, typer.Argument(help="Description")],
    option: Annotated[str, typer.Option("--option", "-o")] = "default",
):
    """Command description for help text."""
    # Implementation
```

2. Add tests in `tests/test_commands.py`
3. Update README with documentation

### Adding a New AI Provider

1. Add provider to `ai/service.py`:

```python
class AIService:
    PROVIDER_ENV_VARS = {
        # ... existing
        "newprovider": "NEWPROVIDER_API_KEY",
    }

    DEFAULT_MODELS = {
        # ... existing
        "newprovider": "default-model",
    }

    def _get_llm(self):
        # ... existing
        elif self.provider == "newprovider":
            from langchain_newprovider import ChatNewProvider
            self._llm = ChatNewProvider(
                model=self.model,
                temperature=self.temperature,
            )
```

2. Add dependency to `pyproject.toml` under `[project.optional-dependencies].ai`
3. Add tests with mocked provider

### Adding Export Format

1. Create format module under `formats/`:

```python
# formats/newformat.py
def export_newformat(adrs: list[ADR], output_path: Path) -> None:
    """Export ADRs to new format."""
    # Implementation
```

2. Register in `commands/export.py`
3. Add to optional dependencies if needed

## Pull Request Process

1. **Ensure all checks pass** locally
2. **Update documentation** if needed
3. **Fill out the PR template** completely
4. **Request review** from maintainers
5. **Address feedback** promptly
6. **Squash commits** if requested

### PR Template

PRs should include:

- Description of changes
- Link to related issue (if any)
- Test coverage for new code
- Documentation updates

## Getting Help

- **Issues**: For bugs and feature requests
- **Discussions**: For questions and ideas
- **Code of Conduct**: Be respectful and inclusive

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
