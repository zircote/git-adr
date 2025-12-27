"""Tests for the git-adr CLI."""

from __future__ import annotations

from git_adr import __version__


def test_version() -> None:
    """Test that version is defined and follows semver pattern."""
    import re

    assert re.match(r"^\d+\.\d+\.\d+", __version__), (
        f"Version {__version__} doesn't match semver"
    )
