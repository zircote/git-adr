"""Shared utility functions for git-adr.

This module provides common utilities used across the codebase.
"""

from __future__ import annotations

from typing import Any


def ensure_list(value: Any) -> list[str]:
    """Ensure a value is a list of strings.

    Handles common cases when parsing YAML frontmatter where values
    may be None, a single string, or already a list.

    Args:
        value: Value to convert.

    Returns:
        List of strings. Empty list if value is None.

    Examples:
        >>> ensure_list(None)
        []
        >>> ensure_list("tag")
        ["tag"]
        >>> ensure_list(["a", "b"])
        ["a", "b"]
        >>> ensure_list([1, 2])
        ["1", "2"]
    """
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    return []
