"""Shared pytest fixtures for git-adr tests.

Provides comprehensive test infrastructure for:
- Temporary git repository creation and cleanup
- Initialized ADR repositories
- Sample ADR data
- Mock AI services
"""

from __future__ import annotations

import os
import shutil
import subprocess
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from git_adr.core.adr import ADR, ADRMetadata, ADRStatus
from git_adr.core.config import Config
from git_adr.core.git import Git

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


# =============================================================================
# Test Markers
# =============================================================================


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers for test categorization."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (require git repos)"
    )
    # Reserved for future use - tests that take >5s
    config.addinivalue_line("markers", "slow: marks tests as slow running")


# =============================================================================
# Git Repository Fixtures
# =============================================================================


@pytest.fixture
def temp_git_repo(tmp_path: Path) -> Iterator[Path]:
    """Create a temporary git repository for testing.

    Yields:
        Path to the temporary git repository.
    """
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()

    # Initialize git repo
    subprocess.run(
        ["git", "init"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    # Configure git user
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    yield repo_path

    # Cleanup is handled by tmp_path fixture


@pytest.fixture
def temp_git_repo_with_commit(temp_git_repo: Path) -> Iterator[Path]:
    """Create a git repo with an initial commit.

    Required for operations that need a commit (like git notes).

    Yields:
        Path to the git repository with initial commit.
    """
    # Create and commit a file
    (temp_git_repo / "README.md").write_text("# Test Repository\n")
    subprocess.run(
        ["git", "add", "."],
        cwd=temp_git_repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=temp_git_repo,
        check=True,
        capture_output=True,
    )

    yield temp_git_repo


@pytest.fixture
def initialized_adr_repo(
    temp_git_repo_with_commit: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[Path]:
    """Create a git repo with git-adr initialized.

    Changes the current working directory to the repo.

    Yields:
        Path to the initialized ADR repository.
    """
    repo_path = temp_git_repo_with_commit

    # Change to repo directory
    monkeypatch.chdir(repo_path)

    # Initialize git-adr by setting config
    git = Git(cwd=repo_path)
    git.config_set("adr.namespace", "adr")
    git.config_set("adr.template", "madr")
    git.config_set("adr.initialized", "true")

    yield repo_path


@pytest.fixture
def adr_repo_with_data(initialized_adr_repo: Path) -> Iterator[Path]:
    """Create an ADR repo with sample ADRs.

    Yields:
        Path to the repository with sample ADRs.
    """
    from git_adr.core import ConfigManager, NotesManager

    repo_path = initialized_adr_repo
    git = Git(cwd=repo_path)
    config_manager = ConfigManager(git)
    config = config_manager.load()
    notes_manager = NotesManager(git, config)

    # Create sample ADRs with valid date-prefixed IDs
    sample_adrs = [
        ADR(
            metadata=ADRMetadata(
                id="20250110-use-postgresql",
                title="Use PostgreSQL for Database",
                date=date(2025, 1, 10),
                status=ADRStatus.ACCEPTED,
                deciders=["Alice", "Bob"],
                tags=["database", "infrastructure"],
            ),
            content="## Context\n\nWe need a relational database.\n\n## Decision\n\nUse PostgreSQL.\n\n## Consequences\n\nGood for complex queries.",
        ),
        ADR(
            metadata=ADRMetadata(
                id="20250112-use-redis",
                title="Use Redis for Caching",
                date=date(2025, 1, 12),
                status=ADRStatus.ACCEPTED,
                deciders=["Alice"],
                tags=["caching", "infrastructure"],
            ),
            content="## Context\n\nNeed fast caching.\n\n## Decision\n\nUse Redis.\n\n## Consequences\n\nImproved performance.",
        ),
        ADR(
            metadata=ADRMetadata(
                id="20250115-use-react",
                title="Use React for Frontend",
                date=date(2025, 1, 15),
                status=ADRStatus.PROPOSED,
                deciders=["Charlie"],
                tags=["frontend", "ui"],
            ),
            content="## Context\n\nNeed a frontend framework.\n\n## Decision\n\nUse React.\n\n## Consequences\n\nComponent-based architecture.",
        ),
    ]

    for adr in sample_adrs:
        notes_manager.add(adr)

    yield repo_path


# =============================================================================
# Git Object Fixtures
# =============================================================================


@pytest.fixture
def git(temp_git_repo: Path) -> Git:
    """Create a Git wrapper for a temp repo."""
    return Git(cwd=temp_git_repo)


@pytest.fixture
def git_with_commit(temp_git_repo_with_commit: Path) -> Git:
    """Create a Git wrapper for a repo with a commit."""
    return Git(cwd=temp_git_repo_with_commit)


# =============================================================================
# Config Fixtures
# =============================================================================


@pytest.fixture
def default_config() -> Config:
    """Create a default configuration."""
    return Config()


@pytest.fixture
def ai_config() -> Config:
    """Create a configuration with AI enabled (for mocking)."""
    return Config(
        ai_provider="openai",
        ai_model="gpt-4o-mini",
        ai_temperature=0.7,
    )


# =============================================================================
# Sample Data Fixtures
# =============================================================================


@pytest.fixture
def sample_adr() -> ADR:
    """Create a sample ADR for testing."""
    today = date.today()
    return ADR(
        metadata=ADRMetadata(
            id=f"{today.strftime('%Y%m%d')}-sample-adr",
            title="Sample ADR for Testing",
            date=today,
            status=ADRStatus.PROPOSED,
            deciders=["Test User"],
            tags=["test"],
        ),
        content="## Context\n\nTest context.\n\n## Decision\n\nTest decision.\n\n## Consequences\n\nTest consequences.",
    )


@pytest.fixture
def sample_adrs() -> list[ADR]:
    """Create multiple sample ADRs for testing."""
    return [
        ADR(
            metadata=ADRMetadata(
                id=f"2025010{i + 1}-adr-{i}",
                title=f"ADR {i}",
                date=date(2025, 1, i + 1),
                status=ADRStatus.ACCEPTED if i % 2 == 0 else ADRStatus.PROPOSED,
                tags=[f"tag{i}"],
            ),
            content=f"## Context\n\nContext {i}.\n\n## Decision\n\nDecision {i}.",
        )
        for i in range(5)
    ]


# =============================================================================
# Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_llm() -> MagicMock:
    """Create a mock LLM for AI service tests."""
    mock = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Mocked AI response content"
    mock.invoke.return_value = mock_response
    return mock


@pytest.fixture
def mock_ai_service(ai_config: Config, mock_llm: MagicMock) -> MagicMock:
    """Create a mock AI service."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        from git_adr.ai import AIService

        service = AIService(ai_config)
        # NOTE: Accessing _llm is intentional for test injection.
        # This allows isolated testing without real API calls.
        service._llm = mock_llm
        return service


# =============================================================================
# CLI Runner Fixtures
# =============================================================================


@pytest.fixture
def cli_runner():
    """Create a CLI runner for command tests."""
    from typer.testing import CliRunner

    return CliRunner()


@pytest.fixture
def invoke_cli(cli_runner, initialized_adr_repo: Path):
    """Create a function to invoke CLI commands in an initialized repo.

    Returns:
        A callable that invokes CLI commands.
    """
    from git_adr.cli import app

    def _invoke(*args: str, **kwargs):
        return cli_runner.invoke(app, list(args), **kwargs)

    return _invoke


# =============================================================================
# Temporary Directory Fixtures
# =============================================================================


@pytest.fixture
def test_tmp_dir(tmp_path: Path) -> Iterator[Path]:
    """Create a temporary directory for test artifacts.

    Uses GIT_ADR_TEST_TMP env var if set (for Makefile integration).
    """
    env_tmp = os.environ.get("GIT_ADR_TEST_TMP")
    if env_tmp:
        test_dir = Path(env_tmp) / f"test_{os.getpid()}"
        test_dir.mkdir(parents=True, exist_ok=True)
        yield test_dir
        shutil.rmtree(test_dir, ignore_errors=True)
    else:
        yield tmp_path


# =============================================================================
# AI Isolation Fixtures
# =============================================================================


def _disable_ai_for_repo(repo: Path) -> Path:
    """Disable AI configuration for the given repository.

    Helper function to ensure consistent AI disabling across fixtures.
    Sets empty provider and model to override any global config.
    """
    git = Git(cwd=repo)
    git.config_set("adr.ai.provider", "")
    git.config_set("adr.ai.model", "")
    return repo


@pytest.fixture
def no_ai_config_repo(adr_repo_with_data: Path) -> Path:
    """Repository with sample data and AI explicitly disabled.

    Use this fixture when testing AI commands that should fail due to
    no AI provider being configured. This overrides any global git config
    that might have adr.ai.provider set.
    """
    return _disable_ai_for_repo(adr_repo_with_data)


@pytest.fixture
def no_ai_initialized_repo(initialized_adr_repo: Path) -> Path:
    """Initialized repository with AI explicitly disabled (no sample data).

    Use this when you need an initialized ADR repo without sample data
    and without AI provider configured.
    """
    return _disable_ai_for_repo(initialized_adr_repo)


@pytest.fixture
def create_commit(temp_git_repo_with_commit: Path) -> Callable[[str], str]:
    """Create a helper function to add commits.

    Returns:
        A callable that creates commits and returns the commit SHA.
    """

    def _create_commit(message: str) -> str:
        repo = temp_git_repo_with_commit

        # Create a unique file
        import uuid

        filename = f"file_{uuid.uuid4().hex[:8]}.txt"
        (repo / filename).write_text(f"Content for: {message}\n")

        subprocess.run(
            ["git", "add", "."],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=repo,
            check=True,
            capture_output=True,
        )

        # Get commit SHA
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    return _create_commit
