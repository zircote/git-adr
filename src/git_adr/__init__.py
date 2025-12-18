"""Git ADR - Architecture Decision Records management for git repositories.

git-adr stores ADRs in git notes, keeping them invisible in the working tree
but visible in history. This approach:
- Eliminates merge conflicts from sequential numbering
- Associates decisions with implementing commits
- Syncs automatically with regular git operations (when configured)
"""

from __future__ import annotations

__version__ = "0.2.3"
__all__ = ["__version__"]
