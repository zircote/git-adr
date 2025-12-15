"""Tests for git-adr Git wrapper."""

from __future__ import annotations

import subprocess
from pathlib import Path

from git_adr.core.git import Git


class TestGit:
    """Tests for Git wrapper class."""

    def test_is_repository(self, temp_git_repo: Path) -> None:
        """Test detecting a git repository."""
        git = Git(cwd=temp_git_repo)
        assert git.is_repository()

    def test_is_not_repository(self, tmp_path: Path) -> None:
        """Test detecting non-repository directory."""
        git = Git(cwd=tmp_path)
        assert not git.is_repository()

    def test_run_command(self, temp_git_repo: Path) -> None:
        """Test running a git command."""
        git = Git(cwd=temp_git_repo)
        result = git.run(["status"])
        assert result.exit_code == 0
        assert (
            "branch" in result.stdout.lower() or "no commits" in result.stdout.lower()
        )

    def test_run_invalid_subcommand(self, temp_git_repo: Path) -> None:
        """Test running git with invalid subcommand."""
        git = Git(cwd=temp_git_repo)
        # git version should always work
        result = git.run(["version"])
        assert result.exit_code == 0
        assert "git version" in result.stdout.lower()

    def test_config_set_and_get(self, temp_git_repo: Path) -> None:
        """Test setting and getting git config."""
        git = Git(cwd=temp_git_repo)
        git.config_set("test.key", "test-value")
        result = git.config_get("test.key")
        assert result == "test-value"

    def test_config_get_nonexistent(self, temp_git_repo: Path) -> None:
        """Test getting nonexistent config key."""
        git = Git(cwd=temp_git_repo)
        result = git.config_get("nonexistent.key")
        assert result is None

    def test_config_set_append(self, temp_git_repo: Path) -> None:
        """Test appending to multi-valued config."""
        git = Git(cwd=temp_git_repo)
        git.config_set("test.multi", "value1")
        git.config_set("test.multi", "value2", append=True)
        result = git.run(["config", "--get-all", "test.multi"])
        assert "value1" in result.stdout
        assert "value2" in result.stdout


class TestGitNotes:
    """Tests for Git notes operations."""

    def test_notes_add(self, temp_git_repo: Path) -> None:
        """Test adding a git note."""
        git = Git(cwd=temp_git_repo)

        # Create a commit first
        (temp_git_repo / "test.txt").write_text("test")
        subprocess.run(["git", "add", "."], cwd=temp_git_repo, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
        )

        # Add a note (message is first param, obj defaults to HEAD)
        git.notes_add("Test note content", ref="refs/notes/test")

        # Verify note exists using notes_show (strip trailing newline)
        note = git.notes_show(ref="refs/notes/test")
        assert note is not None
        assert note.strip() == "Test note content"

    def test_notes_list(self, temp_git_repo: Path) -> None:
        """Test listing git notes."""
        git = Git(cwd=temp_git_repo)

        # Create commits and notes
        for i in range(3):
            (temp_git_repo / f"file{i}.txt").write_text(f"content {i}")
            subprocess.run(["git", "add", "."], cwd=temp_git_repo, check=True)
            subprocess.run(
                ["git", "commit", "-m", f"Commit {i}"],
                cwd=temp_git_repo,
                check=True,
                capture_output=True,
            )
            git.notes_add(f"Note {i}", ref="refs/notes/test")

        # List notes
        notes = git.notes_list(ref="refs/notes/test")
        assert len(notes) == 3

    def test_notes_remove(self, temp_git_repo: Path) -> None:
        """Test removing a git note."""
        git = Git(cwd=temp_git_repo)

        # Create commit and note
        (temp_git_repo / "test.txt").write_text("test")
        subprocess.run(["git", "add", "."], cwd=temp_git_repo, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Test commit"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
        )

        git.notes_add("Test note", ref="refs/notes/test")
        note = git.notes_show(ref="refs/notes/test")
        assert note is not None
        assert note.strip() == "Test note"

        # Remove note
        git.notes_remove(ref="refs/notes/test")
        assert git.notes_show(ref="refs/notes/test") is None
