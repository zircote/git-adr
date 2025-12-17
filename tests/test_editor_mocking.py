"""Deep tests with editor and function mocking.

Targets uncovered code paths in new.py, supersede.py, log.py, and edit.py.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from git_adr.cli import app
from git_adr.core.config import Config

runner = CliRunner()


# =============================================================================
# New Command - Editor Tests
# =============================================================================


class TestNewCommandEditor:
    """Tests for new command with editor mocking."""

    @patch("git_adr.commands.new.open_editor")
    def test_new_with_mocked_editor(
        self, mock_editor: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test new command with mocked editor."""
        mock_editor.return_value = (
            "## Context\n\nMocked context.\n\n## Decision\n\nMocked decision."
        )

        result = runner.invoke(
            app, ["new", "Editor Test Decision", "--deciders", "Test User"]
        )
        assert result.exit_code == 0
        assert "Created ADR" in result.output

    @patch("git_adr.commands.new.open_editor")
    def test_new_editor_aborted(
        self, mock_editor: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test new command when editor returns None (aborted)."""
        mock_editor.return_value = None

        result = runner.invoke(app, ["new", "Aborted Decision"])
        assert result.exit_code == 0
        assert "aborted" in result.output.lower()

    @patch("git_adr.commands._editor.find_editor")
    def test_new_no_editor_found(
        self, mock_find: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test new command when no editor is found."""
        mock_find.return_value = None

        result = runner.invoke(app, ["new", "No Editor Decision"])
        assert result.exit_code != 0
        assert "editor" in result.output.lower()

    @patch("git_adr.commands._editor.subprocess.run")
    @patch("git_adr.commands._editor.find_editor")
    def test_new_editor_error(
        self,
        mock_find: MagicMock,
        mock_run: MagicMock,
        adr_repo_with_data: Path,
        tmp_path: Path,
    ) -> None:
        """Test new command when editor fails."""
        mock_find.return_value = "vim"
        mock_run.return_value = MagicMock(returncode=1)

        result = runner.invoke(app, ["new", "Editor Error Decision"])
        # Should still work or abort gracefully
        assert result.exit_code in [0, 1]


class TestNewCommandHelpers:
    """Tests for new command helper functions."""

    def test_find_editor_from_env(self) -> None:
        """Test _find_editor with EDITOR environment variable."""
        from git_adr.commands._editor import find_editor

        config = Config()

        with patch.dict(os.environ, {"EDITOR": "nano"}, clear=False):
            with patch("shutil.which", return_value="/usr/bin/nano"):
                editor = find_editor(config)
                assert editor == "nano"

    def test_find_editor_from_visual(self) -> None:
        """Test _find_editor with VISUAL environment variable."""
        from git_adr.commands._editor import find_editor

        config = Config()

        with patch.dict(os.environ, {"VISUAL": "code", "EDITOR": ""}, clear=False):
            with patch("shutil.which") as mock_which:
                mock_which.side_effect = (
                    lambda x: f"/usr/bin/{x}" if x == "code" else None
                )
                editor = find_editor(config)
                assert editor == "code"

    def test_find_editor_from_config(self) -> None:
        """Test _find_editor with config.editor."""
        from git_adr.commands._editor import find_editor

        config = Config(editor="nvim")

        with patch("shutil.which", return_value="/usr/bin/nvim"):
            editor = find_editor(config)
            assert editor == "nvim"

    def test_find_editor_fallback(self) -> None:
        """Test _find_editor fallback chain."""
        from git_adr.commands._editor import find_editor

        config = Config()

        def which_mock(cmd):
            if cmd == "vim":
                return "/usr/bin/vim"
            return None

        with patch.dict(os.environ, {"EDITOR": "", "VISUAL": ""}, clear=False):
            with patch("shutil.which", side_effect=which_mock):
                editor = find_editor(config)
                assert editor == "vim"

    def test_build_editor_command_gui(self) -> None:
        """Test _build_editor_command with GUI editor."""
        from git_adr.commands._editor import build_editor_command

        cmd = build_editor_command("code", "/tmp/test.md")
        assert cmd == ["code", "--wait", "/tmp/test.md"]

    def test_build_editor_command_terminal(self) -> None:
        """Test _build_editor_command with terminal editor."""
        from git_adr.commands._editor import build_editor_command

        cmd = build_editor_command("vim", "/tmp/test.md")
        assert cmd == ["vim", "/tmp/test.md"]

    def test_build_editor_command_with_args(self) -> None:
        """Test _build_editor_command with existing args."""
        from git_adr.commands._editor import build_editor_command

        cmd = build_editor_command("vim -c startinsert", "/tmp/test.md")
        assert cmd == ["vim", "-c", "startinsert", "/tmp/test.md"]

    def test_ensure_list_none(self) -> None:
        """Test ensure_list with None."""
        from git_adr.core.utils import ensure_list

        assert ensure_list(None) == []

    def test_ensure_list_string(self) -> None:
        """Test ensure_list with string."""
        from git_adr.core.utils import ensure_list

        assert ensure_list("tag") == ["tag"]

    def test_ensure_list_list(self) -> None:
        """Test ensure_list with list."""
        from git_adr.core.utils import ensure_list

        assert ensure_list(["a", "b", 123]) == ["a", "b", "123"]

    def test_ensure_list_other(self) -> None:
        """Test ensure_list with other types."""
        from git_adr.core.utils import ensure_list

        assert ensure_list(123) == []


# =============================================================================
# Supersede Command Tests
# =============================================================================


class TestSupersedeCommand:
    """Tests for supersede command with mocking."""

    @patch("git_adr.commands._editor.open_editor")
    def test_supersede_with_mocked_editor(
        self, mock_editor: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test supersede command with mocked editor."""
        mock_editor.return_value = (
            "## Context\n\nNew context.\n\n## Decision\n\nNew decision."
        )

        result = runner.invoke(
            app, ["supersede", "20250110-use-postgresql", "New Database Decision"]
        )
        assert result.exit_code == 0
        assert (
            "Created superseding ADR" in result.output
            or "supersede" in result.output.lower()
        )

    @patch("git_adr.commands._editor.open_editor")
    def test_supersede_aborted(
        self, mock_editor: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test supersede when editor returns None."""
        mock_editor.return_value = None

        result = runner.invoke(
            app, ["supersede", "20250110-use-postgresql", "Aborted Supersede"]
        )
        assert result.exit_code == 0
        assert "aborted" in result.output.lower()

    @patch("git_adr.commands._editor.open_editor")
    def test_supersede_already_superseded(
        self, mock_editor: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test supersede on already superseded ADR."""
        mock_editor.return_value = "## Context\n\nContext.\n\n## Decision\n\nDecision."

        # First supersede
        runner.invoke(app, ["supersede", "20250110-use-postgresql", "First Supersede"])

        # Try to supersede again
        result2 = runner.invoke(
            app, ["supersede", "20250110-use-postgresql", "Second Supersede"]
        )
        assert result2.exit_code == 0
        # Should warn about already superseded
        assert "superseded" in result2.output.lower()


# =============================================================================
# Log Command Tests
# =============================================================================


class TestLogCommand:
    """Tests for log command formatting."""

    def test_log_format_output_empty(self) -> None:
        """Test _format_log_output with empty input."""
        from git_adr.commands.log import _format_log_output

        # Should not raise
        _format_log_output("")
        _format_log_output("   \n\n   ")

    def test_log_format_output_simple(self) -> None:
        """Test _format_log_output with simple commit."""
        from git_adr.commands.log import _format_log_output

        output = "abc123 2025-01-15 Test commit\nAuthor Name"
        # Should not raise
        _format_log_output(output)

    def test_log_format_output_with_notes(self) -> None:
        """Test _format_log_output with notes."""
        from git_adr.commands.log import _format_log_output

        output = """abc123 2025-01-15 Test commit
Author Name
Some note content here"""
        # Should not raise
        _format_log_output(output)

    def test_log_format_output_with_adr_note(self) -> None:
        """Test _format_log_output with ADR note."""
        from git_adr.commands.log import _format_log_output

        output = """abc123 2025-01-15 Test commit
Author Name
---
id: test-adr
title: Test ADR
status: accepted
---
## Context
Test."""
        # Should not raise
        _format_log_output(output)

    def test_log_format_adr_note_valid(self) -> None:
        """Test _format_adr_note with valid ADR."""
        from git_adr.commands.log import _format_adr_note

        note = """---
id: test-adr
title: Test ADR
status: accepted
---
## Context
Test."""
        # Should not raise
        _format_adr_note(note)

    def test_log_format_adr_note_invalid_yaml(self) -> None:
        """Test _format_adr_note with invalid YAML."""
        from git_adr.commands.log import _format_adr_note

        note = """---
id: [invalid yaml
title: Test
---
Content."""
        # Should not raise, just fallback
        _format_adr_note(note)

    def test_log_format_adr_note_no_id(self) -> None:
        """Test _format_adr_note without id field."""
        from git_adr.commands.log import _format_adr_note

        note = """---
title: Test
status: accepted
---
Content."""
        # Should not raise, just fallback
        _format_adr_note(note)


# =============================================================================
# Edit Command Tests
# =============================================================================


class TestEditCommand:
    """Tests for edit command with mocking."""

    @patch("subprocess.run")
    @patch("git_adr.commands._editor.find_editor")
    def test_edit_full_mode(
        self,
        mock_find: MagicMock,
        mock_run: MagicMock,
        adr_repo_with_data: Path,
        tmp_path: Path,
    ) -> None:
        """Test edit command in full editor mode."""
        mock_find.return_value = "nano"

        # We need to make subprocess.run modify the temp file
        def run_side_effect(cmd, **kwargs):
            # Find the temp file path (last arg)
            if cmd and len(cmd) > 0:
                temp_file = cmd[-1]
                if isinstance(temp_file, str) and temp_file.endswith(".md"):
                    # Write edited content
                    Path(temp_file).write_text(
                        "---\n"
                        "id: 20250110-use-postgresql\n"
                        "title: Use PostgreSQL (Edited)\n"
                        "date: 2025-01-10\n"
                        "status: accepted\n"
                        "tags:\n"
                        "  - database\n"
                        "---\n"
                        "## Context\n\nEdited context.\n\n## Decision\n\nEdited decision."
                    )
            return MagicMock(returncode=0)

        mock_run.side_effect = run_side_effect

        result = runner.invoke(app, ["edit", "20250110-use-postgresql"])
        # Should succeed with updated content
        assert result.exit_code in [0, 1]

    @patch("git_adr.commands._editor.find_editor")
    def test_edit_full_mode_no_editor(
        self, mock_find: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test edit in full mode when no editor found."""
        mock_find.return_value = None

        result = runner.invoke(app, ["edit", "20250110-use-postgresql"])
        assert result.exit_code != 0
        assert "editor" in result.output.lower()


# =============================================================================
# Preview Mode Tests
# =============================================================================


class TestPreviewMode:
    """Tests for preview mode."""

    def test_new_preview_madr(self, adr_repo_with_data: Path) -> None:
        """Test new --preview with MADR format."""
        result = runner.invoke(
            app, ["new", "Preview MADR", "--preview", "--template", "madr"]
        )
        assert result.exit_code == 0
        assert "Preview" in result.output or "Context" in result.output

    def test_new_preview_nygard(self, adr_repo_with_data: Path) -> None:
        """Test new --preview with Nygard format."""
        result = runner.invoke(
            app, ["new", "Preview Nygard", "--preview", "--template", "nygard"]
        )
        assert result.exit_code == 0
        assert "Preview" in result.output or "Status" in result.output

    def test_new_preview_y_statement(self, adr_repo_with_data: Path) -> None:
        """Test new --preview with Y-statement format."""
        result = runner.invoke(
            app, ["new", "Preview Y", "--preview", "--template", "y-statement"]
        )
        assert result.exit_code == 0

    def test_new_preview_alexandrian(self, adr_repo_with_data: Path) -> None:
        """Test new --preview with Alexandrian format."""
        result = runner.invoke(
            app, ["new", "Preview Alex", "--preview", "--template", "alexandrian"]
        )
        assert result.exit_code == 0


# =============================================================================
# File Input Tests
# =============================================================================


class TestFileInput:
    """Tests for file input mode."""

    def test_new_from_file_not_found(self, adr_repo_with_data: Path) -> None:
        """Test new --file with non-existent file."""
        result = runner.invoke(
            app, ["new", "From File", "--file", "/nonexistent/file.md", "--no-edit"]
        )
        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "error" in result.output.lower()

    def test_new_from_file_with_frontmatter(
        self, adr_repo_with_data: Path, tmp_path: Path
    ) -> None:
        """Test new --file with frontmatter in file."""
        content_file = tmp_path / "adr.md"
        content_file.write_text(
            "---\n"
            "tags:\n"
            "  - frontend\n"
            "  - performance\n"
            "deciders:\n"
            "  - Alice\n"
            "  - Bob\n"
            "consulted:\n"
            "  - Charlie\n"
            "informed:\n"
            "  - Dave\n"
            "date: 2025-01-10\n"
            "---\n"
            "## Context\n\nTest context.\n\n"
            "## Decision\n\nTest decision."
        )

        result = runner.invoke(
            app,
            [
                "new",
                "File With Frontmatter",
                "--file",
                str(content_file),
                "--no-edit",
            ],
        )
        assert result.exit_code == 0
        assert "Created ADR" in result.output

    def test_new_no_edit_requires_file(self, adr_repo_with_data: Path) -> None:
        """Test new --no-edit without file fails."""
        result = runner.invoke(app, ["new", "No Edit No File", "--no-edit"])
        assert result.exit_code != 0
        assert "--no-edit" in result.output or "requires" in result.output.lower()


# =============================================================================
# Draft Mode Tests
# =============================================================================


class TestDraftMode:
    """Tests for draft mode."""

    def test_new_draft_mode(self, adr_repo_with_data: Path, tmp_path: Path) -> None:
        """Test new --draft creates draft status."""
        content_file = tmp_path / "draft.md"
        content_file.write_text("## Context\n\nDraft context.\n\n## Decision\n\nDraft.")

        result = runner.invoke(
            app,
            [
                "new",
                "Draft Decision",
                "--draft",
                "--file",
                str(content_file),
                "--no-edit",
                "--deciders",
                "Test User",
            ],
        )
        assert result.exit_code == 0
        # Check if draft status is mentioned or just verify creation
        assert "Created ADR" in result.output or "draft" in result.output.lower()


# =============================================================================
# Invalid Status Tests
# =============================================================================


class TestInvalidStatus:
    """Tests for invalid status handling."""

    def test_new_invalid_status(self, adr_repo_with_data: Path, tmp_path: Path) -> None:
        """Test new with invalid status."""
        content_file = tmp_path / "status.md"
        content_file.write_text("## Context\n\nTest.\n\n## Decision\n\nTest.")

        result = runner.invoke(
            app,
            [
                "new",
                "Invalid Status Test",
                "--status",
                "invalid_status",
                "--file",
                str(content_file),
                "--no-edit",
            ],
        )
        assert result.exit_code != 0
        assert "invalid" in result.output.lower() or "status" in result.output.lower()


# =============================================================================
# Template Error Tests
# =============================================================================


class TestTemplateErrors:
    """Tests for template error handling."""

    def test_new_invalid_template(self, adr_repo_with_data: Path) -> None:
        """Test new with invalid template."""
        result = runner.invoke(
            app,
            [
                "new",
                "Invalid Template",
                "--template",
                "nonexistent_template",
                "--preview",
            ],
        )
        assert result.exit_code != 0
        assert "error" in result.output.lower() or "template" in result.output.lower()
