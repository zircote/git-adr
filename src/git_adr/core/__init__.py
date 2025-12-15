"""Core infrastructure for git-adr.

This module provides the foundational components:
- Git executor for subprocess operations
- ADR model and parsing
- Notes manager for git notes operations
- Index manager for fast ADR queries
- Configuration management
"""

from __future__ import annotations

from git_adr.core.adr import (
    ADR,
    ADRMetadata,
    ADRStatus,
    generate_adr_id,
    validate_adr,
)
from git_adr.core.config import Config, ConfigManager
from git_adr.core.git import (
    Git,
    GitError,
    GitNotFoundError,
    GitResult,
    NotARepositoryError,
    get_git,
)
from git_adr.core.index import IndexEntry, IndexManager, QueryResult, SearchMatch
from git_adr.core.notes import ArtifactInfo, NotesManager
from git_adr.core.utils import ensure_list

__all__ = [
    # Git
    "Git",
    "GitError",
    "GitNotFoundError",
    "GitResult",
    "NotARepositoryError",
    "get_git",
    # ADR
    "ADR",
    "ADRMetadata",
    "ADRStatus",
    "generate_adr_id",
    "validate_adr",
    # Config
    "Config",
    "ConfigManager",
    # Notes
    "NotesManager",
    "ArtifactInfo",
    # Index
    "IndexManager",
    "IndexEntry",
    "QueryResult",
    "SearchMatch",
    # Utils
    "ensure_list",
]
