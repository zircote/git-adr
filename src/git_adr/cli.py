"""Command-line interface for git-adr."""

from __future__ import annotations

import sys
from typing import NoReturn


def main() -> NoReturn:
    """Entry point for the git-adr CLI."""
    print("git-adr: Architecture Decision Records for git")
    print("Usage: git adr <command> [options]")
    print()
    print("Commands:")
    print("  init      Initialize ADR directory in repository")
    print("  new       Create a new ADR")
    print("  list      List all ADRs")
    print("  show      Show an ADR")
    print("  link      Link ADRs together")
    print("  generate  Generate documentation from ADRs")
    sys.exit(0)


if __name__ == "__main__":
    main()
