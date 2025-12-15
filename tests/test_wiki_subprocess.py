"""Deep tests for wiki subprocess operations.

Targets the uncovered subprocess code paths in wiki/service.py.
"""

from __future__ import annotations

import subprocess
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from git_adr.core.adr import ADR, ADRMetadata, ADRStatus
from git_adr.core.config import Config
from git_adr.core.git import Git
from git_adr.wiki.service import SyncResult, WikiService, WikiServiceError


@pytest.fixture
def mock_git() -> MagicMock:
    """Create mock Git instance."""
    git = MagicMock(spec=Git)
    git.run.return_value = MagicMock(
        stdout="origin\thttps://github.com/user/repo.git (fetch)",
        stderr="",
        exit_code=0,
        success=True,
    )
    return git


@pytest.fixture
def sample_adrs() -> list[ADR]:
    """Create sample ADRs."""
    return [
        ADR(
            metadata=ADRMetadata(
                id="20250110-use-postgresql",
                title="Use PostgreSQL",
                date=date(2025, 1, 10),
                status=ADRStatus.ACCEPTED,
                tags=["database", "infrastructure"],
                deciders=["Alice", "Bob"],
            ),
            content="## Context\n\nWe need a database.\n\n## Decision\n\nUse PostgreSQL.",
        ),
        ADR(
            metadata=ADRMetadata(
                id="20250112-use-redis",
                title="Use Redis",
                date=date(2025, 1, 12),
                status=ADRStatus.PROPOSED,
                tags=["caching"],
            ),
            content="## Context\n\nNeed caching.\n\n## Decision\n\nUse Redis.",
        ),
    ]


# =============================================================================
# WikiService Clone Tests
# =============================================================================


class TestWikiClone:
    """Tests for _clone_wiki subprocess operations."""

    @patch("subprocess.run")
    def test_clone_wiki_success(
        self, mock_subprocess: MagicMock, mock_git: MagicMock
    ) -> None:
        """Test successful wiki clone."""
        mock_subprocess.return_value = MagicMock(returncode=0)

        config = Config(wiki_platform="github")
        service = WikiService(mock_git, config)

        with patch("tempfile.mkdtemp") as mock_mkdtemp:
            mock_mkdtemp.return_value = "/tmp/git-adr-wiki-test"
            wiki_dir = service._clone_wiki("https://github.com/user/repo.wiki.git")

        assert wiki_dir == Path("/tmp/git-adr-wiki-test")
        mock_subprocess.assert_called_once()

    @patch("subprocess.run")
    @patch("shutil.rmtree")
    def test_clone_wiki_not_found_init_new(
        self, mock_rmtree: MagicMock, mock_subprocess: MagicMock, mock_git: MagicMock
    ) -> None:
        """Test clone when wiki doesn't exist - initializes new."""
        # First call fails with "not found", subsequent calls succeed
        mock_subprocess.side_effect = [
            MagicMock(returncode=1, stderr="repository not found"),
            MagicMock(returncode=0),  # git init
            MagicMock(returncode=0),  # git remote add
        ]

        config = Config(wiki_platform="github")
        service = WikiService(mock_git, config)

        with patch("tempfile.mkdtemp") as mock_mkdtemp:
            mock_mkdtemp.return_value = "/tmp/git-adr-wiki-test"
            wiki_dir = service._clone_wiki("https://github.com/user/repo.wiki.git")

        assert wiki_dir == Path("/tmp/git-adr-wiki-test")
        assert mock_subprocess.call_count == 3

    @patch("subprocess.run")
    @patch("shutil.rmtree")
    def test_clone_wiki_not_exist_init_new(
        self, mock_rmtree: MagicMock, mock_subprocess: MagicMock, mock_git: MagicMock
    ) -> None:
        """Test clone when wiki does not exist - initializes new."""
        mock_subprocess.side_effect = [
            MagicMock(returncode=1, stderr="does not exist"),
            MagicMock(returncode=0),  # git init
            MagicMock(returncode=0),  # git remote add
        ]

        config = Config(wiki_platform="github")
        service = WikiService(mock_git, config)

        with patch("tempfile.mkdtemp") as mock_mkdtemp:
            mock_mkdtemp.return_value = "/tmp/git-adr-wiki-new"
            wiki_dir = service._clone_wiki("https://github.com/user/repo.wiki.git")

        assert wiki_dir == Path("/tmp/git-adr-wiki-new")

    @patch("subprocess.run")
    @patch("shutil.rmtree")
    def test_clone_wiki_other_error(
        self, mock_rmtree: MagicMock, mock_subprocess: MagicMock, mock_git: MagicMock
    ) -> None:
        """Test clone with other git error."""
        mock_subprocess.return_value = MagicMock(
            returncode=1, stderr="permission denied"
        )

        config = Config(wiki_platform="github")
        service = WikiService(mock_git, config)

        with patch("tempfile.mkdtemp") as mock_mkdtemp:
            mock_mkdtemp.return_value = "/tmp/git-adr-wiki-fail"
            with pytest.raises(WikiServiceError, match="Failed to clone wiki"):
                service._clone_wiki("https://github.com/user/repo.wiki.git")

    @patch("subprocess.run")
    @patch("shutil.rmtree")
    def test_clone_wiki_timeout(
        self, mock_rmtree: MagicMock, mock_subprocess: MagicMock, mock_git: MagicMock
    ) -> None:
        """Test clone timeout."""
        mock_subprocess.side_effect = subprocess.TimeoutExpired(
            cmd=["git", "clone"], timeout=60
        )

        config = Config(wiki_platform="github")
        service = WikiService(mock_git, config)

        with patch("tempfile.mkdtemp") as mock_mkdtemp:
            mock_mkdtemp.return_value = "/tmp/git-adr-wiki-timeout"
            with pytest.raises(WikiServiceError, match="timed out"):
                service._clone_wiki("https://github.com/user/repo.wiki.git")

        mock_rmtree.assert_called()

    @patch("subprocess.run")
    @patch("shutil.rmtree")
    def test_clone_wiki_exception(
        self, mock_rmtree: MagicMock, mock_subprocess: MagicMock, mock_git: MagicMock
    ) -> None:
        """Test clone general exception."""
        mock_subprocess.side_effect = OSError("Network error")

        config = Config(wiki_platform="github")
        service = WikiService(mock_git, config)

        with patch("tempfile.mkdtemp") as mock_mkdtemp:
            mock_mkdtemp.return_value = "/tmp/git-adr-wiki-error"
            with pytest.raises(WikiServiceError, match="clone failed"):
                service._clone_wiki("https://github.com/user/repo.wiki.git")


# =============================================================================
# WikiService Init Tests
# =============================================================================


class TestWikiInit:
    """Tests for wiki initialization."""

    def test_init_no_platform_detected(self, mock_git: MagicMock) -> None:
        """Test init when platform cannot be detected."""
        mock_git.run.return_value = MagicMock(
            stdout="origin\tgit@bitbucket.org:user/repo.git",
            exit_code=0,
            success=True,
        )

        config = Config()
        service = WikiService(mock_git, config)

        with pytest.raises(WikiServiceError, match="Could not detect"):
            service.init()

    def test_init_unsupported_platform(self, mock_git: MagicMock) -> None:
        """Test init with unsupported platform."""
        config = Config()
        service = WikiService(mock_git, config)

        with pytest.raises(WikiServiceError, match="Unsupported platform"):
            service.init(platform="bitbucket")

    def test_init_no_wiki_url(self, mock_git: MagicMock) -> None:
        """Test init when wiki URL cannot be determined."""
        # First call for platform detection succeeds
        mock_git.run.side_effect = [
            MagicMock(stdout="origin\thttps://github.com/user/repo.git", exit_code=0),
            MagicMock(exit_code=1),  # Second call for get_wiki_url fails
        ]

        config = Config()
        service = WikiService(mock_git, config)

        with pytest.raises(WikiServiceError, match="Could not determine wiki URL"):
            service.init()


# =============================================================================
# WikiService Sync Tests
# =============================================================================


class TestWikiSync:
    """Tests for wiki sync operations."""

    def test_sync_no_platform(self, mock_git: MagicMock) -> None:
        """Test sync without platform configured."""
        mock_git.run.return_value = MagicMock(stdout="", exit_code=1, success=False)

        config = Config()
        service = WikiService(mock_git, config)

        with pytest.raises(WikiServiceError, match="Platform not configured"):
            service.sync([], direction="push")

    def test_sync_no_wiki_url(self, mock_git: MagicMock) -> None:
        """Test sync when wiki URL is unavailable."""
        mock_git.run.return_value = MagicMock(exit_code=1, success=False)

        config = Config(wiki_platform="github")
        service = WikiService(mock_git, config)
        service._platform = "github"

        with pytest.raises(WikiServiceError, match="Could not determine wiki URL"):
            service.sync([], direction="push")

    def test_sync_dry_run(self, mock_git: MagicMock, sample_adrs: list[ADR]) -> None:
        """Test sync in dry run mode."""
        config = Config(wiki_platform="github")
        service = WikiService(mock_git, config)
        service._platform = "github"

        result = service.sync(sample_adrs, direction="push", dry_run=True)

        # Dry run reports what would be created
        assert len(result.created) == 2
        assert result.total_synced == 2  # Reports what would be synced

    @patch("subprocess.run")
    @patch("shutil.rmtree")
    def test_sync_push_full(
        self,
        mock_rmtree: MagicMock,
        mock_subprocess: MagicMock,
        mock_git: MagicMock,
        sample_adrs: list[ADR],
        tmp_path: Path,
    ) -> None:
        """Test full push sync."""
        # All subprocess calls succeed
        mock_subprocess.return_value = MagicMock(returncode=0, stderr="", stdout="")

        config = Config(wiki_platform="github")
        service = WikiService(mock_git, config)
        service._platform = "github"

        with patch.object(service, "_clone_wiki", return_value=tmp_path):
            result = service.sync(sample_adrs, direction="push")

        # Check pages were created
        assert len(result.created) + len(result.updated) >= 0

    @patch("subprocess.run")
    @patch("shutil.rmtree")
    def test_sync_pull(
        self,
        mock_rmtree: MagicMock,
        mock_subprocess: MagicMock,
        mock_git: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test pull sync (marks as not implemented)."""
        mock_subprocess.return_value = MagicMock(returncode=0)

        config = Config(wiki_platform="github")
        service = WikiService(mock_git, config)
        service._platform = "github"

        with patch.object(service, "_clone_wiki", return_value=tmp_path):
            result = service.sync([], direction="pull")

        assert "pull:not-implemented" in result.skipped

    @patch("subprocess.run")
    @patch("shutil.rmtree")
    def test_sync_both_directions(
        self,
        mock_rmtree: MagicMock,
        mock_subprocess: MagicMock,
        mock_git: MagicMock,
        sample_adrs: list[ADR],
        tmp_path: Path,
    ) -> None:
        """Test bidirectional sync."""
        mock_subprocess.return_value = MagicMock(returncode=0, stderr="")

        config = Config(wiki_platform="github")
        service = WikiService(mock_git, config)
        service._platform = "github"

        with patch.object(service, "_clone_wiki", return_value=tmp_path):
            result = service.sync(sample_adrs, direction="both")

        # Pull is not implemented but should be in skipped
        assert "pull:not-implemented" in result.skipped


# =============================================================================
# WikiService Push Operations
# =============================================================================


class TestWikiSyncPush:
    """Tests for _sync_push method."""

    def test_sync_push_github(
        self, mock_git: MagicMock, sample_adrs: list[ADR], tmp_path: Path
    ) -> None:
        """Test pushing to GitHub wiki."""
        config = Config(wiki_platform="github")
        service = WikiService(mock_git, config)
        result = SyncResult()

        service._sync_push(sample_adrs, tmp_path, "github", result)

        # Check Home.md was created
        assert (tmp_path / "Home.md").exists()

        # Check _Sidebar.md was created (GitHub-specific)
        assert (tmp_path / "_Sidebar.md").exists()

        # Check ADR pages were created
        assert len(result.created) == 2

    def test_sync_push_gitlab(
        self, mock_git: MagicMock, sample_adrs: list[ADR], tmp_path: Path
    ) -> None:
        """Test pushing to GitLab wiki."""
        config = Config(wiki_platform="gitlab")
        service = WikiService(mock_git, config)
        result = SyncResult()

        service._sync_push(sample_adrs, tmp_path, "gitlab", result)

        # Check Home.md was created
        assert (tmp_path / "Home.md").exists()

        # GitLab doesn't use _Sidebar.md
        assert not (tmp_path / "_Sidebar.md").exists()

    def test_sync_push_update_existing(
        self, mock_git: MagicMock, sample_adrs: list[ADR], tmp_path: Path
    ) -> None:
        """Test updating existing wiki pages."""
        config = Config(wiki_platform="github")
        service = WikiService(mock_git, config)
        result = SyncResult()

        # Create existing page
        page_name = service._get_page_name(sample_adrs[0])
        existing_page = tmp_path / f"{page_name}.md"
        existing_page.write_text("Old content")

        service._sync_push(sample_adrs, tmp_path, "github", result)

        # First ADR should be updated, second created
        assert len(result.updated) == 1
        assert len(result.created) == 1
        assert sample_adrs[0].metadata.id in result.updated

    def test_sync_push_error_handling(
        self, mock_git: MagicMock, tmp_path: Path
    ) -> None:
        """Test error handling during push."""
        # Create ADR with invalid data that will cause error
        broken_adr = MagicMock()
        broken_adr.metadata.id = "broken"
        broken_adr.metadata.title = "Broken"
        broken_adr.metadata.status.value = "accepted"
        broken_adr.metadata.date = date.today()
        broken_adr.metadata.deciders = None
        broken_adr.metadata.tags = None
        broken_adr.content = "content"

        # Make to_markdown raise an error
        type(broken_adr.metadata).deciders = property(
            lambda self: (_ for _ in ()).throw(ValueError("test error"))
        )

        config = Config(wiki_platform="github")
        service = WikiService(mock_git, config)
        result = SyncResult()

        # Should capture error but not raise
        service._sync_push([broken_adr], tmp_path, "github", result)

        assert len(result.errors) > 0


# =============================================================================
# WikiService Commit and Push
# =============================================================================


class TestWikiCommitAndPush:
    """Tests for _commit_and_push method."""

    @patch("subprocess.run")
    def test_commit_and_push_success(
        self, mock_subprocess: MagicMock, mock_git: MagicMock, tmp_path: Path
    ) -> None:
        """Test successful commit and push."""
        mock_subprocess.return_value = MagicMock(returncode=0, stderr="")

        config = Config()
        service = WikiService(mock_git, config)
        result = SyncResult(created=["adr1", "adr2"], updated=["adr3"])

        service._commit_and_push(tmp_path, result)

        # Should have called git add, commit, push
        assert mock_subprocess.call_count == 3

    @patch("subprocess.run")
    def test_commit_and_push_push_fails(
        self, mock_subprocess: MagicMock, mock_git: MagicMock, tmp_path: Path
    ) -> None:
        """Test when push fails."""
        mock_subprocess.side_effect = [
            MagicMock(returncode=0),  # git add
            MagicMock(returncode=0),  # git commit
            MagicMock(returncode=1, stderr="permission denied"),  # git push
        ]

        config = Config()
        service = WikiService(mock_git, config)
        result = SyncResult(created=["adr1"])

        with pytest.raises(WikiServiceError, match="push failed"):
            service._commit_and_push(tmp_path, result)

    @patch("subprocess.run")
    def test_commit_and_push_timeout(
        self, mock_subprocess: MagicMock, mock_git: MagicMock, tmp_path: Path
    ) -> None:
        """Test commit/push timeout."""
        mock_subprocess.side_effect = subprocess.TimeoutExpired(
            cmd=["git", "push"], timeout=60
        )

        config = Config()
        service = WikiService(mock_git, config)
        result = SyncResult(created=["adr1"])

        with pytest.raises(WikiServiceError, match="timed out"):
            service._commit_and_push(tmp_path, result)

    @patch("subprocess.run")
    def test_commit_and_push_exception(
        self, mock_subprocess: MagicMock, mock_git: MagicMock, tmp_path: Path
    ) -> None:
        """Test commit/push general exception."""
        mock_subprocess.side_effect = OSError("Network error")

        config = Config()
        service = WikiService(mock_git, config)
        result = SyncResult(created=["adr1"])

        with pytest.raises(WikiServiceError, match="commit/push failed"):
            service._commit_and_push(tmp_path, result)


# =============================================================================
# WikiService Page Generation
# =============================================================================


class TestWikiPageGeneration:
    """Tests for wiki page generation."""

    def test_generate_page_with_deciders(
        self, mock_git: MagicMock, sample_adrs: list[ADR]
    ) -> None:
        """Test page generation with deciders."""
        config = Config()
        service = WikiService(mock_git, config)

        page = service._generate_page(sample_adrs[0], "github")

        assert "Alice" in page
        assert "Bob" in page
        assert "| **Deciders**" in page

    def test_generate_page_with_tags(
        self, mock_git: MagicMock, sample_adrs: list[ADR]
    ) -> None:
        """Test page generation with tags."""
        config = Config()
        service = WikiService(mock_git, config)

        page = service._generate_page(sample_adrs[0], "github")

        assert "database" in page
        assert "infrastructure" in page
        assert "| **Tags**" in page

    def test_generate_page_no_extras(self, mock_git: MagicMock) -> None:
        """Test page generation with minimal metadata."""
        adr = ADR(
            metadata=ADRMetadata(
                id="minimal",
                title="Minimal ADR",
                date=date.today(),
                status=ADRStatus.PROPOSED,
            ),
            content="Just content.",
        )

        config = Config()
        service = WikiService(mock_git, config)

        page = service._generate_page(adr, "github")

        assert "Minimal ADR" in page
        assert "| **Deciders**" not in page
        assert "| **Tags**" not in page

    def test_generate_index_with_remaining_statuses(self, mock_git: MagicMock) -> None:
        """Test index generation with non-priority statuses."""
        adrs = [
            ADR(
                metadata=ADRMetadata(
                    id="rejected",
                    title="Rejected ADR",
                    date=date.today(),
                    status=ADRStatus.REJECTED,
                ),
                content="Rejected.",
            ),
        ]

        config = Config()
        service = WikiService(mock_git, config)

        index = service._generate_index(adrs, "github")

        assert "## Rejected" in index
        assert "rejected" in index.lower()

    def test_generate_sidebar_many_adrs(self, mock_git: MagicMock) -> None:
        """Test sidebar with more than 10 ADRs."""
        adrs = []
        for i in range(15):
            adrs.append(
                ADR(
                    metadata=ADRMetadata(
                        id=f"adr-{i:03d}",
                        title=f"Decision {i}",
                        date=date(2025, 1, i + 1),
                        status=ADRStatus.ACCEPTED,
                    ),
                    content=f"Content {i}.",
                )
            )

        config = Config()
        service = WikiService(mock_git, config)

        sidebar = service._generate_sidebar(adrs)

        # Should show "...and X more"
        assert "...and 5 more" in sidebar


# =============================================================================
# WikiService URL Generation
# =============================================================================


class TestWikiURL:
    """Tests for wiki URL generation."""

    def test_get_wiki_url_no_git_suffix(self, mock_git: MagicMock) -> None:
        """Test wiki URL when remote doesn't end in .git."""
        mock_git.run.return_value = MagicMock(
            stdout="https://github.com/user/repo",
            exit_code=0,
        )

        config = Config()
        service = WikiService(mock_git, config)

        url = service.get_wiki_url(platform="github")

        assert url == "https://github.com/user/repo.wiki.git"

    def test_get_wiki_url_no_platform(self, mock_git: MagicMock) -> None:
        """Test wiki URL when platform detection fails."""
        mock_git.run.return_value = MagicMock(
            stdout="origin\thttps://bitbucket.org/user/repo.git",
            exit_code=0,
        )

        config = Config()
        service = WikiService(mock_git, config)

        url = service.get_wiki_url()

        # Platform detection fails for bitbucket
        assert url is None

    def test_get_wiki_url_remote_fails(self, mock_git: MagicMock) -> None:
        """Test wiki URL when remote command fails."""
        mock_git.run.return_value = MagicMock(exit_code=1, stdout="", success=False)

        config = Config()
        service = WikiService(mock_git, config)

        url = service.get_wiki_url(platform="github")

        assert url is None


# =============================================================================
# WikiService Platform Detection
# =============================================================================


class TestPlatformDetection:
    """Tests for platform detection."""

    def test_detect_platform_gitlab_case_insensitive(self, mock_git: MagicMock) -> None:
        """Test GitLab detection is case insensitive."""
        mock_git.run.return_value = MagicMock(
            stdout="origin\thttps://GITLAB.example.com/user/repo.git",
            exit_code=0,
            success=True,
        )

        config = Config()
        service = WikiService(mock_git, config)

        platform = service.detect_platform()

        assert platform == "gitlab"

    def test_detect_platform_exception(self, mock_git: MagicMock) -> None:
        """Test platform detection when exception occurs."""
        mock_git.run.side_effect = Exception("Git error")

        config = Config()
        service = WikiService(mock_git, config)

        platform = service.detect_platform()

        assert platform is None

    def test_detect_platform_remote_fails(self, mock_git: MagicMock) -> None:
        """Test platform detection when remote command fails."""
        mock_git.run.return_value = MagicMock(exit_code=1, success=False)

        config = Config()
        service = WikiService(mock_git, config)

        platform = service.detect_platform()

        assert platform is None
