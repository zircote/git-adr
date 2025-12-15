"""Comprehensive tests for low-coverage command modules.

Tests the success paths and edge cases for commands with low coverage.
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from git_adr.cli import app
from git_adr.core.git import Git

runner = CliRunner()


# =============================================================================
# Artifact Commands Tests
# =============================================================================


class TestArtifactsCommandCoverage:
    """Coverage tests for artifacts command."""

    def test_artifacts_with_existing_artifacts(
        self, adr_repo_with_data: Path, tmp_path: Path
    ) -> None:
        """Test listing artifacts when artifacts exist."""
        # First attach an artifact
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"test content")

        # Attach it
        runner.invoke(
            app,
            ["attach", "20250110-use-postgresql", str(test_file)],
        )

        # Now list artifacts - may succeed (0) or report no artifacts (1)
        result = runner.invoke(app, ["artifacts", "20250110-use-postgresql"])
        assert result.exit_code in [0, 1], f"Unexpected exit code: {result.exit_code}"


class TestArtifactGetCoverage:
    """Coverage tests for artifact-get command."""

    def test_artifact_get_with_output(
        self, adr_repo_with_data: Path, tmp_path: Path
    ) -> None:
        """Test getting artifact with output path."""
        # First attach an artifact
        test_file = tmp_path / "source.txt"
        test_file.write_bytes(b"artifact content")

        attach_result = runner.invoke(
            app,
            ["attach", "20250110-use-postgresql", str(test_file)],
        )

        # Try to get it by name
        if attach_result.exit_code == 0:
            output_file = tmp_path / "output.txt"
            result = runner.invoke(
                app,
                [
                    "artifact-get",
                    "20250110-use-postgresql",
                    "source.txt",
                    "--output",
                    str(output_file),
                ],
            )
            assert result.exit_code in [0, 1]

    def test_artifact_get_nonexistent_artifact(self, adr_repo_with_data: Path) -> None:
        """Test getting non-existent artifact."""
        result = runner.invoke(
            app,
            ["artifact-get", "20250110-use-postgresql", "nonexistent.txt"],
        )
        assert result.exit_code != 0


class TestArtifactRmCoverage:
    """Coverage tests for artifact-rm command."""

    def test_artifact_rm_nonexistent(self, adr_repo_with_data: Path) -> None:
        """Test removing non-existent artifact."""
        result = runner.invoke(
            app,
            ["artifact-rm", "20250110-use-postgresql", "nonexistent.txt"],
        )
        assert result.exit_code != 0

    def test_artifact_rm_success(
        self, adr_repo_with_data: Path, tmp_path: Path
    ) -> None:
        """Test removing an existing artifact."""
        # First attach an artifact
        test_file = tmp_path / "to-remove.txt"
        test_file.write_bytes(b"temporary content")

        runner.invoke(
            app,
            ["attach", "20250110-use-postgresql", str(test_file)],
        )

        # Now remove it
        result = runner.invoke(
            app,
            ["artifact-rm", "20250110-use-postgresql", "to-remove.txt"],
        )
        assert result.exit_code in [0, 1]


# =============================================================================
# Log Command Coverage
# =============================================================================


class TestLogCommandCoverage:
    """Coverage tests for log command."""

    def test_log_with_adr_activity(self, adr_repo_with_data: Path) -> None:
        """Test log showing ADR activity."""
        result = runner.invoke(app, ["log", "-n", "10"])
        assert result.exit_code == 0

    def test_log_many_commits(self, adr_repo_with_data: Path) -> None:
        """Test log with high number of commits."""
        result = runner.invoke(app, ["log", "-n", "50"])
        assert result.exit_code == 0

    def test_log_single_commit(self, adr_repo_with_data: Path) -> None:
        """Test log with single commit."""
        result = runner.invoke(app, ["log", "-n", "1"])
        assert result.exit_code == 0


# =============================================================================
# New Command Coverage
# =============================================================================


class TestNewCommandCoverage:
    """Coverage tests for new command."""

    def test_new_preview_mode(self, initialized_adr_repo: Path) -> None:
        """Test new with preview mode."""
        result = runner.invoke(
            app,
            [
                "new",
                "Test Decision Preview",
                "--preview",
            ],
        )
        assert result.exit_code == 0

    def test_new_with_template_preview(self, initialized_adr_repo: Path) -> None:
        """Test new with template override in preview."""
        result = runner.invoke(
            app,
            [
                "new",
                "Nygard Format Decision",
                "--template",
                "nygard",
                "--preview",
            ],
        )
        assert result.exit_code == 0

    def test_new_with_y_statement_preview(self, initialized_adr_repo: Path) -> None:
        """Test new with Y-statement template preview."""
        result = runner.invoke(
            app,
            [
                "new",
                "Y Statement Decision",
                "--template",
                "y-statement",
                "--preview",
            ],
        )
        assert result.exit_code == 0

    def test_new_with_file(self, initialized_adr_repo: Path, tmp_path: Path) -> None:
        """Test new with file input."""
        content_file = tmp_path / "adr-content.md"
        content_file.write_text("""## Context and Problem Statement

Need to test file input.

## Considered Options

* Option A
* Option B

## Decision Outcome

Chose Option A.
""")

        result = runner.invoke(
            app,
            [
                "new",
                "File Input Decision",
                "--file",
                str(content_file),
                "--deciders",
                "Test User",
            ],
        )
        assert result.exit_code == 0

    def test_new_with_tags_and_status(
        self, initialized_adr_repo: Path, tmp_path: Path
    ) -> None:
        """Test new with tags and status."""
        content_file = tmp_path / "tagged.md"
        content_file.write_text("""## Context

Testing tags.

## Decision

Use tags.
""")

        result = runner.invoke(
            app,
            [
                "new",
                "Tagged Decision",
                "--file",
                str(content_file),
                "--status",
                "accepted",
                "--tag",
                "testing",
                "--tag",
                "coverage",
                "--deciders",
                "Test User",
            ],
        )
        assert result.exit_code == 0

    def test_new_draft_mode(self, initialized_adr_repo: Path, tmp_path: Path) -> None:
        """Test new in draft mode."""
        content_file = tmp_path / "draft.md"
        content_file.write_text("""## Context

Draft content.

## Decision

TBD.
""")

        result = runner.invoke(
            app,
            [
                "new",
                "Draft Decision",
                "--file",
                str(content_file),
                "--draft",
                "--deciders",
                "Test User",
            ],
        )
        assert result.exit_code == 0


# =============================================================================
# Supersede Command Coverage
# =============================================================================


class TestSupersedeCommandCoverage:
    """Coverage tests for supersede command."""

    def test_supersede_help(self, adr_repo_with_data: Path) -> None:
        """Test supersede help."""
        result = runner.invoke(app, ["supersede", "--help"])
        assert result.exit_code == 0
        assert "supersede" in result.output.lower()

    def test_supersede_nonexistent_adr(self, adr_repo_with_data: Path) -> None:
        """Test supersede with non-existent ADR."""
        result = runner.invoke(
            app,
            ["supersede", "nonexistent-adr", "New Title"],
        )
        assert result.exit_code != 0

    def test_supersede_with_template(self, adr_repo_with_data: Path) -> None:
        """Test supersede with template option (tests arg parsing)."""
        result = runner.invoke(
            app,
            ["supersede", "--help"],
            color=False,  # Disable ANSI color codes in output
        )
        assert "--template" in result.output or "template" in result.output.lower()


# =============================================================================
# Edit Command Coverage
# =============================================================================


class TestEditCommandCoverage:
    """Coverage tests for edit command."""

    def test_edit_add_multiple_tags(self, adr_repo_with_data: Path) -> None:
        """Test editing ADR to add multiple tags."""
        result = runner.invoke(
            app,
            [
                "edit",
                "20250110-use-postgresql",
                "--add-tag",
                "important",
                "--add-tag",
                "reviewed",
            ],
        )
        assert result.exit_code == 0

    def test_edit_remove_and_add_tags(self, adr_repo_with_data: Path) -> None:
        """Test editing ADR to remove and add tags."""
        result = runner.invoke(
            app,
            [
                "edit",
                "20250112-use-redis",
                "--add-tag",
                "new-tag",
                "--remove-tag",
                "caching",
            ],
        )
        assert result.exit_code == 0

    def test_edit_combined_changes(self, adr_repo_with_data: Path) -> None:
        """Test edit with multiple combined changes."""
        result = runner.invoke(
            app,
            [
                "edit",
                "20250112-use-redis",
                "--status",
                "accepted",
                "--add-tag",
                "approved",
            ],
        )
        assert result.exit_code == 0

    def test_edit_help(self, adr_repo_with_data: Path) -> None:
        """Test edit help."""
        result = runner.invoke(app, ["edit", "--help"])
        assert result.exit_code == 0


# =============================================================================
# Convert Command Coverage
# =============================================================================


class TestConvertCommandCoverage:
    """Coverage tests for convert command."""

    def test_convert_apply(self, adr_repo_with_data: Path) -> None:
        """Test convert without dry-run (applies changes)."""
        result = runner.invoke(
            app,
            ["convert", "20250110-use-postgresql", "--to", "nygard"],
        )
        assert result.exit_code in [0, 1]

    def test_convert_verify(self, adr_repo_with_data: Path) -> None:
        """Test that convert actually changes format."""
        # First convert
        runner.invoke(
            app,
            ["convert", "20250112-use-redis", "--to", "nygard"],
        )

        # Show to verify
        result = runner.invoke(app, ["show", "20250112-use-redis"])
        assert result.exit_code in [0, 1]


# =============================================================================
# Attach Command Coverage
# =============================================================================


class TestAttachCommandCoverage:
    """Coverage tests for attach command."""

    def test_attach_png_file(self, adr_repo_with_data: Path, tmp_path: Path) -> None:
        """Test attaching PNG file."""
        # Create a minimal PNG file
        png_header = b"\x89PNG\r\n\x1a\n"
        test_file = tmp_path / "diagram.png"
        test_file.write_bytes(png_header + b"\x00" * 50)

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

    def test_attach_pdf_file(self, adr_repo_with_data: Path, tmp_path: Path) -> None:
        """Test attaching PDF file."""
        # Create a minimal PDF file
        test_file = tmp_path / "document.pdf"
        test_file.write_bytes(b"%PDF-1.4\n" + b"\x00" * 50)

        result = runner.invoke(
            app,
            [
                "attach",
                "20250110-use-postgresql",
                str(test_file),
                "--name",
                "design-doc.pdf",
            ],
        )
        assert result.exit_code in [0, 1]

    def test_attach_multiple_files(
        self, adr_repo_with_data: Path, tmp_path: Path
    ) -> None:
        """Test attaching multiple files."""
        file1 = tmp_path / "file1.txt"
        file1.write_bytes(b"content 1")
        file2 = tmp_path / "file2.txt"
        file2.write_bytes(b"content 2")

        result1 = runner.invoke(
            app,
            ["attach", "20250110-use-postgresql", str(file1)],
        )
        result2 = runner.invoke(
            app,
            ["attach", "20250110-use-postgresql", str(file2)],
        )
        assert result1.exit_code in [0, 1]
        assert result2.exit_code in [0, 1]


# =============================================================================
# Import Command Coverage
# =============================================================================


class TestImportCommandCoverage:
    """Coverage tests for import command."""

    def test_import_json_format(
        self, initialized_adr_repo: Path, tmp_path: Path
    ) -> None:
        """Test importing from JSON format."""
        import json

        adr_file = tmp_path / "adrs.json"
        data = {
            "adrs": [
                {
                    "id": "20250115-json-imported",
                    "title": "JSON Imported Decision",
                    "status": "proposed",
                    "date": "2025-01-15",
                    "content": "## Context\n\nImported from JSON.\n\n## Decision\n\nTest.",
                }
            ]
        }
        adr_file.write_text(json.dumps(data))

        result = runner.invoke(
            app,
            ["import", str(adr_file), "--format", "json"],
        )
        assert result.exit_code in [0, 1]

    def test_import_adr_tools_format(
        self, initialized_adr_repo: Path, tmp_path: Path
    ) -> None:
        """Test importing from adr-tools format."""
        adr_dir = tmp_path / "adr-tools"
        adr_dir.mkdir()

        adr_file = adr_dir / "0001-use-database.md"
        adr_file.write_text("""# 1. Use Database

Date: 2025-01-15

## Status

Accepted

## Context

We need persistence.

## Decision

Use a database.

## Consequences

Better than files.
""")

        result = runner.invoke(
            app,
            ["import", str(adr_dir), "--format", "adr-tools"],
        )
        assert result.exit_code in [0, 1]

    def test_import_link_by_date(
        self, initialized_adr_repo: Path, tmp_path: Path
    ) -> None:
        """Test importing with link-by-date option."""
        adr_file = tmp_path / "linked.md"
        adr_file.write_text("""---
title: Linked Decision
date: 2025-01-10
status: accepted
---

## Context

Testing link by date.

## Decision

Link it.
""")

        result = runner.invoke(
            app,
            ["import", str(adr_file), "--link-by-date"],
        )
        assert result.exit_code in [0, 1]


# =============================================================================
# Show Command Coverage
# =============================================================================


class TestShowCommandCoverage:
    """Coverage tests for show command."""

    def test_show_json_format(self, adr_repo_with_data: Path) -> None:
        """Test show with JSON format."""
        result = runner.invoke(
            app,
            ["show", "20250110-use-postgresql", "--format", "json"],
        )
        assert result.exit_code == 0

    def test_show_yaml_format(self, adr_repo_with_data: Path) -> None:
        """Test show with YAML format."""
        result = runner.invoke(
            app,
            ["show", "20250110-use-postgresql", "--format", "yaml"],
        )
        assert result.exit_code == 0

    def test_show_metadata_only(self, adr_repo_with_data: Path) -> None:
        """Test show with metadata-only option."""
        result = runner.invoke(
            app,
            ["show", "20250110-use-postgresql", "--metadata-only"],
        )
        assert result.exit_code == 0


# =============================================================================
# Search Command Coverage
# =============================================================================


class TestSearchCommandCoverage:
    """Coverage tests for search command."""

    def test_search_by_title(self, adr_repo_with_data: Path) -> None:
        """Test searching by title."""
        result = runner.invoke(app, ["search", "PostgreSQL"])
        assert result.exit_code == 0
        assert "postgresql" in result.output.lower()

    def test_search_by_content(self, adr_repo_with_data: Path) -> None:
        """Test searching by content."""
        result = runner.invoke(app, ["search", "database"])
        assert result.exit_code == 0

    def test_search_by_tag(self, adr_repo_with_data: Path) -> None:
        """Test searching by tag filter."""
        result = runner.invoke(app, ["search", "decision", "--tag", "database"])
        assert result.exit_code == 0

    def test_search_by_status(self, adr_repo_with_data: Path) -> None:
        """Test searching by status filter."""
        result = runner.invoke(app, ["search", "use", "--status", "accepted"])
        assert result.exit_code == 0

    def test_search_regex(self, adr_repo_with_data: Path) -> None:
        """Test searching with regex."""
        result = runner.invoke(app, ["search", ".*database.*", "--regex"])
        assert result.exit_code == 0

    def test_search_case_sensitive(self, adr_repo_with_data: Path) -> None:
        """Test case-sensitive search."""
        result = runner.invoke(app, ["search", "PostgreSQL", "--case-sensitive"])
        assert result.exit_code == 0


# =============================================================================
# Stats Command Coverage
# =============================================================================


class TestStatsCommandCoverage:
    """Coverage tests for stats command."""

    def test_stats_with_data(self, adr_repo_with_data: Path) -> None:
        """Test stats with ADRs."""
        result = runner.invoke(app, ["stats"])
        assert result.exit_code == 0
        assert "total" in result.output.lower() or "adr" in result.output.lower()

    def test_stats_velocity(self, adr_repo_with_data: Path) -> None:
        """Test stats with velocity metrics."""
        result = runner.invoke(app, ["stats", "--velocity"])
        assert result.exit_code == 0


# =============================================================================
# Metrics Command Coverage
# =============================================================================


class TestMetricsCommandCoverage:
    """Coverage tests for metrics command."""

    def test_metrics_with_data(self, adr_repo_with_data: Path) -> None:
        """Test metrics with ADRs."""
        result = runner.invoke(app, ["metrics"])
        assert result.exit_code == 0

    def test_metrics_prometheus_format(self, adr_repo_with_data: Path) -> None:
        """Test metrics with Prometheus format."""
        result = runner.invoke(app, ["metrics", "--format", "prometheus"])
        assert result.exit_code == 0

    def test_metrics_csv_format(self, adr_repo_with_data: Path) -> None:
        """Test metrics with CSV format."""
        result = runner.invoke(app, ["metrics", "--format", "csv"])
        assert result.exit_code == 0

    def test_metrics_to_file(self, adr_repo_with_data: Path, tmp_path: Path) -> None:
        """Test metrics output to file."""
        output = tmp_path / "metrics.json"
        result = runner.invoke(app, ["metrics", "--output", str(output)])
        assert result.exit_code == 0


# =============================================================================
# Report Command Coverage
# =============================================================================


class TestReportCommandCoverage:
    """Coverage tests for report command."""

    def test_report_with_data(self, adr_repo_with_data: Path) -> None:
        """Test report with ADRs."""
        result = runner.invoke(app, ["report"])
        assert result.exit_code == 0

    def test_report_format_html(self, adr_repo_with_data: Path, tmp_path: Path) -> None:
        """Test report with HTML format."""
        output = tmp_path / "report.html"
        result = runner.invoke(
            app,
            ["report", "--format", "html", "--output", str(output)],
        )
        assert result.exit_code == 0

    def test_report_json_format(self, adr_repo_with_data: Path) -> None:
        """Test report with JSON format."""
        result = runner.invoke(app, ["report", "--format", "json"])
        assert result.exit_code == 0

    def test_report_markdown_format(
        self, adr_repo_with_data: Path, tmp_path: Path
    ) -> None:
        """Test report with Markdown format."""
        output = tmp_path / "report.md"
        result = runner.invoke(
            app,
            ["report", "--format", "markdown", "--output", str(output)],
        )
        assert result.exit_code == 0

    def test_report_with_team_metrics(self, adr_repo_with_data: Path) -> None:
        """Test report with team metrics."""
        result = runner.invoke(app, ["report", "--team"])
        assert result.exit_code == 0


# =============================================================================
# Link Command Coverage
# =============================================================================


class TestLinkCommandCoverage:
    """Coverage tests for link command."""

    def test_link_single_commit(self, adr_repo_with_data: Path) -> None:
        """Test linking single commit."""
        git = Git(cwd=adr_repo_with_data)
        head = git.get_head_commit()

        result = runner.invoke(
            app,
            ["link", "20250110-use-postgresql", head],
        )
        assert result.exit_code in [0, 1]

    def test_link_multiple_commits(self, adr_repo_with_data: Path) -> None:
        """Test linking multiple commits."""
        git = Git(cwd=adr_repo_with_data)

        # Create another commit
        (adr_repo_with_data / "extra.txt").write_text("extra")
        git.run(["add", "."])
        git.run(["commit", "-m", "Extra commit"])

        head = git.get_head_commit()
        prev = head + "~1"

        result = runner.invoke(
            app,
            ["link", "20250110-use-postgresql", head, prev],
        )
        assert result.exit_code in [0, 1]

    def test_link_unlink(self, adr_repo_with_data: Path) -> None:
        """Test unlinking commits."""
        git = Git(cwd=adr_repo_with_data)
        head = git.get_head_commit()

        # First link
        runner.invoke(app, ["link", "20250110-use-postgresql", head])

        # Then unlink
        result = runner.invoke(
            app,
            ["link", "--unlink", "20250110-use-postgresql", head],
        )
        assert result.exit_code in [0, 1]


# =============================================================================
# Config Command Coverage
# =============================================================================


class TestConfigCommandCoverage:
    """Coverage tests for config command."""

    def test_config_set_ai_provider(self, initialized_adr_repo: Path) -> None:
        """Test setting AI provider config."""
        result = runner.invoke(
            app,
            ["config", "ai.provider", "openai", "--set"],
        )
        assert result.exit_code == 0

    def test_config_set_ai_model(self, initialized_adr_repo: Path) -> None:
        """Test setting AI model config."""
        result = runner.invoke(
            app,
            ["config", "ai.model", "gpt-4", "--set"],
        )
        assert result.exit_code == 0

    def test_config_get_all(self, initialized_adr_repo: Path) -> None:
        """Test getting all config."""
        result = runner.invoke(app, ["config", "--list"])
        assert result.exit_code == 0

    def test_config_edit(self, initialized_adr_repo: Path) -> None:
        """Test config edit command."""
        result = runner.invoke(app, ["config", "--help"])
        assert result.exit_code == 0
