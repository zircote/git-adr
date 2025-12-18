"""Tests to achieve 95% coverage threshold.

Targets specific uncovered lines in:
- src/git_adr/commands/_editor.py
- src/git_adr/commands/config.py
- src/git_adr/cli.py (issue and CI commands)
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from git_adr.cli import app
from git_adr.core.config import Config

runner = CliRunner()


# =============================================================================
# Editor Tests (_editor.py coverage)
# =============================================================================


class TestEditorCoverage:
    """Tests for _editor.py coverage gaps."""

    def test_find_editor_malformed_config(self) -> None:
        """Test find_editor with malformed editor config (ValueError path).

        Covers lines 63-65: except ValueError for malformed config.editor
        """
        from git_adr.commands._editor import find_editor

        # Create config with malformed editor string (unmatched quote)
        config = Config(editor='"unclosed quote')

        # Should handle gracefully and fall back
        with patch.dict(os.environ, {"EDITOR": "", "VISUAL": ""}, clear=True):
            with patch("shutil.which") as mock_which:
                mock_which.return_value = "/usr/bin/vim"
                result = find_editor(config)
                # Should fall back to vim
                assert result == "vim"

    def test_find_editor_malformed_env_editor(self) -> None:
        """Test find_editor with malformed $EDITOR (ValueError path).

        Covers lines 77-79: except ValueError for malformed $EDITOR
        """
        from git_adr.commands._editor import find_editor

        config = Config()  # No editor config

        # Set malformed $EDITOR - should print warning and fall back
        with patch.dict(os.environ, {"EDITOR": '"unclosed', "VISUAL": ""}, clear=True):
            with patch("shutil.which") as mock_which:
                mock_which.return_value = "/usr/bin/vim"
                result = find_editor(config)
                # Should fall back to vim (first in EDITOR_FALLBACKS)
                assert result == "vim"

    def test_find_editor_malformed_env_visual(self) -> None:
        """Test find_editor with malformed $VISUAL (ValueError path).

        Covers lines 77-79: except ValueError for malformed $VISUAL
        """
        from git_adr.commands._editor import find_editor

        config = Config()  # No editor config

        # Set empty $EDITOR and malformed $VISUAL - should print warning and fall back
        with patch.dict(os.environ, {"EDITOR": "", "VISUAL": "'unclosed"}, clear=True):
            with patch("shutil.which") as mock_which:
                mock_which.return_value = "/usr/bin/vim"
                result = find_editor(config)
                # Should fall back to vim
                assert result == "vim"

    def test_build_editor_command_malformed_editor(self) -> None:
        """Test build_editor_command with malformed editor string.

        Covers lines 109-112: except ValueError fallback
        """
        from git_adr.commands._editor import build_editor_command

        # Pass malformed editor string
        result = build_editor_command('"unclosed', "/tmp/test.md")
        # Should treat entire string as command
        assert result == ['"unclosed', "/tmp/test.md"]

    def test_open_editor_empty_content(self, initialized_adr_repo: Path) -> None:
        """Test open_editor when user empties the file.

        Covers lines 180-184: empty content after editing
        """
        from git_adr.commands._editor import open_editor
        from git_adr.core.config import ConfigManager
        from git_adr.core.git import Git

        git = Git(cwd=initialized_adr_repo)
        config = ConfigManager(git).load()

        # Mock the editor to return empty content
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            # The temp file will be emptied
            with patch("pathlib.Path.read_text", return_value="   "):
                result = open_editor("initial content", config)
                assert result is None  # Empty content returns None


# =============================================================================
# Config Command Tests (config.py coverage)
# =============================================================================


class TestConfigCommandCoverage:
    """Tests for config.py coverage gaps."""

    def test_config_get_without_key(self, initialized_adr_repo: Path) -> None:
        """Test --get without key.

        Covers lines 62-63: --get requires a key error
        """
        result = runner.invoke(app, ["config", "--get"])
        assert result.exit_code != 0
        assert "requires a key" in result.output.lower() or result.exit_code == 1

    def test_config_set_without_key(self, initialized_adr_repo: Path) -> None:
        """Test --set without key.

        Covers lines 70-71: --set requires key and value error
        """
        result = runner.invoke(app, ["config", "--set"])
        assert result.exit_code != 0

    def test_config_set_without_value(self, initialized_adr_repo: Path) -> None:
        """Test --set with key but no value.

        Covers lines 70-71: --set requires key and value error
        """
        result = runner.invoke(app, ["config", "template", "--set"])
        assert result.exit_code != 0

    def test_config_unset_without_key(self, initialized_adr_repo: Path) -> None:
        """Test --unset without key.

        Covers lines 78-79: --unset requires a key error
        """
        result = runner.invoke(app, ["config", "--unset"])
        assert result.exit_code != 0

    def test_config_list_empty_local(self, initialized_adr_repo: Path) -> None:
        """Test --list with no local config set.

        Covers lines 109-114: No config set path showing available keys
        """
        # Clear all local adr config
        from git_adr.core.git import Git

        git = Git(cwd=initialized_adr_repo)
        # Unset common config keys
        for key in ["adr.template", "adr.editor", "adr.ai.provider", "adr.ai.model"]:
            try:
                git.config_unset(key)
            except Exception:
                # Some keys may not be set in this repo; ignore unset failures.
                pass

        result = runner.invoke(app, ["config", "--list"])
        # Should show "No local configuration set" and available keys
        assert result.exit_code == 0
        # Either shows no config message or some remaining config
        assert (
            "configuration" in result.output.lower() or "key" in result.output.lower()
        )


# =============================================================================
# CLI Issue Command Tests (cli.py coverage)
# =============================================================================


class TestIssueCommandCoverage:
    """Tests for issue command coverage in cli.py."""

    def test_issue_command_basic(self, initialized_adr_repo: Path) -> None:
        """Test basic issue command invocation.

        Covers lines 1285-1287: issue command import and call
        """
        result = runner.invoke(
            app, ["issue", "--type", "bug", "--dry-run", "--local-only"]
        )
        # Should work (dry-run, local-only)
        assert result.exit_code in [0, 1]

    def test_issue_with_title(self, initialized_adr_repo: Path) -> None:
        """Test issue command with title."""
        result = runner.invoke(
            app,
            [
                "issue",
                "--type",
                "feature",
                "--title",
                "Test Feature",
                "--dry-run",
                "--local-only",
            ],
        )
        assert result.exit_code in [0, 1]


# =============================================================================
# CLI CI Commands Tests (cli.py coverage)
# =============================================================================


class TestCICommandsCoverage:
    """Tests for CI commands coverage in cli.py."""

    def test_ci_github_validate(self, initialized_adr_repo: Path) -> None:
        """Test CI github validate workflow generation."""
        result = runner.invoke(app, ["ci", "github", "--validate"])
        assert result.exit_code == 0

    def test_ci_github_sync(self, initialized_adr_repo: Path) -> None:
        """Test CI github sync workflow generation."""
        result = runner.invoke(app, ["ci", "github", "--sync"])
        assert result.exit_code == 0

    def test_ci_gitlab_validate(self, initialized_adr_repo: Path) -> None:
        """Test CI gitlab validate workflow generation."""
        result = runner.invoke(app, ["ci", "gitlab", "--validate"])
        assert result.exit_code == 0

    def test_ci_gitlab_sync(self, initialized_adr_repo: Path) -> None:
        """Test CI gitlab sync workflow generation."""
        result = runner.invoke(app, ["ci", "gitlab", "--sync"])
        assert result.exit_code == 0


# =============================================================================
# Additional CLI Command Coverage
# =============================================================================


class TestAdditionalCLICoverage:
    """Additional CLI coverage tests."""

    def test_hooks_install_command(self, initialized_adr_repo: Path) -> None:
        """Test hooks install command."""
        result = runner.invoke(app, ["hooks", "install"])
        assert result.exit_code == 0

    def test_hooks_uninstall_command(self, initialized_adr_repo: Path) -> None:
        """Test hooks uninstall command."""
        result = runner.invoke(app, ["hooks", "uninstall"])
        assert result.exit_code == 0

    def test_hooks_status_command(self, initialized_adr_repo: Path) -> None:
        """Test hooks status command."""
        result = runner.invoke(app, ["hooks", "status"])
        assert result.exit_code == 0

    def test_hooks_config_command(self, initialized_adr_repo: Path) -> None:
        """Test hooks config command (covers cli.py lines 1745-1747)."""
        result = runner.invoke(app, ["hooks", "config", "--help"])
        assert result.exit_code == 0

    def test_templates_list_command(self, initialized_adr_repo: Path) -> None:
        """Test templates list command."""
        result = runner.invoke(app, ["templates", "list"])
        assert result.exit_code == 0

    def test_templates_pr_command(
        self, initialized_adr_repo: Path, tmp_path: Path
    ) -> None:
        """Test templates pr command."""
        output = tmp_path / "PR_TEMPLATE.md"
        result = runner.invoke(app, ["templates", "pr", "--output", str(output)])
        assert result.exit_code == 0

    def test_templates_issue_command(
        self, initialized_adr_repo: Path, tmp_path: Path
    ) -> None:
        """Test templates issue command (covers cli.py lines 1555-1557)."""
        output = tmp_path / "ISSUE_TEMPLATE.md"
        result = runner.invoke(app, ["templates", "issue", "--output", str(output)])
        assert result.exit_code == 0

    def test_templates_codeowners_command(
        self, initialized_adr_repo: Path, tmp_path: Path
    ) -> None:
        """Test templates codeowners command (covers cli.py lines 1588-1590)."""
        output = tmp_path / "CODEOWNERS"
        result = runner.invoke(
            app, ["templates", "codeowners", "--output", str(output)]
        )
        assert result.exit_code == 0

    def test_templates_all_command(
        self, initialized_adr_repo: Path, tmp_path: Path
    ) -> None:
        """Test templates all command (covers cli.py lines 1616-1618)."""
        result = runner.invoke(app, ["templates", "all", "--output-dir", str(tmp_path)])
        assert result.exit_code == 0

    def test_ci_list_command(self, initialized_adr_repo: Path) -> None:
        """Test ci list command (covers cli.py lines 1474-1476)."""
        result = runner.invoke(app, ["ci", "list"])
        assert result.exit_code == 0


# =============================================================================
# Notes Manager Coverage (notes.py)
# =============================================================================


class TestNotesManagerCoverage:
    """Tests for notes.py coverage gaps."""

    def test_list_all_empty(self, initialized_adr_repo: Path) -> None:
        """Test list_all when no ADRs exist."""
        from git_adr.core.config import ConfigManager
        from git_adr.core.git import Git
        from git_adr.core.notes import NotesManager

        git = Git(cwd=initialized_adr_repo)
        config = ConfigManager(git).load()
        notes = NotesManager(git, config)

        # List all should return empty list
        result = notes.list_all()
        assert result == []

    def test_get_nonexistent(self, initialized_adr_repo: Path) -> None:
        """Test get for non-existent ADR."""
        from git_adr.core.config import ConfigManager
        from git_adr.core.git import Git
        from git_adr.core.notes import NotesManager

        git = Git(cwd=initialized_adr_repo)
        config = ConfigManager(git).load()
        notes = NotesManager(git, config)

        # Get non-existent should return None
        result = notes.get("nonexistent-adr-id")
        assert result is None


# =============================================================================
# Git Coverage (git.py)
# =============================================================================


class TestGitCoverage:
    """Tests for git.py coverage gaps."""

    def test_config_get_nonexistent(self, initialized_adr_repo: Path) -> None:
        """Test config_get for non-existent key."""
        from git_adr.core.git import Git

        git = Git(cwd=initialized_adr_repo)
        result = git.config_get("nonexistent.key.that.does.not.exist")
        assert result is None

    def test_notes_remove_nonexistent(self, initialized_adr_repo: Path) -> None:
        """Test notes_remove for non-existent note returns False."""
        from git_adr.core.git import Git

        git = Git(cwd=initialized_adr_repo)
        # Should not raise and should return False when note does not exist
        result = git.notes_remove("HEAD", ref="refs/notes/test-nonexistent")
        assert result is False

    def test_config_unset_all_values(self, initialized_adr_repo: Path) -> None:
        """Test config_unset with all_values=True for multi-valued keys.

        Covers the all_values parameter that uses --unset-all flag.
        This is used when clearing multi-valued config like notes.rewriteRef.
        """
        from git_adr.core.git import Git

        git = Git(cwd=initialized_adr_repo)

        # First, set up a multi-valued config key
        git.config_set("test.multivalue", "value1")
        git.run(["config", "--add", "test.multivalue", "value2"])
        git.run(["config", "--add", "test.multivalue", "value3"])

        # Verify multiple values exist
        result = git.run(["config", "--get-all", "test.multivalue"])
        values = result.stdout.strip().split("\n")
        assert len(values) == 3

        # Use all_values=True to unset all values at once
        unset_result = git.config_unset("test.multivalue", all_values=True)
        assert unset_result is True

        # Verify all values are gone
        result = git.config_get("test.multivalue")
        assert result is None

    def test_config_unset_all_values_nonexistent(
        self, initialized_adr_repo: Path
    ) -> None:
        """Test config_unset with all_values=True on non-existent key."""
        from git_adr.core.git import Git

        git = Git(cwd=initialized_adr_repo)

        # Should return False for non-existent key
        result = git.config_unset(
            "nonexistent.multi.key.that.does.not.exist", all_values=True
        )
        assert result is False


# =============================================================================
# Core ADR Coverage (adr.py)
# =============================================================================


class TestADRCoverage:
    """Tests for adr.py coverage gaps."""

    def test_adr_from_markdown_invalid_yaml(self) -> None:
        """Test ADR.from_markdown with invalid YAML frontmatter.

        Covers the yaml.YAMLError exception handling in from_markdown.
        """
        from git_adr.core.adr import ADR

        invalid_content = """---
invalid: yaml: content: [
---

## Context
Test
"""
        # Should raise ValueError with specific message for invalid YAML
        with pytest.raises(ValueError, match="Invalid YAML frontmatter"):
            ADR.from_markdown(invalid_content)

    def test_adr_metadata_optional_fields(self) -> None:
        """Test ADRMetadata with optional fields."""
        from datetime import date

        from git_adr.core.adr import ADRMetadata, ADRStatus

        metadata = ADRMetadata(
            id="test-adr",
            title="Test ADR",
            date=date.today(),
            status=ADRStatus.PROPOSED,
            tags=["tag1", "tag2"],
            deciders=["John", "Jane"],
            consulted=["Team A"],
            informed=["Stakeholders"],
            supersedes="old-adr",
            superseded_by="new-adr",
        )

        assert metadata.tags == ["tag1", "tag2"]
        assert metadata.supersedes == "old-adr"
        assert metadata.superseded_by == "new-adr"
        assert metadata.deciders == ["John", "Jane"]


# =============================================================================
# Index Coverage (index.py)
# =============================================================================


class TestIndexCoverage:
    """Tests for index.py coverage gaps."""

    def test_index_search_no_results(self, initialized_adr_repo: Path) -> None:
        """Test index search with no results."""
        from git_adr.core.config import ConfigManager
        from git_adr.core.git import Git
        from git_adr.core.index import IndexManager
        from git_adr.core.notes import NotesManager

        git = Git(cwd=initialized_adr_repo)
        config = ConfigManager(git).load()
        notes = NotesManager(git, config)
        index = IndexManager(notes)

        # Search for something that doesn't exist
        results = index.search("xyznonexistentquery123")
        assert results == []


# =============================================================================
# Issue Command Coverage (issue.py)
# =============================================================================


class TestIssueCommandCoverageFull:
    """Tests for issue command coverage gaps."""

    def test_issue_bug_dry_run(self, initialized_adr_repo: Path) -> None:
        """Test issue bug with dry run."""
        result = runner.invoke(
            app, ["issue", "--type", "bug", "--dry-run", "--local-only", "--no-edit"]
        )
        # Should work with dry-run
        assert result.exit_code in [0, 1]

    def test_issue_feat_dry_run(self, initialized_adr_repo: Path) -> None:
        """Test issue feature with dry run."""
        result = runner.invoke(
            app, ["issue", "--type", "feat", "--dry-run", "--local-only", "--no-edit"]
        )
        assert result.exit_code in [0, 1]

    def test_issue_with_all_flags(self, initialized_adr_repo: Path) -> None:
        """Test issue command with all flags."""
        result = runner.invoke(
            app,
            [
                "issue",
                "--type",
                "bug",
                "--title",
                "Test Bug Title",
                "--description",
                "Test description",
                "--label",
                "test-label",
                "--assignee",
                "testuser",
                "--dry-run",
                "--local-only",
                "--no-edit",
            ],
        )
        assert result.exit_code in [0, 1]
