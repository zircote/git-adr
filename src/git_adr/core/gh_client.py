"""GitHub CLI integration for issue creation.

This module provides a client for interacting with GitHub via the gh CLI.
The gh CLI is used for authentication and API access, avoiding the need
for custom credential management.
"""

from __future__ import annotations

import subprocess  # nosec B404 - subprocess required for gh CLI wrapper
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from git_adr.core.issue import Issue


@dataclass
class IssueCreateResult:
    """Result of an issue creation operation.

    Attributes:
        success: Whether the operation succeeded.
        url: URL of the created issue (if successful).
        number: Issue number (if successful).
        error: Error message (if failed).
    """

    success: bool
    url: str | None = None
    number: int | None = None
    error: str | None = None


class GitHubIssueClient:
    """Client for creating GitHub issues via the gh CLI.

    Uses subprocess to invoke gh commands, passing issue body via stdin
    to avoid shell escaping issues.
    """

    # Exit code when gh requires authentication
    AUTH_REQUIRED_EXIT_CODE = 4

    def __init__(self, repo: str | None = None) -> None:
        """Initialize the client.

        Args:
            repo: Optional repository in owner/name format. If None, gh CLI
                  will use the current repository.
        """
        self._repo = repo

    @classmethod
    def is_available(cls) -> bool:
        """Check if the gh CLI is installed and in PATH.

        Returns:
            True if gh CLI is available.
        """
        try:
            result = subprocess.run(  # nosec B603 B607 - safe gh CLI call
                ["gh", "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    @classmethod
    def is_authenticated(cls) -> bool:
        """Check if the gh CLI is authenticated.

        Returns:
            True if gh CLI is authenticated with GitHub.
        """
        try:
            result = subprocess.run(  # nosec B603 B607 - safe gh CLI call
                ["gh", "auth", "status"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    @classmethod
    def get_auth_status_message(cls) -> str:
        """Get a human-readable authentication status message.

        Returns:
            Status message describing authentication state.
        """
        try:
            result = subprocess.run(  # nosec B603 B607 - safe gh CLI call
                ["gh", "auth", "status"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return "Authenticated with GitHub"
            return result.stderr.strip() or "Not authenticated with GitHub"
        except FileNotFoundError:
            return "gh CLI not found"
        except subprocess.TimeoutExpired:
            return "Authentication check timed out"

    def create_issue(self, issue: Issue) -> IssueCreateResult:
        """Create a GitHub issue.

        Args:
            issue: The Issue to create.

        Returns:
            IssueCreateResult with success status and URL or error.
        """
        if not self.is_available():
            return IssueCreateResult(
                success=False,
                error="gh CLI is not installed. Install from https://cli.github.com/",
            )

        if not self.is_authenticated():
            return IssueCreateResult(
                success=False,
                error="gh CLI is not authenticated. Run: gh auth login",
            )

        # Build command
        cmd = ["gh", "issue", "create", "--title", issue.title, "--body-file", "-"]

        # Add repo if specified
        if self._repo:
            cmd.extend(["--repo", self._repo])

        # Add labels
        for label in issue.labels:
            cmd.extend(["--label", label])

        # Add assignees
        for assignee in issue.assignees:
            cmd.extend(["--assignee", assignee])

        try:
            result = subprocess.run(  # nosec B603 - safe gh CLI call with trusted args
                cmd,
                check=False,
                input=issue.body,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                # gh outputs the issue URL on success
                url = result.stdout.strip()
                number = self._extract_issue_number(url)
                return IssueCreateResult(
                    success=True,
                    url=url,
                    number=number,
                )

            # Handle specific error codes
            if result.returncode == self.AUTH_REQUIRED_EXIT_CODE:
                return IssueCreateResult(
                    success=False,
                    error="GitHub authentication required. Run: gh auth login",
                )

            return IssueCreateResult(
                success=False,
                error=result.stderr.strip()
                or f"gh exited with code {result.returncode}",
            )

        except subprocess.TimeoutExpired:
            return IssueCreateResult(
                success=False,
                error="Issue creation timed out",
            )
        except FileNotFoundError:
            return IssueCreateResult(
                success=False,
                error="gh CLI not found",
            )

    def _extract_issue_number(self, url: str) -> int | None:
        """Extract issue number from GitHub URL.

        Args:
            url: GitHub issue URL.

        Returns:
            Issue number, or None if not found.
        """
        # URL format: https://github.com/owner/repo/issues/123
        parts = url.rstrip("/").split("/")
        if len(parts) >= 2 and parts[-2] == "issues":
            try:
                return int(parts[-1])
            except ValueError:
                pass
        return None

    @classmethod
    def get_current_repo(cls) -> str | None:
        """Get the current repository from git remote.

        Returns:
            Repository in owner/repo format, or None if not in a git repo.
        """
        try:
            result = subprocess.run(  # nosec B603 B607 - safe gh CLI call
                [
                    "gh",
                    "repo",
                    "view",
                    "--json",
                    "nameWithOwner",
                    "-q",
                    ".nameWithOwner",
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return None


def check_gh_status() -> tuple[bool, str]:
    """Check gh CLI installation and authentication status.

    Returns:
        Tuple of (is_ready, message) where is_ready indicates whether
        issues can be submitted, and message provides status details.
    """
    if not GitHubIssueClient.is_available():
        return False, (
            "gh CLI is not installed.\n"
            "Install from: https://cli.github.com/\n"
            "Issues will be saved locally."
        )

    if not GitHubIssueClient.is_authenticated():
        return False, (
            "gh CLI is not authenticated.\n"
            "Run: gh auth login\n"
            "Issues will be saved locally."
        )

    return True, "Ready to submit issues to GitHub"
