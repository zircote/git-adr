"""Shared utilities for git-adr commands.

This module provides common functionality used across multiple commands,
reducing code duplication and ensuring consistency.
"""

from __future__ import annotations

from git_adr.core import ADRStatus

# Status-to-style mapping for Rich console output
# Used by list, search, and show commands
STATUS_STYLES: dict[ADRStatus, str] = {
    ADRStatus.DRAFT: "dim",
    ADRStatus.PROPOSED: "yellow",
    ADRStatus.ACCEPTED: "green",
    ADRStatus.REJECTED: "red",
    ADRStatus.DEPRECATED: "dim red",
    ADRStatus.SUPERSEDED: "dim",
}


def get_status_style(status: ADRStatus) -> str:
    """Get the Rich style for an ADR status.

    Args:
        status: ADR status.

    Returns:
        Rich style name for the status.
    """
    return STATUS_STYLES.get(status, "default")
