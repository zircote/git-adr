"""Tests for AI service exception handling (CQ-001 fix)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from git_adr.ai.service import AIService, AIServiceError


class TestLLMExceptionHandling:
    """Test that LLM invocation errors are properly wrapped."""

    @pytest.fixture
    def mock_config(self) -> MagicMock:
        """Create mock config for AIService."""
        config = MagicMock()
        config.ai_provider = "openai"
        config.ai_model = "gpt-4o-mini"
        config.ai_temperature = 0.7
        return config

    @pytest.fixture
    def service_with_mock_llm(self, mock_config: MagicMock) -> AIService:
        """Create AIService with mocked LLM."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            service = AIService(mock_config)
            # Create a mock LLM
            mock_llm = MagicMock()
            service._llm = mock_llm
            return service

    def test_draft_adr_wraps_llm_error(self, service_with_mock_llm: AIService) -> None:
        """Test that draft_adr wraps LLM errors in AIServiceError."""
        service_with_mock_llm._llm.invoke.side_effect = RuntimeError("Network timeout")

        with pytest.raises(AIServiceError) as exc_info:
            service_with_mock_llm.draft_adr(title="Test ADR")

        assert "LLM invocation failed" in str(exc_info.value)
        assert "Network timeout" in str(exc_info.value)
        # Check exception chaining
        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, RuntimeError)

    def test_suggest_improvements_wraps_llm_error(
        self, service_with_mock_llm: AIService
    ) -> None:
        """Test that suggest_improvements wraps LLM errors in AIServiceError."""
        from datetime import date

        from git_adr.core.adr import ADR, ADRMetadata, ADRStatus

        mock_adr = ADR(
            metadata=ADRMetadata(
                id="test-adr",
                title="Test",
                date=date.today(),
                status=ADRStatus.PROPOSED,
            ),
            content="Test content",
        )

        service_with_mock_llm._llm.invoke.side_effect = ConnectionError(
            "API unavailable"
        )

        with pytest.raises(AIServiceError) as exc_info:
            service_with_mock_llm.suggest_improvements(mock_adr)

        assert "LLM invocation failed" in str(exc_info.value)
        assert "API unavailable" in str(exc_info.value)

    def test_summarize_adrs_wraps_llm_error(
        self, service_with_mock_llm: AIService
    ) -> None:
        """Test that summarize_adrs wraps LLM errors in AIServiceError."""
        from datetime import date

        from git_adr.core.adr import ADR, ADRMetadata, ADRStatus

        mock_adr = ADR(
            metadata=ADRMetadata(
                id="test-adr",
                title="Test",
                date=date.today(),
                status=ADRStatus.PROPOSED,
            ),
            content="Test content",
        )

        service_with_mock_llm._llm.invoke.side_effect = ValueError(
            "Rate limit exceeded"
        )

        with pytest.raises(AIServiceError) as exc_info:
            service_with_mock_llm.summarize_adrs([mock_adr])

        assert "LLM invocation failed" in str(exc_info.value)
        assert "Rate limit exceeded" in str(exc_info.value)

    def test_ask_question_wraps_llm_error(
        self, service_with_mock_llm: AIService
    ) -> None:
        """Test that ask_question wraps LLM errors in AIServiceError."""
        from datetime import date

        from git_adr.core.adr import ADR, ADRMetadata, ADRStatus

        mock_adr = ADR(
            metadata=ADRMetadata(
                id="test-adr",
                title="Test",
                date=date.today(),
                status=ADRStatus.PROPOSED,
            ),
            content="Test content",
        )

        service_with_mock_llm._llm.invoke.side_effect = TimeoutError(
            "Request timed out"
        )

        with pytest.raises(AIServiceError) as exc_info:
            service_with_mock_llm.ask_question("What?", [mock_adr])

        assert "LLM invocation failed" in str(exc_info.value)
        assert "Request timed out" in str(exc_info.value)

    def test_successful_invocation_returns_response(
        self, service_with_mock_llm: AIService
    ) -> None:
        """Test that successful invocation returns proper response."""
        mock_response = MagicMock()
        mock_response.content = "Generated ADR content"
        service_with_mock_llm._llm.invoke.return_value = mock_response

        response = service_with_mock_llm.draft_adr(title="Test ADR")

        assert response.content == "Generated ADR content"
        assert response.provider == "openai"
        assert response.model == "gpt-4o-mini"
