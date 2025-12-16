"""AI service for ADR operations.

Provides AI-powered features using various LLM providers.
"""

from __future__ import annotations

import os
import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from git_adr.core import ADR, Config

# Suppress LangChain's Pydantic v1 deprecation warning on Python 3.14+
# Must be called before langchain imports in _get_llm()
warnings.filterwarnings(
    "ignore",
    message="Core Pydantic V1 functionality",
    category=UserWarning,
    module="langchain_core",
)


class AIServiceError(Exception):
    """Error in AI service."""

    pass


@dataclass
class AIResponse:
    """Response from AI service."""

    content: str
    model: str
    provider: str
    tokens_used: int | None = None


class AIService:
    """AI service for ADR operations.

    Supports multiple providers:
    - openai: OpenAI (GPT-4, GPT-4-mini)
    - anthropic: Anthropic (Claude)
    - google: Google (Gemini)
    - ollama: Local Ollama
    """

    PROVIDER_ENV_VARS: ClassVar[dict[str, str]] = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
    }

    DEFAULT_MODELS: ClassVar[dict[str, str]] = {
        "openai": "gpt-4o-mini",
        "anthropic": "claude-sonnet-4-20250514",
        "google": "gemini-1.5-flash",
        "ollama": "llama3.2",
    }

    def __init__(self, config: Config):
        """Initialize AI service.

        Args:
            config: git-adr configuration.

        Raises:
            AIServiceError: If provider is not configured or API key is missing.
        """
        self.config = config
        self.provider = config.ai_provider
        self.model = config.ai_model
        self.temperature = config.ai_temperature

        if not self.provider:
            raise AIServiceError(
                "AI provider not configured. Run: git adr config set ai.provider <provider>"
            )

        # Check for API key (except Ollama which is local)
        if self.provider != "ollama":
            env_var = self.PROVIDER_ENV_VARS.get(self.provider)
            if env_var and not os.environ.get(env_var):
                raise AIServiceError(
                    f"API key not found. Set {env_var} environment variable."
                )

        # Set default model if not specified
        if not self.model:
            self.model = self.DEFAULT_MODELS.get(self.provider, "gpt-4o-mini")

        self._llm = None

    def _get_llm(self):
        """Get the LLM instance (lazy initialization)."""
        if self._llm is not None:
            return self._llm

        try:
            if self.provider == "openai":
                from langchain_openai import ChatOpenAI

                self._llm = ChatOpenAI(
                    model=self.model,
                    temperature=self.temperature,
                )
            elif self.provider == "anthropic":
                from langchain_anthropic import ChatAnthropic

                self._llm = ChatAnthropic(
                    model=self.model,
                    temperature=self.temperature,
                )
            elif self.provider == "google":
                from langchain_google_genai import (
                    ChatGoogleGenerativeAI,
                )

                self._llm = ChatGoogleGenerativeAI(
                    model=self.model,
                    temperature=self.temperature,
                )
            elif self.provider == "ollama":
                from langchain_ollama import ChatOllama

                self._llm = ChatOllama(
                    model=self.model,
                    temperature=self.temperature,
                )
            else:
                raise AIServiceError(f"Unsupported provider: {self.provider}")

        except ImportError as e:
            raise AIServiceError(
                f"AI provider '{self.provider}' requires additional dependencies. "
                f"Install with: pip install 'git-adr\\[ai]'\n"
                f"Error: {e}"
            )

        return self._llm

    def draft_adr(
        self,
        title: str,
        context: str | None = None,
        options: list[str] | None = None,
        drivers: list[str] | None = None,
    ) -> AIResponse:
        """Generate an ADR draft using AI.

        Args:
            title: ADR title/decision topic.
            context: Additional context about the decision.
            options: Considered options/alternatives.
            drivers: Decision drivers/forces.

        Returns:
            AIResponse with generated ADR content.
        """
        llm = self._get_llm()

        prompt = f"""You are an expert software architect. Generate a complete Architecture Decision Record (ADR) in MADR 4.0 format.

Title: {title}
{f"Context: {context}" if context else ""}
{f"Options considered: {', '.join(options)}" if options else ""}
{f"Decision drivers: {', '.join(drivers)}" if drivers else ""}

Generate the ADR with these sections:
1. Title (# Title)
2. Context and Problem Statement
3. Decision Drivers (bulleted list)
4. Considered Options (bulleted list)
5. Decision Outcome (Chosen option with justification)
6. Consequences (Good, Bad, Neutral subsections)

Be specific and technical. Use bullet points where appropriate.
Do NOT include YAML frontmatter - just the markdown content."""

        try:
            response = llm.invoke(prompt)
        except Exception as e:
            raise AIServiceError(f"LLM invocation failed: {e}") from e
        content = response.content if hasattr(response, "content") else str(response)

        return AIResponse(
            content=content,
            model=self.model or "unknown",
            provider=self.provider or "unknown",
        )

    def suggest_improvements(self, adr: ADR) -> AIResponse:
        """Suggest improvements to an ADR.

        Args:
            adr: The ADR to analyze.

        Returns:
            AIResponse with improvement suggestions.
        """
        llm = self._get_llm()

        prompt = f"""You are an expert software architect reviewing Architecture Decision Records.

Analyze this ADR and suggest specific improvements:

Title: {adr.metadata.title}
Status: {adr.metadata.status.value}

Content:
{adr.content}

Provide suggestions in these categories:
1. **Context**: Is the problem statement clear? What context is missing?
2. **Options**: Are there alternatives that should be considered?
3. **Consequences**: Are all consequences (good, bad, neutral) documented?
4. **Clarity**: Is the reasoning clear and well-justified?
5. **Completeness**: What information is missing?

For each suggestion, explain WHY it would improve the ADR.
Be specific and actionable."""

        try:
            response = llm.invoke(prompt)
        except Exception as e:
            raise AIServiceError(f"LLM invocation failed: {e}") from e
        content = response.content if hasattr(response, "content") else str(response)

        return AIResponse(
            content=content,
            model=self.model or "unknown",
            provider=self.provider or "unknown",
        )

    def summarize_adrs(
        self,
        adrs: list[ADR],
        format_: str = "markdown",
    ) -> AIResponse:
        """Generate a summary of ADRs.

        Args:
            adrs: List of ADRs to summarize.
            format_: Output format (markdown, slack, email, standup).

        Returns:
            AIResponse with summary.
        """
        llm = self._get_llm()

        # Build ADR context
        adr_context = "\n\n".join(
            f"**{adr.metadata.id}**: {adr.metadata.title}\n"
            f"Status: {adr.metadata.status.value}\n"
            f"Date: {adr.metadata.date}\n"
            f"Tags: {', '.join(adr.metadata.tags) if adr.metadata.tags else 'none'}"
            for adr in adrs
        )

        format_instructions = {
            "markdown": "Use markdown formatting with headers and bullet points.",
            "slack": "Use Slack formatting (*bold*, _italic_, • bullets). Keep it conversational.",
            "email": "Write as a professional email summary. Include greeting and sign-off.",
            "standup": "Write a brief standup update. Max 3 bullet points. Very concise.",
        }

        prompt = f"""You are a technical writer summarizing Architecture Decision Records.

Here are the recent ADRs:

{adr_context}

Generate a {format_} summary of these decisions.
{format_instructions.get(format_, format_instructions["markdown"])}

Highlight:
- Key decisions made
- Common themes or patterns
- Any decisions that might need attention (deprecated, long-pending)"""

        try:
            response = llm.invoke(prompt)
        except Exception as e:
            raise AIServiceError(f"LLM invocation failed: {e}") from e
        content = response.content if hasattr(response, "content") else str(response)

        return AIResponse(
            content=content,
            model=self.model or "unknown",
            provider=self.provider or "unknown",
        )

    def ask_question(
        self,
        question: str,
        adrs: list[ADR],
    ) -> AIResponse:
        """Answer a question about ADRs using RAG.

        Args:
            question: Natural language question.
            adrs: ADRs to search for context.

        Returns:
            AIResponse with answer and citations.
        """
        llm = self._get_llm()

        # Build ADR context for RAG
        adr_context = "\n\n---\n\n".join(
            f"ADR ID: {adr.metadata.id}\n"
            f"Title: {adr.metadata.title}\n"
            f"Status: {adr.metadata.status.value}\n"
            f"Date: {adr.metadata.date}\n"
            f"Content:\n{adr.content[:2000]}"  # Truncate long content
            for adr in adrs[:20]  # Limit context size
        )

        prompt = f"""You are an AI assistant helping developers understand their Architecture Decision Records.

Here are the relevant ADRs from this project:

{adr_context}

---

Question: {question}

Answer the question based ONLY on the ADRs provided above. If the information isn't in the ADRs, say so.

Include citations to specific ADRs when referencing decisions. Format citations as [ADR-ID].
Be specific and technical."""

        try:
            response = llm.invoke(prompt)
        except Exception as e:
            raise AIServiceError(f"LLM invocation failed: {e}") from e
        content = response.content if hasattr(response, "content") else str(response)

        return AIResponse(
            content=content,
            model=self.model or "unknown",
            provider=self.provider or "unknown",
        )
