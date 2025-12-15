"""Wiki service for ADR synchronization.

Provides sync to GitHub and GitLab wikis.
"""

from __future__ import annotations

import shutil
import subprocess  # nosec B404 - subprocess required for git wiki operations
import tempfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar
from urllib.parse import urlparse

if TYPE_CHECKING:
    from git_adr.core import ADR, Config, Git


class WikiServiceError(Exception):
    """Error in wiki service."""

    pass


@dataclass
class SyncResult:
    """Result of a wiki sync operation."""

    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def total_synced(self) -> int:
        """Total number of successfully synced pages."""
        return len(self.created) + len(self.updated)

    @property
    def has_changes(self) -> bool:
        """Whether any changes were made."""
        return bool(self.created or self.updated or self.deleted)


class WikiService:
    """Wiki synchronization service.

    Supports GitHub and GitLab wikis via their git-based wiki repos.
    """

    PLATFORMS: ClassVar[set[str]] = {"github", "gitlab"}

    def __init__(self, git: Git, config: Config):
        """Initialize wiki service.

        Args:
            git: Git interface.
            config: git-adr configuration.
        """
        self.git = git
        self.config = config
        self._wiki_dir: Path | None = None
        self._platform: str | None = None

    def detect_platform(self) -> str | None:
        """Detect the git hosting platform from remote URL.

        Returns:
            Platform name ('github' or 'gitlab') or None.
        """
        try:
            result = self.git.run(["remote", "get-url", "origin"])
            if result.exit_code != 0:
                return None

            remote_url = result.stdout.strip()
            hostname = urlparse(remote_url).hostname
            if hostname and hostname.lower() == "github.com":
                return "github"
            elif hostname and "gitlab" in hostname.lower():
                return "gitlab"
            return None
        except Exception:
            # No remote configured or other error
            return None

    def get_wiki_url(self, platform: str | None = None) -> str | None:
        """Get the wiki repository URL.

        Args:
            platform: Platform name or auto-detect.

        Returns:
            Wiki git URL or None if not detectable.
        """
        platform = platform or self.detect_platform()
        if not platform:
            return None

        result = self.git.run(["remote", "get-url", "origin"])
        if result.exit_code != 0:
            return None

        remote_url = result.stdout.strip()

        # Transform to wiki URL
        # GitHub: https://github.com/user/repo.git -> https://github.com/user/repo.wiki.git
        # GitLab: https://gitlab.com/user/repo.git -> https://gitlab.com/user/repo.wiki.git
        if remote_url.endswith(".git"):
            wiki_url = remote_url[:-4] + ".wiki.git"
        else:
            wiki_url = remote_url + ".wiki.git"

        return wiki_url

    def init(self, platform: str | None = None) -> dict:
        """Initialize wiki synchronization.

        Args:
            platform: Platform name or auto-detect.

        Returns:
            Initialization result with platform info.

        Raises:
            WikiServiceError: If initialization fails.
        """
        platform = platform or self.detect_platform()
        if not platform:
            raise WikiServiceError(
                "Could not detect git platform. Specify platform explicitly."
            )

        if platform not in self.PLATFORMS:
            raise WikiServiceError(
                f"Unsupported platform: {platform}. "
                f"Supported: {', '.join(self.PLATFORMS)}"
            )

        wiki_url = self.get_wiki_url(platform)
        if not wiki_url:
            raise WikiServiceError("Could not determine wiki URL from remote.")

        self._platform = platform

        return {
            "platform": platform,
            "wiki_url": wiki_url,
            "status": "initialized",
        }

    def _clone_wiki(self, wiki_url: str) -> Path:
        """Clone the wiki repository to a temporary directory.

        Args:
            wiki_url: Wiki repository URL.

        Returns:
            Path to cloned wiki.

        Raises:
            WikiServiceError: If clone fails.
        """
        wiki_dir = Path(tempfile.mkdtemp(prefix="git-adr-wiki-"))

        try:
            # wiki_url comes from git remote config (user-controlled).
            # Git validates URL format during clone - invalid URLs fail safely.
            # The nosec comment acknowledges subprocess usage with user input.
            result = subprocess.run(  # nosec B603 B607
                ["git", "clone", "--depth", "1", wiki_url, str(wiki_dir)],
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                # Wiki might not exist yet - initialize empty
                if (
                    "not found" in result.stderr.lower()
                    or "not exist" in result.stderr.lower()
                ):
                    # Initialize new wiki - git CLI with controlled args
                    subprocess.run(  # nosec B603 B607
                        ["git", "init"],
                        check=False,
                        cwd=wiki_dir,
                        capture_output=True,
                        timeout=30,
                    )
                    subprocess.run(  # nosec B603 B607
                        ["git", "remote", "add", "origin", wiki_url],
                        check=False,
                        cwd=wiki_dir,
                        capture_output=True,
                        timeout=30,
                    )
                else:
                    raise WikiServiceError(f"Failed to clone wiki: {result.stderr}")

        except subprocess.TimeoutExpired:
            shutil.rmtree(wiki_dir, ignore_errors=True)
            raise WikiServiceError("Wiki clone timed out")
        except Exception as e:
            shutil.rmtree(wiki_dir, ignore_errors=True)
            raise WikiServiceError(f"Wiki clone failed: {e}")

        return wiki_dir

    def _generate_page(self, adr: ADR, platform: str) -> str:
        """Generate wiki page content from ADR.

        Args:
            adr: ADR to convert.
            platform: Target platform.

        Returns:
            Wiki-formatted markdown content.
        """
        lines = []

        # Title
        lines.append(f"# {adr.metadata.title}")
        lines.append("")

        # Metadata table
        lines.append("| Property | Value |")
        lines.append("|----------|-------|")
        lines.append(f"| **ID** | {adr.metadata.id} |")
        lines.append(f"| **Status** | {adr.metadata.status.value} |")
        lines.append(f"| **Date** | {adr.metadata.date} |")
        if adr.metadata.deciders:
            lines.append(f"| **Deciders** | {', '.join(adr.metadata.deciders)} |")
        if adr.metadata.tags:
            lines.append(f"| **Tags** | {', '.join(adr.metadata.tags)} |")
        lines.append("")

        # Content
        lines.append(adr.content)

        # Footer
        lines.append("")
        lines.append("---")
        lines.append(
            f"*Synced from git-adr on {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}*"
        )

        return "\n".join(lines)

    def _generate_index(self, adrs: list[ADR], platform: str) -> str:
        """Generate wiki index/navigation.

        Args:
            adrs: All ADRs to index.
            platform: Target platform.

        Returns:
            Index page content.
        """
        lines = ["# Architecture Decision Records", ""]

        # Group by status
        by_status: dict[str, list[ADR]] = {}
        for adr in sorted(adrs, key=lambda a: a.metadata.date, reverse=True):
            status = adr.metadata.status.value
            by_status.setdefault(status, []).append(adr)

        # Active decisions first
        priority_order = ["accepted", "proposed", "deprecated", "superseded"]
        for status in priority_order:
            if status in by_status:
                lines.append(f"## {status.title()}")
                lines.append("")
                for adr in by_status[status]:
                    page_name = self._get_page_name(adr)
                    lines.append(
                        f"- [{adr.metadata.id}: {adr.metadata.title}]({page_name})"
                    )
                lines.append("")
                del by_status[status]

        # Remaining statuses
        for status, status_adrs in sorted(by_status.items()):
            lines.append(f"## {status.title()}")
            lines.append("")
            for adr in status_adrs:
                page_name = self._get_page_name(adr)
                lines.append(
                    f"- [{adr.metadata.id}: {adr.metadata.title}]({page_name})"
                )
            lines.append("")

        lines.append("---")
        lines.append(
            f"*Last updated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}*"
        )

        return "\n".join(lines)

    def _generate_sidebar(self, adrs: list[ADR]) -> str:
        """Generate GitHub wiki sidebar navigation.

        Args:
            adrs: All ADRs.

        Returns:
            Sidebar content.
        """
        lines = ["**Architecture Decisions**", ""]
        lines.append("* [[Home]]")
        lines.append("")

        # Recent decisions
        recent = sorted(adrs, key=lambda a: a.metadata.date, reverse=True)[:10]
        for adr in recent:
            page_name = self._get_page_name(adr)
            lines.append(f"* [[{adr.metadata.id}|{page_name}]]")

        if len(adrs) > 10:
            lines.append("")
            lines.append(f"*...and {len(adrs) - 10} more*")

        return "\n".join(lines)

    def _get_page_name(self, adr: ADR) -> str:
        """Get the wiki page filename for an ADR.

        Args:
            adr: ADR to name.

        Returns:
            Page name (without .md extension for wiki links).
        """
        # Sanitize title for filename
        safe_title = "".join(
            c if c.isalnum() or c in "- " else "" for c in adr.metadata.title
        ).strip()
        safe_title = safe_title.replace(" ", "-")
        return f"ADR-{adr.metadata.id}-{safe_title}"

    def sync(
        self,
        adrs: list[ADR],
        direction: str = "push",
        dry_run: bool = False,
        platform: str | None = None,
    ) -> SyncResult:
        """Synchronize ADRs with wiki.

        Args:
            adrs: ADRs to sync.
            direction: Sync direction ('push', 'pull', 'both').
            dry_run: Only show what would be done.
            platform: Platform name or auto-detect.

        Returns:
            SyncResult with sync details.

        Raises:
            WikiServiceError: If sync fails.
        """
        result = SyncResult()
        platform = platform or self._platform or self.detect_platform()

        if not platform:
            raise WikiServiceError(
                "Platform not configured. Run `git adr wiki init` first."
            )

        wiki_url = self.get_wiki_url(platform)
        if not wiki_url:
            raise WikiServiceError("Could not determine wiki URL.")

        if dry_run:
            # Just report what would happen
            for adr in adrs:
                result.created.append(adr.metadata.id)
            return result

        # Clone wiki
        wiki_dir = self._clone_wiki(wiki_url)

        try:
            if direction in ("push", "both"):
                self._sync_push(adrs, wiki_dir, platform, result)

            if direction in ("pull", "both"):
                self._sync_pull(wiki_dir, result)

            # Commit and push if changes
            if result.has_changes and direction in ("push", "both"):
                self._commit_and_push(wiki_dir, result)

        finally:
            # Cleanup
            shutil.rmtree(wiki_dir, ignore_errors=True)

        return result

    def _sync_push(
        self,
        adrs: list[ADR],
        wiki_dir: Path,
        platform: str,
        result: SyncResult,
    ) -> None:
        """Push ADRs to wiki.

        Args:
            adrs: ADRs to push.
            wiki_dir: Wiki directory.
            platform: Target platform.
            result: SyncResult to update.
        """
        # Generate index/home page
        index_content = self._generate_index(adrs, platform)
        index_path = wiki_dir / "Home.md"
        index_path.write_text(index_content)

        # Generate sidebar for GitHub
        if platform == "github":
            sidebar_content = self._generate_sidebar(adrs)
            sidebar_path = wiki_dir / "_Sidebar.md"
            sidebar_path.write_text(sidebar_content)

        # Generate individual pages
        for adr in adrs:
            try:
                page_name = self._get_page_name(adr)
                page_path = wiki_dir / f"{page_name}.md"

                is_new = not page_path.exists()
                page_content = self._generate_page(adr, platform)
                page_path.write_text(page_content)

                if is_new:
                    result.created.append(adr.metadata.id)
                else:
                    result.updated.append(adr.metadata.id)

            except Exception as e:
                result.errors.append(f"{adr.metadata.id}: {e}")

    def _sync_pull(self, wiki_dir: Path, result: SyncResult) -> None:
        """Pull changes from wiki (bidirectional sync).

        Args:
            wiki_dir: Wiki directory.
            result: SyncResult to update.

        Note:
            Full bidirectional sync requires tracking last sync state.
            This is a simplified implementation.
        """
        # For now, just note that pull is not fully implemented
        result.skipped.append("pull:not-implemented")

    def _commit_and_push(self, wiki_dir: Path, result: SyncResult) -> None:
        """Commit and push wiki changes.

        Args:
            wiki_dir: Wiki directory.
            result: SyncResult for commit message.

        Raises:
            WikiServiceError: If commit/push fails.
        """
        try:
            # Stage all changes - git CLI with controlled args
            subprocess.run(  # nosec B603 B607
                ["git", "add", "-A"],
                check=False,
                cwd=wiki_dir,
                capture_output=True,
                timeout=30,
            )

            # Commit changes. Security note: commit_msg is constructed from internal
            # integer counts (len() results), not user input, so this is safe.
            commit_msg = (
                f"Sync {result.total_synced} ADRs from git-adr\n\n"
                f"Created: {len(result.created)}\n"
                f"Updated: {len(result.updated)}\n"
                f"Deleted: {len(result.deleted)}"
            )
            subprocess.run(  # nosec B603 B607
                ["git", "commit", "-m", commit_msg],
                check=False,
                cwd=wiki_dir,
                capture_output=True,
                timeout=30,
            )

            # Push - git CLI with controlled args
            push_result = subprocess.run(  # nosec B603 B607
                ["git", "push", "origin", "HEAD"],
                check=False,
                cwd=wiki_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if push_result.returncode != 0:
                raise WikiServiceError(f"Wiki push failed: {push_result.stderr}")

        except subprocess.TimeoutExpired:
            raise WikiServiceError("Wiki push timed out")
        except WikiServiceError:
            raise
        except Exception as e:
            raise WikiServiceError(f"Wiki commit/push failed: {e}")
