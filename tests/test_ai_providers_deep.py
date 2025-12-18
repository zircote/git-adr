"""Deep tests for AI service provider initialization.

Targets lines 97-125, 134 in ai/service.py.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from git_adr.ai.service import AIService, AIServiceError
from git_adr.cli import app
from git_adr.core.config import Config

runner = CliRunner()


# no_ai_config_repo fixture is now in conftest.py


def make_config(
    provider: str, model: str | None = None, temperature: float = 0.7
) -> Config:
    """Create a Config with AI settings."""
    config = Config()
    config.ai_provider = provider
    config.ai_model = model
    config.ai_temperature = temperature
    return config


class TestAIServiceProviders:
    """Tests for AI service provider initialization."""

    def test_openai_provider_init(self) -> None:
        """Test OpenAI provider initialization (lines 97-100)."""
        mock_chat_openai = MagicMock()
        mock_langchain_openai = ModuleType("langchain_openai")
        mock_langchain_openai.ChatOpenAI = mock_chat_openai

        with patch.dict(sys.modules, {"langchain_openai": mock_langchain_openai}):
            with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
                config = make_config("openai", "gpt-4")
                service = AIService(config)
                service._get_llm()

                mock_chat_openai.assert_called_once()
                call_kwargs = mock_chat_openai.call_args[1]
                assert call_kwargs["model"] == "gpt-4"

    def test_anthropic_provider_init(self) -> None:
        """Test Anthropic provider initialization (lines 104-107)."""
        mock_chat_anthropic = MagicMock()
        mock_langchain_anthropic = ModuleType("langchain_anthropic")
        mock_langchain_anthropic.ChatAnthropic = mock_chat_anthropic

        with patch.dict(sys.modules, {"langchain_anthropic": mock_langchain_anthropic}):
            with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
                config = make_config("anthropic", "claude-3-opus")
                service = AIService(config)
                service._get_llm()

                mock_chat_anthropic.assert_called_once()
                call_kwargs = mock_chat_anthropic.call_args[1]
                assert call_kwargs["model"] == "claude-3-opus"

    def test_google_provider_init(self) -> None:
        """Test Google provider initialization (lines 113-116)."""
        mock_chat_google = MagicMock()
        mock_langchain_google = ModuleType("langchain_google_genai")
        mock_langchain_google.ChatGoogleGenerativeAI = mock_chat_google

        with patch.dict(sys.modules, {"langchain_google_genai": mock_langchain_google}):
            with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key"}):
                config = make_config("google", "gemini-pro")
                service = AIService(config)
                service._get_llm()

                mock_chat_google.assert_called_once()

    def test_ollama_provider_init(self) -> None:
        """Test Ollama provider initialization (lines 120-123)."""
        mock_chat_ollama = MagicMock()
        mock_langchain_ollama = ModuleType("langchain_ollama")
        mock_langchain_ollama.ChatOllama = mock_chat_ollama

        with patch.dict(sys.modules, {"langchain_ollama": mock_langchain_ollama}):
            config = make_config("ollama", "llama2")
            service = AIService(config)
            service._get_llm()

            mock_chat_ollama.assert_called_once()

    def test_unsupported_provider_error(self) -> None:
        """Test unsupported provider raises error (line 125)."""
        config = make_config("unsupported", "test")

        with pytest.raises(AIServiceError) as exc_info:
            service = AIService(config)
            _ = service._get_llm()

        assert "unsupported provider" in str(exc_info.value).lower()

    def test_provider_import_error(self) -> None:
        """Test import error handling (lines 127-132)."""
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if "langchain_openai" in name:
                raise ImportError(f"No module named '{name}'")
            return original_import(name, *args, **kwargs)

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            config = make_config("openai", "gpt-4")
            service = AIService(config)
            # Reset the cached LLM to force re-import
            service._llm = None

            # Mock import to fail for langchain_openai
            with patch.object(builtins, "__import__", side_effect=mock_import):
                with pytest.raises(AIServiceError) as exc_info:
                    _ = service._get_llm()

            error_msg = str(exc_info.value).lower()
            assert (
                "requires additional dependencies" in error_msg or "import" in error_msg
            )

    def test_llm_caching(self) -> None:
        """Test LLM is cached (line 134 return)."""
        mock_llm = MagicMock()
        mock_chat_openai = MagicMock(return_value=mock_llm)
        mock_langchain_openai = ModuleType("langchain_openai")
        mock_langchain_openai.ChatOpenAI = mock_chat_openai

        with patch.dict(sys.modules, {"langchain_openai": mock_langchain_openai}):
            with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
                config = make_config("openai", "gpt-4")
                service = AIService(config)

                # First call creates the LLM
                llm1 = service._get_llm()
                # Second call should return cached instance
                llm2 = service._get_llm()

                # OpenAI should only be called once
                assert mock_chat_openai.call_count == 1
                assert llm1 is llm2


class TestAIServiceTemperature:
    """Tests for AI service temperature settings."""

    def test_custom_temperature(self) -> None:
        """Test custom temperature setting."""
        mock_chat_openai = MagicMock()
        mock_langchain_openai = ModuleType("langchain_openai")
        mock_langchain_openai.ChatOpenAI = mock_chat_openai

        with patch.dict(sys.modules, {"langchain_openai": mock_langchain_openai}):
            with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
                config = make_config("openai", "gpt-4", temperature=0.5)
                service = AIService(config)
                _ = service._get_llm()

                call_kwargs = mock_chat_openai.call_args[1]
                assert call_kwargs["temperature"] == 0.5

    def test_zero_temperature(self) -> None:
        """Test zero temperature for deterministic output."""
        mock_chat_anthropic = MagicMock()
        mock_langchain_anthropic = ModuleType("langchain_anthropic")
        mock_langchain_anthropic.ChatAnthropic = mock_chat_anthropic

        with patch.dict(sys.modules, {"langchain_anthropic": mock_langchain_anthropic}):
            with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
                config = make_config("anthropic", "claude-3", temperature=0.0)
                service = AIService(config)
                _ = service._get_llm()

                call_kwargs = mock_chat_anthropic.call_args[1]
                assert call_kwargs["temperature"] == 0.0


class TestAIServiceNoProvider:
    """Tests for AIService when provider is not configured."""

    def test_no_provider_error(self) -> None:
        """Test error when provider is not set."""
        config = Config()
        config.ai_provider = None

        with pytest.raises(AIServiceError) as exc_info:
            AIService(config)

        assert "not configured" in str(exc_info.value)

    def test_no_api_key_error(self) -> None:
        """Test error when API key is missing."""
        with patch.dict("os.environ", {}, clear=True):
            config = make_config("openai", "gpt-4")

            with pytest.raises(AIServiceError) as exc_info:
                AIService(config)

            assert "api key" in str(exc_info.value).lower()


class TestAIServiceDefaultModel:
    """Tests for default model selection."""

    def test_default_openai_model(self) -> None:
        """Test default OpenAI model is set."""
        mock_chat_openai = MagicMock()
        mock_langchain_openai = ModuleType("langchain_openai")
        mock_langchain_openai.ChatOpenAI = mock_chat_openai

        with patch.dict(sys.modules, {"langchain_openai": mock_langchain_openai}):
            with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
                config = make_config("openai", None)  # No model specified
                service = AIService(config)

                # Default model should be set
                assert service.model == "gpt-4o-mini"

    def test_default_ollama_model(self) -> None:
        """Test default Ollama model is set."""
        mock_chat_ollama = MagicMock()
        mock_langchain_ollama = ModuleType("langchain_ollama")
        mock_langchain_ollama.ChatOllama = mock_chat_ollama

        with patch.dict(sys.modules, {"langchain_ollama": mock_langchain_ollama}):
            config = make_config("ollama", None)
            service = AIService(config)

            # Default model should be set
            assert service.model == "llama3.2"


class TestAICommandsNoProvider:
    """Tests for AI commands when provider not configured."""

    def test_ai_ask_no_provider(self, no_ai_config_repo: Path) -> None:
        """Test ai ask without provider configured."""
        result = runner.invoke(
            app,
            ["ai", "ask", "What databases are used?"],
        )
        # Should fail because provider not configured
        assert result.exit_code == 1
        # Should mention provider not configured
        assert (
            "provider" in result.output.lower()
            or "not configured" in result.output.lower()
        )

    def test_ai_draft_no_provider(self, no_ai_config_repo: Path) -> None:
        """Test ai draft without provider configured."""
        result = runner.invoke(
            app,
            ["ai", "draft", "New feature idea"],
        )
        assert result.exit_code == 1

    def test_ai_suggest_no_provider(self, no_ai_config_repo: Path) -> None:
        """Test ai suggest without provider configured."""
        result = runner.invoke(
            app,
            ["ai", "suggest"],
        )
        # Exit code 1 = provider not configured, 2 = missing required args
        assert result.exit_code in [1, 2]
