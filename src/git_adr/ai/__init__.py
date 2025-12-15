"""AI services for git-adr.

This module provides AI-powered features:
- Draft generation
- ADR improvement suggestions
- Summarization
- Q&A (RAG)
"""

from __future__ import annotations

from git_adr.ai.service import AIService, AIServiceError

__all__ = ["AIService", "AIServiceError"]
