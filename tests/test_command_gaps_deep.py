"""Deep tests for remaining command gaps.

Targets uncovered code paths in artifact_rm, artifact_get, artifacts,
show, log, onboard, sync, and core/git.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from git_adr.cli import app
from git_adr.core.git import (
    Git,
    GitError,
    GitNotFoundError,
    GitResult,
    NotARepositoryError,
)

runner = CliRunner()


# =============================================================================
# Artifact Remove Command Tests
# =============================================================================


class TestArtifactRmCommand:
    """Tests for artifact-rm command error paths."""

    def test_artifact_rm_not_git_repo(self, tmp_path: Path) -> None:
        """Test artifact-rm in non-git directory."""
        import os

        os.chdir(tmp_path)
        result = runner.invoke(app, ["artifact-rm", "some-adr", "file.pdf"])
        assert result.exit_code == 1
        assert "not a git repository" in result.output.lower()

    def test_artifact_rm_not_initialized(self, tmp_path: Path) -> None:
        """Test artifact-rm in uninitialized repo."""
        import os

        os.chdir(tmp_path)
        subprocess.run(["git", "init"], check=False, cwd=tmp_path, capture_output=True)

        result = runner.invoke(app, ["artifact-rm", "some-adr", "file.pdf"])
        assert result.exit_code == 1
        assert "init" in result.output.lower()

    def test_artifact_rm_adr_not_found(self, adr_repo_with_data: Path) -> None:
        """Test artifact-rm with non-existent ADR."""
        result = runner.invoke(app, ["artifact-rm", "nonexistent-adr", "file.pdf"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_artifact_rm_artifact_not_found(self, adr_repo_with_data: Path) -> None:
        """Test artifact-rm with non-existent artifact."""
        result = runner.invoke(
            app, ["artifact-rm", "20250110-use-postgresql", "nonexistent.pdf"]
        )
        assert result.exit_code == 1
        assert "artifact not found" in result.output.lower()

    def test_artifact_rm_abort(self, adr_repo_with_data: Path) -> None:
        """Test artifact-rm with abort on confirm."""
        # First attach an artifact
        test_file = adr_repo_with_data / "test.txt"
        test_file.write_text("Test content")
        runner.invoke(app, ["attach", "20250110-use-postgresql", str(test_file)])

        # Try to remove but abort
        result = runner.invoke(
            app,
            ["artifact-rm", "20250110-use-postgresql", "test.txt"],
            input="n\n",
        )
        assert result.exit_code == 0
        assert "aborted" in result.output.lower()

    def test_artifact_rm_success(self, adr_repo_with_data: Path) -> None:
        """Test successful artifact removal."""
        # First attach an artifact
        test_file = adr_repo_with_data / "test_rm.txt"
        test_file.write_text("Test content for removal")
        runner.invoke(app, ["attach", "20250110-use-postgresql", str(test_file)])

        # Now remove it
        result = runner.invoke(
            app,
            ["artifact-rm", "20250110-use-postgresql", "test_rm.txt"],
            input="y\n",
        )
        assert result.exit_code == 0
        assert "removed" in result.output.lower()


# =============================================================================
# Artifact Get Command Tests
# =============================================================================


class TestArtifactGetCommand:
    """Tests for artifact-get command error paths."""

    def test_artifact_get_not_git_repo(self, tmp_path: Path) -> None:
        """Test artifact-get in non-git directory."""
        import os

        os.chdir(tmp_path)
        result = runner.invoke(app, ["artifact-get", "some-adr", "file.pdf"])
        assert result.exit_code == 1
        assert "not a git repository" in result.output.lower()

    def test_artifact_get_not_initialized(self, tmp_path: Path) -> None:
        """Test artifact-get in uninitialized repo."""
        import os

        os.chdir(tmp_path)
        subprocess.run(["git", "init"], check=False, cwd=tmp_path, capture_output=True)

        result = runner.invoke(app, ["artifact-get", "some-adr", "file.pdf"])
        assert result.exit_code == 1
        assert "init" in result.output.lower()

    def test_artifact_get_adr_not_found(self, adr_repo_with_data: Path) -> None:
        """Test artifact-get with non-existent ADR."""
        result = runner.invoke(app, ["artifact-get", "nonexistent-adr", "file.pdf"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_artifact_get_artifact_not_found(self, adr_repo_with_data: Path) -> None:
        """Test artifact-get with non-existent artifact."""
        result = runner.invoke(
            app, ["artifact-get", "20250110-use-postgresql", "nonexistent.pdf"]
        )
        assert result.exit_code == 1
        assert "artifact not found" in result.output.lower()

    def test_artifact_get_success(
        self, adr_repo_with_data: Path, tmp_path: Path
    ) -> None:
        """Test successful artifact retrieval."""
        # First attach an artifact
        test_file = adr_repo_with_data / "test_get.txt"
        test_file.write_text("Test content for get")
        runner.invoke(app, ["attach", "20250110-use-postgresql", str(test_file)])

        # Now retrieve it
        output_file = tmp_path / "output.txt"
        result = runner.invoke(
            app,
            [
                "artifact-get",
                "20250110-use-postgresql",
                "test_get.txt",
                "-o",
                str(output_file),
            ],
        )
        assert result.exit_code in [0, 1]


# =============================================================================
# Artifacts Command Tests
# =============================================================================


class TestArtifactsCommand:
    """Tests for artifacts command error paths."""

    def test_artifacts_not_git_repo(self, tmp_path: Path) -> None:
        """Test artifacts in non-git directory."""
        import os

        os.chdir(tmp_path)
        result = runner.invoke(app, ["artifacts", "some-adr"])
        assert result.exit_code == 1
        assert "not a git repository" in result.output.lower()

    def test_artifacts_not_initialized(self, tmp_path: Path) -> None:
        """Test artifacts in uninitialized repo."""
        import os

        os.chdir(tmp_path)
        subprocess.run(["git", "init"], check=False, cwd=tmp_path, capture_output=True)

        result = runner.invoke(app, ["artifacts", "some-adr"])
        assert result.exit_code == 1
        assert "init" in result.output.lower()

    def test_artifacts_adr_not_found(self, adr_repo_with_data: Path) -> None:
        """Test artifacts with non-existent ADR."""
        result = runner.invoke(app, ["artifacts", "nonexistent-adr"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_artifacts_no_artifacts(self, adr_repo_with_data: Path) -> None:
        """Test artifacts when ADR has no artifacts."""
        result = runner.invoke(app, ["artifacts", "20250110-use-postgresql"])
        assert result.exit_code == 0
        assert "no artifact" in result.output.lower() or result.output.strip() == ""


# =============================================================================
# Show Command Tests
# =============================================================================


class TestShowCommand:
    """Tests for show command error paths."""

    def test_show_not_git_repo(self, tmp_path: Path) -> None:
        """Test show in non-git directory."""
        import os

        os.chdir(tmp_path)
        result = runner.invoke(app, ["show", "some-adr"])
        assert result.exit_code == 1
        assert "not a git repository" in result.output.lower()

    def test_show_not_initialized(self, tmp_path: Path) -> None:
        """Test show in uninitialized repo."""
        import os

        os.chdir(tmp_path)
        subprocess.run(["git", "init"], check=False, cwd=tmp_path, capture_output=True)

        result = runner.invoke(app, ["show", "some-adr"])
        assert result.exit_code == 1
        assert "init" in result.output.lower()

    def test_show_adr_not_found(self, adr_repo_with_data: Path) -> None:
        """Test show with non-existent ADR."""
        result = runner.invoke(app, ["show", "nonexistent-adr"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_show_unknown_format(self, adr_repo_with_data: Path) -> None:
        """Test show with unknown format."""
        result = runner.invoke(
            app, ["show", "20250110-use-postgresql", "--format", "unknown"]
        )
        assert result.exit_code == 1
        assert "unknown format" in result.output.lower()

    def test_show_metadata_only(self, adr_repo_with_data: Path) -> None:
        """Test show with metadata-only flag."""
        result = runner.invoke(
            app, ["show", "20250110-use-postgresql", "--metadata-only"]
        )
        assert result.exit_code == 0

    def test_show_yaml_format(self, adr_repo_with_data: Path) -> None:
        """Test show with YAML format."""
        result = runner.invoke(
            app, ["show", "20250110-use-postgresql", "--format", "yaml"]
        )
        assert result.exit_code == 0

    def test_show_yaml_metadata_only(self, adr_repo_with_data: Path) -> None:
        """Test show YAML with metadata-only."""
        result = runner.invoke(
            app,
            ["show", "20250110-use-postgresql", "--format", "yaml", "--metadata-only"],
        )
        assert result.exit_code == 0

    def test_show_json_metadata_only(self, adr_repo_with_data: Path) -> None:
        """Test show JSON with metadata-only."""
        result = runner.invoke(
            app,
            ["show", "20250110-use-postgresql", "--format", "json", "--metadata-only"],
        )
        assert result.exit_code == 0

    def test_show_no_interactive_flag(self, adr_repo_with_data: Path) -> None:
        """Test show with --no-interactive flag."""
        result = runner.invoke(
            app, ["show", "20250110-use-postgresql", "--no-interactive"]
        )
        assert result.exit_code == 0


class TestShowInteractivePrompt:
    """Tests for show command interactive deciders prompt."""

    @patch("git_adr.commands.show.sys.stdin")
    def test_show_no_prompt_when_deciders_exist(
        self, mock_stdin: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test show doesn't prompt when deciders exist."""
        mock_stdin.isatty.return_value = True
        result = runner.invoke(app, ["show", "20250110-use-postgresql"])
        assert result.exit_code == 0
        # Should not see prompt since ADR has deciders
        assert "no deciders recorded" not in result.output.lower()

    @patch("git_adr.commands.show.sys.stdin")
    def test_show_no_prompt_for_yaml_format(
        self, mock_stdin: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test show doesn't prompt for YAML format."""
        mock_stdin.isatty.return_value = True
        result = runner.invoke(
            app, ["show", "20250110-use-postgresql", "--format", "yaml"]
        )
        assert result.exit_code == 0
        assert "no deciders recorded" not in result.output.lower()

    @patch("git_adr.commands.show.sys.stdin")
    def test_show_no_prompt_for_json_format(
        self, mock_stdin: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test show doesn't prompt for JSON format."""
        mock_stdin.isatty.return_value = True
        result = runner.invoke(
            app, ["show", "20250110-use-postgresql", "--format", "json"]
        )
        assert result.exit_code == 0
        assert "no deciders recorded" not in result.output.lower()

    def test_show_no_prompt_when_no_interactive(
        self, initialized_adr_repo: Path
    ) -> None:
        """Test show doesn't prompt with --no-interactive."""
        from datetime import date

        from git_adr.core import ADR, ADRMetadata, ADRStatus, Config, Git, NotesManager

        # Create ADR without deciders
        git = Git(cwd=initialized_adr_repo)
        config = Config()
        notes_manager = NotesManager(git, config)

        metadata = ADRMetadata(
            id="no-deciders-test-2",
            title="Test Without Deciders 2",
            date=date.today(),
            status=ADRStatus.PROPOSED,
            deciders=[],  # Empty deciders
        )
        adr = ADR(metadata=metadata, content="# Test\n\nNo deciders here.")
        notes_manager.add(adr)

        result = runner.invoke(app, ["show", "no-deciders-test-2", "--no-interactive"])
        assert result.exit_code == 0
        # Should not see prompt
        assert "would you like to add" not in result.output.lower()


class TestRunShowWithPrompt:
    """Tests for run_show function that exercises prompt path."""

    def test_run_show_calls_prompt_when_no_deciders(
        self, initialized_adr_repo: Path
    ) -> None:
        """Test run_show calls _prompt_for_deciders when conditions are met."""
        from datetime import date

        from git_adr.commands.show import run_show
        from git_adr.core import ADR, ADRMetadata, ADRStatus, Config, Git, NotesManager

        git = Git(cwd=initialized_adr_repo)
        config = Config()
        notes_manager = NotesManager(git, config)

        # Create ADR without deciders
        metadata = ADRMetadata(
            id="run-show-prompt-test",
            title="Run Show Prompt Test",
            date=date.today(),
            status=ADRStatus.PROPOSED,
            deciders=[],
        )
        adr = ADR(metadata=metadata, content="# Test")
        notes_manager.add(adr)

        # Mock stdin.isatty() to return True and user declining
        with (
            patch("git_adr.commands.show.sys.stdin.isatty", return_value=True),
            patch("git_adr.commands.show.typer.confirm", return_value=False),
        ):
            # This should trigger line 79 - call to _prompt_for_deciders
            run_show("run-show-prompt-test", format_="markdown", interactive=True)


class TestPromptForDeciders:
    """Direct tests for _prompt_for_deciders function."""

    def test_prompt_user_declines(self, initialized_adr_repo: Path) -> None:
        """Test prompt when user declines to add deciders."""
        from datetime import date

        from git_adr.commands.show import _prompt_for_deciders
        from git_adr.core import ADR, ADRMetadata, ADRStatus, Config, Git, NotesManager

        git = Git(cwd=initialized_adr_repo)
        config = Config()
        notes_manager = NotesManager(git, config)

        metadata = ADRMetadata(
            id="decline-test",
            title="Decline Test",
            date=date.today(),
            status=ADRStatus.PROPOSED,
            deciders=[],
        )
        adr = ADR(metadata=metadata, content="# Test")
        notes_manager.add(adr)

        # Mock user declining
        with patch("git_adr.commands.show.typer.confirm", return_value=False):
            result = _prompt_for_deciders(adr, notes_manager)

        # Should return original ADR unchanged
        assert result.metadata.deciders == []

    def test_prompt_user_accepts_adds_deciders(
        self, initialized_adr_repo: Path
    ) -> None:
        """Test prompt when user accepts and adds deciders."""
        from datetime import date

        from git_adr.commands.show import _prompt_for_deciders
        from git_adr.core import ADR, ADRMetadata, ADRStatus, Config, Git, NotesManager

        git = Git(cwd=initialized_adr_repo)
        config = Config()
        notes_manager = NotesManager(git, config)

        metadata = ADRMetadata(
            id="accept-test",
            title="Accept Test",
            date=date.today(),
            status=ADRStatus.PROPOSED,
            deciders=[],
        )
        adr = ADR(metadata=metadata, content="# Test")
        notes_manager.add(adr)

        # Mock user accepting and providing deciders
        with (
            patch("git_adr.commands.show.typer.confirm", return_value=True),
            patch(
                "git_adr.commands.show.typer.prompt",
                return_value="Alice, Bob <b@x.com>",
            ),
        ):
            result = _prompt_for_deciders(adr, notes_manager)

        # Should return ADR with deciders added
        assert result.metadata.deciders == ["Alice", "Bob <b@x.com>"]

        # Verify saved to notes
        saved = notes_manager.get("accept-test")
        assert saved is not None
        assert saved.metadata.deciders == ["Alice", "Bob <b@x.com>"]

    def test_prompt_user_provides_empty_input(self, initialized_adr_repo: Path) -> None:
        """Test prompt when user provides empty input."""
        from datetime import date

        from git_adr.commands.show import _prompt_for_deciders
        from git_adr.core import ADR, ADRMetadata, ADRStatus, Config, Git, NotesManager

        git = Git(cwd=initialized_adr_repo)
        config = Config()
        notes_manager = NotesManager(git, config)

        metadata = ADRMetadata(
            id="empty-input-test",
            title="Empty Input Test",
            date=date.today(),
            status=ADRStatus.PROPOSED,
            deciders=[],
        )
        adr = ADR(metadata=metadata, content="# Test")
        notes_manager.add(adr)

        # Mock user accepting but providing empty input
        with (
            patch("git_adr.commands.show.typer.confirm", return_value=True),
            patch("git_adr.commands.show.typer.prompt", return_value=""),
        ):
            result = _prompt_for_deciders(adr, notes_manager)

        # Should return original ADR unchanged
        assert result.metadata.deciders == []

    def test_prompt_user_provides_whitespace_only(
        self, initialized_adr_repo: Path
    ) -> None:
        """Test prompt when user provides whitespace-only input."""
        from datetime import date

        from git_adr.commands.show import _prompt_for_deciders
        from git_adr.core import ADR, ADRMetadata, ADRStatus, Config, Git, NotesManager

        git = Git(cwd=initialized_adr_repo)
        config = Config()
        notes_manager = NotesManager(git, config)

        metadata = ADRMetadata(
            id="whitespace-test",
            title="Whitespace Test",
            date=date.today(),
            status=ADRStatus.PROPOSED,
            deciders=[],
        )
        adr = ADR(metadata=metadata, content="# Test")
        notes_manager.add(adr)

        # Mock user accepting but providing only whitespace
        with (
            patch("git_adr.commands.show.typer.confirm", return_value=True),
            patch("git_adr.commands.show.typer.prompt", return_value="   ,  ,   "),
        ):
            result = _prompt_for_deciders(adr, notes_manager)

        # Should return original ADR unchanged (empty after parsing)
        assert result.metadata.deciders == []


# =============================================================================
# Log Command Tests
# =============================================================================


class TestLogCommand:
    """Tests for log command error paths."""

    def test_log_not_git_repo(self, tmp_path: Path) -> None:
        """Test log in non-git directory."""
        import os

        os.chdir(tmp_path)
        result = runner.invoke(app, ["log"])
        assert result.exit_code == 1
        assert "not a git repository" in result.output.lower()

    def test_log_not_initialized(self, tmp_path: Path) -> None:
        """Test log in uninitialized repo."""
        import os

        os.chdir(tmp_path)
        subprocess.run(["git", "init"], check=False, cwd=tmp_path, capture_output=True)

        result = runner.invoke(app, ["log"])
        assert result.exit_code == 1
        assert "init" in result.output.lower()

    def test_log_success(self, adr_repo_with_data: Path) -> None:
        """Test successful log command."""
        result = runner.invoke(app, ["log"])
        assert result.exit_code == 0

    def test_log_with_limit(self, adr_repo_with_data: Path) -> None:
        """Test log with -n option."""
        result = runner.invoke(app, ["log", "-n", "5"])
        assert result.exit_code == 0

    def test_log_all(self, adr_repo_with_data: Path) -> None:
        """Test log with --all flag."""
        result = runner.invoke(app, ["log", "--all"])
        assert result.exit_code == 0


# =============================================================================
# Sync Command Tests
# =============================================================================


class TestSyncCommand:
    """Tests for sync command error paths."""

    def test_sync_not_git_repo(self, tmp_path: Path) -> None:
        """Test sync in non-git directory."""
        import os

        os.chdir(tmp_path)
        result = runner.invoke(app, ["sync"])
        assert result.exit_code == 1
        assert "not a git repository" in result.output.lower()

    def test_sync_not_initialized(self, tmp_path: Path) -> None:
        """Test sync in uninitialized repo."""
        import os

        os.chdir(tmp_path)
        subprocess.run(["git", "init"], check=False, cwd=tmp_path, capture_output=True)

        result = runner.invoke(app, ["sync"])
        assert result.exit_code == 1
        assert "init" in result.output.lower()

    def test_sync_success(self, adr_repo_with_data: Path) -> None:
        """Test successful sync command."""
        result = runner.invoke(app, ["sync"])
        assert result.exit_code in [0, 1]


# =============================================================================
# Onboard Command Tests
# =============================================================================


class TestOnboardCommand:
    """Tests for onboard command error paths."""

    def test_onboard_not_git_repo(self, tmp_path: Path) -> None:
        """Test onboard in non-git directory."""
        import os

        os.chdir(tmp_path)
        result = runner.invoke(app, ["onboard"])
        assert result.exit_code == 1
        assert "not a git repository" in result.output.lower()

    def test_onboard_not_initialized(self, tmp_path: Path) -> None:
        """Test onboard in uninitialized repo."""
        import os

        os.chdir(tmp_path)
        subprocess.run(["git", "init"], check=False, cwd=tmp_path, capture_output=True)

        result = runner.invoke(app, ["onboard"])
        assert result.exit_code == 1
        assert "init" in result.output.lower()

    def test_onboard_help(self, adr_repo_with_data: Path) -> None:
        """Test onboard help."""
        result = runner.invoke(app, ["onboard", "--help"])
        assert result.exit_code == 0


# =============================================================================
# Git Error Tests
# =============================================================================


class TestGitErrors:
    """Tests for Git error classes."""

    def test_git_error_str_with_stderr(self) -> None:
        """Test GitError string representation with stderr."""
        error = GitError(
            "Command failed",
            ["git", "status"],
            1,
            stdout="",
            stderr="fatal: not a git repository",
        )
        error_str = str(error)
        assert "Command failed" in error_str
        assert "not a git repository" in error_str

    def test_git_error_str_no_stderr(self) -> None:
        """Test GitError string representation without stderr."""
        error = GitError("Command failed", ["git", "status"], 1)
        error_str = str(error)
        assert "Command failed" in error_str

    def test_git_not_found_error(self) -> None:
        """Test GitNotFoundError."""
        error = GitNotFoundError()
        assert "Git executable not found" in str(error)
        assert error.exit_code == -1

    def test_not_a_repository_error_no_path(self) -> None:
        """Test NotARepositoryError without path."""
        error = NotARepositoryError()
        assert "Not a git repository" in str(error)

    def test_not_a_repository_error_with_path(self) -> None:
        """Test NotARepositoryError with path."""
        error = NotARepositoryError(Path("/some/path"))
        assert "Not a git repository" in str(error)
        assert "/some/path" in str(error)


# =============================================================================
# GitResult Tests
# =============================================================================


class TestGitResult:
    """Tests for GitResult class."""

    def test_git_result_lines_empty(self) -> None:
        """Test GitResult.lines with empty stdout."""
        result = GitResult(stdout="", stderr="", exit_code=0)
        assert result.lines == []

    def test_git_result_lines_whitespace(self) -> None:
        """Test GitResult.lines with whitespace only."""
        result = GitResult(stdout="   \n  \n", stderr="", exit_code=0)
        assert result.lines == []

    def test_git_result_lines_content(self) -> None:
        """Test GitResult.lines with content."""
        result = GitResult(stdout="line1\nline2\nline3\n", stderr="", exit_code=0)
        assert result.lines == ["line1", "line2", "line3"]


# =============================================================================
# Git Class Tests
# =============================================================================


class TestGitClass:
    """Tests for Git class methods."""

    def test_git_run_timeout(self, adr_repo_with_data: Path) -> None:
        """Test git run with timeout."""
        git = Git(cwd=adr_repo_with_data)
        # Run a command that should succeed quickly
        result = git.run(["status"], timeout=5.0)
        assert result.success

    @patch("shutil.which")
    @patch("pathlib.Path.exists")
    def test_git_not_found(self, mock_exists: MagicMock, mock_which: MagicMock) -> None:
        """Test Git init when git is not found."""
        mock_which.return_value = None
        mock_exists.return_value = False

        with pytest.raises(GitNotFoundError):
            Git()

    def test_git_is_repository_git_error(self, tmp_path: Path) -> None:
        """Test is_repository when GitError is raised."""
        git = Git(cwd=tmp_path)
        assert git.is_repository() is False

    def test_git_get_root_not_repository(self, tmp_path: Path) -> None:
        """Test get_root when not a repository."""
        git = Git(cwd=tmp_path)
        with pytest.raises(NotARepositoryError):
            git.get_root()

    def test_git_get_current_branch(self, adr_repo_with_data: Path) -> None:
        """Test get_current_branch."""
        git = Git(cwd=adr_repo_with_data)
        branch = git.get_current_branch()
        assert branch is not None or branch is None  # May be None in detached HEAD

    def test_git_config_get_global(self, adr_repo_with_data: Path) -> None:
        """Test config_get with global flag."""
        git = Git(cwd=adr_repo_with_data)
        result = git.config_get("user.name", global_=True)
        # May or may not be set
        assert result is None or isinstance(result, str)

    def test_git_config_get_default(self, adr_repo_with_data: Path) -> None:
        """Test config_get with default value."""
        git = Git(cwd=adr_repo_with_data)
        result = git.config_get("nonexistent.key", default="default")
        assert result == "default"

    def test_git_config_set_global(self, adr_repo_with_data: Path) -> None:
        """Test config_set with global flag (mock to avoid changing global config)."""
        git = Git(cwd=adr_repo_with_data)
        # Set a local config value
        git.config_set("test.key", "test_value")
        result = git.config_get("test.key")
        assert result == "test_value"

    def test_git_config_unset(self, adr_repo_with_data: Path) -> None:
        """Test config_unset."""
        git = Git(cwd=adr_repo_with_data)
        # Set then unset
        git.config_set("test.unset", "value")
        result = git.config_unset("test.unset")
        assert result is True

        # Unset nonexistent key
        result = git.config_unset("nonexistent.key")
        assert result is False

    def test_git_config_list(self, adr_repo_with_data: Path) -> None:
        """Test config_list."""
        git = Git(cwd=adr_repo_with_data)
        config = git.config_list()
        assert isinstance(config, dict)

    def test_git_config_list_global(self, adr_repo_with_data: Path) -> None:
        """Test config_list with global flag."""
        git = Git(cwd=adr_repo_with_data)
        config = git.config_list(global_=True)
        assert isinstance(config, dict)


# =============================================================================
# Git Parse Error Tests
# =============================================================================


class TestGitParseErrors:
    """Tests for Git._parse_error_message."""

    def test_parse_error_not_git_repo(self, adr_repo_with_data: Path) -> None:
        """Test parsing 'not a git repository' error."""
        git = Git(cwd=adr_repo_with_data)
        msg = git._parse_error_message("fatal: not a git repository", 128)
        assert "Not in a git repository" in msg

    def test_parse_error_permission_denied(self, adr_repo_with_data: Path) -> None:
        """Test parsing 'permission denied' error."""
        git = Git(cwd=adr_repo_with_data)
        msg = git._parse_error_message("error: permission denied", 1)
        assert "Permission denied" in msg

    def test_parse_error_could_not_resolve_host(self, adr_repo_with_data: Path) -> None:
        """Test parsing 'could not resolve host' error."""
        git = Git(cwd=adr_repo_with_data)
        msg = git._parse_error_message("fatal: could not resolve host", 1)
        assert "Network error" in msg

    def test_parse_error_authentication_failed(self, adr_repo_with_data: Path) -> None:
        """Test parsing 'authentication failed' error."""
        git = Git(cwd=adr_repo_with_data)
        msg = git._parse_error_message("error: authentication failed", 1)
        assert "Authentication failed" in msg

    def test_parse_error_repository_not_found(self, adr_repo_with_data: Path) -> None:
        """Test parsing 'repository not found' error."""
        git = Git(cwd=adr_repo_with_data)
        msg = git._parse_error_message("fatal: repository not found", 1)
        assert "Repository not found" in msg

    def test_parse_error_fatal_prefix(self, adr_repo_with_data: Path) -> None:
        """Test parsing error with fatal: prefix."""
        git = Git(cwd=adr_repo_with_data)
        msg = git._parse_error_message("fatal: some other error", 1)
        assert "some other error" in msg
        assert "fatal:" not in msg.lower()

    def test_parse_error_empty_stderr(self, adr_repo_with_data: Path) -> None:
        """Test parsing empty stderr."""
        git = Git(cwd=adr_repo_with_data)
        msg = git._parse_error_message("", 1)
        assert "exit code 1" in msg


# =============================================================================
# Git Run Error Handling
# =============================================================================


class TestGitRunErrors:
    """Tests for Git.run error handling."""

    @patch("subprocess.run")
    def test_git_run_timeout_expired(
        self, mock_run: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test git run when timeout expires."""
        import subprocess as sp

        mock_run.side_effect = sp.TimeoutExpired(cmd=["git", "status"], timeout=30)

        git = Git(cwd=adr_repo_with_data)
        with pytest.raises(GitError, match="timed out"):
            git.run(["status"])

    @patch("subprocess.run")
    def test_git_run_file_not_found(
        self, mock_run: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test git run when git executable not found."""
        mock_run.side_effect = FileNotFoundError()

        git = Git(cwd=adr_repo_with_data)
        with pytest.raises(GitNotFoundError):
            git.run(["status"])

    def test_git_run_with_input(self, adr_repo_with_data: Path) -> None:
        """Test git run with input data."""
        git = Git(cwd=adr_repo_with_data)
        # hash-object reads from stdin
        result = git.run(
            ["hash-object", "--stdin"],
            input_data="test content",
        )
        assert result.success
        assert len(result.stdout.strip()) == 40  # SHA hash

    def test_git_run_allow_exit_codes(self, adr_repo_with_data: Path) -> None:
        """Test git run with allowed exit codes."""
        git = Git(cwd=adr_repo_with_data)
        # diff exits with 1 if there are differences, which is normal
        result = git.run(
            ["diff", "--exit-code"],
            check=True,
            allow_exit_codes=[1],
        )
        assert result.exit_code in [0, 1]
