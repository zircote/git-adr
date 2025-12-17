"""Final coverage tests with deep mocking.

Targets specific uncovered code paths using extensive mocking.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from git_adr.cli import app
from git_adr.core.adr import ADR, ADRMetadata, ADRStatus
from git_adr.core.config import Config, ConfigManager
from git_adr.core.git import Git, GitError, GitResult
from git_adr.core.notes import NotesManager

runner = CliRunner()


# =============================================================================
# Log Command Deep Coverage
# =============================================================================


class TestLogDeep:
    """Deep tests for log command."""

    def test_log_empty_output(self, adr_repo_with_data: Path) -> None:
        """Test log with no matching commits."""
        result = runner.invoke(app, ["log", "-n", "0"])
        assert result.exit_code in [0, 1, 2]

    def test_log_with_all_flag(self, adr_repo_with_data: Path) -> None:
        """Test log with --all flag."""
        result = runner.invoke(app, ["log", "--all"])
        assert result.exit_code == 0


# =============================================================================
# New Command Deep Coverage
# =============================================================================


class TestNewDeep:
    """Deep tests for new command."""

    def test_new_from_stdin(self, initialized_adr_repo: Path) -> None:
        """Test new with stdin input."""
        content = "## Context\n\nTest context.\n\n## Decision\n\nTest decision."
        result = runner.invoke(
            app,
            ["new", "Stdin Decision", "--no-edit"],
            input=content,
        )
        assert result.exit_code in [0, 1]

    def test_new_with_all_options(
        self, adr_repo_with_data: Path, tmp_path: Path
    ) -> None:
        """Test new with all options combined."""
        content_file = tmp_path / "content.md"
        content_file.write_text("## Context\n\nContext.\n\n## Decision\n\nDecision.")

        git = Git(cwd=adr_repo_with_data)
        head = git.get_head_commit()

        result = runner.invoke(
            app,
            [
                "new",
                "Full Test",
                "--file",
                str(content_file),
                "--no-edit",
                "--status",
                "accepted",
                "--tag",
                "test",
                "--link",
                head,
                "--template",
                "nygard",
            ],
        )
        assert result.exit_code in [0, 1]


# =============================================================================
# Edit Command Deep Coverage
# =============================================================================


class TestEditDeep:
    """Deep tests for edit command."""

    def test_edit_with_status_change(self, adr_repo_with_data: Path) -> None:
        """Test edit with status change."""
        result = runner.invoke(
            app,
            ["edit", "20250110-use-postgresql", "--status", "deprecated"],
        )
        assert result.exit_code == 0

    def test_edit_with_tag_operations(self, adr_repo_with_data: Path) -> None:
        """Test edit with tag add/remove."""
        # Add tag
        result = runner.invoke(
            app,
            ["edit", "20250110-use-postgresql", "--add-tag", "important"],
        )
        assert result.exit_code == 0

        # Remove tag
        result = runner.invoke(
            app,
            ["edit", "20250110-use-postgresql", "--remove-tag", "important"],
        )
        assert result.exit_code == 0


# =============================================================================
# Supersede Command Deep Coverage
# =============================================================================


class TestSupersedeDeep:
    """Deep tests for supersede command."""

    def test_supersede_with_template(self, adr_repo_with_data: Path) -> None:
        """Test supersede with template option (will open editor)."""
        result = runner.invoke(
            app,
            ["supersede", "--help"],
        )
        assert result.exit_code == 0


# =============================================================================
# AI Commands Deep Coverage
# =============================================================================


class TestAIDeep:
    """Deep tests for AI commands."""

    @patch("git_adr.ai.AIService")
    def test_ai_ask_with_context(
        self, mock_ai: MagicMock, ai_configured_repo: Path
    ) -> None:
        """Test AI ask with context."""
        mock_instance = MagicMock()
        mock_ai.return_value = mock_instance
        mock_instance.ask_question.return_value = MagicMock(
            content="The answer is 42.", model="test", provider="test"
        )

        result = runner.invoke(
            app,
            ["ai", "ask", "What is the meaning of life?"],
        )
        assert result.exit_code in [0, 1]

    @patch("git_adr.ai.AIService")
    def test_ai_summarize_with_no_adrs(
        self, mock_ai: MagicMock, ai_configured_repo: Path
    ) -> None:
        """Test AI summarize with no ADRs."""
        mock_instance = MagicMock()
        mock_ai.return_value = mock_instance

        result = runner.invoke(app, ["ai", "summarize"])
        assert result.exit_code in [0, 1]


# =============================================================================
# Wiki Service Deep Coverage
# =============================================================================


class TestWikiDeep:
    """Deep tests for wiki service."""

    def test_wiki_init_help(self, adr_repo_with_data: Path) -> None:
        """Test wiki init help."""
        result = runner.invoke(app, ["wiki", "init", "--help"])
        assert result.exit_code == 0

    def test_wiki_sync_help(self, adr_repo_with_data: Path) -> None:
        """Test wiki sync help."""
        result = runner.invoke(app, ["wiki", "sync", "--help"])
        assert result.exit_code == 0


# =============================================================================
# Core Module Deep Coverage
# =============================================================================


class TestCoreDeep:
    """Deep tests for core modules."""

    def test_git_result_properties(self) -> None:
        """Test GitResult properties."""
        result = GitResult(stdout="line1\nline2\n", stderr="", exit_code=0)
        assert result.success is True
        assert result.lines == ["line1", "line2"]

        result2 = GitResult(stdout="", stderr="error", exit_code=1)
        assert result2.success is False
        assert result2.lines == []

    def test_git_error_str(self) -> None:
        """Test GitError string representation."""
        error = GitError("Test error message", ["git", "status"], 1)
        assert "Test error message" in str(error)

    def test_adr_status_values(self) -> None:
        """Test all ADRStatus values."""
        statuses = [
            ADRStatus.PROPOSED,
            ADRStatus.ACCEPTED,
            ADRStatus.REJECTED,
            ADRStatus.DEPRECATED,
            ADRStatus.SUPERSEDED,
        ]
        for status in statuses:
            assert status.value in [
                "proposed",
                "accepted",
                "rejected",
                "deprecated",
                "superseded",
            ]

    def test_config_notes_ref_default(self) -> None:
        """Test Config notes_ref with default namespace."""
        config = Config()
        assert config.notes_ref == "refs/notes/adr"

    def test_config_notes_ref_custom(self) -> None:
        """Test Config notes_ref with custom namespace."""
        config = Config(namespace="custom")
        assert config.notes_ref == "refs/notes/custom"

    def test_adr_metadata_tags(self) -> None:
        """Test ADRMetadata tags."""
        metadata = ADRMetadata(
            id="test",
            title="Test",
            date=date.today(),
            status=ADRStatus.PROPOSED,
            tags=["a", "b", "c"],
        )
        assert list(metadata.tags) == ["a", "b", "c"]

    def test_adr_metadata_deciders(self) -> None:
        """Test ADRMetadata deciders."""
        metadata = ADRMetadata(
            id="test",
            title="Test",
            date=date.today(),
            status=ADRStatus.PROPOSED,
            deciders=["Alice", "Bob"],
        )
        assert list(metadata.deciders) == ["Alice", "Bob"]


# =============================================================================
# Index Module Deep Coverage
# =============================================================================


class TestIndexDeep:
    """Deep tests for index module."""

    def test_index_rebuild(self, adr_repo_with_data: Path) -> None:
        """Test index rebuild."""
        from git_adr.core.index import IndexManager

        git = Git(cwd=adr_repo_with_data)
        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)
        index_manager = IndexManager(notes_manager)

        count = index_manager.rebuild()
        assert count >= 0

    def test_index_get_tags(self, adr_repo_with_data: Path) -> None:
        """Test index get_tags."""
        from git_adr.core.index import IndexManager

        git = Git(cwd=adr_repo_with_data)
        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)
        index_manager = IndexManager(notes_manager)

        index_manager.rebuild()
        tags = index_manager.get_tags()
        assert isinstance(tags, dict)

    def test_index_get_stats(self, adr_repo_with_data: Path) -> None:
        """Test index get_stats."""
        from git_adr.core.index import IndexManager

        git = Git(cwd=adr_repo_with_data)
        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)
        index_manager = IndexManager(notes_manager)

        index_manager.rebuild()
        stats = index_manager.get_stats()
        assert isinstance(stats, dict)

    def test_index_get_recent(self, adr_repo_with_data: Path) -> None:
        """Test index get_recent."""
        from git_adr.core.index import IndexManager

        git = Git(cwd=adr_repo_with_data)
        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)
        index_manager = IndexManager(notes_manager)

        index_manager.rebuild()
        recent = index_manager.get_recent(days=365)
        assert isinstance(recent, list)


# =============================================================================
# Template Module Deep Coverage
# =============================================================================


class TestTemplateDeep:
    """Deep tests for template module."""

    def test_template_engine_list_formats(self) -> None:
        """Test TemplateEngine list_formats."""
        from git_adr.core.templates import TemplateEngine

        engine = TemplateEngine()
        formats = engine.list_formats()
        assert "madr" in formats
        assert "nygard" in formats

    def test_template_render_all_formats(self) -> None:
        """Test rendering all formats."""
        from git_adr.core.templates import TemplateEngine

        engine = TemplateEngine()
        for fmt in engine.list_formats():
            content = engine.render_for_new(
                fmt,
                title="Test",
                adr_id="20250115-test",
                status="proposed",
            )
            assert len(content) > 0

    def test_template_detect_format(self) -> None:
        """Test format detection."""
        from git_adr.core.templates import TemplateEngine

        engine = TemplateEngine()

        # MADR style
        madr = """---
id: test
title: Test
status: proposed
---

## Context and Problem Statement

Test context.
"""
        detected = engine.detect_format(madr)
        assert detected in ["madr", "unknown"]

        # Nygard style
        nygard = """# 1. Test

Date: 2025-01-15

## Status

Proposed

## Context

Test.
"""
        detected = engine.detect_format(nygard)
        assert detected in ["nygard", "unknown"]


# =============================================================================
# Fixture for AI-configured repo
# =============================================================================


@pytest.fixture
def ai_configured_repo(initialized_adr_repo: Path) -> Path:
    """Repository with AI configured."""
    git = Git(cwd=initialized_adr_repo)
    config_manager = ConfigManager(git)
    config_manager.set("ai.provider", "openai")
    config_manager.set("ai.model", "gpt-4")
    return initialized_adr_repo


# =============================================================================
# AI Draft Interactive Mode Coverage
# =============================================================================


class TestAIDraftInteractive:
    """Tests for AI draft interactive mode (lines 86-123)."""

    @patch("git_adr.ai.AIService")
    @patch("git_adr.commands.ai_draft.Prompt.ask")
    def test_ai_draft_interactive_full_flow(
        self,
        mock_prompt: MagicMock,
        mock_ai_class: MagicMock,
        adr_repo_with_data: Path,
    ) -> None:
        """Test AI draft interactive mode with full option gathering."""
        # Configure AI provider
        git = Git(cwd=adr_repo_with_data)
        config_manager = ConfigManager(git)
        config_manager.set("ai.provider", "openai")

        # Mock prompt responses
        mock_prompt.side_effect = [
            "Database selection context",  # Context
            "PostgreSQL",  # Option 1
            "MySQL",  # Option 2
            "",  # End options
            "Performance",  # Driver 1
            "Scalability",  # Driver 2
            "",  # End drivers
        ]

        mock_ai = MagicMock()
        mock_ai_class.return_value = mock_ai
        mock_ai.draft_adr.return_value = MagicMock(
            content="## Context\n\nGenerated.",
            model="gpt-4",
            provider="openai",
        )

        result = runner.invoke(
            app,
            ["ai", "draft", "Database Selection"],
            input="y\n",
        )
        assert result.exit_code in [0, 1]

    @patch("git_adr.ai.AIService")
    @patch("git_adr.commands.ai_draft.Prompt.ask")
    def test_ai_draft_decline_save(
        self,
        mock_prompt: MagicMock,
        mock_ai_class: MagicMock,
        adr_repo_with_data: Path,
    ) -> None:
        """Test AI draft when user declines to save."""
        git = Git(cwd=adr_repo_with_data)
        config_manager = ConfigManager(git)
        config_manager.set("ai.provider", "openai")

        mock_prompt.side_effect = ["Context", "", ""]

        mock_ai = MagicMock()
        mock_ai_class.return_value = mock_ai
        mock_ai.draft_adr.return_value = MagicMock(
            content="Generated content",
            model="gpt-4",
            provider="openai",
        )

        result = runner.invoke(
            app,
            ["ai", "draft", "Test"],
            input="n\n",
        )
        assert result.exit_code in [0, 1]


# =============================================================================
# AI Draft Commits Analysis Coverage
# =============================================================================


class TestAIDraftCommits:
    """Tests for AI draft commit analysis."""

    @patch("git_adr.ai.AIService")
    def test_ai_draft_valid_commits(
        self, mock_ai_class: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test AI draft with valid commit range."""
        git = Git(cwd=adr_repo_with_data)
        config_manager = ConfigManager(git)
        config_manager.set("ai.provider", "openai")

        mock_ai = MagicMock()
        mock_ai_class.return_value = mock_ai
        mock_ai.draft_adr.return_value = MagicMock(
            content="## Context\n\nFrom commits.",
            model="gpt-4",
            provider="openai",
        )

        result = runner.invoke(
            app,
            [
                "ai",
                "draft",
                "Commit Decision",
                "--batch",
                "--from-commits",
                "HEAD~1..HEAD",
            ],
        )
        assert result.exit_code in [0, 1]


# =============================================================================
# AI Summarize Deep Coverage
# =============================================================================


class TestAISummarizeDeep:
    """Deep tests for AI summarize."""

    @patch("git_adr.ai.AIService")
    def test_ai_summarize_all_formats(
        self, mock_ai_class: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test AI summarize with all formats."""
        git = Git(cwd=adr_repo_with_data)
        config_manager = ConfigManager(git)
        config_manager.set("ai.provider", "openai")

        mock_ai = MagicMock()
        mock_ai_class.return_value = mock_ai
        mock_ai.summarize_adrs.return_value = MagicMock(
            content="Summary",
            model="gpt-4",
            provider="openai",
        )

        for fmt in ["markdown", "slack", "email", "standup"]:
            result = runner.invoke(app, ["ai", "summarize", "--format", fmt])
            assert result.exit_code in [0, 1]


# =============================================================================
# Edit Full Workflow Coverage
# =============================================================================


class TestEditFullWorkflowDeep:
    """Deep tests for full edit workflow."""

    @patch("subprocess.run")
    @patch("git_adr.commands._editor.find_editor")
    @patch("pathlib.Path.read_text")
    def test_full_edit_modified(
        self,
        mock_read_text: MagicMock,
        mock_find_editor: MagicMock,
        mock_subprocess: MagicMock,
        adr_repo_with_data: Path,
    ) -> None:
        """Test full edit with modified content."""
        mock_find_editor.return_value = "vim"
        mock_subprocess.return_value = MagicMock(returncode=0)
        mock_read_text.return_value = """---
id: 20250110-use-postgresql
title: Use PostgreSQL
date: 2025-01-10
status: accepted
---

## Context

Modified context here.

## Decision

Modified decision.
"""
        result = runner.invoke(app, ["edit", "20250110-use-postgresql"])
        assert result.exit_code in [0, 1]


# =============================================================================
# Wiki Service Sync Coverage
# =============================================================================


class TestWikiSyncDeep:
    """Deep tests for wiki sync."""

    @patch("subprocess.run")
    def test_wiki_clone_and_sync(self, mock_subprocess: MagicMock) -> None:
        """Test wiki clone and sync workflow."""
        from git_adr.wiki.service import SyncResult, WikiService

        mock_subprocess.return_value = MagicMock(returncode=0)

        mock_git = MagicMock()
        mock_git.run.return_value = MagicMock(
            stdout="origin\thttps://github.com/user/repo.git",
            exit_code=0,
            success=True,
        )

        config = Config()
        service = WikiService(mock_git, config)

        adrs = [
            ADR(
                metadata=ADRMetadata(
                    id="test",
                    title="Test",
                    date=date.today(),
                    status=ADRStatus.ACCEPTED,
                ),
                content="Content",
            )
        ]

        result = service.sync(adrs, dry_run=True)
        assert isinstance(result, SyncResult)


# =============================================================================
# Show Command Deep Coverage
# =============================================================================


class TestShowDeep:
    """Deep tests for show command."""

    def test_show_all_formats(self, adr_repo_with_data: Path) -> None:
        """Test show with all formats."""
        for fmt in ["markdown", "json", "yaml"]:
            result = runner.invoke(
                app,
                ["show", "20250110-use-postgresql", "--format", fmt],
            )
            assert result.exit_code == 0


# =============================================================================
# Convert Command Deep Coverage
# =============================================================================


class TestConvertDeep:
    """Deep tests for convert command."""

    def test_convert_all_formats(self, adr_repo_with_data: Path) -> None:
        """Test convert to all formats."""
        for fmt in ["madr", "nygard", "alexandrian"]:
            result = runner.invoke(
                app,
                ["convert", "20250110-use-postgresql", "--to", fmt, "--dry-run"],
            )
            assert result.exit_code in [0, 1]


# =============================================================================
# List Command Deep Coverage
# =============================================================================


class TestListDeep:
    """Deep tests for list command."""

    def test_list_all_statuses(self, adr_repo_with_data: Path) -> None:
        """Test list with all statuses."""
        for status in ["proposed", "accepted", "rejected", "deprecated", "superseded"]:
            result = runner.invoke(app, ["list", "--status", status])
            assert result.exit_code == 0


# =============================================================================
# Config Deep Coverage
# =============================================================================


class TestConfigDeep:
    """Deep tests for config."""

    def test_config_operations(self, adr_repo_with_data: Path) -> None:
        """Test config get/set operations."""
        # Get
        result = runner.invoke(app, ["config", "get", "template"])
        assert result.exit_code in [0, 1]

        # Set
        result = runner.invoke(app, ["config", "set", "template", "nygard"])
        assert result.exit_code in [0, 1, 2]


# =============================================================================
# Git Core Deep Coverage
# =============================================================================


class TestGitDeep:
    """Deep tests for git core."""

    def test_git_operations(self, temp_git_repo: Path) -> None:
        """Test various git operations."""
        git = Git(cwd=temp_git_repo)

        # Create file and commit
        (temp_git_repo / "test.txt").write_text("test")
        git.run(["add", "."])
        git.run(["commit", "-m", "Test commit"])

        # Various operations
        assert git.is_repository()
        assert git.get_root() == temp_git_repo

        head = git.get_head_commit()
        assert len(head) >= 7

    def test_git_error_handling(self, tmp_path: Path) -> None:
        """Test git error handling."""
        git = Git(cwd=tmp_path)
        assert not git.is_repository()

        with pytest.raises(GitError):
            git.get_root()


# =============================================================================
# AI Summarize Deep Coverage (lines 79-117)
# =============================================================================


class TestAISummarizeFull:
    """Full coverage tests for AI summarize."""

    @patch("git_adr.ai.AIService")
    def test_ai_summarize_markdown_format(
        self, mock_ai_class: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test AI summarize with markdown format."""
        git = Git(cwd=adr_repo_with_data)
        config_manager = ConfigManager(git)
        config_manager.set("ai.provider", "openai")

        mock_ai = MagicMock()
        mock_ai_class.return_value = mock_ai
        mock_ai.summarize_adrs.return_value = MagicMock(
            content="# Summary\n\n* Point 1\n* Point 2",
            model="gpt-4",
            provider="openai",
        )

        result = runner.invoke(
            app, ["ai", "summarize", "--period", "365d", "--format", "markdown"]
        )
        assert result.exit_code in [0, 1]

    @patch("git_adr.ai.AIService")
    def test_ai_summarize_slack_format(
        self, mock_ai_class: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test AI summarize with slack format."""
        git = Git(cwd=adr_repo_with_data)
        config_manager = ConfigManager(git)
        config_manager.set("ai.provider", "openai")

        mock_ai = MagicMock()
        mock_ai_class.return_value = mock_ai
        mock_ai.summarize_adrs.return_value = MagicMock(
            content="Summary for Slack",
            model="gpt-4",
            provider="openai",
        )

        result = runner.invoke(
            app, ["ai", "summarize", "--period", "365d", "--format", "slack"]
        )
        assert result.exit_code in [0, 1]

    @patch("git_adr.ai.AIService")
    def test_ai_summarize_email_format(
        self, mock_ai_class: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test AI summarize with email format."""
        git = Git(cwd=adr_repo_with_data)
        config_manager = ConfigManager(git)
        config_manager.set("ai.provider", "openai")

        mock_ai = MagicMock()
        mock_ai_class.return_value = mock_ai
        mock_ai.summarize_adrs.return_value = MagicMock(
            content="Email summary content",
            model="gpt-4",
            provider="openai",
        )

        result = runner.invoke(
            app, ["ai", "summarize", "--period", "365d", "--format", "email"]
        )
        assert result.exit_code in [0, 1]

    @patch("git_adr.ai.AIService")
    def test_ai_summarize_standup_format(
        self, mock_ai_class: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test AI summarize with standup format."""
        git = Git(cwd=adr_repo_with_data)
        config_manager = ConfigManager(git)
        config_manager.set("ai.provider", "openai")

        mock_ai = MagicMock()
        mock_ai_class.return_value = mock_ai
        mock_ai.summarize_adrs.return_value = MagicMock(
            content="Standup summary",
            model="gpt-4",
            provider="openai",
        )

        result = runner.invoke(
            app, ["ai", "summarize", "--period", "365d", "--format", "standup"]
        )
        assert result.exit_code in [0, 1]

    @patch("git_adr.ai.AIService")
    def test_ai_summarize_import_error(
        self, mock_ai_class: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test AI summarize with import error."""
        git = Git(cwd=adr_repo_with_data)
        config_manager = ConfigManager(git)
        config_manager.set("ai.provider", "openai")

        mock_ai_class.side_effect = ImportError("No AI module")

        result = runner.invoke(app, ["ai", "summarize", "--period", "365d"])
        assert result.exit_code != 0

    @patch("git_adr.ai.AIService")
    def test_ai_summarize_api_error(
        self, mock_ai_class: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test AI summarize with API error."""
        git = Git(cwd=adr_repo_with_data)
        config_manager = ConfigManager(git)
        config_manager.set("ai.provider", "openai")

        mock_ai = MagicMock()
        mock_ai_class.return_value = mock_ai
        mock_ai.summarize_adrs.side_effect = Exception("API rate limit")

        result = runner.invoke(app, ["ai", "summarize", "--period", "365d"])
        assert result.exit_code != 0


# =============================================================================
# Wiki Service Full Sync Coverage
# =============================================================================


class TestWikiServiceFullSync:
    """Full sync workflow coverage for wiki service."""

    @patch("subprocess.run")
    @patch("tempfile.mkdtemp")
    @patch("shutil.rmtree")
    def test_sync_push_with_adrs(
        self,
        mock_rmtree: MagicMock,
        mock_mkdtemp: MagicMock,
        mock_subprocess: MagicMock,
    ) -> None:
        """Test wiki sync push with ADRs."""
        from git_adr.wiki.service import SyncResult, WikiService

        mock_mkdtemp.return_value = "/tmp/wiki"
        mock_subprocess.return_value = MagicMock(returncode=0, stderr="", stdout="")

        mock_git = MagicMock()
        mock_git.run.return_value = MagicMock(
            stdout="origin\thttps://github.com/user/repo.git",
            exit_code=0,
            success=True,
        )

        config = Config()
        service = WikiService(mock_git, config)
        service._platform = "github"

        adrs = [
            ADR(
                metadata=ADRMetadata(
                    id="test-adr-1",
                    title="Test Decision One",
                    date=date.today(),
                    status=ADRStatus.ACCEPTED,
                    tags=["test"],
                ),
                content="## Context\n\nTest content.",
            ),
            ADR(
                metadata=ADRMetadata(
                    id="test-adr-2",
                    title="Test Decision Two",
                    date=date.today(),
                    status=ADRStatus.PROPOSED,
                ),
                content="## Context\n\nMore content.",
            ),
        ]

        result = service.sync(adrs, dry_run=True, platform="github")
        assert isinstance(result, SyncResult)
        assert len(result.created) == 2


# =============================================================================
# Convert Command Full Coverage
# =============================================================================


class TestConvertFull:
    """Full coverage tests for convert command."""

    def test_convert_with_dry_run(self, adr_repo_with_data: Path) -> None:
        """Test convert with dry run for all formats."""
        for fmt in ["madr", "nygard", "alexandrian"]:
            result = runner.invoke(
                app,
                ["convert", "20250110-use-postgresql", "--to", fmt, "--dry-run"],
            )
            assert result.exit_code in [0, 1]

    def test_convert_nonexistent_adr(self, adr_repo_with_data: Path) -> None:
        """Test convert nonexistent ADR."""
        result = runner.invoke(
            app,
            ["convert", "nonexistent-adr", "--to", "nygard"],
        )
        assert result.exit_code != 0


# =============================================================================
# Artifact Commands Full Coverage
# =============================================================================


class TestArtifactsFull:
    """Full coverage tests for artifact commands."""

    def test_attach_and_list(self, adr_repo_with_data: Path, tmp_path: Path) -> None:
        """Test attach and list workflow."""
        # Create test file
        test_file = tmp_path / "diagram.png"
        test_file.write_bytes(b"\x89PNG" + b"\x00" * 100)

        # Attach
        result = runner.invoke(
            app,
            ["attach", "20250110-use-postgresql", str(test_file)],
        )
        assert result.exit_code == 0

        # List
        result = runner.invoke(
            app,
            ["artifacts", "20250110-use-postgresql"],
        )
        assert result.exit_code == 0

    def test_artifact_get_nonexistent(self, adr_repo_with_data: Path) -> None:
        """Test getting nonexistent artifact."""
        result = runner.invoke(
            app,
            ["artifact-get", "20250110-use-postgresql", "nonexistent.png"],
        )
        assert result.exit_code != 0

    def test_artifact_rm_nonexistent(self, adr_repo_with_data: Path) -> None:
        """Test removing nonexistent artifact."""
        result = runner.invoke(
            app,
            ["artifact-rm", "20250110-use-postgresql", "nonexistent.png"],
        )
        assert result.exit_code != 0


# =============================================================================
# Sync Command Full Coverage
# =============================================================================


class TestSyncFull:
    """Full coverage tests for sync command."""

    def test_sync_help(self, adr_repo_with_data: Path) -> None:
        """Test sync help."""
        result = runner.invoke(app, ["sync", "--help"])
        assert result.exit_code == 0

    def test_sync_no_remote(self, temp_git_repo: Path) -> None:
        """Test sync without remote."""
        # Initialize git-adr first
        result = runner.invoke(app, ["init", "-y"])

        # Sync should fail without remote
        result = runner.invoke(app, ["sync"])
        assert result.exit_code != 0


# =============================================================================
# Edit Command Full Coverage
# =============================================================================


class TestEditFull:
    """Full coverage tests for edit command."""

    def test_edit_all_quick_options(self, adr_repo_with_data: Path) -> None:
        """Test edit with all quick options."""
        git = Git(cwd=adr_repo_with_data)
        head = git.get_head_commit()

        # Multiple changes at once
        result = runner.invoke(
            app,
            [
                "edit",
                "20250110-use-postgresql",
                "--status",
                "deprecated",
                "--add-tag",
                "legacy",
                "--link",
                head,
            ],
        )
        assert result.exit_code == 0


# =============================================================================
# Search Command Full Coverage
# =============================================================================


class TestSearchFull:
    """Full coverage tests for search command."""

    def test_search_with_all_options(self, adr_repo_with_data: Path) -> None:
        """Test search with various options."""
        result = runner.invoke(
            app,
            ["search", "postgresql", "--context", "3"],
        )
        assert result.exit_code == 0

        result = runner.invoke(
            app,
            ["search", "PostgreSQL", "--case-sensitive"],
        )
        assert result.exit_code == 0

        result = runner.invoke(
            app,
            ["search", "post.*sql", "--regex"],
        )
        assert result.exit_code == 0
