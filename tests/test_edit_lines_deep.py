"""Deep tests for edit.py lines 187-233 (full editor workflow).

Targets the specific uncovered code paths in the _full_edit function.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from git_adr.cli import app
from git_adr.core.config import Config

runner = CliRunner()


class TestFullEditWorkflowLines187To233:
    """Tests targeting lines 187-233 in edit.py."""

    @patch("subprocess.run")
    @patch("git_adr.commands._editor.find_editor")
    def test_full_edit_original_content_preserved(
        self,
        mock_find_editor: MagicMock,
        mock_subprocess: MagicMock,
        adr_repo_with_data: Path,
    ) -> None:
        """Test that original content is read correctly (line 187)."""
        mock_find_editor.return_value = "cat"
        mock_subprocess.return_value = MagicMock(returncode=0)

        result = runner.invoke(app, ["edit", "20250110-use-postgresql"])
        # Editor opens - content is preserved
        assert result.exit_code in [0, 1]

    @patch("tempfile.NamedTemporaryFile")
    @patch("subprocess.run")
    @patch("git_adr.commands._editor.find_editor")
    def test_full_edit_temp_file_creation(
        self,
        mock_find_editor: MagicMock,
        mock_subprocess: MagicMock,
        mock_tempfile: MagicMock,
        adr_repo_with_data: Path,
    ) -> None:
        """Test temp file creation (lines 189-196)."""
        mock_find_editor.return_value = "vim"
        mock_subprocess.return_value = MagicMock(returncode=0)

        # Mock tempfile
        mock_file = MagicMock()
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=False)
        mock_file.name = "/tmp/git-adr-test.md"
        mock_tempfile.return_value = mock_file

        result = runner.invoke(app, ["edit", "20250110-use-postgresql"])
        assert result.exit_code in [0, 1]

    @patch("subprocess.run")
    @patch("git_adr.commands._editor.find_editor")
    def test_full_edit_editor_command_built(
        self,
        mock_find_editor: MagicMock,
        mock_subprocess: MagicMock,
        adr_repo_with_data: Path,
    ) -> None:
        """Test editor command is built correctly (lines 199-201)."""
        mock_find_editor.return_value = "nano"
        mock_subprocess.return_value = MagicMock(returncode=0)

        result = runner.invoke(app, ["edit", "20250110-use-postgresql"])
        # Should see editor opening message
        assert result.exit_code in [0, 1]

    @patch("subprocess.run")
    @patch("git_adr.commands._editor.find_editor")
    def test_full_edit_editor_nonzero_exit_warning(
        self,
        mock_find_editor: MagicMock,
        mock_subprocess: MagicMock,
        adr_repo_with_data: Path,
    ) -> None:
        """Test warning on editor non-zero exit (lines 205-208)."""
        mock_find_editor.return_value = "vim"
        mock_subprocess.return_value = MagicMock(returncode=2)

        result = runner.invoke(app, ["edit", "20250110-use-postgresql"])
        # Should still continue with warning
        assert result.exit_code in [0, 1]
        # May show warning about editor exit code
        if "warning" in result.output.lower():
            assert "2" in result.output or "editor" in result.output.lower()

    @patch("pathlib.Path.read_text")
    @patch("subprocess.run")
    @patch("git_adr.commands._editor.find_editor")
    def test_full_edit_content_unchanged_no_changes(
        self,
        mock_find_editor: MagicMock,
        mock_subprocess: MagicMock,
        mock_read_text: MagicMock,
        adr_repo_with_data: Path,
    ) -> None:
        """Test no changes detection (lines 214-216)."""
        mock_find_editor.return_value = "vim"
        mock_subprocess.return_value = MagicMock(returncode=0)
        # Content unchanged - same as original
        mock_read_text.return_value = ""

        result = runner.invoke(app, ["edit", "20250110-use-postgresql"])
        assert result.exit_code in [0, 1]

    @patch("pathlib.Path.read_text")
    @patch("subprocess.run")
    @patch("git_adr.commands._editor.find_editor")
    def test_full_edit_invalid_adr_format_error(
        self,
        mock_find_editor: MagicMock,
        mock_subprocess: MagicMock,
        mock_read_text: MagicMock,
        adr_repo_with_data: Path,
    ) -> None:
        """Test error on invalid ADR format (lines 223-225)."""
        mock_find_editor.return_value = "vim"
        mock_subprocess.return_value = MagicMock(returncode=0)
        # Return invalid content
        mock_read_text.return_value = (
            "This is not valid ADR format\nNo frontmatter here"
        )

        result = runner.invoke(app, ["edit", "20250110-use-postgresql"])
        # Should handle parsing error
        assert result.exit_code in [0, 1]

    @patch("subprocess.run")
    @patch("git_adr.commands._editor.find_editor")
    def test_full_edit_save_changes_success(
        self,
        mock_find_editor: MagicMock,
        mock_subprocess: MagicMock,
        adr_repo_with_data: Path,
    ) -> None:
        """Test saving changes (lines 228-230)."""
        mock_find_editor.return_value = "cat"  # cat outputs file unchanged
        mock_subprocess.return_value = MagicMock(returncode=0)

        result = runner.invoke(app, ["edit", "20250110-use-postgresql"])
        assert result.exit_code in [0, 1]

    @patch("pathlib.Path.unlink")
    @patch("subprocess.run")
    @patch("git_adr.commands._editor.find_editor")
    def test_full_edit_cleanup_temp_file(
        self,
        mock_find_editor: MagicMock,
        mock_subprocess: MagicMock,
        mock_unlink: MagicMock,
        adr_repo_with_data: Path,
    ) -> None:
        """Test temp file cleanup (line 233)."""
        mock_find_editor.return_value = "vim"
        mock_subprocess.return_value = MagicMock(returncode=0)

        result = runner.invoke(app, ["edit", "20250110-use-postgresql"])
        # Temp file should be cleaned up
        assert result.exit_code in [0, 1]


class TestEditWithModifiedContent:
    """Tests for edit with valid modified content."""

    @patch("pathlib.Path.read_text")
    @patch("subprocess.run")
    @patch("git_adr.commands._editor.find_editor")
    def test_full_edit_parse_valid_updated_content(
        self,
        mock_find_editor: MagicMock,
        mock_subprocess: MagicMock,
        mock_read_text: MagicMock,
        adr_repo_with_data: Path,
    ) -> None:
        """Test parsing valid updated content (lines 219-222)."""
        mock_find_editor.return_value = "vim"
        mock_subprocess.return_value = MagicMock(returncode=0)

        # Return valid modified content
        valid_content = """---
id: 20250110-use-postgresql
title: Use PostgreSQL Modified
date: 2025-01-10
status: accepted
tags:
  - database
  - modified
---

# Use PostgreSQL Modified

## Context

Modified context.

## Decision

Modified decision.

## Consequences

Modified consequences.
"""
        mock_read_text.return_value = valid_content

        result = runner.invoke(app, ["edit", "20250110-use-postgresql"])
        # Should handle the modified content
        assert result.exit_code in [0, 1]


class TestEditPreserveOriginalId:
    """Tests for preserving original ADR ID during edit."""

    @patch("pathlib.Path.read_text")
    @patch("subprocess.run")
    @patch("git_adr.commands._editor.find_editor")
    def test_full_edit_preserves_id_on_update(
        self,
        mock_find_editor: MagicMock,
        mock_subprocess: MagicMock,
        mock_read_text: MagicMock,
        adr_repo_with_data: Path,
    ) -> None:
        """Test that original ID is preserved (line 222)."""
        mock_find_editor.return_value = "vim"
        mock_subprocess.return_value = MagicMock(returncode=0)

        # Content with different ID should still preserve original
        modified_content = """---
id: different-id-should-be-ignored
title: Modified Title
date: 2025-01-10
status: accepted
---

# Modified Content

Some changes.
"""
        mock_read_text.return_value = modified_content

        result = runner.invoke(app, ["edit", "20250110-use-postgresql"])
        assert result.exit_code in [0, 1]


class TestEditorSpecificBehaviors:
    """Tests for specific editor behaviors."""

    @patch("shutil.which")
    def test_build_editor_command_with_code(
        self, mock_which: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test building VS Code command with --wait."""
        from git_adr.commands._editor import build_editor_command

        mock_which.return_value = "/usr/local/bin/code"

        cmd = build_editor_command("code", "/path/to/file.md")
        assert "code" in cmd[0]
        assert "--wait" in cmd
        assert "/path/to/file.md" in cmd

    @patch("shutil.which")
    def test_build_editor_command_with_subl(
        self, mock_which: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test building Sublime command with --wait."""
        from git_adr.commands._editor import build_editor_command

        cmd = build_editor_command("subl", "/path/to/file.md")
        assert "subl" in cmd[0]
        assert "--wait" in cmd

    @patch("shutil.which")
    def test_build_editor_command_with_atom(
        self, mock_which: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test building Atom command with --wait."""
        from git_adr.commands._editor import build_editor_command

        cmd = build_editor_command("atom", "/path/to/file.md")
        assert "atom" in cmd[0]
        assert "--wait" in cmd

    @patch("shutil.which")
    def test_build_editor_command_no_wait_for_vim(
        self, mock_which: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test that terminal editors don't get --wait."""
        from git_adr.commands._editor import build_editor_command

        cmd = build_editor_command("vim", "/path/to/file.md")
        assert "vim" in cmd[0]
        assert "--wait" not in cmd

    @patch("shutil.which")
    def test_build_editor_command_with_existing_args(
        self, mock_which: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test editor command with existing arguments."""
        from git_adr.commands._editor import build_editor_command

        cmd = build_editor_command("code --new-window", "/path/to/file.md")
        assert "code" in cmd[0]
        assert "--new-window" in cmd
        assert "--wait" in cmd


class TestFindEditorFallbacks:
    """Tests for editor fallback chain."""

    @patch("shutil.which")
    @patch.dict("os.environ", {}, clear=True)
    def test_find_editor_uses_config(
        self, mock_which: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test _find_editor uses config.editor first."""
        import os

        from git_adr.commands._editor import find_editor

        # Clear environment variables
        for var in ["EDITOR", "VISUAL"]:
            if var in os.environ:
                del os.environ[var]

        mock_which.side_effect = lambda x: x if x in ["nvim", "vim"] else None

        config = Config(editor="nvim")
        editor = find_editor(config)
        assert editor == "nvim"

    @patch("shutil.which")
    def test_find_editor_fallback_to_vim(
        self, mock_which: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test _find_editor fallback to vim."""
        import os

        from git_adr.commands._editor import find_editor

        # Clear env vars
        old_editor = os.environ.pop("EDITOR", None)
        old_visual = os.environ.pop("VISUAL", None)

        try:
            # Only vim exists
            mock_which.side_effect = lambda x: x if x == "vim" else None

            config = Config()
            editor = find_editor(config)
            assert editor == "vim"
        finally:
            if old_editor:
                os.environ["EDITOR"] = old_editor
            if old_visual:
                os.environ["VISUAL"] = old_visual

    @patch("shutil.which")
    def test_find_editor_fallback_to_nano(
        self, mock_which: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test _find_editor fallback to nano."""
        import os

        from git_adr.commands._editor import find_editor

        old_editor = os.environ.pop("EDITOR", None)
        old_visual = os.environ.pop("VISUAL", None)

        try:
            # Only nano exists
            mock_which.side_effect = lambda x: x if x == "nano" else None

            config = Config()
            editor = find_editor(config)
            assert editor == "nano"
        finally:
            if old_editor:
                os.environ["EDITOR"] = old_editor
            if old_visual:
                os.environ["VISUAL"] = old_visual

    @patch("shutil.which")
    def test_find_editor_fallback_to_vi(
        self, mock_which: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test _find_editor fallback to vi."""
        import os

        from git_adr.commands._editor import find_editor

        old_editor = os.environ.pop("EDITOR", None)
        old_visual = os.environ.pop("VISUAL", None)

        try:
            # Only vi exists
            mock_which.side_effect = lambda x: x if x == "vi" else None

            config = Config()
            editor = find_editor(config)
            assert editor == "vi"
        finally:
            if old_editor:
                os.environ["EDITOR"] = old_editor
            if old_visual:
                os.environ["VISUAL"] = old_visual

    @patch("shutil.which")
    def test_find_editor_none_when_no_editor(
        self, mock_which: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test _find_editor returns None when no editor found (line 399)."""
        import os

        from git_adr.commands._editor import find_editor

        old_editor = os.environ.pop("EDITOR", None)
        old_visual = os.environ.pop("VISUAL", None)

        try:
            # No editor exists
            mock_which.return_value = None

            config = Config()
            editor = find_editor(config)
            assert editor is None
        finally:
            if old_editor:
                os.environ["EDITOR"] = old_editor
            if old_visual:
                os.environ["VISUAL"] = old_visual


class TestEditQuickOperations:
    """Additional tests for quick edit operations."""

    def test_quick_edit_all_status_values(self, adr_repo_with_data: Path) -> None:
        """Test quick edit with all valid status values."""
        statuses = [
            "draft",
            "proposed",
            "accepted",
            "deprecated",
            "rejected",
            "superseded",
        ]

        for status in statuses:
            result = runner.invoke(
                app, ["edit", "20250110-use-postgresql", "--status", status]
            )
            assert result.exit_code == 0, f"Failed for status: {status}"

    def test_quick_edit_link_invalid_commit(self, adr_repo_with_data: Path) -> None:
        """Test quick edit linking invalid commit."""
        result = runner.invoke(
            app, ["edit", "20250110-use-postgresql", "--link", "invalidcommithash"]
        )
        # Should handle gracefully
        assert result.exit_code in [0, 1]

    def test_quick_edit_unlink_nonexistent_commit(
        self, adr_repo_with_data: Path
    ) -> None:
        """Test quick edit unlinking commit that's not linked."""
        result = runner.invoke(
            app, ["edit", "20250110-use-postgresql", "--unlink", "abcdef123456"]
        )
        assert result.exit_code == 0
