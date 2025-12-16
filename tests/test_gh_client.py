"""Tests for GitHub CLI integration."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from git_adr.core.gh_client import (
    GitHubIssueClient,
    IssueCreateResult,
    check_gh_status,
)
from git_adr.core.issue import Issue


class TestIssueCreateResult:
    """Tests for IssueCreateResult dataclass."""

    def test_success_result(self) -> None:
        """Test successful result."""
        result = IssueCreateResult(
            success=True,
            url="https://github.com/owner/repo/issues/123",
            number=123,
        )
        assert result.success is True
        assert result.url == "https://github.com/owner/repo/issues/123"
        assert result.number == 123
        assert result.error is None

    def test_failure_result(self) -> None:
        """Test failure result."""
        result = IssueCreateResult(
            success=False,
            error="Authentication required",
        )
        assert result.success is False
        assert result.error == "Authentication required"
        assert result.url is None


class TestGitHubIssueClient:
    """Tests for GitHubIssueClient class."""

    def test_create_client(self) -> None:
        """Test creating a client."""
        client = GitHubIssueClient()
        assert client._repo is None

        client = GitHubIssueClient(repo="owner/repo")
        assert client._repo == "owner/repo"

    @patch("subprocess.run")
    def test_is_available_true(self, mock_run: MagicMock) -> None:
        """Test is_available returns True when gh is installed."""
        mock_run.return_value.returncode = 0
        assert GitHubIssueClient.is_available() is True
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_is_available_false(self, mock_run: MagicMock) -> None:
        """Test is_available returns False when gh is not installed."""
        mock_run.side_effect = FileNotFoundError()
        assert GitHubIssueClient.is_available() is False

    @patch("subprocess.run")
    def test_is_authenticated_true(self, mock_run: MagicMock) -> None:
        """Test is_authenticated returns True when logged in."""
        mock_run.return_value.returncode = 0
        assert GitHubIssueClient.is_authenticated() is True

    @patch("subprocess.run")
    def test_is_authenticated_false(self, mock_run: MagicMock) -> None:
        """Test is_authenticated returns False when not logged in."""
        mock_run.return_value.returncode = 1
        assert GitHubIssueClient.is_authenticated() is False

    @patch.object(GitHubIssueClient, "is_available", return_value=False)
    def test_create_issue_gh_not_available(self, mock_available: MagicMock) -> None:
        """Test create_issue when gh is not installed."""
        client = GitHubIssueClient()
        issue = Issue(title="Test", body="Test body")

        result = client.create_issue(issue)

        assert result.success is False
        assert "not installed" in result.error

    @patch.object(GitHubIssueClient, "is_available", return_value=True)
    @patch.object(GitHubIssueClient, "is_authenticated", return_value=False)
    def test_create_issue_not_authenticated(
        self,
        mock_auth: MagicMock,
        mock_available: MagicMock,
    ) -> None:
        """Test create_issue when not authenticated."""
        client = GitHubIssueClient()
        issue = Issue(title="Test", body="Test body")

        result = client.create_issue(issue)

        assert result.success is False
        assert "not authenticated" in result.error

    @patch.object(GitHubIssueClient, "is_available", return_value=True)
    @patch.object(GitHubIssueClient, "is_authenticated", return_value=True)
    @patch("subprocess.run")
    def test_create_issue_success(
        self,
        mock_run: MagicMock,
        mock_auth: MagicMock,
        mock_available: MagicMock,
    ) -> None:
        """Test successful issue creation."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "https://github.com/owner/repo/issues/42\n"

        client = GitHubIssueClient()
        issue = Issue(
            title="Test Issue",
            body="Test body",
            labels=["bug"],
            assignees=["alice"],
        )

        result = client.create_issue(issue)

        assert result.success is True
        assert result.url == "https://github.com/owner/repo/issues/42"
        assert result.number == 42

        # Verify the command
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert "gh" in cmd
        assert "issue" in cmd
        assert "create" in cmd
        assert "--title" in cmd
        assert "--body-file" in cmd
        assert "-" in cmd  # stdin
        assert "--label" in cmd
        assert "--assignee" in cmd

    @patch.object(GitHubIssueClient, "is_available", return_value=True)
    @patch.object(GitHubIssueClient, "is_authenticated", return_value=True)
    @patch("subprocess.run")
    def test_create_issue_with_repo(
        self,
        mock_run: MagicMock,
        mock_auth: MagicMock,
        mock_available: MagicMock,
    ) -> None:
        """Test issue creation with explicit repo."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "https://github.com/other/repo/issues/1\n"

        client = GitHubIssueClient(repo="other/repo")
        issue = Issue(title="Test", body="Body")

        client.create_issue(issue)

        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert "--repo" in cmd
        assert "other/repo" in cmd

    @patch.object(GitHubIssueClient, "is_available", return_value=True)
    @patch.object(GitHubIssueClient, "is_authenticated", return_value=True)
    @patch("subprocess.run")
    def test_create_issue_auth_error(
        self,
        mock_run: MagicMock,
        mock_auth: MagicMock,
        mock_available: MagicMock,
    ) -> None:
        """Test handling auth required exit code."""
        mock_run.return_value.returncode = 4  # AUTH_REQUIRED_EXIT_CODE
        mock_run.return_value.stderr = ""

        client = GitHubIssueClient()
        issue = Issue(title="Test", body="Body")

        result = client.create_issue(issue)

        assert result.success is False
        assert "authentication required" in result.error.lower()

    @patch.object(GitHubIssueClient, "is_available", return_value=True)
    @patch.object(GitHubIssueClient, "is_authenticated", return_value=True)
    @patch("subprocess.run")
    def test_create_issue_other_error(
        self,
        mock_run: MagicMock,
        mock_auth: MagicMock,
        mock_available: MagicMock,
    ) -> None:
        """Test handling other errors."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Repository not found"

        client = GitHubIssueClient()
        issue = Issue(title="Test", body="Body")

        result = client.create_issue(issue)

        assert result.success is False
        assert "Repository not found" in result.error

    def test_extract_issue_number(self) -> None:
        """Test extracting issue number from URL."""
        client = GitHubIssueClient()

        assert (
            client._extract_issue_number("https://github.com/owner/repo/issues/42")
            == 42
        )

        assert (
            client._extract_issue_number("https://github.com/owner/repo/issues/123/")
            == 123
        )

        assert (
            client._extract_issue_number("https://github.com/owner/repo/pulls/42")
            is None
        )

        assert client._extract_issue_number("invalid-url") is None

    @patch("subprocess.run")
    def test_get_current_repo(self, mock_run: MagicMock) -> None:
        """Test getting current repo."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "owner/repo\n"

        repo = GitHubIssueClient.get_current_repo()
        assert repo == "owner/repo"

    @patch("subprocess.run")
    def test_get_current_repo_not_in_repo(self, mock_run: MagicMock) -> None:
        """Test getting current repo when not in a git repo."""
        mock_run.return_value.returncode = 1

        repo = GitHubIssueClient.get_current_repo()
        assert repo is None


class TestCheckGhStatus:
    """Tests for check_gh_status function."""

    @patch.object(GitHubIssueClient, "is_available", return_value=False)
    def test_gh_not_available(self, mock_available: MagicMock) -> None:
        """Test status when gh is not installed."""
        is_ready, message = check_gh_status()
        assert is_ready is False
        assert "not installed" in message

    @patch.object(GitHubIssueClient, "is_available", return_value=True)
    @patch.object(GitHubIssueClient, "is_authenticated", return_value=False)
    def test_gh_not_authenticated(
        self,
        mock_auth: MagicMock,
        mock_available: MagicMock,
    ) -> None:
        """Test status when not authenticated."""
        is_ready, message = check_gh_status()
        assert is_ready is False
        assert "not authenticated" in message

    @patch.object(GitHubIssueClient, "is_available", return_value=True)
    @patch.object(GitHubIssueClient, "is_authenticated", return_value=True)
    def test_gh_ready(
        self,
        mock_auth: MagicMock,
        mock_available: MagicMock,
    ) -> None:
        """Test status when ready."""
        is_ready, message = check_gh_status()
        assert is_ready is True
        assert "Ready" in message
