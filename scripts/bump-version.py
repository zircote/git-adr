#!/usr/bin/env python3
"""Version bumping utility for git-adr.

Updates version in pyproject.toml, src/git_adr/__init__.py, and .claude-plugin/plugin.json.

Usage:
    ./scripts/bump-version.py [major|minor|patch|VERSION]
    ./scripts/bump-version.py --show

Examples:
    ./scripts/bump-version.py patch        # 0.2.3 -> 0.2.4
    ./scripts/bump-version.py minor        # 0.2.3 -> 0.3.0
    ./scripts/bump-version.py major        # 0.2.3 -> 1.0.0
    ./scripts/bump-version.py 1.0.0-beta.1 # Set explicit version
    ./scripts/bump-version.py --show       # Display current version
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import NamedTuple


class Version(NamedTuple):
    """Semantic version components."""

    major: int
    minor: int
    patch: int
    prerelease: str = ""

    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        return f"{base}{self.prerelease}" if self.prerelease else base

    def bump(self, component: str) -> Version:
        """Bump the specified version component."""
        if component == "major":
            return Version(self.major + 1, 0, 0)
        elif component == "minor":
            return Version(self.major, self.minor + 1, 0)
        elif component == "patch":
            return Version(self.major, self.minor, self.patch + 1)
        else:
            raise ValueError(f"Unknown component: {component}")


# Project root relative to this script
PROJECT_ROOT = Path(__file__).parent.parent
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
INIT_PATH = PROJECT_ROOT / "src" / "git_adr" / "__init__.py"
PLUGIN_PATH = PROJECT_ROOT / ".claude-plugin" / "plugin.json"

# Patterns for version matching
VERSION_PATTERN = re.compile(r"(\d+)\.(\d+)\.(\d+)([-.\w]*)?")
PYPROJECT_VERSION_RE = re.compile(r'^version\s*=\s*"([^"]+)"', re.MULTILINE)
INIT_VERSION_RE = re.compile(r'^__version__\s*=\s*"([^"]+)"', re.MULTILINE)


def parse_version(version_str: str) -> Version:
    """Parse a version string into components."""
    match = VERSION_PATTERN.match(version_str)
    if not match:
        raise ValueError(f"Invalid version format: {version_str}")
    major, minor, patch, prerelease = match.groups()
    return Version(int(major), int(minor), int(patch), prerelease or "")


def get_current_version() -> str:
    """Read current version from pyproject.toml."""
    content = PYPROJECT_PATH.read_text()
    match = PYPROJECT_VERSION_RE.search(content)
    if not match:
        raise RuntimeError("Could not find version in pyproject.toml")
    return match.group(1)


def update_pyproject(new_version: str) -> None:
    """Update version in pyproject.toml."""
    content = PYPROJECT_PATH.read_text()
    updated = PYPROJECT_VERSION_RE.sub(f'version = "{new_version}"', content)
    PYPROJECT_PATH.write_text(updated)


def update_init(new_version: str) -> None:
    """Update version in __init__.py."""
    content = INIT_PATH.read_text()
    updated = INIT_VERSION_RE.sub(f'__version__ = "{new_version}"', content)
    INIT_PATH.write_text(updated)


def update_plugin(new_version: str) -> None:
    """Update version in plugin.json if it exists."""
    if not PLUGIN_PATH.exists():
        return
    data = json.loads(PLUGIN_PATH.read_text())
    data["version"] = new_version
    PLUGIN_PATH.write_text(json.dumps(data, indent=4) + "\n")


def bump_version(component_or_version: str) -> tuple[str, str]:
    """
    Bump version by component or set explicit version.

    Args:
        component_or_version: One of 'major', 'minor', 'patch', or explicit version string

    Returns:
        Tuple of (old_version, new_version)
    """
    old_version = get_current_version()

    if component_or_version in ("major", "minor", "patch"):
        current = parse_version(old_version)
        new = current.bump(component_or_version)
        new_version = str(new)
    else:
        # Validate explicit version format
        parse_version(component_or_version)  # Raises if invalid
        new_version = component_or_version

    # Update all version files
    update_pyproject(new_version)
    update_init(new_version)
    update_plugin(new_version)

    return old_version, new_version


def main() -> int:
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    arg = sys.argv[1]

    if arg in ("--show", "-s", "show"):
        version = get_current_version()
        print(version)
        return 0

    if arg in ("--help", "-h", "help"):
        print(__doc__)
        return 0

    try:
        old, new = bump_version(arg)
        print(f"{old} -> {new}")
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Failed to bump version: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
