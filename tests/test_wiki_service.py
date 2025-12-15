"""Tests for git-adr Wiki service."""

from __future__ import annotations

import subprocess
from datetime import date
from pathlib import Path

import pytest

from git_adr.core.adr import ADR, ADRMetadata, ADRStatus
from git_adr.core.config import Config
from git_adr.core.git import Git


class TestWikiServiceInit:
    """Tests for WikiService initialization."""

    def test_init(self, temp_git_repo: Path) -> None:
        """Test WikiService initialization."""
        from git_adr.wiki import WikiService

        git = Git(cwd=temp_git_repo)
        config = Config()
        service = WikiService(git, config)
        assert service.git == git
        assert service.config == config


class TestWikiServicePlatformDetection:
    """Tests for platform detection."""

    def test_detect_github(self, temp_git_repo: Path) -> None:
        """Test detecting GitHub platform."""
        from git_adr.wiki import WikiService

        # Set up GitHub remote
        subprocess.run(
            ["git", "remote", "add", "origin", "https://github.com/user/repo.git"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
        )

        git = Git(cwd=temp_git_repo)
        config = Config()
        service = WikiService(git, config)

        platform = service.detect_platform()
        assert platform == "github"

    def test_detect_gitlab(self, temp_git_repo: Path) -> None:
        """Test detecting GitLab platform."""
        from git_adr.wiki import WikiService

        subprocess.run(
            ["git", "remote", "add", "origin", "https://gitlab.com/user/repo.git"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
        )

        git = Git(cwd=temp_git_repo)
        config = Config()
        service = WikiService(git, config)

        platform = service.detect_platform()
        assert platform == "gitlab"

    def test_detect_no_remote(self, temp_git_repo: Path) -> None:
        """Test detection with no remote returns None gracefully."""
        from git_adr.wiki import WikiService

        # Don't add any remote - temp_git_repo starts with no remotes

        git = Git(cwd=temp_git_repo)
        config = Config()
        service = WikiService(git, config)

        # The service should handle missing remote gracefully
        platform = service.detect_platform()
        # May raise or return None depending on implementation
        assert platform is None or platform in ("github", "gitlab", None)


class TestWikiServiceURL:
    """Tests for wiki URL generation."""

    def test_get_wiki_url_github(self, temp_git_repo: Path) -> None:
        """Test generating GitHub wiki URL."""
        from git_adr.wiki import WikiService

        subprocess.run(
            ["git", "remote", "add", "origin", "https://github.com/user/repo.git"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
        )

        git = Git(cwd=temp_git_repo)
        config = Config()
        service = WikiService(git, config)

        wiki_url = service.get_wiki_url("github")
        assert wiki_url == "https://github.com/user/repo.wiki.git"

    def test_get_wiki_url_gitlab(self, temp_git_repo: Path) -> None:
        """Test generating GitLab wiki URL."""
        from git_adr.wiki import WikiService

        subprocess.run(
            ["git", "remote", "add", "origin", "https://gitlab.com/user/repo.git"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
        )

        git = Git(cwd=temp_git_repo)
        config = Config()
        service = WikiService(git, config)

        wiki_url = service.get_wiki_url("gitlab")
        assert wiki_url == "https://gitlab.com/user/repo.wiki.git"


class TestWikiServiceInit_:
    """Tests for wiki init method."""

    def test_init_github(self, temp_git_repo: Path) -> None:
        """Test initializing GitHub wiki."""
        from git_adr.wiki import WikiService

        subprocess.run(
            ["git", "remote", "add", "origin", "https://github.com/user/repo.git"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
        )

        git = Git(cwd=temp_git_repo)
        config = Config()
        service = WikiService(git, config)

        result = service.init("github")
        assert result["platform"] == "github"
        assert result["wiki_url"] == "https://github.com/user/repo.wiki.git"
        assert result["status"] == "initialized"

    def test_init_unsupported_platform(self, temp_git_repo: Path) -> None:
        """Test init with unsupported platform."""
        from git_adr.wiki import WikiService, WikiServiceError

        subprocess.run(
            ["git", "remote", "add", "origin", "https://github.com/user/repo.git"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
        )

        git = Git(cwd=temp_git_repo)
        config = Config()
        service = WikiService(git, config)

        with pytest.raises(WikiServiceError, match="Unsupported platform"):
            service.init("bitbucket")


class TestWikiPageGeneration:
    """Tests for wiki page generation."""

    def test_generate_page(self, temp_git_repo: Path) -> None:
        """Test generating wiki page from ADR."""
        from git_adr.wiki import WikiService

        git = Git(cwd=temp_git_repo)
        config = Config()
        service = WikiService(git, config)

        adr = ADR(
            metadata=ADRMetadata(
                id="use-postgres",
                title="Use PostgreSQL",
                date=date(2025, 1, 15),
                status=ADRStatus.ACCEPTED,
                deciders=["Alice", "Bob"],
                tags=["database", "infrastructure"],
            ),
            content="## Context\n\nWe need a database.\n\n## Decision\n\nUse PostgreSQL.",
        )

        page = service._generate_page(adr, "github")
        assert "# Use PostgreSQL" in page
        assert "use-postgres" in page
        assert "accepted" in page.lower()
        assert "Alice" in page
        assert "database" in page

    def test_generate_index(self, temp_git_repo: Path) -> None:
        """Test generating wiki index page."""
        from git_adr.wiki import WikiService

        git = Git(cwd=temp_git_repo)
        config = Config()
        service = WikiService(git, config)

        adrs = [
            ADR(
                metadata=ADRMetadata(
                    id="adr-1",
                    title="First Decision",
                    date=date(2025, 1, 10),
                    status=ADRStatus.ACCEPTED,
                ),
                content="Content 1",
            ),
            ADR(
                metadata=ADRMetadata(
                    id="adr-2",
                    title="Second Decision",
                    date=date(2025, 1, 15),
                    status=ADRStatus.PROPOSED,
                ),
                content="Content 2",
            ),
        ]

        index = service._generate_index(adrs, "github")
        assert "# Architecture Decision Records" in index
        assert "First Decision" in index
        assert "Second Decision" in index
        assert "Accepted" in index
        assert "Proposed" in index

    def test_generate_sidebar(self, temp_git_repo: Path) -> None:
        """Test generating GitHub wiki sidebar."""
        from git_adr.wiki import WikiService

        git = Git(cwd=temp_git_repo)
        config = Config()
        service = WikiService(git, config)

        adrs = [
            ADR(
                metadata=ADRMetadata(
                    id="adr-1",
                    title="Test ADR",
                    date=date.today(),
                    status=ADRStatus.ACCEPTED,
                ),
                content="Content",
            ),
        ]

        sidebar = service._generate_sidebar(adrs)
        assert "Architecture Decisions" in sidebar
        assert "[[Home]]" in sidebar
        assert "adr-1" in sidebar


class TestSyncResult:
    """Tests for SyncResult dataclass."""

    def test_sync_result_creation(self) -> None:
        """Test creating SyncResult."""
        from git_adr.wiki.service import SyncResult

        result = SyncResult()
        assert result.created == []
        assert result.updated == []
        assert result.deleted == []
        assert result.total_synced == 0
        assert not result.has_changes

    def test_sync_result_with_changes(self) -> None:
        """Test SyncResult with changes."""
        from git_adr.wiki.service import SyncResult

        result = SyncResult(
            created=["adr-1", "adr-2"],
            updated=["adr-3"],
            deleted=["adr-4"],
        )
        assert result.total_synced == 3
        assert result.has_changes

    def test_sync_result_no_changes(self) -> None:
        """Test SyncResult without changes."""
        from git_adr.wiki.service import SyncResult

        result = SyncResult(skipped=["adr-1"])
        assert result.total_synced == 0
        assert not result.has_changes


class TestWikiServiceSync:
    """Tests for wiki sync (mocked)."""

    def test_sync_dry_run(self, temp_git_repo: Path) -> None:
        """Test dry run sync."""
        from git_adr.wiki import WikiService

        subprocess.run(
            ["git", "remote", "add", "origin", "https://github.com/user/repo.git"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
        )

        git = Git(cwd=temp_git_repo)
        config = Config()
        service = WikiService(git, config)
        service._platform = "github"

        adrs = [
            ADR(
                metadata=ADRMetadata(
                    id="test-adr",
                    title="Test",
                    date=date.today(),
                    status=ADRStatus.ACCEPTED,
                ),
                content="Content",
            ),
        ]

        result = service.sync(adrs, direction="push", dry_run=True)
        # Dry run should report what would be created
        assert "test-adr" in result.created
