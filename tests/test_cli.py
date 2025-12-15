"""Tests for the git-adr CLI."""

from __future__ import annotations

from git_adr import __version__


def test_version() -> None:
    """Test that version is defined."""
    assert __version__ == "0.1.0"
