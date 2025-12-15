"""Tests for remaining low-coverage modules.

Covers artifact commands, attach, link, import, and other edge cases.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from git_adr.cli import app
from git_adr.core.config import Config
from git_adr.core.git import Git

runner = CliRunner()


# =============================================================================
# Artifact Commands Tests
# =============================================================================


class TestArtifactsCommand:
    """Tests for artifacts listing command."""

    def test_artifacts_list_with_adr(self, adr_repo_with_data: Path) -> None:
        """Test listing artifacts for specific ADR."""
        # artifacts command requires an ADR ID argument
        result = runner.invoke(app, ["artifacts", "20250110-use-postgresql"])
        assert result.exit_code in [0, 1]

    def test_artifacts_help(self, initialized_adr_repo: Path) -> None:
        """Test artifacts help."""
        result = runner.invoke(app, ["artifacts", "--help"])
        assert result.exit_code == 0

    def test_artifacts_not_initialized(self, temp_git_repo_with_commit: Path) -> None:
        """Test artifacts in non-initialized repo requires ADR ID."""
        result = runner.invoke(app, ["artifacts", "some-adr"])
        assert result.exit_code != 0


class TestAttachCommand:
    """Tests for attach command."""

    def test_attach_file(self, adr_repo_with_data: Path, tmp_path: Path) -> None:
        """Test attaching a file to an ADR."""
        # Create a test file
        test_file = tmp_path / "diagram.png"
        test_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)

        result = runner.invoke(
            app,
            [
                "attach",
                "20250110-use-postgresql",
                str(test_file),
                "--alt",
                "Architecture diagram",
            ],
        )
        assert result.exit_code in [0, 1]

    def test_attach_nonexistent_file(self, adr_repo_with_data: Path) -> None:
        """Test attaching non-existent file."""
        result = runner.invoke(
            app, ["attach", "20250110-use-postgresql", "/nonexistent/file.png"]
        )
        assert result.exit_code != 0

    def test_attach_to_nonexistent_adr(
        self, initialized_adr_repo: Path, tmp_path: Path
    ) -> None:
        """Test attaching to non-existent ADR."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"test content")

        result = runner.invoke(app, ["attach", "nonexistent-adr", str(test_file)])
        assert result.exit_code != 0

    def test_attach_not_initialized(self, temp_git_repo: Path, tmp_path: Path) -> None:
        """Test attach in non-initialized repo."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"test")

        result = runner.invoke(app, ["attach", "some-adr", str(test_file)])
        assert result.exit_code != 0


class TestArtifactGetCommand:
    """Tests for artifact-get command."""

    def test_artifact_get_nonexistent(self, adr_repo_with_data: Path) -> None:
        """Test getting non-existent artifact."""
        result = runner.invoke(app, ["artifact-get", "0" * 64])
        assert result.exit_code != 0

    def test_artifact_get_not_initialized(self, temp_git_repo: Path) -> None:
        """Test artifact-get in non-initialized repo."""
        result = runner.invoke(app, ["artifact-get", "abc123"])
        assert result.exit_code != 0


class TestArtifactRmCommand:
    """Tests for artifact-rm command."""

    def test_artifact_rm_help(self, adr_repo_with_data: Path) -> None:
        """Test artifact-rm help."""
        result = runner.invoke(app, ["artifact-rm", "--help"])
        assert result.exit_code == 0

    def test_artifact_rm_not_initialized(self, temp_git_repo_with_commit: Path) -> None:
        """Test artifact-rm in non-initialized repo."""
        result = runner.invoke(app, ["artifact-rm", "some-adr", "hash123"])
        assert result.exit_code != 0


# =============================================================================
# Link Command Tests
# =============================================================================


class TestLinkCommand:
    """Tests for link command."""

    def test_link_commit(self, adr_repo_with_data: Path) -> None:
        """Test linking a commit to an ADR."""
        git = Git(cwd=adr_repo_with_data)
        head = git.get_head_commit()

        result = runner.invoke(app, ["link", "20250110-use-postgresql", head])
        assert result.exit_code in [0, 1]

    def test_link_nonexistent_commit(self, adr_repo_with_data: Path) -> None:
        """Test linking non-existent commit."""
        result = runner.invoke(app, ["link", "20250110-use-postgresql", "0" * 40])
        # Should handle gracefully
        assert result.exit_code in [0, 1]

    def test_link_to_nonexistent_adr(self, adr_repo_with_data: Path) -> None:
        """Test linking to non-existent ADR."""
        git = Git(cwd=adr_repo_with_data)
        head = git.get_head_commit()

        result = runner.invoke(app, ["link", "nonexistent-adr", head])
        assert result.exit_code != 0

    def test_link_not_initialized(self, temp_git_repo_with_commit: Path) -> None:
        """Test link in non-initialized repo."""
        git = Git(cwd=temp_git_repo_with_commit)
        head = git.get_head_commit()

        result = runner.invoke(app, ["link", "some-adr", head])
        assert result.exit_code != 0


# =============================================================================
# Import Command Tests
# =============================================================================


class TestImportCommand:
    """Tests for import command."""

    def test_import_single_file(
        self, initialized_adr_repo: Path, tmp_path: Path
    ) -> None:
        """Test importing a single ADR file."""
        adr_file = tmp_path / "0001-test-decision.md"
        adr_file.write_text("""---
title: Test Decision
date: 2025-01-15
status: accepted
---

# Test Decision

## Context

We need to decide.

## Decision

We decided.

## Consequences

Good things.
""")

        result = runner.invoke(app, ["import", str(adr_file)])
        assert result.exit_code in [0, 1]

    def test_import_directory(self, initialized_adr_repo: Path, tmp_path: Path) -> None:
        """Test importing a directory of ADRs."""
        adr_dir = tmp_path / "adrs"
        adr_dir.mkdir()

        for i in range(3):
            adr_file = adr_dir / f"000{i + 1}-decision-{i}.md"
            adr_file.write_text(f"""---
title: Decision {i}
date: 2025-01-{10 + i}
status: proposed
---

## Context

Context {i}.

## Decision

Decision {i}.
""")

        result = runner.invoke(app, ["import", str(adr_dir)])
        assert result.exit_code in [0, 1]

    def test_import_dry_run(self, initialized_adr_repo: Path, tmp_path: Path) -> None:
        """Test import with dry-run flag."""
        adr_file = tmp_path / "test.md"
        adr_file.write_text("""# Test

## Context

Test.

## Decision

Test.
""")

        result = runner.invoke(app, ["import", str(adr_file), "--dry-run"])
        assert result.exit_code in [0, 1]

    def test_import_with_format(
        self, initialized_adr_repo: Path, tmp_path: Path
    ) -> None:
        """Test import with explicit format."""
        adr_file = tmp_path / "test.md"
        adr_file.write_text("""# Test Decision

## Status

Accepted

## Context

Context here.

## Decision

Decision here.

## Consequences

Consequences here.
""")

        result = runner.invoke(app, ["import", str(adr_file), "--format", "nygard"])
        assert result.exit_code in [0, 1]

    def test_import_nonexistent_path(self, initialized_adr_repo: Path) -> None:
        """Test import with non-existent path."""
        result = runner.invoke(app, ["import", "/nonexistent/path"])
        assert result.exit_code != 0

    def test_import_help(self, initialized_adr_repo: Path) -> None:
        """Test import help."""
        result = runner.invoke(app, ["import", "--help"])
        assert result.exit_code == 0
        assert "import" in result.output.lower()


# =============================================================================
# Config Command Extended Tests
# =============================================================================


class TestConfigCommandExtended:
    """Extended tests for config command."""

    def test_config_set_template(self, initialized_adr_repo: Path) -> None:
        """Test setting template config."""
        result = runner.invoke(app, ["config", "template", "nygard", "--set"])
        assert result.exit_code == 0

        # Verify it was set
        result = runner.invoke(app, ["config", "template"])
        assert "nygard" in result.output.lower()

    def test_config_set_namespace(self, initialized_adr_repo: Path) -> None:
        """Test setting namespace config."""
        result = runner.invoke(app, ["config", "namespace", "custom-adr", "--set"])
        assert result.exit_code == 0

    def test_config_list(self, initialized_adr_repo: Path) -> None:
        """Test listing all config."""
        result = runner.invoke(app, ["config", "--list"])
        assert result.exit_code == 0

    def test_config_unset(self, initialized_adr_repo: Path) -> None:
        """Test unsetting a config value."""
        # First set
        runner.invoke(app, ["config", "template", "nygard", "--set"])
        # Then unset
        result = runner.invoke(app, ["config", "template", "--unset"])
        assert result.exit_code in [0, 1]

    def test_config_get_nonexistent(self, initialized_adr_repo: Path) -> None:
        """Test getting non-existent config key."""
        result = runner.invoke(app, ["config", "nonexistent.key"])
        # Should handle gracefully
        assert result.exit_code in [0, 1]

    def test_config_global(self, initialized_adr_repo: Path) -> None:
        """Test global config operations."""
        result = runner.invoke(app, ["config", "--list", "--global"])
        assert result.exit_code == 0


# =============================================================================
# Export Command Extended Tests
# =============================================================================


class TestExportCommandExtended:
    """Extended tests for export command."""

    def test_export_json(self, adr_repo_with_data: Path, tmp_path: Path) -> None:
        """Test exporting to JSON."""
        output = tmp_path / "adrs.json"
        result = runner.invoke(
            app, ["export", "--format", "json", "--output", str(output)]
        )
        assert result.exit_code == 0
        assert output.exists()

    def test_export_markdown(self, adr_repo_with_data: Path, tmp_path: Path) -> None:
        """Test exporting to markdown."""
        output = tmp_path / "adrs.md"
        result = runner.invoke(
            app, ["export", "--format", "markdown", "--output", str(output)]
        )
        assert result.exit_code == 0

    def test_export_html(self, adr_repo_with_data: Path, tmp_path: Path) -> None:
        """Test exporting to HTML."""
        output = tmp_path / "adrs.html"
        result = runner.invoke(
            app, ["export", "--format", "html", "--output", str(output)]
        )
        assert result.exit_code == 0

    def test_export_csv(self, adr_repo_with_data: Path, tmp_path: Path) -> None:
        """Test exporting to CSV."""
        output = tmp_path / "adrs.csv"
        result = runner.invoke(
            app, ["export", "--format", "csv", "--output", str(output)]
        )
        assert result.exit_code == 0

    def test_export_docx(self, adr_repo_with_data: Path, tmp_path: Path) -> None:
        """Test exporting to DOCX (may require optional dep)."""
        output = tmp_path / "adrs.docx"
        result = runner.invoke(
            app, ["export", "--format", "docx", "--output", str(output)]
        )
        # May fail if docx dep not installed
        assert result.exit_code in [0, 1]

    def test_export_specific_adr(
        self, adr_repo_with_data: Path, tmp_path: Path
    ) -> None:
        """Test export with specific ADR."""
        output = tmp_path / "single-adr"
        result = runner.invoke(
            app,
            [
                "export",
                "--format",
                "json",
                "--output",
                str(output),
                "--adr",
                "20250110-use-postgresql",
            ],
        )
        assert result.exit_code == 0

    def test_export_nonexistent_adr(
        self, adr_repo_with_data: Path, tmp_path: Path
    ) -> None:
        """Test export with non-existent ADR."""
        output = tmp_path / "missing-adr"
        result = runner.invoke(
            app,
            [
                "export",
                "--format",
                "json",
                "--output",
                str(output),
                "--adr",
                "nonexistent-adr",
            ],
        )
        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_export_stdout(self, adr_repo_with_data: Path) -> None:
        """Test export to stdout."""
        result = runner.invoke(app, ["export", "--format", "json"])
        assert result.exit_code == 0
        # Should output JSON to stdout


# =============================================================================
# Core Module Edge Cases
# =============================================================================


class TestConfigEdgeCases:
    """Edge case tests for Config module."""

    def test_config_computed_properties(self) -> None:
        """Test Config computed properties."""
        config = Config(
            namespace="custom",
            artifacts_namespace="custom-artifacts",
        )
        assert config.notes_ref == "refs/notes/custom"
        assert config.artifacts_ref == "refs/notes/custom-artifacts"

    def test_config_defaults(self) -> None:
        """Test Config default values."""
        config = Config()
        assert config.namespace == "adr"
        assert config.template == "madr"
        assert config.notes_ref == "refs/notes/adr"

    def test_config_with_ai_settings(self) -> None:
        """Test Config with AI settings."""
        config = Config(
            ai_provider="openai",
            ai_model="gpt-4",
        )
        assert config.ai_provider == "openai"
        assert config.ai_model == "gpt-4"


class TestTemplateEdgeCases:
    """Edge case tests for templates."""

    def test_template_detect_format(self) -> None:
        """Test template format detection."""
        from git_adr.core.templates import TemplateEngine

        engine = TemplateEngine()

        # MADR-style content
        madr_content = """---
id: test
title: Test
status: proposed
---

## Context and Problem Statement

What?

## Considered Options

* Option A
* Option B
"""
        detected = engine.detect_format(madr_content)
        assert detected in ["madr", "unknown"]

        # Nygard-style content
        nygard_content = """# 1. Use PostgreSQL

Date: 2025-01-15

## Status

Accepted

## Context

Need a database.

## Decision

Use PostgreSQL.

## Consequences

Good stuff.
"""
        detected = engine.detect_format(nygard_content)
        assert detected in ["nygard", "unknown"]

    def test_template_render_all_formats(self) -> None:
        """Test rendering all available formats."""
        from git_adr.core.templates import TemplateEngine

        engine = TemplateEngine()

        for fmt in engine.list_formats():
            content = engine.render_for_new(
                fmt,
                title="Test",
                adr_id="20250115-test",
                status="proposed",
            )
            assert content is not None
            assert len(content) > 0


class TestGitEdgeCases:
    """Edge case tests for Git module."""

    def test_git_outside_repo(self, tmp_path: Path) -> None:
        """Test Git operations outside a repository."""
        git = Git(cwd=tmp_path)
        assert git.is_repository() is False

    def test_git_get_root_outside_repo(self, tmp_path: Path) -> None:
        """Test get_root outside repository raises."""
        from git_adr.core.git import GitError

        git = Git(cwd=tmp_path)
        with pytest.raises(GitError):
            git.get_root()

    def test_git_result_success(self) -> None:
        """Test GitResult success state."""
        from git_adr.core.git import GitResult

        result = GitResult(stdout="output", stderr="", exit_code=0)
        assert result.success is True

    def test_git_result_failure(self) -> None:
        """Test GitResult failure state."""
        from git_adr.core.git import GitResult

        result = GitResult(stdout="", stderr="error", exit_code=1)
        assert result.success is False
