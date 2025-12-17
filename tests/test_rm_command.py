"""Tests for git adr rm command."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from git_adr.cli import app

runner = CliRunner()


class TestRmCommand:
    """Tests for rm command."""

    def test_rm_help(self) -> None:
        """Test rm --help."""
        result = runner.invoke(app, ["rm", "--help"])
        assert result.exit_code == 0
        assert "remove" in result.output.lower() or "adr" in result.output.lower()

    def test_rm_not_initialized(self, temp_git_repo: Path) -> None:
        """Test rm in non-initialized repo."""
        result = runner.invoke(app, ["rm", "some-adr"])
        assert result.exit_code != 0
        assert (
            "not initialized" in result.output.lower()
            or "error" in result.output.lower()
        )

    def test_rm_not_found(self, adr_repo_with_data: Path) -> None:
        """Test rm for non-existent ADR."""
        result = runner.invoke(app, ["rm", "nonexistent-adr", "--force"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_rm_success_force(self, adr_repo_with_data: Path) -> None:
        """Test successful rm with --force."""
        # Verify ADR exists first
        list_result = runner.invoke(app, ["list"])
        assert "20250110-use-postgresql" in list_result.output

        # Remove with force
        result = runner.invoke(app, ["rm", "20250110-use-postgresql", "--force"])
        assert result.exit_code == 0
        assert "removed" in result.output.lower()

        # Verify ADR is gone
        list_result = runner.invoke(app, ["list"])
        assert "20250110-use-postgresql" not in list_result.output

    def test_rm_interactive_confirm(self, adr_repo_with_data: Path) -> None:
        """Test rm with interactive confirmation (yes)."""
        result = runner.invoke(
            app,
            ["rm", "20250112-use-redis"],
            input="y\n",
        )
        assert result.exit_code == 0
        assert "removed" in result.output.lower()

    def test_rm_interactive_abort(self, adr_repo_with_data: Path) -> None:
        """Test rm with interactive abort (no)."""
        result = runner.invoke(
            app,
            ["rm", "20250115-use-react"],
            input="n\n",
        )
        assert result.exit_code == 0
        assert "aborted" in result.output.lower()

        # Verify ADR still exists
        list_result = runner.invoke(app, ["list"])
        assert "20250115-use-react" in list_result.output

    def test_rm_shows_adr_info(self, adr_repo_with_data: Path) -> None:
        """Test rm displays ADR info before confirmation."""
        result = runner.invoke(
            app,
            ["rm", "20250110-use-postgresql"],
            input="n\n",
        )
        # Should show title in output
        assert "postgresql" in result.output.lower()
        # Should show status
        assert "accepted" in result.output.lower() or "status" in result.output.lower()


class TestRmCommandEdgeCases:
    """Edge case tests for rm command."""

    def test_rm_outside_git_repo(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test rm outside git repo."""
        # Create a non-git directory
        non_git_dir = tmp_path / "not-a-repo"
        non_git_dir.mkdir()
        monkeypatch.chdir(non_git_dir)

        result = runner.invoke(app, ["rm", "some-adr", "--force"])
        assert result.exit_code != 0
        assert (
            "not a git repository" in result.output.lower()
            or "error" in result.output.lower()
        )

    def test_rm_preserves_other_adrs(self, adr_repo_with_data: Path) -> None:
        """Test that rm only removes the specified ADR."""
        # Remove one ADR
        result = runner.invoke(app, ["rm", "20250110-use-postgresql", "--force"])
        assert result.exit_code == 0

        # Other ADRs should still exist
        list_result = runner.invoke(app, ["list"])
        assert "20250112-use-redis" in list_result.output
        assert "20250115-use-react" in list_result.output


class TestRmWithLinkedCommits:
    """Tests for rm command with linked commits."""

    def test_rm_shows_linked_commits_warning(self, adr_repo_with_data: Path) -> None:
        """Test rm displays warning for ADR with linked commits."""
        from git_adr.core import ConfigManager, NotesManager
        from git_adr.core.git import Git

        git = Git(cwd=adr_repo_with_data)
        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)

        # Link a commit to the ADR
        adr = notes_manager.get("20250110-use-postgresql")
        if adr:
            adr.metadata.linked_commits = ["abc12345", "def67890"]
            notes_manager.update(adr)

        result = runner.invoke(
            app,
            ["rm", "20250110-use-postgresql"],
            input="n\n",
        )
        assert (
            "linked to commits" in result.output.lower() or "abc1234" in result.output
        )


class TestRmWithSupersession:
    """Tests for rm command with supersession relationships."""

    def test_rm_shows_supersedes_warning(self, adr_repo_with_data: Path) -> None:
        """Test rm displays warning for ADR that supersedes another."""
        from git_adr.core import ConfigManager, NotesManager
        from git_adr.core.git import Git

        git = Git(cwd=adr_repo_with_data)
        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)

        # Set supersedes on the ADR
        adr = notes_manager.get("20250110-use-postgresql")
        if adr:
            adr.metadata.supersedes = "20240101-use-mysql"
            notes_manager.update(adr)

        result = runner.invoke(
            app,
            ["rm", "20250110-use-postgresql"],
            input="n\n",
        )
        assert "supersedes" in result.output.lower()

    def test_rm_shows_superseded_by_warning(self, adr_repo_with_data: Path) -> None:
        """Test rm displays warning for ADR superseded by another."""
        from git_adr.core import ConfigManager, NotesManager
        from git_adr.core.git import Git

        git = Git(cwd=adr_repo_with_data)
        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)

        # Set superseded_by on the ADR
        adr = notes_manager.get("20250110-use-postgresql")
        if adr:
            adr.metadata.superseded_by = "20250201-use-sqlite"
            notes_manager.update(adr)

        result = runner.invoke(
            app,
            ["rm", "20250110-use-postgresql"],
            input="n\n",
        )
        assert "superseded by" in result.output.lower()


class TestRmGitErrors:
    """Tests for rm command with git errors."""

    def test_rm_git_error_handling(
        self, adr_repo_with_data: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test rm handles GitError gracefully."""
        from unittest.mock import patch

        from git_adr.core import GitError

        # Mock NotesManager.remove to raise GitError
        # GitError requires: message, command (list), exit_code
        with patch(
            "git_adr.core.notes.NotesManager.remove",
            side_effect=GitError(
                "Simulated git error",
                ["git", "notes", "remove"],
                1,
            ),
        ):
            result = runner.invoke(app, ["rm", "20250110-use-postgresql", "--force"])
            assert result.exit_code != 0
            assert "error" in result.output.lower()

    def test_rm_remove_failure(
        self, adr_repo_with_data: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test rm handles remove returning False."""
        from unittest.mock import patch

        # Mock NotesManager.remove to return False
        with patch(
            "git_adr.core.notes.NotesManager.remove",
            return_value=False,
        ):
            result = runner.invoke(app, ["rm", "20250110-use-postgresql", "--force"])
            assert result.exit_code != 0
            assert "failed" in result.output.lower() or "error" in result.output.lower()
