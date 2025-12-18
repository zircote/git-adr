"""Tests for shared command utilities.

Tests the helper functions in git_adr.commands._shared that
reduce code duplication across command implementations.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import typer

from git_adr.commands._shared import CommandContext, setup_command_context
from git_adr.core import ConfigManager, NotesManager
from git_adr.core.index import IndexManager


class TestSetupCommandContext:
    """Tests for setup_command_context helper function."""

    def test_setup_in_non_git_repo(self, tmp_path: Path) -> None:
        """Test that setup_command_context fails in non-git directory."""
        with pytest.raises(typer.Exit) as exc_info:
            setup_command_context(cwd=tmp_path)
        assert exc_info.value.exit_code == 1

    def test_setup_in_uninitialized_repo(self, temp_git_repo: Path) -> None:
        """Test that setup_command_context fails in uninitialized git-adr repo."""
        with pytest.raises(typer.Exit) as exc_info:
            setup_command_context(cwd=temp_git_repo)
        assert exc_info.value.exit_code == 1

    def test_setup_in_initialized_repo(self, initialized_adr_repo: Path) -> None:
        """Test that setup_command_context succeeds in initialized repo."""
        ctx = setup_command_context(cwd=initialized_adr_repo)

        # Verify all components are initialized
        assert ctx.git is not None
        assert ctx.config_manager is not None
        assert ctx.config is not None
        assert ctx.notes_manager is not None
        assert ctx.index_manager is None  # Not requested by default

    def test_setup_with_index_manager(self, initialized_adr_repo: Path) -> None:
        """Test that setup_command_context creates IndexManager when requested."""
        ctx = setup_command_context(cwd=initialized_adr_repo, require_index=True)

        assert ctx.index_manager is not None
        assert isinstance(ctx.index_manager, IndexManager)

    def test_setup_uses_current_directory_by_default(
        self, initialized_adr_repo: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that setup_command_context uses current directory when cwd is None."""
        # Change to initialized repo directory
        monkeypatch.chdir(initialized_adr_repo)

        ctx = setup_command_context()

        assert ctx.git.cwd == initialized_adr_repo

    def test_command_context_dataclass(self, initialized_adr_repo: Path) -> None:
        """Test CommandContext dataclass structure."""
        ctx = setup_command_context(cwd=initialized_adr_repo)

        # Verify it's a proper dataclass with expected attributes
        assert isinstance(ctx, CommandContext)
        assert hasattr(ctx, "git")
        assert hasattr(ctx, "config_manager")
        assert hasattr(ctx, "config")
        assert hasattr(ctx, "notes_manager")
        assert hasattr(ctx, "index_manager")

        # Verify types
        assert isinstance(ctx.config_manager, ConfigManager)
        assert isinstance(ctx.notes_manager, NotesManager)
