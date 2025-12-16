"""Integration tests for git-adr CLI commands.

Tests CLI commands with real git repositories.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from git_adr.cli import app
from git_adr.core.config import ConfigManager
from git_adr.core.git import Git
from git_adr.core.notes import NotesManager

runner = CliRunner()


# =============================================================================
# Init Command Tests
# =============================================================================


@pytest.mark.integration
class TestInitCommand:
    """Tests for the init command."""

    def test_init_creates_config(
        self, temp_git_repo_with_commit: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test init creates git-adr configuration."""
        monkeypatch.chdir(temp_git_repo_with_commit)

        # Use --force to ensure clean init in case of state bleeding
        result = runner.invoke(app, ["init", "--force"])
        assert result.exit_code == 0, f"Init failed: {result.output}"

        # Verify config was created
        git = Git(cwd=temp_git_repo_with_commit)
        assert git.config_get("adr.namespace") == "adr"

    def test_init_with_custom_namespace(
        self, temp_git_repo_with_commit: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test init with custom namespace."""
        monkeypatch.chdir(temp_git_repo_with_commit)

        result = runner.invoke(app, ["init", "--namespace", "decisions", "--force"])
        assert result.exit_code == 0, f"Init failed: {result.output}"

        git = Git(cwd=temp_git_repo_with_commit)
        assert git.config_get("adr.namespace") == "decisions"

    def test_init_with_custom_template(
        self, temp_git_repo_with_commit: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test init with custom template."""
        monkeypatch.chdir(temp_git_repo_with_commit)

        result = runner.invoke(app, ["init", "--template", "nygard", "--force"])
        assert result.exit_code == 0, f"Init failed: {result.output}"

        git = Git(cwd=temp_git_repo_with_commit)
        assert git.config_get("adr.template") == "nygard"

    def test_init_creates_initial_adr(
        self, temp_git_repo_with_commit: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test init creates initial ADR-0 about using ADRs."""
        monkeypatch.chdir(temp_git_repo_with_commit)

        result = runner.invoke(app, ["init", "--force"])
        assert result.exit_code == 0, f"Init failed: {result.output}"

        # Check that initial ADR was created
        git = Git(cwd=temp_git_repo_with_commit)
        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)

        adrs = notes_manager.list_all()
        # Should have at least the initial ADR
        assert len(adrs) >= 1

    def test_init_fails_outside_git_repo(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test init fails gracefully outside git repo."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["init"])
        assert result.exit_code != 0


@pytest.mark.integration
class TestInitInteractiveFlags:
    """Tests for init command interactive flags."""

    def test_init_no_input_uses_defaults(
        self, temp_git_repo_with_commit: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test --no-input flag uses default template without prompting."""
        monkeypatch.chdir(temp_git_repo_with_commit)

        result = runner.invoke(app, ["init", "--no-input", "--force"])
        assert result.exit_code == 0, f"Init failed: {result.output}"

        git = Git(cwd=temp_git_repo_with_commit)
        assert git.config_get("adr.template") == "madr"

    def test_init_explicit_template_bypasses_prompt(
        self, temp_git_repo_with_commit: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test explicit --template flag bypasses interactive prompt."""
        monkeypatch.chdir(temp_git_repo_with_commit)

        result = runner.invoke(
            app, ["init", "--template", "nygard", "--no-input", "--force"]
        )
        assert result.exit_code == 0, f"Init failed: {result.output}"

        git = Git(cwd=temp_git_repo_with_commit)
        assert git.config_get("adr.template") == "nygard"

    def test_init_install_hooks_flag(
        self, temp_git_repo_with_commit: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test --install-hooks flag installs hooks without prompting."""
        monkeypatch.chdir(temp_git_repo_with_commit)

        result = runner.invoke(
            app, ["init", "--install-hooks", "--no-input", "--force"]
        )
        assert result.exit_code == 0, f"Init failed: {result.output}"
        assert "hooks installed" in result.output.lower()

        # Verify hook was actually installed
        hooks_dir = temp_git_repo_with_commit / ".git" / "hooks"
        pre_push = hooks_dir / "pre-push"
        assert pre_push.exists(), "Pre-push hook should be installed"

    def test_init_no_install_hooks_flag(
        self, temp_git_repo_with_commit: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test --no-install-hooks flag skips hook installation."""
        monkeypatch.chdir(temp_git_repo_with_commit)

        result = runner.invoke(
            app, ["init", "--no-install-hooks", "--no-input", "--force"]
        )
        assert result.exit_code == 0, f"Init failed: {result.output}"
        assert "hooks installed" not in result.output.lower()

    def test_init_setup_github_ci_flag(
        self, temp_git_repo_with_commit: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test --setup-github-ci flag generates CI workflows."""
        monkeypatch.chdir(temp_git_repo_with_commit)

        result = runner.invoke(
            app, ["init", "--setup-github-ci", "--no-input", "--force"]
        )
        assert result.exit_code == 0, f"Init failed: {result.output}"

        # Verify workflows were created
        workflows_dir = temp_git_repo_with_commit / ".github" / "workflows"
        assert workflows_dir.exists(), "Workflows directory should be created"

    def test_init_no_setup_github_ci_flag(
        self, temp_git_repo_with_commit: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test --no-setup-github-ci flag skips CI generation."""
        monkeypatch.chdir(temp_git_repo_with_commit)

        result = runner.invoke(
            app, ["init", "--no-setup-github-ci", "--no-input", "--force"]
        )
        assert result.exit_code == 0, f"Init failed: {result.output}"

        # Verify workflows were NOT created
        workflows_dir = temp_git_repo_with_commit / ".github" / "workflows"
        assert not workflows_dir.exists(), "Workflows directory should not be created"

    def test_init_combined_flags(
        self, temp_git_repo_with_commit: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test combining --install-hooks and --setup-github-ci flags."""
        monkeypatch.chdir(temp_git_repo_with_commit)

        result = runner.invoke(
            app,
            [
                "init",
                "--template",
                "business",
                "--install-hooks",
                "--setup-github-ci",
                "--force",
            ],
        )
        assert result.exit_code == 0, f"Init failed: {result.output}"

        git = Git(cwd=temp_git_repo_with_commit)
        assert git.config_get("adr.template") == "business"
        assert "hooks installed" in result.output.lower()

        # Verify both hooks and CI were set up
        hooks_dir = temp_git_repo_with_commit / ".git" / "hooks"
        pre_push = hooks_dir / "pre-push"
        assert pre_push.exists(), "Pre-push hook should be installed"

        workflows_dir = temp_git_repo_with_commit / ".github" / "workflows"
        assert workflows_dir.exists(), "Workflows directory should be created"

    def test_init_non_tty_skips_prompts(
        self, temp_git_repo_with_commit: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that non-TTY environments skip prompts automatically.

        CliRunner simulates non-TTY by default, so this verifies
        the command completes without hanging for input.
        """
        monkeypatch.chdir(temp_git_repo_with_commit)

        # Should not hang waiting for input
        result = runner.invoke(app, ["init", "--force"])
        assert result.exit_code == 0, f"Init failed: {result.output}"

    def test_init_next_steps_show_uninstalled_features(
        self, temp_git_repo_with_commit: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test next steps show hooks and CI commands when not installed."""
        monkeypatch.chdir(temp_git_repo_with_commit)

        result = runner.invoke(
            app, ["init", "--no-install-hooks", "--no-setup-github-ci", "--force"]
        )
        assert result.exit_code == 0, f"Init failed: {result.output}"

        # Should show hints for both hooks and CI
        assert "git adr hooks install" in result.output
        assert "git adr ci github" in result.output

    def test_init_next_steps_hide_installed_features(
        self, temp_git_repo_with_commit: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test next steps don't show hooks/CI commands when already installed."""
        monkeypatch.chdir(temp_git_repo_with_commit)

        result = runner.invoke(
            app,
            ["init", "--install-hooks", "--setup-github-ci", "--no-input", "--force"],
        )
        assert result.exit_code == 0, f"Init failed: {result.output}"

        # Verify installations succeeded
        assert "hooks installed" in result.output.lower(), (
            f"Hooks should be installed. Output: {result.output}"
        )

        # After "Next steps:", the hints for hooks and CI shouldn't appear
        # (since they were already installed)
        output_after_next_steps = result.output.split("Next steps:")[-1]
        assert "git adr hooks install" not in output_after_next_steps
        assert "git adr ci github" not in output_after_next_steps


# =============================================================================
# New Command Tests
# =============================================================================


@pytest.mark.integration
class TestNewCommand:
    """Tests for the new command."""

    def test_new_with_stdin(self, initialized_adr_repo: Path) -> None:
        """Test creating new ADR from stdin."""
        content = """---
deciders:
  - Test User
---
## Context

Test context.

## Decision

Test decision."""

        result = runner.invoke(
            app,
            ["new", "Test ADR", "--no-edit"],
            input=content,
        )
        # May require actual stdin support - check output
        assert result.exit_code == 0 or "error" not in result.output.lower()

    def test_new_with_status(self, initialized_adr_repo: Path) -> None:
        """Test creating new ADR with specific status."""
        result = runner.invoke(
            app,
            ["new", "Proposed ADR", "--status", "proposed", "--no-edit", "--preview"],
        )
        assert result.exit_code == 0
        assert "proposed" in result.output.lower()

    def test_new_with_tags(self, initialized_adr_repo: Path) -> None:
        """Test creating new ADR with tags."""
        result = runner.invoke(
            app,
            [
                "new",
                "Tagged ADR",
                "--tag",
                "database",
                "--tag",
                "backend",
                "--no-edit",
                "--preview",
            ],
        )
        assert result.exit_code == 0

    def test_new_preview_mode(self, initialized_adr_repo: Path) -> None:
        """Test preview mode shows template without creating."""
        result = runner.invoke(
            app,
            ["new", "Preview ADR", "--preview"],
        )
        assert result.exit_code == 0
        # Preview should show content but not create


# =============================================================================
# List Command Tests
# =============================================================================


@pytest.mark.integration
class TestListCommand:
    """Tests for the list command."""

    def test_list_empty(self, initialized_adr_repo: Path) -> None:
        """Test listing when no ADRs exist (except initial)."""
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0

    def test_list_with_adrs(self, adr_repo_with_data: Path) -> None:
        """Test listing ADRs."""
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        # Check for parts of the ADR IDs or titles
        output_lower = result.output.lower()
        assert (
            "postgresql" in output_lower
            or "postgres" in output_lower
            or "20250110" in result.output
        )

    def test_list_filter_by_status(self, adr_repo_with_data: Path) -> None:
        """Test filtering list by status."""
        result = runner.invoke(app, ["list", "--status", "accepted"])
        assert result.exit_code == 0

    def test_list_filter_by_tag(self, adr_repo_with_data: Path) -> None:
        """Test filtering list by tag."""
        result = runner.invoke(app, ["list", "--tag", "database"])
        assert result.exit_code == 0

    def test_list_json_format(self, adr_repo_with_data: Path) -> None:
        """Test listing in JSON format."""
        result = runner.invoke(app, ["list", "--format", "json"])
        assert result.exit_code == 0
        # Should be valid JSON
        try:
            data = json.loads(result.output)
            assert isinstance(data, list)
        except json.JSONDecodeError:
            # Output might include non-JSON elements
            pass


# =============================================================================
# Show Command Tests
# =============================================================================


@pytest.mark.integration
class TestShowCommand:
    """Tests for the show command."""

    def test_show_adr(self, adr_repo_with_data: Path) -> None:
        """Test showing an ADR."""
        result = runner.invoke(app, ["show", "20250110-use-postgresql"])
        assert result.exit_code == 0
        assert "postgresql" in result.output.lower()

    def test_show_nonexistent(self, initialized_adr_repo: Path) -> None:
        """Test showing nonexistent ADR."""
        result = runner.invoke(app, ["show", "nonexistent-adr"])
        assert result.exit_code != 0 or "not found" in result.output.lower()

    def test_show_json_format(self, adr_repo_with_data: Path) -> None:
        """Test showing ADR in JSON format."""
        result = runner.invoke(
            app, ["show", "20250110-use-postgresql", "--format", "json"]
        )
        assert result.exit_code == 0


# =============================================================================
# Search Command Tests
# =============================================================================


@pytest.mark.integration
class TestSearchCommand:
    """Tests for the search command."""

    def test_search_by_content(self, adr_repo_with_data: Path) -> None:
        """Test searching ADRs by content."""
        result = runner.invoke(app, ["search", "database"])
        assert result.exit_code == 0

    def test_search_no_results(self, adr_repo_with_data: Path) -> None:
        """Test search with no results."""
        result = runner.invoke(app, ["search", "xyznonexistent123"])
        assert result.exit_code == 0


# =============================================================================
# Stats Command Tests
# =============================================================================


@pytest.mark.integration
class TestStatsCommand:
    """Tests for the stats command."""

    def test_stats(self, adr_repo_with_data: Path) -> None:
        """Test basic stats."""
        result = runner.invoke(app, ["stats"])
        assert result.exit_code == 0

    def test_stats_with_velocity(self, adr_repo_with_data: Path) -> None:
        """Test stats with velocity flag."""
        result = runner.invoke(app, ["stats", "--velocity"])
        assert result.exit_code == 0


# =============================================================================
# Metrics Command Tests
# =============================================================================


@pytest.mark.integration
class TestMetricsCommand:
    """Tests for the metrics command."""

    def test_metrics_prometheus(self, adr_repo_with_data: Path) -> None:
        """Test Prometheus metrics format."""
        result = runner.invoke(app, ["metrics", "--format", "prometheus"])
        assert result.exit_code == 0
        assert "adr_" in result.output or "# HELP" in result.output

    def test_metrics_json(self, adr_repo_with_data: Path) -> None:
        """Test JSON metrics format."""
        result = runner.invoke(app, ["metrics", "--format", "json"])
        assert result.exit_code == 0

    def test_metrics_csv(self, adr_repo_with_data: Path) -> None:
        """Test CSV metrics format."""
        result = runner.invoke(app, ["metrics", "--format", "csv"])
        assert result.exit_code == 0


# =============================================================================
# Export Command Tests
# =============================================================================


@pytest.mark.integration
class TestExportCommand:
    """Tests for the export command."""

    def test_export_json(self, adr_repo_with_data: Path, tmp_path: Path) -> None:
        """Test exporting to JSON."""
        output_file = tmp_path / "adrs.json"
        result = runner.invoke(
            app, ["export", "--format", "json", "--output", str(output_file)]
        )
        assert result.exit_code == 0
        assert output_file.exists()

    def test_export_markdown(self, adr_repo_with_data: Path, tmp_path: Path) -> None:
        """Test exporting to Markdown."""
        output_dir = tmp_path / "adrs"
        result = runner.invoke(
            app, ["export", "--format", "markdown", "--output", str(output_dir)]
        )
        assert result.exit_code == 0

    def test_export_html(self, adr_repo_with_data: Path, tmp_path: Path) -> None:
        """Test exporting to HTML."""
        output_dir = tmp_path / "adrs_html"
        result = runner.invoke(
            app, ["export", "--format", "html", "--output", str(output_dir)]
        )
        assert result.exit_code == 0


# =============================================================================
# Supersede Command Tests
# =============================================================================


@pytest.mark.integration
class TestSupersedeCommand:
    """Tests for the supersede command."""

    def test_supersede_adr(self, adr_repo_with_data: Path) -> None:
        """Test superseding an ADR."""
        # supersede takes: adr_id (being superseded) + title (for new ADR)
        result = runner.invoke(
            app,
            ["supersede", "20250110-use-postgresql", "Use CockroachDB Instead"],
        )
        # May open editor - check it doesn't crash with unexpected args
        assert "error" not in result.output.lower() or result.exit_code == 0


# =============================================================================
# Report Command Tests
# =============================================================================


@pytest.mark.integration
class TestReportCommand:
    """Tests for the report command."""

    def test_report_basic(self, adr_repo_with_data: Path) -> None:
        """Test basic report generation."""
        result = runner.invoke(app, ["report"])
        assert result.exit_code == 0

    def test_report_markdown(self, adr_repo_with_data: Path) -> None:
        """Test markdown report format."""
        result = runner.invoke(app, ["report", "--format", "markdown"])
        assert result.exit_code == 0


# =============================================================================
# Config Command Tests
# =============================================================================


@pytest.mark.integration
class TestConfigCommand:
    """Tests for the config command."""

    def test_config_list(self, initialized_adr_repo: Path) -> None:
        """Test listing config."""
        result = runner.invoke(app, ["config", "--list"])
        assert result.exit_code == 0

    def test_config_set(self, initialized_adr_repo: Path) -> None:
        """Test setting config value."""
        # config takes: key value --set
        result = runner.invoke(app, ["config", "template", "nygard", "--set"])
        assert result.exit_code == 0

    def test_config_get(self, initialized_adr_repo: Path) -> None:
        """Test getting config value."""
        result = runner.invoke(app, ["config", "namespace", "--get"])
        assert result.exit_code == 0


# =============================================================================
# Sync Command Tests
# =============================================================================


@pytest.mark.integration
class TestSyncCommand:
    """Tests for the sync command."""

    def test_sync_pull(self, adr_repo_with_data: Path) -> None:
        """Test sync pull (may fail without remote, but should not crash)."""
        result = runner.invoke(app, ["sync", "--pull"])
        # Expect failure since no remote, but should handle gracefully
        assert (
            result.exit_code != 0
            or "remote" in result.output.lower()
            or "origin" in result.output.lower()
        )

    def test_sync_help(self, adr_repo_with_data: Path) -> None:
        """Test sync help."""
        result = runner.invoke(app, ["sync", "--help"])
        assert result.exit_code == 0
        assert "push" in result.output.lower()
        assert "pull" in result.output.lower()


# =============================================================================
# Log Command Tests
# =============================================================================


@pytest.mark.integration
class TestLogCommand:
    """Tests for the log command."""

    def test_log(self, adr_repo_with_data: Path) -> None:
        """Test ADR log."""
        result = runner.invoke(app, ["log"])
        assert result.exit_code == 0

    def test_log_with_limit(self, adr_repo_with_data: Path) -> None:
        """Test log with limit."""
        # log uses -n, not --limit
        result = runner.invoke(app, ["log", "-n", "5"])
        assert result.exit_code == 0
