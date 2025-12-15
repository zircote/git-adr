"""Wiki synchronization services for git-adr.

This module provides wiki sync functionality:
- GitHub Wiki integration
- GitLab Wiki integration
- Bidirectional sync support
"""

from __future__ import annotations

from git_adr.wiki.service import WikiService, WikiServiceError

__all__ = ["WikiService", "WikiServiceError"]
