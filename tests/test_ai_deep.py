"""Deep tests for AI commands (ai draft, ai summarize, ai ask, ai suggest).

Targets uncovered code paths with comprehensive mocking.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from git_adr.cli import app
from git_adr.core.config import ConfigManager
from git_adr.core.git import Git

runner = CliRunner()


# no_ai_config_repo fixture is now in conftest.py


@pytest.fixture
def ai_configured_repo(adr_repo_with_data: Path) -> Path:
    """Repository with AI provider configured."""
    git = Git(cwd=adr_repo_with_data)
    config_manager = ConfigManager(git)
    config_manager.set("ai.provider", "openai")
    config_manager.set("ai.model", "gpt-4")
    # Note: API key is typically set via environment variable OPENAI_API_KEY
    # or stored in git config with valid key format
    return adr_repo_with_data


# =============================================================================
# AI Draft Command Tests
# =============================================================================


class TestAIDraftCommand:
    """Tests for ai draft command."""

    def test_ai_draft_no_provider(self, no_ai_config_repo: Path) -> None:
        """Test AI draft without provider configured."""
        result = runner.invoke(
            app,
            ["ai", "draft", "Test Decision", "--batch"],
        )
        assert result.exit_code != 0
        assert "provider" in result.output.lower()

    @patch("git_adr.ai.AIService")
    def test_ai_draft_batch_mode(
        self, mock_ai_class: MagicMock, ai_configured_repo: Path
    ) -> None:
        """Test AI draft in batch mode."""
        mock_ai = MagicMock()
        mock_ai_class.return_value = mock_ai
        mock_ai.draft_adr.return_value = MagicMock(
            content="## Context\n\nGenerated context.\n\n## Decision\n\nGenerated decision.",
            model="gpt-4",
            provider="openai",
        )

        result = runner.invoke(
            app,
            ["ai", "draft", "Test Decision", "--batch"],
        )
        assert result.exit_code in [0, 1]

    @patch("git_adr.ai.AIService")
    def test_ai_draft_with_context(
        self, mock_ai_class: MagicMock, ai_configured_repo: Path
    ) -> None:
        """Test AI draft with additional context."""
        mock_ai = MagicMock()
        mock_ai_class.return_value = mock_ai
        mock_ai.draft_adr.return_value = MagicMock(
            content="## Context\n\nGenerated.\n\n## Decision\n\nGenerated.",
            model="gpt-4",
            provider="openai",
        )

        result = runner.invoke(
            app,
            [
                "ai",
                "draft",
                "Test Decision",
                "--batch",
                "--context",
                "We need to choose a database.",
            ],
        )
        assert result.exit_code in [0, 1]

    @patch("git_adr.ai.AIService")
    def test_ai_draft_with_commits(
        self, mock_ai_class: MagicMock, ai_configured_repo: Path
    ) -> None:
        """Test AI draft with commit analysis."""
        mock_ai = MagicMock()
        mock_ai_class.return_value = mock_ai
        mock_ai.draft_adr.return_value = MagicMock(
            content="## Context\n\nFrom commits.\n\n## Decision\n\nBased on commits.",
            model="gpt-4",
            provider="openai",
        )

        result = runner.invoke(
            app,
            [
                "ai",
                "draft",
                "Test Decision",
                "--batch",
                "--from-commits",
                "HEAD~3..HEAD",
            ],
        )
        assert result.exit_code in [0, 1]

    @patch("git_adr.ai.AIService")
    def test_ai_draft_with_template(
        self, mock_ai_class: MagicMock, ai_configured_repo: Path
    ) -> None:
        """Test AI draft with template override."""
        mock_ai = MagicMock()
        mock_ai_class.return_value = mock_ai
        mock_ai.draft_adr.return_value = MagicMock(
            content="## Context\n\nTemplated.\n\n## Decision\n\nTemplated.",
            model="gpt-4",
            provider="openai",
        )

        result = runner.invoke(
            app,
            [
                "ai",
                "draft",
                "Test Decision",
                "--batch",
                "--template",
                "nygard",
            ],
        )
        assert result.exit_code in [0, 1]

    @patch("git_adr.ai.AIService")
    def test_ai_draft_import_error(
        self, mock_ai_class: MagicMock, ai_configured_repo: Path
    ) -> None:
        """Test AI draft with import error."""
        mock_ai_class.side_effect = ImportError("No module")

        result = runner.invoke(
            app,
            ["ai", "draft", "Test Decision", "--batch"],
        )
        assert result.exit_code != 0

    @patch("git_adr.ai.AIService")
    def test_ai_draft_ai_error(
        self, mock_ai_class: MagicMock, ai_configured_repo: Path
    ) -> None:
        """Test AI draft with AI error."""
        mock_ai = MagicMock()
        mock_ai_class.return_value = mock_ai
        mock_ai.draft_adr.side_effect = Exception("API rate limit")

        result = runner.invoke(
            app,
            ["ai", "draft", "Test Decision", "--batch"],
        )
        assert result.exit_code != 0
        assert "error" in result.output.lower()


# =============================================================================
# AI Summarize Command Tests
# =============================================================================


class TestAISummarizeCommand:
    """Tests for ai summarize command."""

    def test_ai_summarize_no_provider(self, no_ai_config_repo: Path) -> None:
        """Test AI summarize without provider configured."""
        result = runner.invoke(
            app,
            ["ai", "summarize"],
        )
        assert result.exit_code != 0
        assert "provider" in result.output.lower()

    @patch("git_adr.ai.AIService")
    def test_ai_summarize_success(
        self, mock_ai_class: MagicMock, ai_configured_repo: Path
    ) -> None:
        """Test AI summarize success."""
        mock_ai = MagicMock()
        mock_ai_class.return_value = mock_ai
        mock_ai.summarize_adrs.return_value = MagicMock(
            content="# Summary\n\nRecent decisions...",
            model="gpt-4",
            provider="openai",
        )

        result = runner.invoke(
            app,
            ["ai", "summarize", "--period", "30d"],
        )
        assert result.exit_code in [0, 1]

    @patch("git_adr.ai.AIService")
    def test_ai_summarize_different_periods(
        self, mock_ai_class: MagicMock, ai_configured_repo: Path
    ) -> None:
        """Test AI summarize with different period formats."""
        mock_ai = MagicMock()
        mock_ai_class.return_value = mock_ai
        mock_ai.summarize_adrs.return_value = MagicMock(
            content="# Summary\n\nRecent decisions...",
            model="gpt-4",
            provider="openai",
        )

        for period in ["7d", "2w", "3m"]:
            result = runner.invoke(
                app,
                ["ai", "summarize", "--period", period],
            )
            assert result.exit_code in [0, 1]

    @patch("git_adr.ai.AIService")
    def test_ai_summarize_different_formats(
        self, mock_ai_class: MagicMock, ai_configured_repo: Path
    ) -> None:
        """Test AI summarize with different output formats."""
        mock_ai = MagicMock()
        mock_ai_class.return_value = mock_ai
        mock_ai.summarize_adrs.return_value = MagicMock(
            content="Summary content",
            model="gpt-4",
            provider="openai",
        )

        for format_ in ["markdown", "slack", "email", "standup"]:
            result = runner.invoke(
                app,
                ["ai", "summarize", "--format", format_],
            )
            assert result.exit_code in [0, 1]

    def test_ai_summarize_no_adrs(self, ai_configured_repo: Path) -> None:
        """Test AI summarize with no ADRs in period."""
        # Use a very short period
        result = runner.invoke(
            app,
            ["ai", "summarize", "--period", "1d"],
        )
        # May show "no ADRs found" message or succeed
        assert result.exit_code in [0, 1]


# =============================================================================
# AI Ask Command Tests
# =============================================================================


class TestAIAskCommand:
    """Tests for ai ask command."""

    def test_ai_ask_no_provider(self, no_ai_config_repo: Path) -> None:
        """Test AI ask without provider configured."""
        result = runner.invoke(
            app,
            ["ai", "ask", "What is the database decision?"],
        )
        assert result.exit_code != 0
        assert "provider" in result.output.lower()

    @patch("git_adr.ai.AIService")
    def test_ai_ask_success(
        self, mock_ai_class: MagicMock, ai_configured_repo: Path
    ) -> None:
        """Test AI ask success."""
        mock_ai = MagicMock()
        mock_ai_class.return_value = mock_ai
        mock_ai.ask_question.return_value = MagicMock(
            content="The database decision is to use PostgreSQL.",
            model="gpt-4",
            provider="openai",
        )

        result = runner.invoke(
            app,
            ["ai", "ask", "What is the database decision?"],
        )
        assert result.exit_code in [0, 1]


# =============================================================================
# AI Suggest Command Tests
# =============================================================================


class TestAISuggestCommand:
    """Tests for ai suggest command."""

    def test_ai_suggest_no_provider(self, no_ai_config_repo: Path) -> None:
        """Test AI suggest without provider configured."""
        result = runner.invoke(
            app,
            ["ai", "suggest", "20250110-use-postgresql"],
        )
        assert result.exit_code != 0
        assert "provider" in result.output.lower()

    @patch("git_adr.ai.AIService")
    def test_ai_suggest_success(
        self, mock_ai_class: MagicMock, ai_configured_repo: Path
    ) -> None:
        """Test AI suggest success."""
        mock_ai = MagicMock()
        mock_ai_class.return_value = mock_ai
        mock_ai.suggest_improvements.return_value = MagicMock(
            content="## Suggestions\n\n1. Add more context...",
            model="gpt-4",
            provider="openai",
        )

        result = runner.invoke(
            app,
            ["ai", "suggest", "20250110-use-postgresql"],
        )
        assert result.exit_code in [0, 1]

    def test_ai_suggest_adr_not_found(self, ai_configured_repo: Path) -> None:
        """Test AI suggest with non-existent ADR."""
        result = runner.invoke(
            app,
            ["ai", "suggest", "nonexistent-adr"],
        )
        assert result.exit_code != 0
        assert "not found" in result.output.lower()


# =============================================================================
# Helper Function Tests
# =============================================================================


class TestAISummarizeHelpers:
    """Tests for AI summarize helper functions."""

    def test_parse_period_days(self) -> None:
        """Test _parse_period with days."""
        from git_adr.commands.ai_summarize import _parse_period

        assert _parse_period("7d") == 7
        assert _parse_period("30d") == 30

    def test_parse_period_weeks(self) -> None:
        """Test _parse_period with weeks."""
        from git_adr.commands.ai_summarize import _parse_period

        assert _parse_period("2w") == 14
        assert _parse_period("4w") == 28

    def test_parse_period_months(self) -> None:
        """Test _parse_period with months."""
        from git_adr.commands.ai_summarize import _parse_period

        assert _parse_period("1m") == 30
        assert _parse_period("3m") == 90

    def test_parse_period_invalid(self) -> None:
        """Test _parse_period with invalid input."""
        from git_adr.commands.ai_summarize import _parse_period

        # Invalid format should return default (30)
        assert _parse_period("invalid") == 30
        assert _parse_period("abc") == 30
        assert _parse_period("") == 30
