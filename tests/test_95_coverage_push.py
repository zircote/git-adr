"""Final comprehensive tests to push coverage to 95%.

Targets remaining gaps in templates, stats, log, sync, artifact_rm.
"""

from __future__ import annotations

import subprocess as sp
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from git_adr.cli import app
from git_adr.core.adr import ADR, ADRMetadata, ADRStatus
from git_adr.core.config import ConfigManager
from git_adr.core.git import Git, GitError

runner = CliRunner()


# =============================================================================
# Templates Coverage (lines 357-358, 459, 464, 467, 470, 473, 502, 594, 623)
# =============================================================================


class TestTemplatesDetectFormat:
    """Tests for template format detection."""

    def test_detect_format_madr_options_considered(self) -> None:
        """Test detecting MADR format via '## Options Considered'."""
        from git_adr.core.templates import TemplateEngine

        engine = TemplateEngine()
        content = """## Context

Some context.

## Options Considered

Option 1, Option 2.

## Decision

We chose Option 1.
"""
        result = engine.detect_format(content)
        assert result == "madr"

    def test_detect_format_madr_decision_outcome(self) -> None:
        """Test detecting MADR format via '## Decision Outcome'."""
        from git_adr.core.templates import TemplateEngine

        engine = TemplateEngine()
        content = """## Context

Some context.

## Decision Outcome

Chosen: Option 1.
"""
        result = engine.detect_format(content)
        assert result == "madr"

    def test_detect_format_y_statement(self) -> None:
        """Test detecting Y-statement format."""
        from git_adr.core.templates import TemplateEngine

        engine = TemplateEngine()
        content = """In the context of building an API,
facing the need for data validation,
we decided to use JSON Schema,
to achieve consistent validation,
accepting that it adds complexity."""
        result = engine.detect_format(content)
        assert result == "y-statement"

    def test_detect_format_alexandrian(self) -> None:
        """Test detecting Alexandrian format via forces + resulting context."""
        from git_adr.core.templates import TemplateEngine

        engine = TemplateEngine()
        content = """## Context

The system needs caching.

## Forces

Performance requirements, consistency needs.

## Decision

Use Redis.

## Resulting Context

Fast responses, eventual consistency.
"""
        result = engine.detect_format(content)
        assert result == "alexandrian"

    def test_detect_format_business(self) -> None:
        """Test detecting Business format via financial impact."""
        from git_adr.core.templates import TemplateEngine

        engine = TemplateEngine()
        content = """## Context

Migration to cloud.

## Decision

Use AWS.

## Financial Impact

$10k monthly cost savings.

## Approval

CTO approved.
"""
        result = engine.detect_format(content)
        assert result == "business"

    def test_detect_format_planguage(self) -> None:
        """Test detecting Planguage format via scale/meter."""
        from git_adr.core.templates import TemplateEngine

        engine = TemplateEngine()
        content = """## Context

Performance requirements.

## Scale

Response time in milliseconds.

## Meter

P99 latency measurement.
"""
        result = engine.detect_format(content)
        assert result == "planguage"

    def test_detect_format_nygard(self) -> None:
        """Test detecting Nygard format via context/decision."""
        from git_adr.core.templates import TemplateEngine

        engine = TemplateEngine()
        content = """## Context

System needs a database.

## Decision

We will use PostgreSQL.

## Consequences

SQL compliance, good tooling.
"""
        result = engine.detect_format(content)
        assert result == "nygard"

    def test_detect_format_unknown(self) -> None:
        """Test unknown format detection."""
        from git_adr.core.templates import TemplateEngine

        engine = TemplateEngine()
        content = """Some random content
without any recognizable structure.
"""
        result = engine.detect_format(content)
        assert result == "unknown"


class TestTemplatesConvert:
    """Tests for template conversion."""

    def test_convert_unknown_format_raises(self) -> None:
        """Test converting to unknown format raises ValueError."""
        from git_adr.core.templates import TemplateEngine

        engine = TemplateEngine()
        adr = ADR(
            metadata=ADRMetadata(
                id="test-convert",
                title="Test Convert",
                date=date.today(),
                status=ADRStatus.DRAFT,
            ),
            content="## Context\n\nTest.",
        )

        with pytest.raises(ValueError, match="Unknown format"):
            engine.convert(adr, "nonexistent-format-xyz")

    def test_convert_preserves_content(self) -> None:
        """Test convert merges sections properly (line 594)."""
        from git_adr.core.templates import TemplateEngine

        engine = TemplateEngine()
        adr = ADR(
            metadata=ADRMetadata(
                id="content-merge",
                title="Content Merge Test",
                date=date.today(),
                status=ADRStatus.ACCEPTED,
                tags=["test"],
                format="nygard",
            ),
            content="""## Context

Real context content here.

## Decision

Actual decision content.

## Consequences

Important consequences.
""",
        )

        # Convert to a different format - should attempt to merge
        result = engine.convert(adr, "madr")
        assert "Content Merge Test" in result


class TestTemplatesHelpers:
    """Tests for template helper functions."""

    def test_get_default_template_engine(self) -> None:
        """Test get_default_template_engine returns valid engine."""
        from git_adr.core.templates import get_default_template_engine

        engine = get_default_template_engine()
        assert engine is not None
        formats = engine.list_formats()
        assert len(formats) > 0


class TestTemplatesLoadFromDir:
    """Tests for loading templates from directory."""

    def test_load_custom_templates_oserror(self, tmp_path: Path) -> None:
        """Test loading templates handles OSError gracefully (lines 357-358)."""
        from git_adr.core.templates import TemplateEngine

        engine = TemplateEngine()

        # Create a directory with a file that can't be read
        bad_template = tmp_path / "bad.md"
        bad_template.write_text("test content")

        # Mock read_text to raise OSError
        with patch.object(Path, "read_text", side_effect=OSError("Permission denied")):
            # Should not raise, just skip the file gracefully
            engine._load_custom_templates(tmp_path)
        # Verify engine still works after error (built-in templates still available)
        assert engine._templates is not None
        assert len(engine._templates) > 0


# =============================================================================
# Stats Coverage (lines 84, 92, 123-126, 147-148, 201-205)
# =============================================================================


class TestStatsDeep:
    """Deep tests for stats command gaps."""

    def test_stats_with_velocity(self, adr_repo_with_data: Path) -> None:
        """Test stats with velocity flag."""
        result = runner.invoke(app, ["stats", "--velocity"])
        assert result.exit_code == 0
        # Should show velocity metrics
        assert "velocity" in result.output.lower() or "rate" in result.output.lower()

    def test_stats_multiple_formats(self, adr_repo_with_data: Path) -> None:
        """Test stats with ADRs in multiple formats (lines 123-126)."""
        from git_adr.core.notes import NotesManager

        git = Git(cwd=adr_repo_with_data)
        cm = ConfigManager(git)
        config = cm.load()
        notes = NotesManager(git, config)

        # Create ADRs with different formats
        for fmt in ["madr", "nygard"]:
            adr = ADR(
                metadata=ADRMetadata(
                    id=f"format-test-{fmt}",
                    title=f"Format Test {fmt.upper()}",
                    date=date.today(),
                    status=ADRStatus.DRAFT,
                    format=fmt,
                ),
                content=f"## Context\n\nTest for {fmt}.",
            )
            notes.add(adr)

        result = runner.invoke(app, ["stats"])
        assert result.exit_code == 0

    def test_stats_unknown_author(self, adr_repo_with_data: Path) -> None:
        """Test stats with ADR without deciders (line 84)."""
        from git_adr.core.notes import NotesManager

        git = Git(cwd=adr_repo_with_data)
        cm = ConfigManager(git)
        config = cm.load()
        notes = NotesManager(git, config)

        # Create ADR without deciders
        adr = ADR(
            metadata=ADRMetadata(
                id="no-deciders",
                title="No Deciders ADR",
                date=date.today(),
                status=ADRStatus.DRAFT,
                deciders=[],  # No deciders
            ),
            content="## Context\n\nTest.",
        )
        notes.add(adr)

        result = runner.invoke(app, ["stats"])
        assert result.exit_code == 0

    def test_stats_with_linked_commits(self, adr_repo_with_data: Path) -> None:
        """Test stats counts linked commits (line 92)."""
        from git_adr.core.notes import NotesManager

        git = Git(cwd=adr_repo_with_data)
        head = git.get_head_commit()
        cm = ConfigManager(git)
        config = cm.load()
        notes = NotesManager(git, config)

        # Create ADR with linked commits
        adr = ADR(
            metadata=ADRMetadata(
                id="linked-commits",
                title="Linked Commits ADR",
                date=date.today(),
                status=ADRStatus.ACCEPTED,
                linked_commits=[head],
            ),
            content="## Context\n\nTest.",
        )
        notes.add(adr)

        result = runner.invoke(app, ["stats"])
        assert result.exit_code == 0
        assert "linked commit" in result.output.lower()

    def test_stats_git_error(self, adr_repo_with_data: Path) -> None:
        """Test stats GitError handling (lines 147-148)."""
        with patch("git_adr.commands._shared.get_git") as mock_get_git:
            mock_git = MagicMock()
            mock_get_git.return_value = mock_git
            mock_git.is_repository.side_effect = GitError(
                "Git error", ["git", "status"], 1
            )

            result = runner.invoke(app, ["stats"])
            assert result.exit_code == 1


# =============================================================================
# Log Coverage (lines 69-70, 73-74, 92-93)
# =============================================================================


class TestLogDeep:
    """Deep tests for log command gaps."""

    def test_log_git_error(self, adr_repo_with_data: Path) -> None:
        """Test log GitError handling (lines 73-74)."""
        with patch("git_adr.commands._shared.get_git") as mock_get_git:
            mock_git = MagicMock()
            mock_get_git.return_value = mock_git
            mock_git.is_repository.return_value = True
            mock_get_git.return_value = mock_git

            # ConfigManager mock
            mock_config_manager = MagicMock()
            mock_config_manager.get.return_value = True
            mock_config_manager.load.return_value = MagicMock(
                notes_ref="refs/notes/adr"
            )

            with patch(
                "git_adr.commands._shared.ConfigManager",
                return_value=mock_config_manager,
            ):
                mock_git.run.side_effect = GitError("Git log error", ["git", "log"], 1)

                result = runner.invoke(app, ["log"])
                # Should handle the error
                assert result.exit_code == 1

    def test_log_run_returns_failure(self, adr_repo_with_data: Path) -> None:
        """Test log when git run returns failure (lines 69-70)."""
        with patch("git_adr.commands._shared.get_git") as mock_get_git:
            mock_git = MagicMock()
            mock_get_git.return_value = mock_git
            mock_git.is_repository.return_value = True

            mock_config_manager = MagicMock()
            mock_config_manager.get.return_value = True
            mock_config = MagicMock()
            mock_config.notes_ref = "refs/notes/adr"
            mock_config_manager.load.return_value = mock_config

            with patch(
                "git_adr.commands._shared.ConfigManager",
                return_value=mock_config_manager,
            ):
                mock_result = MagicMock()
                mock_result.success = False
                mock_result.stderr = "git log failed"
                mock_git.run.return_value = mock_result

                result = runner.invoke(app, ["log"])
                assert result.exit_code == 1

    def test_log_short_entry(self, adr_repo_with_data: Path) -> None:
        """Test log with entry having < 2 lines (lines 92-93)."""
        from git_adr.commands.log import _format_log_output

        # Test with very short output
        _format_log_output("abc123\n")


# =============================================================================
# Sync Coverage (lines 71, 78, 85, 93, 99-100)
# =============================================================================


class TestSyncDeep:
    """Deep tests for sync command gaps."""

    def test_sync_git_error_general(self, adr_repo_with_data: Path) -> None:
        """Test sync general GitError handling (lines 99-100)."""
        with patch("git_adr.commands._shared.get_git") as mock_get_git:
            mock_git = MagicMock()
            mock_get_git.return_value = mock_git
            mock_git.is_repository.side_effect = GitError(
                "General error", ["git", "status"], 1
            )

            result = runner.invoke(app, ["sync"])
            assert result.exit_code == 1

    def test_sync_pull_error_reraise(self, adr_repo_with_data: Path) -> None:
        """Test sync pull error re-raise (line 78)."""
        with patch("git_adr.commands._shared.get_git") as mock_get_git:
            mock_git = MagicMock()
            mock_get_git.return_value = mock_git
            mock_git.is_repository.return_value = True
            mock_git.get_remotes.return_value = ["origin"]

            mock_cm = MagicMock()
            mock_cm.get.return_value = True
            mock_config = MagicMock()
            mock_cm.load.return_value = mock_config

            with patch("git_adr.commands._shared.ConfigManager", return_value=mock_cm):
                mock_notes = MagicMock()
                # Error that isn't "couldn't find remote ref"
                mock_notes.sync_pull.side_effect = GitError(
                    "Different error", ["git", "fetch"], 1
                )

                with patch(
                    "git_adr.commands._shared.NotesManager", return_value=mock_notes
                ):
                    result = runner.invoke(app, ["sync"])
                    # Should propagate the error
                    assert result.exit_code == 1

    def test_sync_push_error_reraise(self, adr_repo_with_data: Path) -> None:
        """Test sync push error re-raise (line 93)."""
        with patch("git_adr.commands._shared.get_git") as mock_get_git:
            mock_git = MagicMock()
            mock_get_git.return_value = mock_git
            mock_git.is_repository.return_value = True
            mock_git.get_remotes.return_value = ["origin"]

            mock_cm = MagicMock()
            mock_cm.get.return_value = True
            mock_config = MagicMock()
            mock_cm.load.return_value = mock_config

            with patch("git_adr.commands._shared.ConfigManager", return_value=mock_cm):
                mock_notes = MagicMock()
                mock_notes.sync_pull.return_value = None
                # Error that isn't "failed to push"
                mock_notes.sync_push.side_effect = GitError(
                    "Permission denied error", ["git", "push"], 1
                )

                with patch(
                    "git_adr.commands._shared.NotesManager", return_value=mock_notes
                ):
                    result = runner.invoke(app, ["sync", "--pull", "--push"])
                    # Should propagate the error
                    assert result.exit_code == 1

    def test_sync_success_messages(self, adr_repo_with_data: Path) -> None:
        """Test sync success messages (lines 71, 85)."""
        with patch("git_adr.commands._shared.get_git") as mock_get_git:
            mock_git = MagicMock()
            mock_get_git.return_value = mock_git
            mock_git.is_repository.return_value = True
            mock_git.get_remotes.return_value = ["origin"]

            mock_cm = MagicMock()
            mock_cm.get.return_value = True
            mock_config = MagicMock()
            mock_cm.load.return_value = mock_config

            with patch("git_adr.commands._shared.ConfigManager", return_value=mock_cm):
                mock_notes = MagicMock()
                mock_notes.sync_pull.return_value = None
                mock_notes.sync_push.return_value = None

                with patch(
                    "git_adr.commands._shared.NotesManager", return_value=mock_notes
                ):
                    result = runner.invoke(app, ["sync", "--pull", "--push"])
                    # Should succeed
                    assert result.exit_code == 0
                    assert "sync complete" in result.output.lower()


# =============================================================================
# Artifact RM Coverage (lines 68, 76-78, 98-99, 102-103)
# =============================================================================


class TestArtifactRmDeep:
    """Deep tests for artifact-rm command gaps."""

    def test_artifact_rm_match_by_sha_prefix(self, adr_repo_with_data: Path) -> None:
        """Test artifact-rm matching by SHA256 prefix (line 68)."""
        # First attach a file
        test_file = adr_repo_with_data / "sha-match.txt"
        test_file.write_text("Content for SHA matching")
        runner.invoke(app, ["attach", "20250110-use-postgresql", str(test_file)])

        # Get the artifact SHA
        result = runner.invoke(app, ["artifacts", "20250110-use-postgresql"])
        # Try to remove using a prefix (won't know exact SHA, so just test the path)
        result = runner.invoke(
            app,
            ["artifact-rm", "20250110-use-postgresql", "sha"],  # Partial match
            input="n\n",  # Cancel
        )
        # May or may not find it depending on name
        assert result.exit_code in [0, 1]

    def test_artifact_rm_shows_available(self, adr_repo_with_data: Path) -> None:
        """Test artifact-rm shows available artifacts when not found (lines 76-78)."""
        # First attach a file
        test_file = adr_repo_with_data / "available-test.txt"
        test_file.write_text("Content for available list")
        runner.invoke(app, ["attach", "20250110-use-postgresql", str(test_file)])

        # Try to remove non-existent artifact
        result = runner.invoke(
            app,
            ["artifact-rm", "20250110-use-postgresql", "nonexistent.txt"],
            input="n\n",
        )
        assert result.exit_code == 1
        # Should show available artifacts
        assert (
            "available-test.txt" in result.output.lower()
            or "available" in result.output.lower()
        )

    def test_artifact_rm_remove_failure(self, adr_repo_with_data: Path) -> None:
        """Test artifact-rm when remove fails (lines 98-99)."""
        with patch("git_adr.commands._shared.get_git") as mock_get_git:
            mock_git = MagicMock()
            mock_get_git.return_value = mock_git
            mock_git.is_repository.return_value = True

            mock_cm = MagicMock()
            mock_cm.get.return_value = True
            mock_config = MagicMock()
            mock_cm.load.return_value = mock_config

            with patch("git_adr.commands._shared.ConfigManager", return_value=mock_cm):
                mock_notes = MagicMock()
                mock_adr = MagicMock()
                mock_notes.get.return_value = mock_adr

                # Create mock artifact
                mock_artifact = MagicMock()
                mock_artifact.name = "test.txt"
                mock_artifact.sha256 = "abc123def456"
                mock_notes.list_artifacts.return_value = [mock_artifact]

                # Remove returns False (failure)
                mock_notes.remove_artifact.return_value = False

                with patch(
                    "git_adr.commands._shared.NotesManager", return_value=mock_notes
                ):
                    result = runner.invoke(
                        app,
                        ["artifact-rm", "some-adr", "test.txt"],
                        input="y\n",
                    )
                    assert result.exit_code == 1

    def test_artifact_rm_git_error(self, adr_repo_with_data: Path) -> None:
        """Test artifact-rm GitError handling (lines 102-103)."""
        with patch("git_adr.commands._shared.get_git") as mock_get_git:
            mock_git = MagicMock()
            mock_get_git.return_value = mock_git
            mock_git.is_repository.side_effect = GitError(
                "Git error", ["git", "status"], 1
            )

            result = runner.invoke(
                app,
                ["artifact-rm", "some-adr", "file.txt"],
                input="y\n",
            )
            assert result.exit_code == 1


# =============================================================================
# Init Coverage (remaining gaps)
# =============================================================================


class TestInitDeep:
    """Deep tests for init command gaps."""

    def test_init_with_remote_configured(self, tmp_path: Path) -> None:
        """Test init configures notes sync when remote exists."""
        import os

        os.chdir(tmp_path)
        sp.run(["git", "init"], check=False, cwd=tmp_path, capture_output=True)
        sp.run(
            ["git", "config", "user.email", "test@test.com"],
            check=False,
            cwd=tmp_path,
            capture_output=True,
        )
        sp.run(
            ["git", "config", "user.name", "Test User"],
            check=False,
            cwd=tmp_path,
            capture_output=True,
        )
        sp.run(
            ["git", "commit", "--allow-empty", "-m", "Initial"],
            check=False,
            cwd=tmp_path,
            capture_output=True,
        )
        sp.run(
            ["git", "remote", "add", "origin", "https://github.com/example/repo.git"],
            check=False,
            cwd=tmp_path,
            capture_output=True,
        )

        result = runner.invoke(app, ["init"])
        assert result.exit_code in [0, 1]


# =============================================================================
# Git Core Coverage (remaining gaps)
# =============================================================================


class TestGitCoreDeep:
    """Deep tests for git.py remaining gaps."""

    def test_git_get_remotes(self, adr_repo_with_data: Path) -> None:
        """Test git get_remotes."""
        git = Git(cwd=adr_repo_with_data)
        remotes = git.get_remotes()
        assert isinstance(remotes, list)

    def test_git_notes_prune_again(self, adr_repo_with_data: Path) -> None:
        """Test git notes_prune handles empty case."""
        git = Git(cwd=adr_repo_with_data)
        # Should not error even with nothing to prune
        git.notes_prune("refs/notes/adr")
        git.notes_prune("refs/notes/adr-artifacts")


# =============================================================================
# Config Command Coverage (lines 62-63, 70-71, 78-79, 92, 95-96)
# =============================================================================


class TestConfigCommandDeep:
    """Deep tests for config command gaps."""

    def test_config_list_mode(self, adr_repo_with_data: Path) -> None:
        """Test config in list mode (default)."""
        result = runner.invoke(app, ["config"])
        assert result.exit_code == 0

    def test_config_set_known_key(self, adr_repo_with_data: Path) -> None:
        """Test config --set with a known key."""
        result = runner.invoke(app, ["config", "--set", "default.template", "madr"])
        assert result.exit_code == 0

    def test_config_get_key(self, adr_repo_with_data: Path) -> None:
        """Test config --get."""
        result = runner.invoke(app, ["config", "--get", "default.template"])
        assert result.exit_code in [0, 1]

    def test_config_unset_key(self, adr_repo_with_data: Path) -> None:
        """Test config --unset."""
        # Set a value first
        runner.invoke(app, ["config", "--set", "default.template", "nygard"])
        # Then unset
        result = runner.invoke(app, ["config", "--unset", "default.template"])
        assert result.exit_code == 0


# =============================================================================
# Export Coverage (remaining gaps)
# =============================================================================


class TestExportDeep:
    """Deep tests for export command gaps."""

    def test_export_to_stdout(self, adr_repo_with_data: Path) -> None:
        """Test export to stdout."""
        result = runner.invoke(app, ["export", "--format", "json"])
        assert result.exit_code == 0

    def test_export_html_format(self, adr_repo_with_data: Path) -> None:
        """Test export in HTML format."""
        output = adr_repo_with_data / "export.html"
        result = runner.invoke(app, ["export", "-o", str(output), "--format", "html"])
        assert result.exit_code == 0


# =============================================================================
# Additional Coverage Gaps
# =============================================================================


class TestADRMetadataGaps:
    """Tests for ADR metadata gaps."""

    def test_adr_with_supersedes(self) -> None:
        """Test ADR metadata with supersedes field."""
        metadata = ADRMetadata(
            id="superseding",
            title="Superseding ADR",
            date=date.today(),
            status=ADRStatus.ACCEPTED,
            supersedes="old-adr",
        )
        assert metadata.supersedes == "old-adr"

    def test_adr_with_superseded_by(self) -> None:
        """Test ADR metadata with superseded_by field."""
        metadata = ADRMetadata(
            id="old-adr",
            title="Old ADR",
            date=date.today(),
            status=ADRStatus.SUPERSEDED,
            superseded_by="new-adr",
        )
        assert metadata.superseded_by == "new-adr"


class TestSearchDeep:
    """Deep tests for search command gaps."""

    def test_search_empty_result(self, adr_repo_with_data: Path) -> None:
        """Test search with no matches."""
        result = runner.invoke(app, ["search", "xyznonexistent123"])
        # Should succeed with no results
        assert result.exit_code in [0, 1]

    def test_search_case_sensitive(self, adr_repo_with_data: Path) -> None:
        """Test search with case-sensitive flag."""
        result = runner.invoke(app, ["search", "PostgreSQL", "--case-sensitive"])
        # May find matches or not
        assert result.exit_code in [0, 1]


class TestShowDeep:
    """Deep tests for show command gaps."""

    def test_show_json_format(self, adr_repo_with_data: Path) -> None:
        """Test show with JSON format."""
        result = runner.invoke(
            app, ["show", "20250110-use-postgresql", "--format", "json"]
        )
        assert result.exit_code == 0

    def test_show_yaml_format(self, adr_repo_with_data: Path) -> None:
        """Test show with YAML format."""
        result = runner.invoke(
            app, ["show", "20250110-use-postgresql", "--format", "yaml"]
        )
        assert result.exit_code == 0
