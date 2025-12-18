"""Git subprocess executor for git-adr.

This module provides a clean abstraction over git subprocess calls,
handling execution, error handling, and output parsing.

Based on research of git extension patterns (git-lfs, git-flow, git-crypt,
github-cli, git-absorb), subprocess to git binary is the industry standard
approach for git extensions.
"""

from __future__ import annotations

import os
import shutil
import subprocess  # nosec B404 - subprocess is required for git CLI wrapper functionality
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


class GitError(Exception):
    """Exception raised when a git command fails.

    Attributes:
        command: The git command that was executed.
        exit_code: The exit code from git.
        stdout: Standard output from git.
        stderr: Standard error from git.
    """

    def __init__(
        self,
        message: str,
        command: list[str],
        exit_code: int,
        stdout: str = "",
        stderr: str = "",
    ) -> None:
        super().__init__(message)
        self.command = command
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr

    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.stderr:
            parts.append(f"stderr: {self.stderr.strip()}")
        return "\n".join(parts)


class GitNotFoundError(GitError):
    """Exception raised when git executable is not found."""

    def __init__(self) -> None:
        super().__init__(
            message="Git executable not found. Please install git.",
            command=[],
            exit_code=-1,
        )


class NotARepositoryError(GitError):
    """Exception raised when not in a git repository."""

    def __init__(self, path: Path | None = None) -> None:
        msg = "Not a git repository"
        if path:
            msg = f"Not a git repository: {path}"
        super().__init__(message=msg, command=[], exit_code=128)


@dataclass(frozen=True, slots=True)
class GitResult:
    """Result from a git command execution.

    Attributes:
        stdout: Standard output from the command.
        stderr: Standard error from the command.
        exit_code: The exit code (0 for success).
    """

    stdout: str
    stderr: str
    exit_code: int

    @property
    def success(self) -> bool:
        """Check if the command succeeded."""
        return self.exit_code == 0

    @property
    def lines(self) -> list[str]:
        """Split stdout into lines, excluding empty trailing lines."""
        return self.stdout.rstrip("\n").split("\n") if self.stdout.strip() else []


@dataclass
class Git:
    """Git command executor.

    This class wraps subprocess calls to the git binary, providing
    a clean interface for git operations with proper error handling.

    Attributes:
        cwd: Working directory for git commands.
        git_executable: Path to git executable (auto-detected if not provided).
        env: Additional environment variables for git commands.
    """

    cwd: Path | None = None
    git_executable: str | None = None
    env: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize and validate the git executor."""
        if self.git_executable is None:
            self.git_executable = self._find_git_executable()

        if self.git_executable is None:
            raise GitNotFoundError()

    @staticmethod
    def _find_git_executable() -> str | None:
        """Find the git executable on the system.

        Checks common locations and PATH for the git binary.

        Returns:
            Path to git executable, or None if not found.
        """
        # First try PATH
        git_path = shutil.which("git")
        if git_path:
            return git_path

        # Common locations on different platforms
        common_paths = [
            "/usr/bin/git",
            "/usr/local/bin/git",
            "/opt/homebrew/bin/git",  # macOS Apple Silicon
            "C:\\Program Files\\Git\\bin\\git.exe",  # Windows
            "C:\\Program Files (x86)\\Git\\bin\\git.exe",  # Windows 32-bit
        ]

        for path in common_paths:
            if Path(path).exists():
                return path

        return None

    def _build_env(self) -> dict[str, str]:
        """Build environment dict for subprocess.

        Returns:
            Environment dictionary with git-specific settings.
        """
        env = os.environ.copy()

        # Prevent git from prompting for credentials in non-interactive mode
        env["GIT_TERMINAL_PROMPT"] = "0"

        # Force C locale for consistent git output parsing.
        # This ensures git messages/formats are predictable across systems.
        # Note: Non-ASCII filenames still work; this only affects UI messages.
        env["LC_ALL"] = "C"

        # Merge any custom environment variables
        env.update(self.env)

        return env

    def run(
        self,
        args: Sequence[str],
        *,
        check: bool = True,
        capture_output: bool = True,
        input_data: str | None = None,
        timeout: float | None = 30.0,
        allow_exit_codes: Sequence[int] | None = None,
    ) -> GitResult:
        """Execute a git command.

        Args:
            args: Arguments to pass to git (excluding 'git' itself).
            check: If True, raise GitError on non-zero exit.
            capture_output: If True, capture stdout/stderr.
            input_data: Data to send to stdin.
            timeout: Command timeout in seconds.
            allow_exit_codes: Additional exit codes to allow besides 0.

        Returns:
            GitResult containing stdout, stderr, and exit code.

        Raises:
            GitError: If the command fails and check=True.
            GitNotFoundError: If git executable is not found.
        """
        if not self.git_executable:
            raise GitNotFoundError()

        cmd = [self.git_executable, *args]
        allowed = {0, *(allow_exit_codes or [])}

        try:
            # subprocess with list args (not shell=True) is safe; cmd is built
            # from validated git executable path + controlled args, not user input
            result = subprocess.run(  # nosec B603
                cmd,
                check=False,
                cwd=self.cwd,
                env=self._build_env(),
                capture_output=capture_output,
                text=True,
                input=input_data,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as e:
            raise GitError(
                message=f"Git command timed out after {timeout}s",
                command=cmd,
                exit_code=-1,
                stderr=str(e),
            ) from e
        except FileNotFoundError as e:
            raise GitNotFoundError() from e

        git_result = GitResult(
            stdout=result.stdout or "",
            stderr=result.stderr or "",
            exit_code=result.returncode,
        )

        if check and result.returncode not in allowed:
            # Parse common git errors for better messages
            error_msg = self._parse_error_message(result.stderr, result.returncode)
            raise GitError(
                message=error_msg,
                command=cmd,
                exit_code=result.returncode,
                stdout=result.stdout or "",
                stderr=result.stderr or "",
            )

        return git_result

    def _parse_error_message(self, stderr: str, exit_code: int) -> str:
        """Parse stderr to provide a user-friendly error message.

        Args:
            stderr: Standard error output from git.
            exit_code: The exit code from git.

        Returns:
            A user-friendly error message.
        """
        stderr_lower = stderr.lower()

        if "not a git repository" in stderr_lower:
            return "Not in a git repository"
        if "permission denied" in stderr_lower:
            return "Permission denied"
        if "could not resolve host" in stderr_lower:
            return "Network error: could not resolve host"
        if "authentication failed" in stderr_lower:
            return "Authentication failed"
        if "repository not found" in stderr_lower:
            return "Repository not found"

        # Default: use first line of stderr or generic message
        first_line = stderr.strip().split("\n")[0] if stderr.strip() else ""
        if first_line:
            # Remove "fatal: " prefix if present
            if first_line.lower().startswith("fatal:"):
                first_line = first_line[6:].strip()
            return first_line

        return f"Git command failed with exit code {exit_code}"

    # =========================================================================
    # Repository Information
    # =========================================================================

    def is_repository(self) -> bool:
        """Check if the current directory is a git repository.

        Returns:
            True if in a git repository, False otherwise.
        """
        try:
            result = self.run(
                ["rev-parse", "--git-dir"],
                check=False,
            )
            return result.exit_code == 0
        except GitError:
            return False

    def get_root(self) -> Path:
        """Get the root directory of the git repository.

        Returns:
            Path to the repository root.

        Raises:
            NotARepositoryError: If not in a git repository.
        """
        try:
            result = self.run(["rev-parse", "--show-toplevel"])
            return Path(result.stdout.strip())
        except GitError as e:
            if "not a git repository" in e.stderr.lower():
                raise NotARepositoryError(self.cwd) from e
            raise

    def get_git_dir(self) -> Path:
        """Get the .git directory path.

        Returns:
            Path to the .git directory.
        """
        result = self.run(["rev-parse", "--git-dir"])
        return Path(result.stdout.strip())

    def get_root_tree(self) -> str:
        """Get the SHA of the repository's root tree object.

        The root tree is a stable attachment point for notes that survives
        rebase and amend operations. This is where ADRs are attached.

        Returns:
            SHA of the root tree object.

        Raises:
            GitError: If there are no commits yet.
        """
        # Get the tree object for HEAD
        result = self.run(["rev-parse", "HEAD^{tree}"])
        return result.stdout.strip()

    def get_head_commit(self) -> str:
        """Get the SHA of HEAD commit.

        Returns:
            SHA of the HEAD commit.
        """
        result = self.run(["rev-parse", "HEAD"])
        return result.stdout.strip()

    def get_current_branch(self) -> str | None:
        """Get the current branch name.

        Returns:
            Branch name, or None if detached HEAD.
        """
        result = self.run(
            ["symbolic-ref", "--short", "HEAD"],
            check=False,
        )
        if result.exit_code == 0:
            return result.stdout.strip()
        return None

    # =========================================================================
    # Configuration
    # =========================================================================

    def config_get(
        self,
        key: str,
        *,
        global_: bool = False,
        default: str | None = None,
    ) -> str | None:
        """Get a git config value.

        Args:
            key: Config key (e.g., "adr.namespace").
            global_: If True, read from global config.
            default: Default value if key not found.

        Returns:
            Config value, or default if not found.
        """
        args = ["config"]
        if global_:
            args.append("--global")
        args.extend(["--get", key])

        result = self.run(args, check=False, allow_exit_codes=[1])
        if result.exit_code == 0:
            return result.stdout.strip()
        return default

    def config_set(
        self,
        key: str,
        value: str,
        *,
        global_: bool = False,
        append: bool = False,
    ) -> None:
        """Set a git config value.

        Args:
            key: Config key to set.
            value: Value to set.
            global_: If True, set in global config.
            append: If True, add to multi-valued key instead of replacing.
        """
        args = ["config"]
        if global_:
            args.append("--global")
        if append:
            args.append("--add")
        args.extend([key, value])
        self.run(args)

    def config_unset(
        self,
        key: str,
        *,
        global_: bool = False,
        all_values: bool = False,
    ) -> bool:
        """Unset a git config value.

        Args:
            key: Config key to unset.
            global_: If True, unset from global config.
            all_values: If True, unset all values for multi-valued keys.

        Returns:
            True if the key was found and removed, False if it didn't exist.
        """
        args = ["config"]
        if global_:
            args.append("--global")
        unset_flag = "--unset-all" if all_values else "--unset"
        args.extend([unset_flag, key])

        result = self.run(args, check=False, allow_exit_codes=[5])
        return result.exit_code == 0

    def config_list(self, *, global_: bool = False) -> dict[str, str]:
        """List all config values.

        Args:
            global_: If True, list only global config.

        Returns:
            Dictionary of config key-value pairs.
        """
        args = ["config", "--list"]
        if global_:
            args.append("--global")

        result = self.run(args, check=False)
        config: dict[str, str] = {}

        for line in result.lines:
            if "=" in line:
                key, _, value = line.partition("=")
                config[key] = value

        return config

    def config_add(
        self,
        key: str,
        value: str,
        *,
        global_: bool = False,
    ) -> None:
        """Add a config value (allows multiple values for same key).

        Args:
            key: Config key.
            value: Value to add.
            global_: If True, add to global config.
        """
        args = ["config"]
        if global_:
            args.append("--global")
        args.extend(["--add", key, value])
        self.run(args)

    def config_get_all(
        self,
        key: str,
        *,
        global_: bool = False,
    ) -> list[str]:
        """Get all values for a multi-valued config key.

        Args:
            key: Config key (e.g., "remote.origin.push").
            global_: If True, read from global config.

        Returns:
            List of all values for the key (empty list if not found).
        """
        args = ["config"]
        if global_:
            args.append("--global")
        args.extend(["--get-all", key])

        result = self.run(args, check=False, allow_exit_codes=[1])
        if result.exit_code == 0:
            return [line for line in result.lines if line]
        return []

    # =========================================================================
    # Remote Operations
    # =========================================================================

    def get_remotes(self) -> list[str]:
        """Get list of configured remotes.

        Returns:
            List of remote names.
        """
        result = self.run(["remote"], check=False)
        return result.lines if result.success else []

    def get_remote_url(self, remote: str = "origin") -> str | None:
        """Get the URL for a remote.

        Args:
            remote: Remote name.

        Returns:
            Remote URL, or None if remote doesn't exist.
        """
        result = self.run(
            ["remote", "get-url", remote],
            check=False,
        )
        if result.success:
            return result.stdout.strip()
        return None

    # =========================================================================
    # Commit Operations
    # =========================================================================

    def commit_exists(self, sha: str) -> bool:
        """Check if a commit SHA exists.

        Args:
            sha: Commit SHA to check.

        Returns:
            True if commit exists, False otherwise.
        """
        result = self.run(
            ["cat-file", "-t", sha],
            check=False,
        )
        return result.success and result.stdout.strip() == "commit"

    def get_commit_message(self, sha: str) -> str:
        """Get the commit message for a SHA.

        Args:
            sha: Commit SHA.

        Returns:
            Commit message.
        """
        result = self.run(["log", "-1", "--format=%B", sha])
        return result.stdout.strip()

    def get_commit_date(self, sha: str) -> str:
        """Get the commit date in ISO format.

        Args:
            sha: Commit SHA.

        Returns:
            Commit date in ISO 8601 format.
        """
        result = self.run(["log", "-1", "--format=%aI", sha])
        return result.stdout.strip()

    # =========================================================================
    # Git Notes Operations
    # =========================================================================

    def notes_add(
        self,
        message: str,
        obj: str | None = None,
        ref: str = "refs/notes/commits",
        *,
        force: bool = False,
    ) -> None:
        """Add a note to an object.

        Args:
            message: Note content.
            obj: Object to annotate (default: HEAD).
            ref: Notes reference (default: refs/notes/commits).
            force: If True, overwrite existing note.
        """
        args = ["notes", f"--ref={ref}", "add"]
        if force:
            args.append("-f")
        args.extend(["-m", message])
        if obj:
            args.append(obj)
        self.run(args)

    def notes_append(
        self,
        message: str,
        obj: str | None = None,
        ref: str = "refs/notes/commits",
    ) -> None:
        """Append to an existing note.

        Args:
            message: Content to append.
            obj: Object with the note.
            ref: Notes reference.
        """
        args = ["notes", f"--ref={ref}", "append", "-m", message]
        if obj:
            args.append(obj)
        self.run(args)

    def notes_show(
        self,
        obj: str | None = None,
        ref: str = "refs/notes/commits",
    ) -> str | None:
        """Get the note for an object.

        Args:
            obj: Object to get note for (default: HEAD).
            ref: Notes reference.

        Returns:
            Note content, or None if no note exists.
        """
        args = ["notes", f"--ref={ref}", "show"]
        if obj:
            args.append(obj)

        result = self.run(args, check=False, allow_exit_codes=[1])
        if result.exit_code == 0:
            return result.stdout
        return None

    def notes_list(
        self,
        ref: str = "refs/notes/commits",
    ) -> list[tuple[str, str]]:
        """List all notes in a reference.

        Args:
            ref: Notes reference.

        Returns:
            List of (note_sha, object_sha) tuples.
        """
        args = ["notes", f"--ref={ref}", "list"]
        result = self.run(args, check=False, allow_exit_codes=[1])

        if not result.success:
            return []

        notes: list[tuple[str, str]] = []
        for line in result.lines:
            parts = line.split()
            if len(parts) == 2:
                notes.append((parts[0], parts[1]))

        return notes

    def notes_remove(
        self,
        obj: str | None = None,
        ref: str = "refs/notes/commits",
    ) -> bool:
        """Remove a note from an object.

        Args:
            obj: Object to remove note from (default: HEAD).
            ref: Notes reference.

        Returns:
            True if note was removed, False if no note existed.
        """
        args = ["notes", f"--ref={ref}", "remove"]
        if obj:
            args.append(obj)

        result = self.run(args, check=False, allow_exit_codes=[1])
        return result.exit_code == 0

    def notes_copy(
        self,
        from_obj: str,
        to_obj: str,
        ref: str = "refs/notes/commits",
        *,
        force: bool = False,
    ) -> None:
        """Copy a note from one object to another.

        Args:
            from_obj: Source object.
            to_obj: Destination object.
            ref: Notes reference.
            force: If True, overwrite existing note on destination.
        """
        args = ["notes", f"--ref={ref}", "copy"]
        if force:
            args.append("-f")
        args.extend([from_obj, to_obj])
        self.run(args)

    def notes_merge(
        self,
        ref: str,
        source_ref: str,
        *,
        strategy: str = "union",
    ) -> None:
        """Merge notes from one reference into another.

        Args:
            ref: Target notes reference.
            source_ref: Source notes reference.
            strategy: Merge strategy (union, ours, theirs, cat_sort_uniq).
        """
        args = ["notes", f"--ref={ref}", "merge", f"--strategy={strategy}", source_ref]
        self.run(args)

    def notes_prune(self, ref: str = "refs/notes/commits") -> None:
        """Remove notes for objects that no longer exist.

        Args:
            ref: Notes reference to prune.
        """
        self.run(["notes", f"--ref={ref}", "prune"])

    def cat_file_batch(
        self,
        shas: list[str],
    ) -> dict[str, str | None]:
        """Fetch multiple objects in a single subprocess call.

        Uses `git cat-file --batch` for efficient batch retrieval,
        reducing N subprocess calls to 1.

        Args:
            shas: List of object SHAs to retrieve.

        Returns:
            Dictionary mapping SHA to content (None if not found).
        """
        if not shas:
            return {}

        # Build input: one SHA per line
        input_data = "\n".join(shas) + "\n"

        result = self.run(
            ["cat-file", "--batch"],
            input_data=input_data,
            check=False,
            timeout=60.0,
        )

        if not result.success:
            return dict.fromkeys(shas)

        # Parse batch output:
        # <sha> <type> <size>\n<content>\n
        # or: <sha> missing\n
        contents: dict[str, str | None] = {}
        output = result.stdout
        pos = 0

        for sha in shas:
            # Find the header line for this object
            newline_pos = output.find("\n", pos)
            if newline_pos == -1:
                contents[sha] = None
                continue

            header = output[pos:newline_pos]
            pos = newline_pos + 1

            if "missing" in header:
                contents[sha] = None
                continue

            # Parse header: <sha> <type> <size>
            parts = header.split()
            if len(parts) < 3:
                contents[sha] = None
                continue

            try:
                size = int(parts[2])
            except ValueError:
                contents[sha] = None
                continue

            # Extract content of specified size
            content = output[pos : pos + size]
            pos = pos + size + 1  # +1 for trailing newline

            contents[sha] = content

        return contents

    # =========================================================================
    # Fetch/Push Operations
    # =========================================================================

    def fetch(
        self,
        remote: str = "origin",
        refspec: str | None = None,
        *,
        prune: bool = False,
    ) -> None:
        """Fetch from a remote.

        Args:
            remote: Remote name.
            refspec: Specific refspec to fetch.
            prune: If True, prune deleted remote branches.
        """
        args = ["fetch", remote]
        if refspec:
            args.append(refspec)
        if prune:
            args.append("--prune")
        self.run(args, timeout=60.0)

    def push(
        self,
        remote: str = "origin",
        refspec: str | None = None,
        *,
        force: bool = False,
        timeout: float | None = None,
    ) -> None:
        """Push to a remote.

        Args:
            remote: Remote name.
            refspec: Specific refspec to push.
            force: If True, force push.
            timeout: Optional timeout in seconds (default: 60.0).
        """
        args = ["push", remote]
        if refspec:
            args.append(refspec)
        if force:
            args.append("--force")
        self.run(args, timeout=timeout if timeout is not None else 60.0)

    def fetch_notes(
        self,
        remote: str = "origin",
        ref: str = "refs/notes/adr",
    ) -> None:
        """Fetch notes from a remote.

        Args:
            remote: Remote name.
            ref: Notes reference to fetch.
        """
        # Fetch notes ref
        refspec = f"+{ref}:{ref}"
        self.fetch(remote, refspec)

    def push_notes(
        self,
        remote: str = "origin",
        ref: str = "refs/notes/adr",
        *,
        force: bool = False,
        timeout: float | None = None,
    ) -> None:
        """Push notes to a remote.

        Args:
            remote: Remote name.
            ref: Notes reference to push.
            force: If True, force push.
            timeout: Optional timeout in seconds.
        """
        self.push(remote, ref, force=force, timeout=timeout)


def get_git(cwd: Path | None = None) -> Git:
    """Get a Git executor for the given directory.

    This is the primary factory function for creating Git instances.

    Args:
        cwd: Working directory (default: current directory).

    Returns:
        Configured Git executor.

    Raises:
        GitNotFoundError: If git is not installed.
    """
    return Git(cwd=cwd)
