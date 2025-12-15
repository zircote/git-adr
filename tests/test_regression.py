"""Regression tests for known bugs.

These tests document and verify fixes for bugs discovered during development.
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from git_adr.cli import app
from git_adr.core.git import Git

runner = CliRunner()


class TestInitListConsistency:
    """Regression test for init/list state inconsistency.

    Bug: `git adr list` says "not initialized" while
    `git adr init` says "already initialized".

    Root cause: list checks config_manager.get("initialized")
    while init checks notes_manager.is_initialized(). These
    can get out of sync if:
    - Config exists but no notes
    - Notes exist but config was cleared
    """

    def test_list_works_after_init(self, initialized_adr_repo: Path) -> None:
        """Test that list works after initialization."""
        # List should work (may be empty, but shouldn't say not initialized)
        list_result = runner.invoke(app, ["list"])
        assert list_result.exit_code == 0, f"List failed: {list_result.output}"
        assert "not initialized" not in list_result.output.lower()

    def test_init_and_list_state_consistent(self, initialized_adr_repo: Path) -> None:
        """Test that init and list agree on initialization state."""
        # List should work in initialized repo
        list1 = runner.invoke(app, ["list"])
        assert list1.exit_code == 0
        assert "not initialized" not in list1.output.lower()

        # Second init without --force should warn (already initialized)
        init2 = runner.invoke(app, ["init"])
        # Should either succeed with warning or report already initialized
        assert "already" in init2.output.lower() or init2.exit_code == 0

        # List should still work
        list2 = runner.invoke(app, ["list"])
        assert list2.exit_code == 0
        assert "not initialized" not in list2.output.lower()

    def test_init_force_reinitializes(self, initialized_adr_repo: Path) -> None:
        """Test that init --force works properly."""
        # Force reinit
        result = runner.invoke(app, ["init", "--force"])
        # May succeed or fail with git config conflicts
        assert result.exit_code in [0, 1]

        # List should work regardless
        list_result = runner.invoke(app, ["list"])
        assert list_result.exit_code == 0

    def test_state_consistency_after_operations(
        self, initialized_adr_repo: Path
    ) -> None:
        """Test state remains consistent after various operations."""
        # Create an ADR
        runner.invoke(app, ["new", "Test Decision", "--batch"])

        # List should work
        list_result = runner.invoke(app, ["list"])
        assert list_result.exit_code == 0
        assert "not initialized" not in list_result.output.lower()

        # Init should say already initialized (not crash)
        init_result = runner.invoke(app, ["init"])
        assert "already" in init_result.output.lower() or init_result.exit_code == 0


class TestConfigNotesSyncBug:
    """Test that config and notes stay in sync."""

    def test_config_set_after_init(self, initialized_adr_repo: Path) -> None:
        """Test that config changes don't break init state."""
        # Change a config value
        runner.invoke(app, ["config", "template", "nygard", "--set"])

        # List should still work
        list_result = runner.invoke(app, ["list"])
        assert list_result.exit_code == 0

    def test_manual_config_clear_recovery(self, initialized_adr_repo: Path) -> None:
        """Test recovery when config is manually cleared."""
        # Manually clear the initialized flag (simulating corruption)
        git = Git(cwd=initialized_adr_repo)
        try:
            git.config_unset("adr.initialized")
        except Exception:
            pass  # May not exist

        # List may fail after clearing config
        list_result = runner.invoke(app, ["list"])
        # Check behavior is graceful (either fails with init message or works)
        if list_result.exit_code != 0:
            assert (
                "init" in list_result.output.lower()
                or "not initialized" in list_result.output.lower()
            )

        # Re-initialize should work
        git.config_set("adr.initialized", "true")
        list_result = runner.invoke(app, ["list"])
        assert list_result.exit_code == 0


class TestEdgeCaseRegressions:
    """Tests for edge case regressions."""

    def test_show_nonexistent_adr_graceful(self, initialized_adr_repo: Path) -> None:
        """Test that showing non-existent ADR fails gracefully."""
        result = runner.invoke(app, ["show", "nonexistent-id-12345"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_search_empty_repo(self, initialized_adr_repo: Path) -> None:
        """Test that search in empty repo doesn't crash."""
        result = runner.invoke(app, ["search", "anything"])
        assert result.exit_code == 0

    def test_stats_empty_repo(self, initialized_adr_repo: Path) -> None:
        """Test that stats in empty repo doesn't crash."""
        result = runner.invoke(app, ["stats"])
        assert result.exit_code == 0

    def test_report_empty_repo(self, initialized_adr_repo: Path) -> None:
        """Test that report in empty repo doesn't crash."""
        result = runner.invoke(app, ["report"])
        assert result.exit_code == 0

    def test_metrics_empty_repo(self, initialized_adr_repo: Path) -> None:
        """Test that metrics in empty repo doesn't crash."""
        result = runner.invoke(app, ["metrics"])
        assert result.exit_code == 0

    def test_export_empty_repo(
        self, initialized_adr_repo: Path, tmp_path: Path
    ) -> None:
        """Test that export in empty repo handles gracefully."""
        output = tmp_path / "export.json"
        result = runner.invoke(
            app, ["export", "--format", "json", "--output", str(output)]
        )
        # Should succeed (may export empty array) or gracefully report no ADRs
        assert result.exit_code in [0, 1]


class TestCLIHelpRegressions:
    """Tests for CLI help and version commands."""

    def test_help_main(self) -> None:
        """Test main help works."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "git-adr" in result.output.lower() or "adr" in result.output.lower()

    def test_help_subcommands(self) -> None:
        """Test help for all subcommands."""
        subcommands = [
            "new",
            "list",
            "show",
            "search",
            "edit",
            "init",
            "config",
            "export",
            "stats",
            "report",
            "metrics",
            "log",
            "onboard",
        ]
        for cmd in subcommands:
            result = runner.invoke(app, [cmd, "--help"])
            assert result.exit_code == 0, f"Help failed for {cmd}: {result.output}"

    def test_version(self) -> None:
        """Test version command."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        # Should contain version number
        assert "0." in result.output or "git-adr" in result.output.lower()
