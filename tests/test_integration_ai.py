"""Integration tests for git-adr AI commands.

Tests AI functionality with mocked LLM services.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from git_adr.ai import AIService, AIServiceError
from git_adr.cli import app
from git_adr.core.adr import ADR, ADRMetadata, ADRStatus
from git_adr.core.config import Config

runner = CliRunner()


# no_ai_config_repo fixture is now in conftest.py


# =============================================================================
# AI Service Tests
# =============================================================================


class TestAIServiceConfiguration:
    """Tests for AI service configuration."""

    def test_init_without_provider_raises(self) -> None:
        """Test that AIService raises without provider."""
        config = Config()  # No AI provider
        with pytest.raises(AIServiceError, match="provider not configured"):
            AIService(config)

    def test_init_without_api_key_raises(self) -> None:
        """Test that AIService raises without API key."""
        config = Config(ai_provider="openai")
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(AIServiceError, match="API key"):
                AIService(config)

    def test_init_ollama_no_key_required(self) -> None:
        """Test that Ollama doesn't require API key."""
        config = Config(ai_provider="ollama")
        service = AIService(config)
        assert service.provider == "ollama"

    def test_default_model_per_provider(self) -> None:
        """Test default model selection per provider."""
        test_cases = [
            ("openai", "gpt-4o-mini", "OPENAI_API_KEY"),
            ("anthropic", "claude-sonnet-4-20250514", "ANTHROPIC_API_KEY"),
            ("google", "gemini-1.5-flash", "GOOGLE_API_KEY"),
        ]

        for provider, expected_model, env_var in test_cases:
            config = Config(ai_provider=provider)
            with patch.dict("os.environ", {env_var: "test-key"}):
                service = AIService(config)
                assert service.model == expected_model, f"Failed for {provider}"


class TestAIServiceMethods:
    """Tests for AI service methods with mocked LLM."""

    @pytest.fixture
    def mock_service(self) -> AIService:
        """Create AIService with mocked LLM."""
        config = Config(ai_provider="openai", ai_model="gpt-4o-mini")
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            service = AIService(config)

            # Mock the LLM
            mock_llm = MagicMock()
            mock_response = MagicMock()
            mock_response.content = """---
id: use-kubernetes
title: Use Kubernetes
date: 2025-01-15
status: proposed
---

## Context

We need container orchestration.

## Decision

Use Kubernetes.

## Consequences

Scalable infrastructure.
"""
            mock_llm.invoke.return_value = mock_response
            service._llm = mock_llm

            return service

    def test_draft_adr(self, mock_service: AIService) -> None:
        """Test drafting an ADR."""
        response = mock_service.draft_adr(
            title="Use Kubernetes",
            context="Need container orchestration",
            options=["Kubernetes", "Docker Swarm"],
            drivers=["Scalability", "Ecosystem"],
        )

        assert response.content is not None
        assert response.provider == "openai"
        assert response.model == "gpt-4o-mini"

    def test_suggest_improvements(self, mock_service: AIService) -> None:
        """Test suggesting improvements."""
        adr = ADR(
            metadata=ADRMetadata(
                id="test-adr",
                title="Test",
                date=date.today(),
                status=ADRStatus.PROPOSED,
            ),
            content="## Context\n\nVague context.",
        )

        response = mock_service.suggest_improvements(adr)
        assert response.content is not None

    def test_summarize_adrs(self, mock_service: AIService) -> None:
        """Test summarizing ADRs."""
        adrs = [
            ADR(
                metadata=ADRMetadata(
                    id=f"adr-{i}",
                    title=f"ADR {i}",
                    date=date.today(),
                    status=ADRStatus.ACCEPTED,
                ),
                content=f"Content {i}",
            )
            for i in range(3)
        ]

        response = mock_service.summarize_adrs(adrs, format_="markdown")
        assert response.content is not None

    def test_ask_question(self, mock_service: AIService) -> None:
        """Test asking questions about ADRs."""
        adrs = [
            ADR(
                metadata=ADRMetadata(
                    id="use-postgres",
                    title="Use PostgreSQL",
                    date=date.today(),
                    status=ADRStatus.ACCEPTED,
                    tags=["database"],
                ),
                content="## Context\n\nNeed a database.\n\n## Decision\n\nUse PostgreSQL.",
            )
        ]

        response = mock_service.ask_question("Why PostgreSQL?", adrs)
        assert response.content is not None


# =============================================================================
# AI Command Tests (CLI)
# =============================================================================


@pytest.mark.integration
class TestAIDraftCommand:
    """Tests for ai draft command."""

    def test_draft_help(self) -> None:
        """Test draft help."""
        result = runner.invoke(app, ["ai", "draft", "--help"])
        assert result.exit_code == 0
        assert "draft" in result.output.lower()

    def test_draft_without_ai_config(self, initialized_adr_repo: Path) -> None:
        """Test draft fails without AI configuration."""
        result = runner.invoke(app, ["ai", "draft", "Test Title", "--no-edit"])
        # Should fail gracefully
        assert (
            "error" in result.output.lower()
            or "provider" in result.output.lower()
            or result.exit_code != 0
        )

    def test_draft_with_mock_ai(self, initialized_adr_repo: Path) -> None:
        """Test draft with mocked AI service."""
        # This would need more complex mocking of the command internals
        result = runner.invoke(app, ["ai", "draft", "--help"])
        assert result.exit_code == 0


@pytest.mark.integration
class TestAISuggestCommand:
    """Tests for ai suggest command."""

    def test_suggest_help(self) -> None:
        """Test suggest help."""
        result = runner.invoke(app, ["ai", "suggest", "--help"])
        assert result.exit_code == 0

    def test_suggest_without_ai(self, no_ai_config_repo: Path) -> None:
        """Test suggest without AI configuration."""
        result = runner.invoke(app, ["ai", "suggest", "use-postgresql"])
        # Should fail gracefully without AI config
        assert (
            result.exit_code != 0
            or "error" in result.output.lower()
            or "provider" in result.output.lower()
        )


@pytest.mark.integration
class TestAISummarizeCommand:
    """Tests for ai summarize command."""

    def test_summarize_help(self) -> None:
        """Test summarize help."""
        result = runner.invoke(app, ["ai", "summarize", "--help"])
        assert result.exit_code == 0

    def test_summarize_without_ai(self, no_ai_config_repo: Path) -> None:
        """Test summarize without AI configuration."""
        result = runner.invoke(app, ["ai", "summarize"])
        assert result.exit_code != 0 or "provider" in result.output.lower()


@pytest.mark.integration
class TestAIAskCommand:
    """Tests for ai ask command."""

    def test_ask_help(self) -> None:
        """Test ask help."""
        result = runner.invoke(app, ["ai", "ask", "--help"])
        assert result.exit_code == 0

    def test_ask_without_ai(self, no_ai_config_repo: Path) -> None:
        """Test ask without AI configuration."""
        result = runner.invoke(app, ["ai", "ask", "Why PostgreSQL?"])
        assert result.exit_code != 0 or "provider" in result.output.lower()


# =============================================================================
# AI Response Tests
# =============================================================================


class TestAIResponse:
    """Tests for AIResponse dataclass."""

    def test_ai_response_creation(self) -> None:
        """Test creating AIResponse."""
        from git_adr.ai.service import AIResponse

        response = AIResponse(
            content="Test content",
            model="gpt-4",
            provider="openai",
            tokens_used=100,
        )

        assert response.content == "Test content"
        assert response.model == "gpt-4"
        assert response.provider == "openai"
        assert response.tokens_used == 100

    def test_ai_response_without_tokens(self) -> None:
        """Test AIResponse without token count."""
        from git_adr.ai.service import AIResponse

        response = AIResponse(
            content="Test content",
            model="gpt-4",
            provider="openai",
        )

        assert response.tokens_used is None
