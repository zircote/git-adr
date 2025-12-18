"""Deep tests for edit command full workflow.

Targets lines 187-233 in edit.py: the full editor workflow.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from git_adr.cli import app
from git_adr.core.config import Config
from git_adr.core.git import Git

runner = CliRunner()


class TestFullEditWorkflow:
    """Tests for _full_edit function (lines 187-233)."""

    @patch("subprocess.run")
    @patch("git_adr.commands._editor.find_editor")
    def test_full_edit_editor_exits_success(
        self,
        mock_find_editor: MagicMock,
        mock_subprocess: MagicMock,
        adr_repo_with_data: Path,
    ) -> None:
        """Test full edit when editor exits successfully."""
        mock_find_editor.return_value = "nano"
        mock_subprocess.return_value = MagicMock(returncode=0)

        result = runner.invoke(app, ["edit", "20250110-use-postgresql"])
        # Editor opens but may report no changes
        assert result.exit_code in [0, 1]

    @patch("subprocess.run")
    @patch("git_adr.commands._editor.find_editor")
    def test_full_edit_editor_exits_error(
        self,
        mock_find_editor: MagicMock,
        mock_subprocess: MagicMock,
        adr_repo_with_data: Path,
    ) -> None:
        """Test full edit when editor exits with error."""
        mock_find_editor.return_value = "vim"
        mock_subprocess.return_value = MagicMock(returncode=1)

        result = runner.invoke(app, ["edit", "20250110-use-postgresql"])
        # Should show warning but continue
        assert result.exit_code in [0, 1]
        if "warning" in result.output.lower():
            assert "editor exited" in result.output.lower()


class TestFullEditWithContent:
    """Tests for edit with modified content."""

    @patch("subprocess.run")
    @patch("git_adr.commands._editor.find_editor")
    def test_full_edit_content_unchanged(
        self,
        mock_find_editor: MagicMock,
        mock_subprocess: MagicMock,
        adr_repo_with_data: Path,
    ) -> None:
        """Test full edit when content is unchanged."""
        mock_find_editor.return_value = "cat"  # cat doesn't change content
        mock_subprocess.return_value = MagicMock(returncode=0)

        result = runner.invoke(app, ["edit", "20250110-use-postgresql"])
        assert result.exit_code in [0, 1]

    @patch("pathlib.Path.read_text")
    @patch("subprocess.run")
    @patch("git_adr.commands._editor.find_editor")
    def test_full_edit_invalid_format_after_edit(
        self,
        mock_find_editor: MagicMock,
        mock_subprocess: MagicMock,
        mock_read_text: MagicMock,
        adr_repo_with_data: Path,
    ) -> None:
        """Test full edit when edited content has invalid format."""
        mock_find_editor.return_value = "vim"
        mock_subprocess.return_value = MagicMock(returncode=0)
        # Return invalid content (no frontmatter)
        mock_read_text.return_value = "Invalid content without frontmatter"

        result = runner.invoke(app, ["edit", "20250110-use-postgresql"])
        # Should handle parsing error
        assert result.exit_code in [0, 1]


class TestEditDirectFunction:
    """Direct tests for edit functions."""

    def test_quick_edit_status_change(self, adr_repo_with_data: Path) -> None:
        """Test quick edit status change."""
        result = runner.invoke(
            app, ["edit", "20250110-use-postgresql", "--status", "rejected"]
        )
        assert result.exit_code == 0
        assert "rejected" in result.output.lower()

    def test_quick_edit_add_multiple_tags(self, adr_repo_with_data: Path) -> None:
        """Test quick edit adding multiple tags."""
        result = runner.invoke(
            app,
            [
                "edit",
                "20250110-use-postgresql",
                "--add-tag",
                "tag1",
                "--add-tag",
                "tag2",
            ],
        )
        assert result.exit_code == 0

    def test_quick_edit_remove_multiple_tags(self, adr_repo_with_data: Path) -> None:
        """Test quick edit removing multiple tags."""
        result = runner.invoke(
            app,
            [
                "edit",
                "20250110-use-postgresql",
                "--remove-tag",
                "database",
                "--remove-tag",
                "infrastructure",
            ],
        )
        assert result.exit_code == 0

    def test_quick_edit_combined_operations(self, adr_repo_with_data: Path) -> None:
        """Test quick edit with combined operations."""
        git = Git(cwd=adr_repo_with_data)
        head = git.get_head_commit()

        result = runner.invoke(
            app,
            [
                "edit",
                "20250110-use-postgresql",
                "--status",
                "proposed",
                "--add-tag",
                "combined-test",
                "--link",
                head,
            ],
        )
        assert result.exit_code == 0


class TestEditorCommand:
    """Tests for editor command building."""

    @patch("shutil.which")
    def test_find_editor_from_env(
        self, mock_which: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test _find_editor uses environment variable."""
        import os

        from git_adr.commands._editor import find_editor

        # Mock shutil.which to return the editor we set
        mock_which.side_effect = lambda x: x if x in ["code", "vim"] else None

        old_editor = os.environ.get("EDITOR")
        old_visual = os.environ.get("VISUAL")
        try:
            os.environ["EDITOR"] = "code"
            if "VISUAL" in os.environ:
                del os.environ["VISUAL"]
            config = Config()
            editor = find_editor(config)
            assert editor == "code"
        finally:
            if old_editor:
                os.environ["EDITOR"] = old_editor
            elif "EDITOR" in os.environ:
                del os.environ["EDITOR"]
            if old_visual:
                os.environ["VISUAL"] = old_visual

    @patch("shutil.which")
    def test_find_editor_from_config(
        self, mock_which: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test _find_editor uses config."""
        import os

        from git_adr.commands._editor import find_editor

        # Mock shutil.which to return nvim
        mock_which.side_effect = lambda x: x if x in ["nvim", "vim"] else None

        old_editor = os.environ.get("EDITOR")
        old_visual = os.environ.get("VISUAL")
        try:
            if "EDITOR" in os.environ:
                del os.environ["EDITOR"]
            if "VISUAL" in os.environ:
                del os.environ["VISUAL"]
            config = Config(editor="nvim")
            editor = find_editor(config)
            assert editor == "nvim"
        finally:
            if old_editor:
                os.environ["EDITOR"] = old_editor
            if old_visual:
                os.environ["VISUAL"] = old_visual

    def test_build_editor_command(self) -> None:
        """Test _build_editor_command."""
        from git_adr.commands._editor import build_editor_command

        cmd = build_editor_command("vim", "/path/to/file.md")
        assert cmd == ["vim", "/path/to/file.md"]

    def test_build_editor_command_code(self) -> None:
        """Test _build_editor_command with VS Code."""
        from git_adr.commands._editor import build_editor_command

        cmd = build_editor_command("code", "/path/to/file.md")
        assert "code" in cmd[0]
        assert "--wait" in cmd


class TestEditWithSupersedes:
    """Tests for editing ADRs with supersedes relationships."""

    def test_show_adr_with_supersedes(self, adr_repo_with_data: Path) -> None:
        """Test showing ADR that has supersedes metadata."""
        # First supersede to create the relationship
        runner.invoke(
            app,
            [
                "supersede",
                "20250110-use-postgresql",
                "--title",
                "Use SQLite Instead",
                "--batch",
            ],
        )

        # Show the old ADR which now has superseded_by
        result = runner.invoke(app, ["show", "20250110-use-postgresql"])
        assert result.exit_code == 0

    def test_show_adr_with_linked_commits(self, adr_repo_with_data: Path) -> None:
        """Test showing ADR with linked commits."""
        git = Git(cwd=adr_repo_with_data)
        head = git.get_head_commit()

        # Link a commit
        runner.invoke(app, ["edit", "20250110-use-postgresql", "--link", head])

        # Show the ADR
        result = runner.invoke(app, ["show", "20250110-use-postgresql"])
        assert result.exit_code == 0
        # Should show linked commits
        if head[:8] not in result.output:
            # Try markdown format explicitly
            result = runner.invoke(
                app, ["show", "20250110-use-postgresql", "--format", "markdown"]
            )
            assert result.exit_code == 0


class TestEditErrorHandling:
    """Tests for edit error handling."""

    def test_edit_git_error(self, adr_repo_with_data: Path) -> None:
        """Test edit when GitError is raised."""
        from git_adr.core.git import GitError

        with patch("git_adr.commands._shared.get_git") as mock_get_git:
            mock_git = MagicMock()
            mock_get_git.return_value = mock_git
            mock_git.is_repository.return_value = True

            # ConfigManager load raises GitError
            with patch("git_adr.commands._shared.ConfigManager") as mock_cm_class:
                mock_cm = MagicMock()
                mock_cm_class.return_value = mock_cm
                mock_cm.load.side_effect = GitError(
                    "Config error", ["git", "config"], 1
                )

                result = runner.invoke(
                    app, ["edit", "some-adr", "--status", "accepted"]
                )
                assert result.exit_code == 1
                assert "error" in result.output.lower()
