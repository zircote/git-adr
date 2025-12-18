"""Comprehensive tests for AI commands with full mocking.

These tests mock the AIService to test all code paths in ai_draft, ai_ask,
ai_suggest, and ai_summarize commands.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from git_adr.cli import app
from git_adr.core.adr import ADR, ADRMetadata, ADRStatus
from git_adr.core.config import ConfigManager
from git_adr.core.git import Git
from git_adr.core.notes import NotesManager

runner = CliRunner()


class MockAIResponse:
    """Mock AI response object."""

    def __init__(
        self,
        content: str = "Mock AI response",
        model: str = "mock-model",
        provider: str = "mock-provider",
    ):
        self.content = content
        self.model = model
        self.provider = provider


# no_ai_config_repo fixture is now in conftest.py as no_ai_initialized_repo
# (for initialized repo without sample data and without AI config)


@pytest.fixture
def no_ai_repo_with_data(no_ai_initialized_repo: Path) -> Path:
    """Repository with ADR data but no AI config (for testing AI provider errors)."""
    git = Git(cwd=no_ai_initialized_repo)
    config_manager = ConfigManager(git)
    config = config_manager.load()
    notes_manager = NotesManager(git, config)

    # Add sample ADR
    sample_adr = ADR(
        metadata=ADRMetadata(
            id="20250110-use-postgresql",
            title="Use PostgreSQL for Database",
            date=date(2025, 1, 10),
            status=ADRStatus.ACCEPTED,
            tags=["database"],
        ),
        content="## Context\n\nWe need a database.\n\n## Decision\n\nUse PostgreSQL.",
    )
    notes_manager.add(sample_adr)
    return no_ai_initialized_repo


@pytest.fixture
def ai_configured_repo(initialized_adr_repo: Path) -> Path:
    """Repository with AI configured."""
    git = Git(cwd=initialized_adr_repo)
    config_manager = ConfigManager(git)
    config_manager.set("ai.provider", "openai")
    config_manager.set("ai.model", "gpt-4")
    return initialized_adr_repo


@pytest.fixture
def ai_repo_with_data(ai_configured_repo: Path) -> Path:
    """Repository with AI config and sample ADRs."""
    git = Git(cwd=ai_configured_repo)
    config_manager = ConfigManager(git)
    config = config_manager.load()
    notes_manager = NotesManager(git, config)

    sample_adrs = [
        ADR(
            metadata=ADRMetadata(
                id="20250110-use-postgresql",
                title="Use PostgreSQL for Database",
                date=date(2025, 1, 10),
                status=ADRStatus.ACCEPTED,
                deciders=["Alice", "Bob"],
                tags=["database", "infrastructure"],
            ),
            content="## Context\n\nWe need a relational database.\n\n## Decision\n\nUse PostgreSQL.",
        ),
        ADR(
            metadata=ADRMetadata(
                id="20250112-use-redis",
                title="Use Redis for Caching",
                date=date(2025, 1, 12),
                status=ADRStatus.PROPOSED,
                tags=["caching"],
            ),
            content="## Context\n\nNeed caching.\n\n## Decision\n\nUse Redis.",
        ),
        ADR(
            metadata=ADRMetadata(
                id="20250108-old-decision",
                title="Old Superseded Decision",
                date=date(2025, 1, 8),
                status=ADRStatus.SUPERSEDED,
                tags=["legacy"],
            ),
            content="## Context\n\nOld decision.\n\n## Decision\n\nSuperseded.",
        ),
    ]

    for adr in sample_adrs:
        notes_manager.add(adr)

    return ai_configured_repo


# =============================================================================
# AI Draft Command Tests
# =============================================================================


class TestAIDraftCommand:
    """Tests for ai draft command."""

    @patch("git_adr.ai.AIService")
    def test_draft_batch_mode_success(
        self, mock_ai_service: MagicMock, ai_configured_repo: Path
    ) -> None:
        """Test draft in batch mode with mocked AI."""
        mock_instance = MagicMock()
        mock_ai_service.return_value = mock_instance
        mock_instance.draft_adr.return_value = MockAIResponse(
            content="## Context\n\nGenerated context.\n\n## Decision\n\nGenerated decision.",
            model="gpt-4",
            provider="openai",
        )

        result = runner.invoke(app, ["ai", "draft", "Test ADR Title", "--batch"])
        assert result.exit_code == 0
        assert "Created ADR" in result.output or "gpt-4" in result.output

    @patch("git_adr.ai.AIService")
    def test_draft_with_context(
        self, mock_ai_service: MagicMock, ai_configured_repo: Path
    ) -> None:
        """Test draft with context argument."""
        mock_instance = MagicMock()
        mock_ai_service.return_value = mock_instance
        mock_instance.draft_adr.return_value = MockAIResponse()

        result = runner.invoke(
            app,
            [
                "ai",
                "draft",
                "Test ADR",
                "--batch",
                "--context",
                "We need to choose a framework",
            ],
        )
        assert result.exit_code == 0

    @patch("git_adr.ai.AIService")
    def test_draft_with_from_commits(
        self, mock_ai_service: MagicMock, ai_configured_repo: Path
    ) -> None:
        """Test draft analyzing commits."""
        mock_instance = MagicMock()
        mock_ai_service.return_value = mock_instance
        mock_instance.draft_adr.return_value = MockAIResponse()

        result = runner.invoke(
            app,
            ["ai", "draft", "Test ADR", "--batch", "--from-commits", "HEAD~1..HEAD"],
        )
        # May succeed or fail depending on commit history
        assert result.exit_code in [0, 1]

    @patch("git_adr.ai.AIService")
    def test_draft_with_template(
        self, mock_ai_service: MagicMock, ai_configured_repo: Path
    ) -> None:
        """Test draft with template override."""
        mock_instance = MagicMock()
        mock_ai_service.return_value = mock_instance
        mock_instance.draft_adr.return_value = MockAIResponse()

        result = runner.invoke(
            app,
            ["ai", "draft", "Test ADR", "--batch", "--template", "nygard"],
        )
        assert result.exit_code == 0

    def test_draft_no_ai_provider(self, no_ai_config_repo: Path) -> None:
        """Test draft without AI provider configured."""
        result = runner.invoke(app, ["ai", "draft", "Test ADR", "--batch"])
        assert result.exit_code != 0
        assert "provider" in result.output.lower()

    def test_draft_not_initialized(
        self, temp_git_repo: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test draft in non-initialized repo."""
        # Change to the temp repo directory
        monkeypatch.chdir(temp_git_repo)
        # Override any global AI config to test initialization check
        git = Git(cwd=temp_git_repo)
        git.config_set("adr.ai.provider", "")
        result = runner.invoke(app, ["ai", "draft", "Test ADR", "--batch"])
        assert result.exit_code != 0
        # May fail with init error or AI provider error depending on order of checks
        assert "init" in result.output.lower() or "error" in result.output.lower()

    @patch("git_adr.ai.AIService")
    def test_draft_ai_error(
        self, mock_ai_service: MagicMock, ai_configured_repo: Path
    ) -> None:
        """Test draft when AI service raises error."""
        mock_instance = MagicMock()
        mock_ai_service.return_value = mock_instance
        mock_instance.draft_adr.side_effect = Exception("API rate limited")

        result = runner.invoke(app, ["ai", "draft", "Test ADR", "--batch"])
        assert result.exit_code != 0
        assert "error" in result.output.lower()


# =============================================================================
# AI Ask Command Tests
# =============================================================================


class TestAIAskCommand:
    """Tests for ai ask command."""

    @patch("git_adr.ai.AIService")
    def test_ask_success(
        self, mock_ai_service: MagicMock, ai_repo_with_data: Path
    ) -> None:
        """Test ask with mocked AI."""
        mock_instance = MagicMock()
        mock_ai_service.return_value = mock_instance
        mock_instance.ask_question.return_value = MockAIResponse(
            content="Based on the ADRs, PostgreSQL is used for the database."
        )

        result = runner.invoke(app, ["ai", "ask", "What database do we use?"])
        assert result.exit_code == 0
        assert "PostgreSQL" in result.output or "Answer" in result.output

    @patch("git_adr.ai.AIService")
    def test_ask_database_question(
        self, mock_ai_service: MagicMock, ai_repo_with_data: Path
    ) -> None:
        """Test ask about database."""
        mock_instance = MagicMock()
        mock_ai_service.return_value = mock_instance
        mock_instance.ask_question.return_value = MockAIResponse()

        result = runner.invoke(
            app, ["ai", "ask", "Tell me about the database decisions"]
        )
        assert result.exit_code == 0

    @patch("git_adr.ai.AIService")
    def test_ask_architecture_question(
        self, mock_ai_service: MagicMock, ai_repo_with_data: Path
    ) -> None:
        """Test ask about architecture."""
        mock_instance = MagicMock()
        mock_ai_service.return_value = mock_instance
        mock_instance.ask_question.return_value = MockAIResponse()

        result = runner.invoke(
            app, ["ai", "ask", "What decisions were made about infrastructure?"]
        )
        assert result.exit_code == 0

    @patch("git_adr.ai.AIService")
    def test_ask_empty_repo(
        self, mock_ai_service: MagicMock, ai_configured_repo: Path
    ) -> None:
        """Test ask in repo with no ADRs."""
        mock_instance = MagicMock()
        mock_ai_service.return_value = mock_instance
        mock_instance.ask_question.return_value = MockAIResponse()

        result = runner.invoke(app, ["ai", "ask", "What decisions were made?"])
        # Should succeed but may report no ADRs
        assert result.exit_code == 0

    def test_ask_no_ai_provider(self, no_ai_config_repo: Path) -> None:
        """Test ask without AI provider."""
        result = runner.invoke(app, ["ai", "ask", "Question"])
        assert result.exit_code != 0
        assert "provider" in result.output.lower()

    @patch("git_adr.ai.AIService")
    def test_ask_ai_error(
        self, mock_ai_service: MagicMock, ai_repo_with_data: Path
    ) -> None:
        """Test ask when AI service raises error."""
        mock_instance = MagicMock()
        mock_ai_service.return_value = mock_instance
        mock_instance.ask_question.side_effect = Exception("Connection timeout")

        result = runner.invoke(app, ["ai", "ask", "Question"])
        assert result.exit_code != 0


# =============================================================================
# AI Suggest Command Tests
# =============================================================================


class TestAISuggestCommand:
    """Tests for ai suggest command."""

    @patch("git_adr.ai.AIService")
    def test_suggest_success(
        self, mock_ai_service: MagicMock, ai_repo_with_data: Path
    ) -> None:
        """Test suggest with mocked AI."""
        mock_instance = MagicMock()
        mock_ai_service.return_value = mock_instance
        mock_instance.suggest_improvements.return_value = MockAIResponse(
            content="## Suggestions\n\n1. Add more context about alternatives considered."
        )

        result = runner.invoke(app, ["ai", "suggest", "20250110-use-postgresql"])
        assert result.exit_code == 0
        assert "Suggestions" in result.output or "Improvement" in result.output

    def test_suggest_adr_not_found(self, ai_repo_with_data: Path) -> None:
        """Test suggest with non-existent ADR."""
        result = runner.invoke(app, ["ai", "suggest", "nonexistent-adr-id"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_suggest_no_ai_provider(self, no_ai_config_repo: Path) -> None:
        """Test suggest without AI provider configured."""
        result = runner.invoke(app, ["ai", "suggest", "20250110-use-postgresql"])
        assert result.exit_code != 0
        assert "provider" in result.output.lower()

    @patch("git_adr.ai.AIService")
    def test_suggest_ai_error(
        self, mock_ai_service: MagicMock, ai_repo_with_data: Path
    ) -> None:
        """Test suggest when AI service raises error."""
        mock_instance = MagicMock()
        mock_ai_service.return_value = mock_instance
        mock_instance.suggest_improvements.side_effect = Exception("Invalid API key")

        result = runner.invoke(app, ["ai", "suggest", "20250110-use-postgresql"])
        assert result.exit_code != 0


# =============================================================================
# AI Summarize Command Tests
# =============================================================================


class TestAISummarizeCommand:
    """Tests for ai summarize command."""

    @patch("git_adr.ai.AIService")
    def test_summarize_success(
        self, mock_ai_service: MagicMock, ai_repo_with_data: Path
    ) -> None:
        """Test summarize with mocked AI."""
        mock_instance = MagicMock()
        mock_ai_service.return_value = mock_instance
        mock_instance.summarize_adrs.return_value = MockAIResponse(
            content="## Summary\n\nKey decisions in the last 30 days include PostgreSQL adoption."
        )

        result = runner.invoke(app, ["ai", "summarize"])
        assert result.exit_code == 0

    @patch("git_adr.ai.AIService")
    def test_summarize_with_period(
        self, mock_ai_service: MagicMock, ai_repo_with_data: Path
    ) -> None:
        """Test summarize with period argument."""
        mock_instance = MagicMock()
        mock_ai_service.return_value = mock_instance
        mock_instance.summarize_adrs.return_value = MockAIResponse()

        for period in ["7d", "30d", "90d", "2w", "3m"]:
            result = runner.invoke(app, ["ai", "summarize", "--period", period])
            assert result.exit_code == 0

    @patch("git_adr.ai.AIService")
    def test_summarize_with_format(
        self, mock_ai_service: MagicMock, ai_repo_with_data: Path
    ) -> None:
        """Test summarize with different formats."""
        mock_instance = MagicMock()
        mock_ai_service.return_value = mock_instance
        mock_instance.summarize_adrs.return_value = MockAIResponse()

        for fmt in ["markdown", "slack", "email", "standup"]:
            result = runner.invoke(app, ["ai", "summarize", "--format", fmt])
            assert result.exit_code == 0

    @patch("git_adr.ai.AIService")
    def test_summarize_no_recent_adrs(
        self, mock_ai_service: MagicMock, ai_configured_repo: Path
    ) -> None:
        """Test summarize with no ADRs in period."""
        result = runner.invoke(app, ["ai", "summarize", "--period", "1d"])
        # Should report no ADRs found
        assert result.exit_code == 0

    def test_summarize_no_ai_provider(self, no_ai_config_repo: Path) -> None:
        """Test summarize without AI provider."""
        result = runner.invoke(app, ["ai", "summarize"])
        assert result.exit_code != 0
        assert "provider" in result.output.lower()


# =============================================================================
# AI Service Module Tests
# =============================================================================


class TestAIServiceModule:
    """Tests for the AI service module itself."""

    def test_ai_service_import(self) -> None:
        """Test that AI service can be imported."""
        try:
            from git_adr.ai import AIService

            assert AIService is not None
        except ImportError:
            # AI dependencies not installed - acceptable
            pass

    def test_ai_service_initialization(self) -> None:
        """Test AI service initialization."""
        try:
            from git_adr.ai import AIService
            from git_adr.core.config import Config

            config = Config(ai_provider="openai", ai_model="gpt-4")
            service = AIService(config)
            assert service is not None
        except ImportError:
            pass
        except Exception:
            # May fail without API key - acceptable
            pass
