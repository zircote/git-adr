"""Tests for git-adr AI service."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from git_adr.core.adr import ADR, ADRMetadata, ADRStatus
from git_adr.core.config import Config

if TYPE_CHECKING:
    from git_adr.ai import AIService


class TestAIServiceInit:
    """Tests for AIService initialization."""

    def test_init_without_provider(self) -> None:
        """Test initialization fails without provider."""
        from git_adr.ai import AIService, AIServiceError

        config = Config()  # No AI provider set
        with pytest.raises(AIServiceError, match="provider not configured"):
            AIService(config)

    def test_init_without_api_key(self) -> None:
        """Test initialization fails without API key."""
        from git_adr.ai import AIService, AIServiceError

        config = Config(ai_provider="openai")
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(AIServiceError, match="API key"):
                AIService(config)

    def test_init_ollama_no_api_key_required(self) -> None:
        """Test Ollama doesn't require API key."""
        from git_adr.ai import AIService

        config = Config(ai_provider="ollama")
        # Should not raise - Ollama is local
        service = AIService(config)
        assert service.provider == "ollama"

    def test_init_with_api_key(self) -> None:
        """Test initialization with API key."""
        from git_adr.ai import AIService

        config = Config(ai_provider="openai", ai_model="gpt-4o-mini")
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            service = AIService(config)
            assert service.provider == "openai"
            assert service.model == "gpt-4o-mini"

    def test_default_model_selection(self) -> None:
        """Test default model is set when not specified."""
        from git_adr.ai import AIService

        config = Config(ai_provider="anthropic")
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            service = AIService(config)
            assert service.model == "claude-sonnet-4-20250514"


class TestAIServiceMethods:
    """Tests for AIService methods (mocked)."""

    @pytest.fixture
    def mock_ai_service(self) -> AIService:
        """Create AIService with mocked LLM."""
        from git_adr.ai import AIService

        config = Config(ai_provider="openai", ai_model="gpt-4o-mini")
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            service = AIService(config)
            # Mock the LLM
            mock_llm = MagicMock()
            mock_response = MagicMock()
            mock_response.content = "Mocked AI response"
            mock_llm.invoke.return_value = mock_response
            service._llm = mock_llm
            return service

    def test_draft_adr(self, mock_ai_service: AIService) -> None:
        """Test draft ADR generation."""
        response = mock_ai_service.draft_adr(
            title="Use Kubernetes",
            context="We need container orchestration",
            options=["Kubernetes", "Docker Swarm", "Nomad"],
            drivers=["Scalability", "Community support"],
        )
        assert response.content == "Mocked AI response"
        assert response.provider == "openai"
        assert response.model == "gpt-4o-mini"

    def test_suggest_improvements(self, mock_ai_service: AIService) -> None:
        """Test improvement suggestions."""
        adr = ADR(
            metadata=ADRMetadata(
                id="test-adr",
                title="Test ADR",
                date=date.today(),
                status=ADRStatus.PROPOSED,
            ),
            content="# Test\n\nSome content.",
        )
        response = mock_ai_service.suggest_improvements(adr)
        assert response.content == "Mocked AI response"

    def test_summarize_adrs(self, mock_ai_service: AIService) -> None:
        """Test ADR summarization."""
        adrs = [
            ADR(
                metadata=ADRMetadata(
                    id="adr-1",
                    title="First ADR",
                    date=date.today(),
                    status=ADRStatus.ACCEPTED,
                    tags=["database"],
                ),
                content="Content 1",
            ),
            ADR(
                metadata=ADRMetadata(
                    id="adr-2",
                    title="Second ADR",
                    date=date.today(),
                    status=ADRStatus.PROPOSED,
                ),
                content="Content 2",
            ),
        ]
        response = mock_ai_service.summarize_adrs(adrs, format_="markdown")
        assert response.content == "Mocked AI response"

    def test_ask_question(self, mock_ai_service: AIService) -> None:
        """Test Q&A functionality."""
        adrs = [
            ADR(
                metadata=ADRMetadata(
                    id="db-adr",
                    title="Use PostgreSQL",
                    date=date.today(),
                    status=ADRStatus.ACCEPTED,
                ),
                content="We chose PostgreSQL for ACID compliance.",
            ),
        ]
        response = mock_ai_service.ask_question("Why did we choose PostgreSQL?", adrs)
        assert response.content == "Mocked AI response"


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
            content="Test",
            model="claude-3",
            provider="anthropic",
        )
        assert response.tokens_used is None
