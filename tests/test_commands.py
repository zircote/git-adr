"""Integration tests for git-adr commands.

Note: These tests use CliRunner which has limitations with working directory
changes. Tests that require initialized repos are marked with pytest.mark.skip
when they can't be reliably executed in the test environment.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from git_adr.cli import app

runner = CliRunner()


class TestCLIBasics:
    """Basic CLI tests that don't require repo initialization."""

    def test_version(self) -> None:
        """Test --version flag."""
        import re

        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert re.search(r"\d+\.\d+\.\d+", result.output), "Version not found in output"

    def test_help(self) -> None:
        """Test --help flag."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "git-adr" in result.output.lower() or "adr" in result.output.lower()

    def test_init_help(self) -> None:
        """Test init --help."""
        result = runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0

    def test_new_help(self) -> None:
        """Test new --help."""
        result = runner.invoke(app, ["new", "--help"])
        assert result.exit_code == 0

    def test_list_help(self) -> None:
        """Test list --help."""
        result = runner.invoke(app, ["list", "--help"])
        assert result.exit_code == 0

    def test_show_help(self) -> None:
        """Test show --help."""
        result = runner.invoke(app, ["show", "--help"])
        assert result.exit_code == 0

    def test_stats_help(self) -> None:
        """Test stats --help."""
        result = runner.invoke(app, ["stats", "--help"])
        assert result.exit_code == 0
        assert "velocity" in result.output.lower()

    def test_metrics_help(self) -> None:
        """Test metrics --help."""
        result = runner.invoke(app, ["metrics", "--help"])
        assert result.exit_code == 0

    def test_export_help(self) -> None:
        """Test export --help."""
        result = runner.invoke(app, ["export", "--help"])
        assert result.exit_code == 0


class TestCLIInNonRepo:
    """Test CLI behavior when not in a git repository."""

    def test_init_not_a_repo(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test init fails gracefully outside git repo."""
        # Change to tmp_path which is not a git repository
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["init"])
        # Should fail with non-zero exit code when not in a git repository
        assert result.exit_code != 0, "Expected non-zero exit code outside git repo"
        assert "repository" in result.output.lower() or "error" in result.output.lower()


class TestCommandSubgroups:
    """Test command subgroups exist."""

    def test_ai_subgroup(self) -> None:
        """Test ai subcommand group."""
        result = runner.invoke(app, ["ai", "--help"])
        assert result.exit_code == 0
        assert "draft" in result.output.lower() or "AI" in result.output

    def test_wiki_subgroup(self) -> None:
        """Test wiki subcommand group."""
        result = runner.invoke(app, ["wiki", "--help"])
        assert result.exit_code == 0

    def test_config_subgroup(self) -> None:
        """Test config subcommand group."""
        result = runner.invoke(app, ["config", "--help"])
        assert result.exit_code == 0


class TestCommandRegistration:
    """Test that all expected commands are registered."""

    def test_core_commands_exist(self) -> None:
        """Verify core commands are registered."""
        result = runner.invoke(app, ["--help"])
        output = result.output.lower()

        # Core commands
        assert "init" in output
        assert "new" in output
        assert "list" in output
        assert "show" in output
        assert "search" in output

    def test_analytics_commands_exist(self) -> None:
        """Verify analytics commands are registered."""
        result = runner.invoke(app, ["--help"])
        output = result.output.lower()

        assert "stats" in output
        assert "report" in output
        assert "metrics" in output

    def test_export_import_commands_exist(self) -> None:
        """Verify export/import commands are registered."""
        result = runner.invoke(app, ["--help"])
        output = result.output.lower()

        assert "export" in output
        assert "import" in output

    def test_status_commands_exist(self) -> None:
        """Verify status change commands are registered."""
        result = runner.invoke(app, ["--help"])
        output = result.output.lower()

        # supersede is a top-level command
        assert "supersede" in output
        # Other status commands may be organized differently
        # The main help shows "supersede" for status changes
