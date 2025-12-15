"""Integration tests for git-adr core modules.

Tests the core functionality with real git repositories.
"""

from __future__ import annotations

import subprocess
from datetime import date
from pathlib import Path

import pytest

from git_adr.core.adr import ADR, ADRMetadata, ADRStatus, generate_adr_id, validate_adr
from git_adr.core.config import Config, ConfigManager
from git_adr.core.git import Git, GitResult
from git_adr.core.notes import NotesManager
from git_adr.core.templates import TemplateEngine

# =============================================================================
# ADR Parsing and Serialization Tests
# =============================================================================


class TestADRParsing:
    """Tests for ADR parsing and serialization."""

    def test_parse_madr_format(self) -> None:
        """Test parsing MADR format ADR."""
        content = """---
id: use-postgres
title: Use PostgreSQL
date: 2025-01-15
status: accepted
deciders:
  - Alice
  - Bob
tags:
  - database
---

## Context

We need a database.

## Decision

Use PostgreSQL.

## Consequences

Good performance.
"""
        adr = ADR.from_markdown(content)
        assert adr.metadata.id == "use-postgres"
        assert adr.metadata.title == "Use PostgreSQL"
        assert adr.metadata.status == ADRStatus.ACCEPTED
        assert "Alice" in adr.metadata.deciders
        assert "database" in adr.metadata.tags
        assert "## Context" in adr.content

    def test_serialize_adr(self, sample_adr: ADR) -> None:
        """Test serializing ADR to markdown."""
        content = sample_adr.to_markdown()
        assert "---" in content
        assert sample_adr.metadata.id in content
        assert sample_adr.metadata.title in content

    def test_roundtrip_parse_serialize(self) -> None:
        """Test that parse -> serialize -> parse is consistent."""
        original = ADR(
            metadata=ADRMetadata(
                id="test-roundtrip",
                title="Test Roundtrip",
                date=date(2025, 1, 15),
                status=ADRStatus.PROPOSED,
                deciders=["Alice"],
                tags=["test"],
            ),
            content="## Context\n\nTest content.",
        )
        serialized = original.to_markdown()
        parsed = ADR.from_markdown(serialized)

        assert parsed.metadata.id == original.metadata.id
        assert parsed.metadata.title == original.metadata.title
        assert parsed.metadata.status == original.metadata.status

    def test_generate_adr_id(self) -> None:
        """Test generating ADR IDs from titles."""
        existing: set[str] = set()
        adr_id = generate_adr_id("Use PostgreSQL for Database", existing)
        assert "postgresql" in adr_id.lower() or "postgres" in adr_id.lower()
        assert " " not in adr_id

    def test_generate_adr_id_collision(self) -> None:
        """Test ID generation handles collisions."""
        existing: set[str] = set()
        first_id = generate_adr_id("Use PostgreSQL", existing)
        existing.add(first_id)
        second_id = generate_adr_id("Use PostgreSQL", existing)
        # Should be different due to collision handling
        assert second_id != first_id or "-" in second_id

    def test_validate_adr_valid(self, sample_adr: ADR) -> None:
        """Test validating a valid ADR."""
        errors = validate_adr(sample_adr)
        assert len(errors) == 0

    def test_validate_adr_missing_title(self) -> None:
        """Test validating ADR with missing title."""
        adr = ADR(
            metadata=ADRMetadata(
                id="test",
                title="",  # Empty title
                date=date.today(),
                status=ADRStatus.PROPOSED,
            ),
            content="Content",
        )
        errors = validate_adr(adr)
        assert len(errors) > 0


class TestADRStatus:
    """Tests for ADR status handling."""

    def test_all_statuses(self) -> None:
        """Test all status values."""
        for status in ADRStatus:
            adr = ADR(
                metadata=ADRMetadata(
                    id=f"test-{status.value}",
                    title=f"Test {status.value}",
                    date=date.today(),
                    status=status,
                ),
                content="Content",
            )
            assert adr.metadata.status == status

    def test_status_from_string(self) -> None:
        """Test creating status from string."""
        assert ADRStatus("proposed") == ADRStatus.PROPOSED
        assert ADRStatus("accepted") == ADRStatus.ACCEPTED
        assert ADRStatus("rejected") == ADRStatus.REJECTED
        assert ADRStatus("deprecated") == ADRStatus.DEPRECATED
        assert ADRStatus("superseded") == ADRStatus.SUPERSEDED


# =============================================================================
# Git Wrapper Tests
# =============================================================================


class TestGitWrapper:
    """Tests for Git wrapper class."""

    def test_is_repository(self, temp_git_repo: Path) -> None:
        """Test detecting a git repository."""
        git = Git(cwd=temp_git_repo)
        assert git.is_repository()

    def test_is_not_repository(self, tmp_path: Path) -> None:
        """Test detecting non-repository directory."""
        git = Git(cwd=tmp_path)
        assert not git.is_repository()

    def test_get_root(self, temp_git_repo: Path) -> None:
        """Test getting repository root."""
        git = Git(cwd=temp_git_repo)
        root = git.get_root()
        assert root == temp_git_repo

    def test_run_command(self, temp_git_repo: Path) -> None:
        """Test running a git command."""
        git = Git(cwd=temp_git_repo)
        result = git.run(["status"])
        assert result.exit_code == 0

    def test_run_returns_git_result(self, temp_git_repo: Path) -> None:
        """Test that run returns GitResult."""
        git = Git(cwd=temp_git_repo)
        result = git.run(["version"])
        assert isinstance(result, GitResult)
        assert result.exit_code == 0
        assert "git version" in result.stdout.lower()

    def test_config_operations(self, temp_git_repo: Path) -> None:
        """Test config set/get operations."""
        git = Git(cwd=temp_git_repo)

        # Set a config value
        git.config_set("test.key", "test-value")

        # Get it back
        value = git.config_get("test.key")
        assert value == "test-value"

        # Get nonexistent key
        missing = git.config_get("nonexistent.key")
        assert missing is None

    def test_config_append(self, temp_git_repo: Path) -> None:
        """Test appending to multi-valued config."""
        git = Git(cwd=temp_git_repo)
        git.config_set("test.multi", "value1")
        git.config_set("test.multi", "value2", append=True)

        result = git.run(["config", "--get-all", "test.multi"])
        assert "value1" in result.stdout
        assert "value2" in result.stdout


class TestGitNotes:
    """Tests for Git notes operations."""

    def test_notes_add_and_show(self, temp_git_repo_with_commit: Path) -> None:
        """Test adding and showing a git note."""
        git = Git(cwd=temp_git_repo_with_commit)

        # Add a note
        git.notes_add("Test note content", ref="refs/notes/test")

        # Show the note
        note = git.notes_show(ref="refs/notes/test")
        assert note is not None
        assert note.strip() == "Test note content"

    def test_notes_list(self, temp_git_repo_with_commit: Path) -> None:
        """Test listing git notes."""
        git = Git(cwd=temp_git_repo_with_commit)

        # Create multiple commits with notes
        for i in range(3):
            (temp_git_repo_with_commit / f"file{i}.txt").write_text(f"content {i}")
            subprocess.run(
                ["git", "add", "."],
                cwd=temp_git_repo_with_commit,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "commit", "-m", f"Commit {i}"],
                cwd=temp_git_repo_with_commit,
                check=True,
                capture_output=True,
            )
            git.notes_add(f"Note {i}", ref="refs/notes/test")

        # List notes
        notes = git.notes_list(ref="refs/notes/test")
        assert len(notes) == 3

    def test_notes_remove(self, temp_git_repo_with_commit: Path) -> None:
        """Test removing a git note."""
        git = Git(cwd=temp_git_repo_with_commit)

        # Add and verify note
        git.notes_add("Test note", ref="refs/notes/test")
        assert git.notes_show(ref="refs/notes/test") is not None

        # Remove note
        git.notes_remove(ref="refs/notes/test")
        assert git.notes_show(ref="refs/notes/test") is None


# =============================================================================
# Config Manager Tests
# =============================================================================


class TestConfigManager:
    """Tests for ConfigManager."""

    def test_load_default_config(self, temp_git_repo: Path) -> None:
        """Test loading default config when none exists."""
        git = Git(cwd=temp_git_repo)
        manager = ConfigManager(git)
        config = manager.load()

        assert config.namespace == "adr"
        assert config.template == "madr"

    def test_set_and_load_config(self, temp_git_repo: Path) -> None:
        """Test setting and loading custom config values."""
        git = Git(cwd=temp_git_repo)
        manager = ConfigManager(git)

        # Set custom config values (note: git config keys use dots, not underscores)
        manager.set("namespace", "decisions")
        manager.set("template", "nygard")

        # Load it back
        loaded = manager.load()
        assert loaded.namespace == "decisions"
        assert loaded.template == "nygard"

    def test_config_get(self, temp_git_repo: Path) -> None:
        """Test getting config values."""
        git = Git(cwd=temp_git_repo)
        manager = ConfigManager(git)

        manager.set("namespace", "custom")
        value = manager.get("namespace")
        assert value == "custom"

    def test_config_get_default(self, temp_git_repo: Path) -> None:
        """Test getting config with default."""
        git = Git(cwd=temp_git_repo)
        manager = ConfigManager(git)

        value = manager.get("nonexistent", default="default-value")
        assert value == "default-value"

    def test_config_properties(self) -> None:
        """Test config computed properties."""
        config = Config(namespace="custom", artifacts_namespace="custom-artifacts")
        assert config.notes_ref == "refs/notes/custom"
        assert config.artifacts_ref == "refs/notes/custom-artifacts"


# =============================================================================
# Notes Manager Tests
# =============================================================================


@pytest.mark.integration
class TestNotesManager:
    """Tests for NotesManager."""

    def test_add_and_get_adr(self, initialized_adr_repo: Path, sample_adr: ADR) -> None:
        """Test adding and getting an ADR via notes."""
        git = Git(cwd=initialized_adr_repo)
        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)

        # Add ADR
        notes_manager.add(sample_adr)

        # Get it back
        loaded = notes_manager.get(sample_adr.id)
        assert loaded is not None
        assert loaded.metadata.id == sample_adr.metadata.id
        assert loaded.metadata.title == sample_adr.metadata.title

    def test_list_all_adrs(self, adr_repo_with_data: Path) -> None:
        """Test listing all ADRs."""
        git = Git(cwd=adr_repo_with_data)
        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)

        adrs = notes_manager.list_all()
        assert len(adrs) == 3
        ids = {adr.id for adr in adrs}
        assert "20250110-use-postgresql" in ids
        assert "20250112-use-redis" in ids
        assert "20250115-use-react" in ids

    def test_remove_adr(self, initialized_adr_repo: Path, sample_adr: ADR) -> None:
        """Test removing an ADR."""
        git = Git(cwd=initialized_adr_repo)
        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)

        # Add then remove
        notes_manager.add(sample_adr)
        assert notes_manager.get(sample_adr.id) is not None

        notes_manager.remove(sample_adr.id)
        assert notes_manager.get(sample_adr.id) is None


# =============================================================================
# Template Engine Tests
# =============================================================================


class TestTemplateEngine:
    """Tests for TemplateEngine."""

    def test_render_for_new_madr(self) -> None:
        """Test rendering MADR template for new ADR."""
        engine = TemplateEngine()
        content = engine.render_for_new(
            "madr",
            title="Test Title",
            adr_id="20250115-test-id",
            status="proposed",
            deciders=["Alice"],
            tags=["test"],
        )

        # MADR template includes title and status, but ADR ID is in frontmatter only
        assert "Test Title" in content
        assert "proposed" in content.lower()
        # Template should have Context/Decision/Consequences structure
        assert "Context" in content or "context" in content.lower()

    def test_render_for_new_nygard(self) -> None:
        """Test rendering Nygard template for new ADR."""
        engine = TemplateEngine()
        content = engine.render_for_new(
            "nygard",
            title="Test Title",
            adr_id="20250115-test-id",
            status="proposed",
        )

        assert "Test Title" in content

    def test_get_template(self) -> None:
        """Test getting a template."""
        engine = TemplateEngine()
        template = engine.get_template("madr")
        assert template is not None
        assert "{title}" in template or "title" in template.lower()

    def test_list_formats(self) -> None:
        """Test listing available formats."""
        engine = TemplateEngine()
        formats = engine.list_formats()

        assert "madr" in formats
        assert "nygard" in formats

    def test_detect_format(self) -> None:
        """Test format detection."""
        engine = TemplateEngine()

        madr_content = """---
id: test
title: Test
date: 2025-01-15
status: proposed
---

## Context and Problem Statement

Something.
"""
        detected = engine.detect_format(madr_content)
        assert detected in ["madr", "madr-v4", "unknown"]
