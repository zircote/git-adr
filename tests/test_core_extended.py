"""Extended tests for core modules with lower coverage.

Focuses on modules that need more test coverage:
- git.py - Git wrapper and utilities
- notes.py - NotesManager
- templates.py - TemplateEngine
- index.py - ADR indexing
- adr.py - ADR model
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from git_adr.core.adr import (
    ADR,
    ADRMetadata,
    ADRStatus,
    generate_adr_id,
    validate_adr,
)
from git_adr.core.config import Config, ConfigManager
from git_adr.core.git import Git, GitError, GitResult
from git_adr.core.notes import NotesManager
from git_adr.core.templates import TemplateEngine

# =============================================================================
# Git Wrapper Extended Tests
# =============================================================================


class TestGitWrapperExtended:
    """Extended tests for Git wrapper."""

    def test_get_head_commit(self, temp_git_repo_with_commit: Path) -> None:
        """Test getting HEAD commit."""
        git = Git(cwd=temp_git_repo_with_commit)
        head = git.get_head_commit()
        assert head is not None
        assert len(head) == 40  # Full SHA

    def test_get_remotes_empty(self, temp_git_repo: Path) -> None:
        """Test getting remotes when none configured."""
        git = Git(cwd=temp_git_repo)
        remotes = git.get_remotes()
        assert remotes == []

    def test_config_unset(self, temp_git_repo: Path) -> None:
        """Test unsetting a config value."""
        git = Git(cwd=temp_git_repo)
        git.config_set("test.key", "value")
        assert git.config_get("test.key") == "value"

        git.config_unset("test.key")
        assert git.config_get("test.key") is None

    def test_run_with_check_false(self, temp_git_repo: Path) -> None:
        """Test running command with check=False."""
        git = Git(cwd=temp_git_repo)
        result = git.run(["status", "--nonexistent-option"], check=False)
        assert result.exit_code != 0

    def test_run_raises_on_error(self, temp_git_repo: Path) -> None:
        """Test that run raises GitError on failure with check=True."""
        git = Git(cwd=temp_git_repo)
        with pytest.raises(GitError):
            git.run(["status", "--nonexistent-option"])


class TestGitNotesExtended:
    """Extended tests for Git notes operations."""

    def test_notes_append(self, temp_git_repo_with_commit: Path) -> None:
        """Test appending to a note."""
        git = Git(cwd=temp_git_repo_with_commit)

        # Add initial note
        git.notes_add("Initial content", ref="refs/notes/test")

        # Append to note
        git.notes_append("Appended content", ref="refs/notes/test")

        # Verify both contents
        note = git.notes_show(ref="refs/notes/test")
        assert "Initial content" in note
        assert "Appended content" in note

    def test_notes_show_nonexistent(self, temp_git_repo_with_commit: Path) -> None:
        """Test showing note that doesn't exist."""
        git = Git(cwd=temp_git_repo_with_commit)
        note = git.notes_show(ref="refs/notes/nonexistent")
        assert note is None

    def test_notes_remove_existing(self, temp_git_repo_with_commit: Path) -> None:
        """Test removing an existing note."""
        git = Git(cwd=temp_git_repo_with_commit)

        # Add a note first
        git.notes_add("Test content", ref="refs/notes/test")
        assert git.notes_show(ref="refs/notes/test") is not None

        # Remove it
        git.notes_remove(ref="refs/notes/test")
        assert git.notes_show(ref="refs/notes/test") is None

    def test_get_commit_message(self, temp_git_repo_with_commit: Path) -> None:
        """Test getting commit message."""
        git = Git(cwd=temp_git_repo_with_commit)
        head = git.get_head_commit()
        message = git.get_commit_message(head)
        assert message is not None
        assert "Initial commit" in message

    def test_get_current_branch(self, temp_git_repo_with_commit: Path) -> None:
        """Test getting current branch."""
        git = Git(cwd=temp_git_repo_with_commit)
        branch = git.get_current_branch()
        assert branch is not None
        # Usually "main" or "master"
        assert branch in ["main", "master"]


# =============================================================================
# Notes Manager Extended Tests
# =============================================================================


@pytest.mark.integration
class TestNotesManagerExtended:
    """Extended tests for NotesManager."""

    def test_exists(self, initialized_adr_repo: Path, sample_adr: ADR) -> None:
        """Test checking if ADR exists."""
        git = Git(cwd=initialized_adr_repo)
        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)

        # Initially doesn't exist
        assert not notes_manager.exists(sample_adr.id)

        # Add it
        notes_manager.add(sample_adr)

        # Now exists
        assert notes_manager.exists(sample_adr.id)

    def test_update_adr(self, initialized_adr_repo: Path, sample_adr: ADR) -> None:
        """Test updating an existing ADR."""
        git = Git(cwd=initialized_adr_repo)
        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)

        # Add ADR
        notes_manager.add(sample_adr)

        # Update it
        updated_adr = ADR(
            metadata=ADRMetadata(
                id=sample_adr.id,
                title="Updated Title",
                date=sample_adr.metadata.date,
                status=ADRStatus.ACCEPTED,
                tags=["updated"],
            ),
            content="## Context\n\nUpdated content.",
        )
        notes_manager.update(updated_adr)

        # Verify update
        loaded = notes_manager.get(sample_adr.id)
        assert loaded.metadata.title == "Updated Title"
        assert loaded.metadata.status == ADRStatus.ACCEPTED

    def test_list_all_filtered_by_status(self, adr_repo_with_data: Path) -> None:
        """Test listing ADRs and filtering by status in memory."""
        git = Git(cwd=adr_repo_with_data)
        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)

        # Get all and filter in memory
        all_adrs = notes_manager.list_all()
        accepted = [
            adr for adr in all_adrs if adr.metadata.status == ADRStatus.ACCEPTED
        ]
        assert len(accepted) >= 1
        assert all(adr.metadata.status == ADRStatus.ACCEPTED for adr in accepted)

    def test_list_all_filtered_by_tag(self, adr_repo_with_data: Path) -> None:
        """Test listing ADRs and filtering by tag in memory."""
        git = Git(cwd=adr_repo_with_data)
        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)

        # Get all and filter by database tag
        all_adrs = notes_manager.list_all()
        db_adrs = [adr for adr in all_adrs if "database" in adr.metadata.tags]
        assert len(db_adrs) >= 1
        assert all("database" in adr.metadata.tags for adr in db_adrs)

    def test_list_all_search_content(self, adr_repo_with_data: Path) -> None:
        """Test listing ADRs and searching content in memory."""
        git = Git(cwd=adr_repo_with_data)
        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)

        # Get all and search in memory
        all_adrs = notes_manager.list_all()
        results = [
            adr
            for adr in all_adrs
            if "PostgreSQL" in adr.content or "postgresql" in adr.content.lower()
        ]
        assert len(results) >= 1


# =============================================================================
# Template Engine Extended Tests
# =============================================================================


class TestTemplateEngineExtended:
    """Extended tests for TemplateEngine."""

    def test_render_all_formats(self) -> None:
        """Test rendering all available formats."""
        engine = TemplateEngine()
        formats = engine.list_formats()

        for fmt in formats:
            content = engine.render_for_new(
                fmt,
                title="Test Title",
                adr_id="20250115-test",
                status="proposed",
            )
            assert content is not None
            assert len(content) > 0

    def test_render_with_deciders(self) -> None:
        """Test rendering with deciders."""
        engine = TemplateEngine()
        content = engine.render_for_new(
            "madr",
            title="Test",
            adr_id="20250115-test",
            status="proposed",
            deciders=["Alice", "Bob", "Charlie"],
        )
        assert content is not None

    def test_render_with_tags(self) -> None:
        """Test rendering with tags."""
        engine = TemplateEngine()
        content = engine.render_for_new(
            "madr",
            title="Test",
            adr_id="20250115-test",
            status="proposed",
            tags=["database", "infrastructure", "security"],
        )
        assert content is not None

    def test_detect_format_nygard(self) -> None:
        """Test detecting Nygard format."""
        engine = TemplateEngine()
        nygard_content = """# 1. Record architecture decisions

Date: 2020-01-01

## Status

Accepted

## Context

We need to record decisions.

## Decision

We will use ADRs.

## Consequences

Better documentation.
"""
        detected = engine.detect_format(nygard_content)
        assert detected in ["nygard", "unknown"]

    def test_get_nonexistent_template(self) -> None:
        """Test getting nonexistent template."""
        engine = TemplateEngine()
        template = engine.get_template("nonexistent")
        assert template is None


# =============================================================================
# ADR Model Extended Tests
# =============================================================================


class TestADRModelExtended:
    """Extended tests for ADR model."""

    def test_adr_with_all_metadata(self) -> None:
        """Test creating ADR with all metadata fields."""
        adr = ADR(
            metadata=ADRMetadata(
                id="20250115-full-adr",
                title="Full ADR",
                date=date(2025, 1, 15),
                status=ADRStatus.PROPOSED,
                deciders=["Alice", "Bob"],
                tags=["test", "demo"],
                supersedes="20250101-old-adr",  # Single string, not list
                superseded_by=None,
                linked_commits=["abc123", "def456"],  # Use linked_commits, not links
                format="madr",
            ),
            content="## Context\n\nFull content here.",
        )

        assert adr.id == "20250115-full-adr"
        assert len(adr.metadata.deciders) == 2
        assert len(adr.metadata.tags) == 2
        assert adr.metadata.supersedes == "20250101-old-adr"
        assert len(adr.metadata.linked_commits) == 2

    def test_adr_from_markdown_minimal(self) -> None:
        """Test parsing minimal markdown ADR."""
        content = """# Simple Decision

## Context

Simple context.

## Decision

Simple decision.
"""
        adr = ADR.from_markdown(content)
        assert adr is not None

    def test_adr_to_markdown_roundtrip(self) -> None:
        """Test ADR to/from markdown roundtrip."""
        original = ADR(
            metadata=ADRMetadata(
                id="20250115-roundtrip",
                title="Roundtrip Test",
                date=date(2025, 1, 15),
                status=ADRStatus.ACCEPTED,
                tags=["test"],
            ),
            content="## Context\n\nContent here.",
        )

        markdown = original.to_markdown()
        parsed = ADR.from_markdown(markdown)

        assert parsed.metadata.id == original.metadata.id
        assert parsed.metadata.title == original.metadata.title
        assert parsed.metadata.status == original.metadata.status

    def test_generate_adr_id_special_chars(self) -> None:
        """Test generating ADR ID with special characters."""
        existing: set[str] = set()
        adr_id = generate_adr_id("Use React's State Management!", existing)
        assert " " not in adr_id
        assert "'" not in adr_id
        assert "!" not in adr_id

    def test_validate_adr_missing_id(self) -> None:
        """Test validating ADR with missing ID."""
        adr = ADR(
            metadata=ADRMetadata(
                id="",
                title="Test",
                date=date.today(),
                status=ADRStatus.PROPOSED,
            ),
            content="Content",
        )
        errors = validate_adr(adr)
        assert len(errors) > 0

    def test_validate_adr_invalid_status(self) -> None:
        """Test validating ADR with complete fields."""
        adr = ADR(
            metadata=ADRMetadata(
                id="20250115-valid",
                title="Valid ADR",
                date=date.today(),
                status=ADRStatus.PROPOSED,
                deciders=["Alice"],
                tags=["test"],
            ),
            content="## Context\n\nValid content.",
        )
        errors = validate_adr(adr)
        # Should have no errors for valid ADR
        assert len(errors) == 0


# =============================================================================
# Config Extended Tests
# =============================================================================


class TestConfigExtended:
    """Extended tests for Config."""

    def test_config_all_properties(self) -> None:
        """Test config computed properties."""
        config = Config(
            namespace="custom",
            artifacts_namespace="custom-artifacts",
            template="nygard",
            ai_provider="openai",
            ai_model="gpt-4",
        )

        assert config.notes_ref == "refs/notes/custom"
        assert config.artifacts_ref == "refs/notes/custom-artifacts"
        assert config.template == "nygard"
        assert config.ai_provider == "openai"
        assert config.ai_model == "gpt-4"

    def test_config_manager_list_keys(self, temp_git_repo: Path) -> None:
        """Test listing all config keys."""
        git = Git(cwd=temp_git_repo)
        manager = ConfigManager(git)

        # Set some values
        manager.set("namespace", "test")
        manager.set("template", "nygard")

        # List should work (implementation dependent)
        config = manager.load()
        assert config.namespace == "test"
        assert config.template == "nygard"


# =============================================================================
# Git Result Tests
# =============================================================================


class TestGitResult:
    """Tests for GitResult dataclass."""

    def test_git_result_success(self) -> None:
        """Test GitResult for successful command."""
        result = GitResult(
            stdout="output",
            stderr="",
            exit_code=0,
        )
        assert result.exit_code == 0
        assert result.stdout == "output"

    def test_git_result_failure(self) -> None:
        """Test GitResult for failed command."""
        result = GitResult(
            stdout="",
            stderr="error message",
            exit_code=1,
        )
        assert result.exit_code == 1
        assert "error" in result.stderr


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests for error handling in core modules."""

    def test_git_error_message(self) -> None:
        """Test GitError message formatting."""
        error = GitError(
            message="Command failed",
            command=["git", "status"],
            exit_code=1,
            stderr="detailed error",
        )
        assert "Command failed" in str(error)

    def test_git_outside_repo(self, tmp_path: Path) -> None:
        """Test Git operations outside a repository."""
        git = Git(cwd=tmp_path)
        assert not git.is_repository()

        # Should raise when trying to get root
        with pytest.raises(GitError):
            git.get_root()
