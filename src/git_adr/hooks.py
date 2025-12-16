"""Git hooks management for git-adr.

This module provides hook installation, versioning, and lifecycle management
for automatic ADR notes synchronization via git hooks.
"""

from __future__ import annotations

import re
import stat
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import ClassVar


class HookStatus(Enum):
    """Status of a git hook."""

    NOT_INSTALLED = "not_installed"
    INSTALLED = "installed"
    OUTDATED = "outdated"
    FOREIGN = "foreign"  # Exists but not ours


HOOK_VERSION = "1.0"
HOOK_MARKER = "# git-adr hook"

# Pre-push hook script template
PRE_PUSH_TEMPLATE = """#!/bin/sh
# git-adr hook - pre-push
# Version: {version}
# Installed by: git adr hooks install

# Recursion guard - prevent infinite loops
[ -n "$GIT_ADR_HOOK_RUNNING" ] && exit 0
export GIT_ADR_HOOK_RUNNING=1

# Skip if disabled via environment
[ "$GIT_ADR_SKIP" = "1" ] && exit 0

# Skip if disabled via config
skip=$(git config --get adr.hooks.skip 2>/dev/null)
[ "$skip" = "true" ] && exit 0

# Check if git-adr is available
command -v git-adr >/dev/null 2>&1 || {{
    printf >&2 '\\ngit-adr not found in PATH. Hook skipped.\\n'
    exit 0
}}

# Get remote name from arguments
remote="$1"

# Only sync if pushing branches (not tags)
has_branch=false
while read local_ref local_sha remote_ref remote_sha; do
    case "$remote_ref" in
        refs/heads/*) has_branch=true; break ;;
    esac
done
[ "$has_branch" = "true" ] || exit 0

# Sync notes to remote (delegate to git-adr)
git adr hook pre-push "$remote" || {{
    # Check if blocking is enabled
    block=$(git config --get adr.hooks.blockOnFailure 2>/dev/null)
    if [ "$block" = "true" ]; then
        printf >&2 'git-adr: notes sync failed, push blocked\\n'
        exit 1
    fi
    printf >&2 'git-adr: notes sync failed (non-blocking)\\n'
}}

# Chain to backup hook if exists
backup_hook="$(dirname "$0")/pre-push.git-adr-backup"
if [ -f "$backup_hook" ]; then
    "$backup_hook" "$@"
fi

exit 0
"""


@dataclass
class Hook:
    """Manager for a single git hook.

    Handles installation, uninstallation, backup-and-chain for existing hooks,
    and version tracking for upgrades.
    """

    hook_type: str
    hooks_dir: Path
    version: str = HOOK_VERSION

    @property
    def hook_path(self) -> Path:
        """Path to the hook script."""
        return self.hooks_dir / self.hook_type

    @property
    def backup_path(self) -> Path:
        """Path to the backup of any existing hook."""
        return self.hooks_dir / f"{self.hook_type}.git-adr-backup"

    def get_script_content(self) -> str:
        """Get the hook script content for this hook type."""
        if self.hook_type == "pre-push":
            return PRE_PUSH_TEMPLATE.format(version=self.version)
        raise ValueError(f"Unknown hook type: {self.hook_type}")

    def is_installed(self) -> bool:
        """Check if our hook is installed."""
        return self.hook_path.exists() and self.is_ours()

    def is_ours(self) -> bool:
        """Check if the existing hook was installed by git-adr."""
        if not self.hook_path.exists():
            return False
        try:
            content = self.hook_path.read_text()
            return HOOK_MARKER in content
        except OSError:
            return False

    def get_installed_version(self) -> str | None:
        """Get the version of the installed hook, if any."""
        if not self.hook_path.exists():
            return None
        try:
            content = self.hook_path.read_text()
            match = re.search(r"# Version: (\d+\.\d+)", content)
            return match.group(1) if match else None
        except OSError:
            return None

    def get_status(self) -> HookStatus:
        """Get the current status of this hook."""
        if not self.hook_path.exists():
            return HookStatus.NOT_INSTALLED

        if not self.is_ours():
            return HookStatus.FOREIGN

        installed_version = self.get_installed_version()
        if installed_version and installed_version < self.version:
            return HookStatus.OUTDATED

        return HookStatus.INSTALLED

    def install(self, force: bool = False) -> str:
        """Install the hook.

        Args:
            force: If True, overwrite existing hooks (backs up first)

        Returns:
            Status message describing what was done

        Raises:
            FileExistsError: If hook exists and force=False and not ours
        """
        # Ensure hooks directory exists
        self.hooks_dir.mkdir(parents=True, exist_ok=True)

        # Handle existing hook
        if self.hook_path.exists():
            if self.is_ours():
                if not force:
                    installed_ver = self.get_installed_version()
                    if installed_ver == self.version:
                        return f"{self.hook_type}: already installed (v{self.version})"
                # Reinstall/upgrade - no backup needed for our own hook
            else:
                # Foreign hook - backup before replacing
                self._backup_existing()

        # Write the hook script
        content = self.get_script_content()
        self.hook_path.write_text(content)

        # Make executable (rwxr-xr-x)
        self.hook_path.chmod(
            stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
        )

        if self.backup_path.exists():
            return f"{self.hook_type}: installed (existing hook backed up)"
        return f"{self.hook_type}: installed"

    def uninstall(self) -> str:
        """Uninstall the hook.

        Returns:
            Status message describing what was done
        """
        if not self.hook_path.exists():
            return f"{self.hook_type}: not installed"

        if not self.is_ours():
            return f"{self.hook_type}: not our hook (skipped)"

        # Remove our hook
        self.hook_path.unlink()

        # Restore backup if exists
        if self.backup_path.exists():
            self.backup_path.rename(self.hook_path)
            return f"{self.hook_type}: uninstalled (original hook restored)"

        return f"{self.hook_type}: uninstalled"

    def _backup_existing(self) -> None:
        """Backup the existing hook."""
        if self.hook_path.exists() and not self.backup_path.exists():
            # Copy to backup (don't move - we want atomic replacement)
            content = self.hook_path.read_bytes()
            self.backup_path.write_bytes(content)
            # Preserve executable bit on backup
            mode = self.hook_path.stat().st_mode
            self.backup_path.chmod(mode)

    def get_manual_instructions(self) -> str:
        """Get instructions for manual hook integration.

        Returns:
            Shell snippet to add to existing hook
        """
        return f"""# Add this to your {self.hook_type} hook:

# git-adr integration
if command -v git-adr >/dev/null 2>&1; then
    [ -z "$GIT_ADR_SKIP" ] && git adr hook {self.hook_type} "$@" || true
fi
"""


class HooksManager:
    """Manager for all git-adr hooks.

    Provides high-level operations to install/uninstall all hooks
    and query their status.
    """

    # Hook types managed by git-adr
    HOOK_TYPES: ClassVar[list[str]] = ["pre-push"]

    def __init__(self, git_dir: Path | None = None) -> None:
        """Initialize the hooks manager.

        Args:
            git_dir: Path to .git directory. If None, auto-detect from cwd.
        """
        if git_dir is None:
            git_dir = self._find_git_dir()
        self.git_dir = git_dir
        self.hooks_dir = git_dir / "hooks"

    @staticmethod
    def _find_git_dir() -> Path:
        """Find the .git directory from current working directory."""
        cwd = Path.cwd()

        # Check for .git file (worktree) or directory
        git_path = cwd / ".git"
        if git_path.is_file():
            # Worktree - .git is a file pointing to the real git dir
            content = git_path.read_text().strip()
            if content.startswith("gitdir:"):
                return Path(content[7:].strip())
        elif git_path.is_dir():
            return git_path

        # Walk up to find .git
        for parent in cwd.parents:
            git_path = parent / ".git"
            if git_path.is_file():
                content = git_path.read_text().strip()
                if content.startswith("gitdir:"):
                    return Path(content[7:].strip())
            elif git_path.is_dir():
                return git_path

        raise FileNotFoundError("Not in a git repository")

    def _get_hook(self, hook_type: str) -> Hook:
        """Get a Hook instance for the given type."""
        return Hook(hook_type=hook_type, hooks_dir=self.hooks_dir)

    def install_all(self, force: bool = False) -> list[str]:
        """Install all git-adr hooks.

        Args:
            force: If True, overwrite existing hooks

        Returns:
            List of status messages for each hook
        """
        results = []
        for hook_type in self.HOOK_TYPES:
            hook = self._get_hook(hook_type)
            result = hook.install(force=force)
            results.append(result)
        return results

    def uninstall_all(self) -> list[str]:
        """Uninstall all git-adr hooks.

        Returns:
            List of status messages for each hook
        """
        results = []
        for hook_type in self.HOOK_TYPES:
            hook = self._get_hook(hook_type)
            result = hook.uninstall()
            results.append(result)
        return results

    def get_status(self) -> dict[str, HookStatus]:
        """Get status of all managed hooks.

        Returns:
            Dictionary mapping hook type to status
        """
        return {
            hook_type: self._get_hook(hook_type).get_status()
            for hook_type in self.HOOK_TYPES
        }

    def get_manual_instructions(self) -> str:
        """Get manual integration instructions for all hooks.

        Returns:
            Instructions for manually integrating git-adr into existing hooks
        """
        instructions = ["# Manual git-adr hook integration\n"]
        for hook_type in self.HOOK_TYPES:
            hook = self._get_hook(hook_type)
            instructions.append(hook.get_manual_instructions())
        return "\n".join(instructions)


def get_hooks_manager(git_dir: Path | None = None) -> HooksManager:
    """Get a HooksManager instance.

    Args:
        git_dir: Optional path to .git directory

    Returns:
        HooksManager instance
    """
    return HooksManager(git_dir)
