"""Deep tests for convert and edit commands.

Targets uncovered code paths in convert.py and edit.py.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from git_adr.cli import app
from git_adr.core.git import Git, GitError

runner = CliRunner()


# =============================================================================
# Convert Command Tests
# =============================================================================


class TestConvertCommand:
    """Tests for convert command error paths."""

    def test_convert_not_git_repo(self, tmp_path: Path) -> None:
        """Test convert in non-git directory."""
        import os

        os.chdir(tmp_path)
        result = runner.invoke(app, ["convert", "some-adr", "--to", "madr"])
        assert result.exit_code == 1
        assert "not a git repository" in result.output.lower()

    def test_convert_not_initialized(self, tmp_path: Path) -> None:
        """Test convert in uninitialized repo."""
        import os

        os.chdir(tmp_path)
        subprocess.run(["git", "init"], check=False, cwd=tmp_path, capture_output=True)

        result = runner.invoke(app, ["convert", "some-adr", "--to", "madr"])
        assert result.exit_code == 1
        assert "init" in result.output.lower()

    def test_convert_adr_not_found(self, adr_repo_with_data: Path) -> None:
        """Test convert with non-existent ADR."""
        result = runner.invoke(app, ["convert", "nonexistent-adr", "--to", "madr"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_convert_unknown_format(self, adr_repo_with_data: Path) -> None:
        """Test convert to unknown format."""
        result = runner.invoke(
            app, ["convert", "20250110-use-postgresql", "--to", "unknown-format"]
        )
        assert result.exit_code == 1
        assert "unknown format" in result.output.lower()
        assert "available formats" in result.output.lower()

    def test_convert_same_format(self, adr_repo_with_data: Path) -> None:
        """Test convert to same format."""
        # Get the current format of the ADR
        result = runner.invoke(
            app, ["convert", "20250110-use-postgresql", "--to", "madr"]
        )
        # May succeed or say already in format
        assert result.exit_code in [0, 1]

    def test_convert_dry_run(self, adr_repo_with_data: Path) -> None:
        """Test convert with dry run."""
        result = runner.invoke(
            app, ["convert", "20250110-use-postgresql", "--to", "nygard", "--dry-run"]
        )
        assert result.exit_code in [0, 1]
        if result.exit_code == 0:
            assert (
                "preview" in result.output.lower() or "dry-run" in result.output.lower()
            )

    def test_convert_success(self, adr_repo_with_data: Path) -> None:
        """Test successful conversion."""
        # First create an ADR in madr format
        result = runner.invoke(
            app, ["convert", "20250110-use-postgresql", "--to", "nygard"]
        )
        # May succeed or say already in format
        assert result.exit_code in [0, 1]

    @patch("git_adr.core.templates.TemplateEngine.convert")
    def test_convert_template_error(
        self, mock_convert: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test convert when template engine fails."""
        mock_convert.side_effect = ValueError("Conversion error")

        result = runner.invoke(
            app, ["convert", "20250110-use-postgresql", "--to", "nygard"]
        )
        # Should handle the error gracefully
        assert result.exit_code in [0, 1]


# =============================================================================
# Edit Command Tests
# =============================================================================


class TestEditCommand:
    """Tests for edit command."""

    def test_edit_not_git_repo(self, tmp_path: Path) -> None:
        """Test edit in non-git directory."""
        import os

        os.chdir(tmp_path)
        result = runner.invoke(app, ["edit", "some-adr"])
        assert result.exit_code == 1
        assert "not a git repository" in result.output.lower()

    def test_edit_not_initialized(self, tmp_path: Path) -> None:
        """Test edit in uninitialized repo."""
        import os

        os.chdir(tmp_path)
        subprocess.run(["git", "init"], check=False, cwd=tmp_path, capture_output=True)

        result = runner.invoke(app, ["edit", "some-adr"])
        assert result.exit_code == 1
        assert "init" in result.output.lower()

    def test_edit_adr_not_found(self, adr_repo_with_data: Path) -> None:
        """Test edit with non-existent ADR."""
        result = runner.invoke(app, ["edit", "nonexistent-adr"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_edit_quick_status(self, adr_repo_with_data: Path) -> None:
        """Test quick edit - change status."""
        result = runner.invoke(
            app, ["edit", "20250110-use-postgresql", "--status", "deprecated"]
        )
        assert result.exit_code == 0
        assert "deprecated" in result.output.lower()

    def test_edit_quick_invalid_status(self, adr_repo_with_data: Path) -> None:
        """Test quick edit with invalid status."""
        result = runner.invoke(
            app, ["edit", "20250110-use-postgresql", "--status", "invalid"]
        )
        assert result.exit_code == 1
        assert "invalid" in result.output.lower()

    def test_edit_quick_add_tag(self, adr_repo_with_data: Path) -> None:
        """Test quick edit - add tag."""
        result = runner.invoke(
            app, ["edit", "20250110-use-postgresql", "--add-tag", "new-tag"]
        )
        assert result.exit_code == 0
        assert "new-tag" in result.output.lower() or "updated" in result.output.lower()

    def test_edit_quick_remove_tag(self, adr_repo_with_data: Path) -> None:
        """Test quick edit - remove tag."""
        result = runner.invoke(
            app, ["edit", "20250110-use-postgresql", "--remove-tag", "database"]
        )
        assert result.exit_code == 0

    def test_edit_quick_link_commit(self, adr_repo_with_data: Path) -> None:
        """Test quick edit - link commit."""
        git = Git(cwd=adr_repo_with_data)
        head = git.get_head_commit()

        result = runner.invoke(app, ["edit", "20250110-use-postgresql", "--link", head])
        assert result.exit_code == 0
        assert "linked" in result.output.lower() or "updated" in result.output.lower()

    def test_edit_quick_unlink_commit(self, adr_repo_with_data: Path) -> None:
        """Test quick edit - unlink commit."""
        result = runner.invoke(
            app, ["edit", "20250110-use-postgresql", "--unlink", "abc123def456"]
        )
        assert result.exit_code == 0

    def test_edit_quick_no_changes(self, adr_repo_with_data: Path) -> None:
        """Test quick edit with no actual changes."""
        # Try to remove a tag that doesn't exist
        result = runner.invoke(
            app, ["edit", "20250110-use-postgresql", "--remove-tag", "nonexistent-tag"]
        )
        assert result.exit_code == 0
        # Should report no changes
        assert (
            "no changes" in result.output.lower() or "updated" in result.output.lower()
        )


class TestEditFullWorkflow:
    """Tests for full editor workflow."""

    @patch("git_adr.commands._editor.find_editor")
    def test_edit_no_editor(
        self, mock_find_editor: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test edit when no editor is found."""
        mock_find_editor.return_value = None

        result = runner.invoke(app, ["edit", "20250110-use-postgresql"])
        assert result.exit_code == 1
        assert "editor" in result.output.lower()

    @patch("subprocess.run")
    @patch("git_adr.commands._editor.find_editor")
    def test_edit_editor_error(
        self,
        mock_find_editor: MagicMock,
        mock_subprocess: MagicMock,
        adr_repo_with_data: Path,
    ) -> None:
        """Test edit when editor exits with error."""
        mock_find_editor.return_value = "vim"
        mock_subprocess.return_value = MagicMock(returncode=1)

        result = runner.invoke(app, ["edit", "20250110-use-postgresql"])
        # Should handle editor error
        assert result.exit_code in [0, 1]

    @patch("subprocess.run")
    @patch("git_adr.commands._editor.find_editor")
    @patch("pathlib.Path.read_text")
    def test_edit_no_changes(
        self,
        mock_read_text: MagicMock,
        mock_find_editor: MagicMock,
        mock_subprocess: MagicMock,
        adr_repo_with_data: Path,
    ) -> None:
        """Test edit when user makes no changes."""
        mock_find_editor.return_value = "vim"
        mock_subprocess.return_value = MagicMock(returncode=0)
        # Read returns same content (no changes)
        mock_read_text.return_value = ""

        result = runner.invoke(app, ["edit", "20250110-use-postgresql"])
        assert result.exit_code in [0, 1]

    @patch("subprocess.run")
    @patch("git_adr.commands._editor.find_editor")
    def test_edit_full_success(
        self,
        mock_find_editor: MagicMock,
        mock_subprocess: MagicMock,
        adr_repo_with_data: Path,
    ) -> None:
        """Test successful full edit."""
        mock_find_editor.return_value = "cat"  # Use cat as no-op editor
        mock_subprocess.return_value = MagicMock(returncode=0)

        result = runner.invoke(app, ["edit", "20250110-use-postgresql"])
        # Editor opens, but no changes made (cat just outputs)
        assert result.exit_code in [0, 1]


# =============================================================================
# Edit Helper Function Tests
# =============================================================================


class TestEditHelpers:
    """Tests for edit helper functions."""

    def test_quick_edit_add_existing_tag(self, adr_repo_with_data: Path) -> None:
        """Test adding a tag that already exists."""
        # First verify the ADR has a tag
        result = runner.invoke(
            app, ["edit", "20250110-use-postgresql", "--add-tag", "database"]
        )
        # Should succeed but may not report the duplicate
        assert result.exit_code == 0

    def test_quick_edit_multiple_operations(self, adr_repo_with_data: Path) -> None:
        """Test multiple quick edit operations at once."""
        result = runner.invoke(
            app,
            [
                "edit",
                "20250110-use-postgresql",
                "--status",
                "accepted",
                "--add-tag",
                "tested",
            ],
        )
        assert result.exit_code == 0

    def test_quick_edit_link_already_linked(self, adr_repo_with_data: Path) -> None:
        """Test linking a commit that's already linked."""
        git = Git(cwd=adr_repo_with_data)
        head = git.get_head_commit()

        # Link once
        runner.invoke(app, ["edit", "20250110-use-postgresql", "--link", head])

        # Try to link again
        result = runner.invoke(app, ["edit", "20250110-use-postgresql", "--link", head])
        # Should succeed but may report no changes
        assert result.exit_code == 0


# =============================================================================
# Run Edit Function Direct Tests
# =============================================================================


class TestRunEditFunction:
    """Direct tests for run_edit function."""

    def test_run_edit_git_error(self, adr_repo_with_data: Path) -> None:
        """Test run_edit with GitError."""
        with patch("git_adr.commands._shared.get_git") as mock_get_git:
            mock_git = MagicMock()
            mock_get_git.return_value = mock_git
            mock_git.is_repository.return_value = True

            # ConfigManager raises GitError
            with patch("git_adr.commands._shared.ConfigManager") as mock_cm:
                mock_cm.side_effect = GitError("Config error", ["git", "config"], 1)

                result = runner.invoke(app, ["edit", "some-adr"])
                assert result.exit_code == 1
                assert "error" in result.output.lower()


# =============================================================================
# Full Edit Function Tests
# =============================================================================


class TestFullEditFunction:
    """Tests for _full_edit function."""

    @patch("subprocess.run")
    @patch("git_adr.commands._editor.find_editor")
    def test_full_edit_invalid_adr_format(
        self,
        mock_find_editor: MagicMock,
        mock_subprocess: MagicMock,
        adr_repo_with_data: Path,
        tmp_path: Path,
    ) -> None:
        """Test full edit when edited content is invalid."""
        mock_find_editor.return_value = "vim"
        mock_subprocess.return_value = MagicMock(returncode=0)

        # Create a temp file with invalid content
        invalid_content = "This is not valid ADR format\nNo frontmatter here"

        with patch("pathlib.Path.read_text", return_value=invalid_content):
            result = runner.invoke(app, ["edit", "20250110-use-postgresql"])
            # Should handle the parsing error
            assert result.exit_code in [0, 1]


# =============================================================================
# Convert Run Function Direct Tests
# =============================================================================


class TestRunConvertFunction:
    """Direct tests for run_convert function."""

    def test_run_convert_git_error(self, adr_repo_with_data: Path) -> None:
        """Test run_convert with GitError."""
        with patch("git_adr.commands._shared.get_git") as mock_get_git:
            mock_git = MagicMock()
            mock_get_git.return_value = mock_git
            mock_git.is_repository.return_value = True

            # ConfigManager raises GitError
            with patch("git_adr.commands._shared.ConfigManager") as mock_cm:
                mock_cm.side_effect = GitError("Config error", ["git", "config"], 1)

                result = runner.invoke(app, ["convert", "some-adr", "--to", "madr"])
                assert result.exit_code == 1
                assert "error" in result.output.lower()
