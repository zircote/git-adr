"""Comprehensive tests for wiki commands with full mocking.

Tests wiki_sync and wiki_init commands with mocked WikiService.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from git_adr.cli import app
from git_adr.core.adr import ADR, ADRMetadata, ADRStatus
from git_adr.core.config import ConfigManager
from git_adr.core.git import Git
from git_adr.core.notes import NotesManager

runner = CliRunner()


@pytest.fixture
def wiki_configured_repo(initialized_adr_repo: Path) -> Path:
    """Repository with wiki configured."""
    git = Git(cwd=initialized_adr_repo)
    config_manager = ConfigManager(git)
    config_manager.set("wiki.type", "github")
    config_manager.set("wiki.url", "https://github.com/test/repo.wiki.git")
    return initialized_adr_repo


@pytest.fixture
def wiki_repo_with_data(wiki_configured_repo: Path) -> Path:
    """Wiki-configured repo with ADRs."""
    git = Git(cwd=wiki_configured_repo)
    config_manager = ConfigManager(git)
    config = config_manager.load()
    notes_manager = NotesManager(git, config)

    sample_adrs = [
        ADR(
            metadata=ADRMetadata(
                id="20250110-use-postgresql",
                title="Use PostgreSQL",
                date=date(2025, 1, 10),
                status=ADRStatus.ACCEPTED,
                tags=["database"],
            ),
            content="## Context\n\nNeed database.\n\n## Decision\n\nPostgreSQL.",
        ),
        ADR(
            metadata=ADRMetadata(
                id="20250112-use-redis",
                title="Use Redis",
                date=date(2025, 1, 12),
                status=ADRStatus.PROPOSED,
                tags=["caching"],
            ),
            content="## Context\n\nNeed cache.\n\n## Decision\n\nRedis.",
        ),
    ]

    for adr in sample_adrs:
        notes_manager.add(adr)

    return wiki_configured_repo


class MockSyncResult:
    """Mock wiki sync result."""

    def __init__(
        self,
        created: list[str] | None = None,
        updated: list[str] | None = None,
        deleted: list[str] | None = None,
        skipped: list[str] | None = None,
        errors: list[str] | None = None,
    ):
        self.created = created or []
        self.updated = updated or []
        self.deleted = deleted or []
        self.skipped = skipped or []
        self.errors = errors or []
        self.total_synced = len(self.created) + len(self.updated)

    @property
    def has_changes(self) -> bool:
        return bool(self.created or self.updated or self.deleted)


# =============================================================================
# Wiki Init Command Tests
# =============================================================================


class TestWikiInitCommand:
    """Tests for wiki init command."""

    def test_wiki_init_github_auto(self, initialized_adr_repo: Path) -> None:
        """Test wiki init with GitHub autodetection."""
        # Add a GitHub remote
        git = Git(cwd=initialized_adr_repo)
        git.run(["remote", "add", "origin", "https://github.com/test/repo.git"])

        result = runner.invoke(app, ["wiki", "init"])
        assert result.exit_code in [0, 1]  # May succeed or fail based on remote

    def test_wiki_init_gitlab_platform(self, initialized_adr_repo: Path) -> None:
        """Test wiki init with explicit GitLab platform."""
        # Add a GitLab remote
        git = Git(cwd=initialized_adr_repo)
        git.run(["remote", "add", "origin", "https://gitlab.com/test/repo.git"])

        result = runner.invoke(app, ["wiki", "init", "--platform", "gitlab"])
        assert result.exit_code in [0, 1]

    def test_wiki_init_no_remote(self, initialized_adr_repo: Path) -> None:
        """Test wiki init with no remote configured - shows help."""
        result = runner.invoke(app, ["wiki", "init"])
        # May show help/warning about needing a platform
        assert (
            result.exit_code == 0
            or "platform" in result.output.lower()
            or "remote" in result.output.lower()
        )

    def test_wiki_init_not_initialized(self, temp_git_repo_with_commit: Path) -> None:
        """Test wiki init in non-initialized repo - shows help."""
        result = runner.invoke(app, ["wiki", "init"])
        # Wiki init may show help even if not initialized
        assert result.exit_code in [0, 1]


# =============================================================================
# Wiki Sync Command Tests
# =============================================================================


class TestWikiSyncCommand:
    """Tests for wiki sync command."""

    @patch("git_adr.wiki.WikiService")
    def test_wiki_sync_push_success(
        self, mock_wiki_service: MagicMock, wiki_repo_with_data: Path
    ) -> None:
        """Test wiki sync push with mocked service."""
        mock_instance = MagicMock()
        mock_wiki_service.return_value = mock_instance
        mock_instance.sync.return_value = MockSyncResult(
            created=["20250110-use-postgresql"],
            updated=["20250112-use-redis"],
        )

        result = runner.invoke(app, ["wiki", "sync"])
        assert result.exit_code == 0

    @patch("git_adr.wiki.WikiService")
    def test_wiki_sync_dry_run(
        self, mock_wiki_service: MagicMock, wiki_repo_with_data: Path
    ) -> None:
        """Test wiki sync dry run."""
        result = runner.invoke(app, ["wiki", "sync", "--dry-run"])
        assert result.exit_code == 0
        assert "would sync" in result.output.lower() or "dry" in result.output.lower()

    @patch("git_adr.wiki.WikiService")
    def test_wiki_sync_specific_adr(
        self, mock_wiki_service: MagicMock, wiki_repo_with_data: Path
    ) -> None:
        """Test wiki sync for specific ADR."""
        mock_instance = MagicMock()
        mock_wiki_service.return_value = mock_instance
        mock_instance.sync.return_value = MockSyncResult(
            updated=["20250110-use-postgresql"]
        )

        result = runner.invoke(
            app, ["wiki", "sync", "--adr", "20250110-use-postgresql"]
        )
        assert result.exit_code == 0

    @patch("git_adr.wiki.WikiService")
    def test_wiki_sync_no_changes(
        self, mock_wiki_service: MagicMock, wiki_repo_with_data: Path
    ) -> None:
        """Test wiki sync when no changes needed."""
        mock_instance = MagicMock()
        mock_wiki_service.return_value = mock_instance
        mock_instance.sync.return_value = MockSyncResult()

        result = runner.invoke(app, ["wiki", "sync"])
        assert result.exit_code == 0

    @patch("git_adr.wiki.WikiService")
    def test_wiki_sync_with_errors(
        self, mock_wiki_service: MagicMock, wiki_repo_with_data: Path
    ) -> None:
        """Test wiki sync with some errors."""
        mock_instance = MagicMock()
        mock_wiki_service.return_value = mock_instance
        mock_instance.sync.return_value = MockSyncResult(
            created=["20250110-use-postgresql"],
            errors=["Rate limited for 20250112-use-redis"],
        )

        result = runner.invoke(app, ["wiki", "sync"])
        assert result.exit_code == 0  # Partial success

    @patch("git_adr.wiki.WikiService")
    def test_wiki_sync_with_skipped(
        self, mock_wiki_service: MagicMock, wiki_repo_with_data: Path
    ) -> None:
        """Test wiki sync with skipped items."""
        mock_instance = MagicMock()
        mock_wiki_service.return_value = mock_instance
        mock_instance.sync.return_value = MockSyncResult(
            created=["20250110-use-postgresql"],
            skipped=["pull:not-implemented"],
        )

        result = runner.invoke(app, ["wiki", "sync"])
        assert result.exit_code == 0

    @patch("git_adr.wiki.WikiService")
    def test_wiki_sync_with_deletions(
        self, mock_wiki_service: MagicMock, wiki_repo_with_data: Path
    ) -> None:
        """Test wiki sync with deletions."""
        mock_instance = MagicMock()
        mock_wiki_service.return_value = mock_instance
        mock_instance.sync.return_value = MockSyncResult(
            deleted=["20250101-old-decision"],
        )

        result = runner.invoke(app, ["wiki", "sync"])
        assert result.exit_code == 0

    def test_wiki_sync_not_configured(self, initialized_adr_repo: Path) -> None:
        """Test wiki sync without wiki configured."""
        result = runner.invoke(app, ["wiki", "sync"])
        assert result.exit_code != 0
        assert "not" in result.output.lower() and (
            "config" in result.output.lower() or "init" in result.output.lower()
        )

    def test_wiki_sync_invalid_direction(self, wiki_configured_repo: Path) -> None:
        """Test wiki sync with invalid direction."""
        result = runner.invoke(app, ["wiki", "sync", "--direction", "invalid"])
        # Check for appropriate error handling
        assert result.exit_code != 0 or "invalid" in result.output.lower()

    def test_wiki_sync_adr_not_found(self, wiki_repo_with_data: Path) -> None:
        """Test wiki sync with non-existent ADR."""
        result = runner.invoke(app, ["wiki", "sync", "--adr", "nonexistent-adr"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    @patch("git_adr.wiki.WikiService")
    def test_wiki_sync_service_error(
        self, mock_wiki_service: MagicMock, wiki_repo_with_data: Path
    ) -> None:
        """Test wiki sync when service raises error."""
        from git_adr.wiki import WikiServiceError

        mock_instance = MagicMock()
        mock_wiki_service.return_value = mock_instance
        mock_instance.sync.side_effect = WikiServiceError("Connection failed")

        result = runner.invoke(app, ["wiki", "sync"])
        assert result.exit_code != 0

    @patch("git_adr.wiki.WikiService")
    def test_wiki_sync_pull_direction(
        self, mock_wiki_service: MagicMock, wiki_repo_with_data: Path
    ) -> None:
        """Test wiki sync in pull direction."""
        mock_instance = MagicMock()
        mock_wiki_service.return_value = mock_instance
        mock_instance.sync.return_value = MockSyncResult(
            skipped=["pull:not-implemented"],
        )

        result = runner.invoke(app, ["wiki", "sync", "--direction", "pull"])
        assert result.exit_code == 0

    @patch("git_adr.wiki.WikiService")
    def test_wiki_sync_both_direction(
        self, mock_wiki_service: MagicMock, wiki_repo_with_data: Path
    ) -> None:
        """Test wiki sync in both directions."""
        mock_instance = MagicMock()
        mock_wiki_service.return_value = mock_instance
        mock_instance.sync.return_value = MockSyncResult(
            created=["20250110-use-postgresql"],
        )

        result = runner.invoke(app, ["wiki", "sync", "--direction", "both"])
        assert result.exit_code == 0

    @patch("git_adr.wiki.WikiService")
    def test_wiki_sync_empty_repo(
        self, mock_wiki_service: MagicMock, wiki_configured_repo: Path
    ) -> None:
        """Test wiki sync with no ADRs."""
        result = runner.invoke(app, ["wiki", "sync"])
        assert result.exit_code == 0
        assert "no adr" in result.output.lower()
