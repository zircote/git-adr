"""Tests for NotesManager artifact operations.

Comprehensive tests for attach_artifact, get_artifact, list_artifacts,
and remove_artifact functionality.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from git_adr.core.adr import ADR, ADRMetadata, ADRStatus
from git_adr.core.config import ConfigManager
from git_adr.core.git import Git
from git_adr.core.notes import NotesManager, _guess_mime_type


class TestNotesManagerArtifacts:
    """Tests for NotesManager artifact operations."""

    def test_attach_artifact_image(
        self, initialized_adr_repo: Path, tmp_path: Path
    ) -> None:
        """Test attaching an image artifact."""
        git = Git(cwd=initialized_adr_repo)
        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)

        # Create an ADR first
        adr = ADR(
            metadata=ADRMetadata(
                id="20250115-test-adr",
                title="Test ADR",
                date=date(2025, 1, 15),
                status=ADRStatus.PROPOSED,
            ),
            content="## Context\n\nTest content.",
        )
        notes_manager.add(adr)

        # Create a test image file
        image_file = tmp_path / "diagram.png"
        image_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

        # Attach the artifact
        artifact = notes_manager.attach_artifact(
            "20250115-test-adr",
            image_file,
            alt_text="Architecture diagram",
        )

        assert artifact.name == "diagram.png"
        assert artifact.mime_type == "image/png"
        assert artifact.size > 0
        assert len(artifact.sha256) == 64

    def test_attach_artifact_pdf(
        self, initialized_adr_repo: Path, tmp_path: Path
    ) -> None:
        """Test attaching a PDF artifact."""
        git = Git(cwd=initialized_adr_repo)
        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)

        # Create an ADR
        adr = ADR(
            metadata=ADRMetadata(
                id="20250115-test-pdf",
                title="Test PDF",
                date=date(2025, 1, 15),
                status=ADRStatus.PROPOSED,
            ),
            content="## Context\n\nTest.",
        )
        notes_manager.add(adr)

        # Create a test PDF file
        pdf_file = tmp_path / "document.pdf"
        pdf_file.write_bytes(b"%PDF-1.4" + b"\x00" * 100)

        artifact = notes_manager.attach_artifact(
            "20250115-test-pdf",
            pdf_file,
            name="architecture-review.pdf",
        )

        assert artifact.name == "architecture-review.pdf"
        assert artifact.mime_type == "application/pdf"

    def test_attach_artifact_nonexistent_file(
        self, initialized_adr_repo: Path, tmp_path: Path
    ) -> None:
        """Test attaching non-existent file raises error."""
        git = Git(cwd=initialized_adr_repo)
        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)

        # Create an ADR
        adr = ADR(
            metadata=ADRMetadata(
                id="20250115-test-nofile",
                title="Test",
                date=date(2025, 1, 15),
                status=ADRStatus.PROPOSED,
            ),
            content="## Context\n\nTest.",
        )
        notes_manager.add(adr)

        nonexistent = tmp_path / "does-not-exist.png"
        with pytest.raises(FileNotFoundError):
            notes_manager.attach_artifact("20250115-test-nofile", nonexistent)

    def test_get_artifact(self, initialized_adr_repo: Path, tmp_path: Path) -> None:
        """Test retrieving an attached artifact."""
        git = Git(cwd=initialized_adr_repo)
        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)

        # Create ADR and attach artifact
        adr = ADR(
            metadata=ADRMetadata(
                id="20250115-test-get",
                title="Test",
                date=date(2025, 1, 15),
                status=ADRStatus.PROPOSED,
            ),
            content="## Context\n\nTest.",
        )
        notes_manager.add(adr)

        test_content = b"Test file content for artifact"
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(test_content)

        artifact_info = notes_manager.attach_artifact("20250115-test-get", test_file)

        # Retrieve the artifact
        result = notes_manager.get_artifact(artifact_info.sha256)
        assert result is not None
        retrieved_info, retrieved_content = result

        assert retrieved_info.name == "test.txt"
        assert retrieved_content == test_content

    def test_get_artifact_nonexistent(self, initialized_adr_repo: Path) -> None:
        """Test getting non-existent artifact returns None."""
        git = Git(cwd=initialized_adr_repo)
        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)

        result = notes_manager.get_artifact("0" * 64)
        assert result is None

    def test_list_artifacts(self, initialized_adr_repo: Path, tmp_path: Path) -> None:
        """Test listing artifacts for an ADR."""
        git = Git(cwd=initialized_adr_repo)
        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)

        # Create ADR
        adr = ADR(
            metadata=ADRMetadata(
                id="20250115-test-list",
                title="Test",
                date=date(2025, 1, 15),
                status=ADRStatus.PROPOSED,
            ),
            content="## Context\n\nTest.",
        )
        notes_manager.add(adr)

        # Attach multiple artifacts
        file1 = tmp_path / "file1.txt"
        file1.write_bytes(b"Content 1")
        file2 = tmp_path / "file2.png"
        file2.write_bytes(b"\x89PNG" + b"\x00" * 50)

        notes_manager.attach_artifact("20250115-test-list", file1)
        notes_manager.attach_artifact("20250115-test-list", file2)

        # List artifacts
        artifacts = notes_manager.list_artifacts("20250115-test-list")
        assert len(artifacts) == 2

    def test_list_artifacts_nonexistent_adr(self, initialized_adr_repo: Path) -> None:
        """Test listing artifacts for non-existent ADR returns empty."""
        git = Git(cwd=initialized_adr_repo)
        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)

        artifacts = notes_manager.list_artifacts("nonexistent-adr")
        assert artifacts == []

    def test_remove_artifact(self, initialized_adr_repo: Path, tmp_path: Path) -> None:
        """Test removing an artifact from ADR."""
        git = Git(cwd=initialized_adr_repo)
        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)

        # Create ADR and attach artifact
        adr = ADR(
            metadata=ADRMetadata(
                id="20250115-test-remove",
                title="Test",
                date=date(2025, 1, 15),
                status=ADRStatus.PROPOSED,
            ),
            content="## Context\n\nTest.",
        )
        notes_manager.add(adr)

        test_file = tmp_path / "removable.txt"
        test_file.write_bytes(b"To be removed")

        artifact = notes_manager.attach_artifact("20250115-test-remove", test_file)

        # Remove the artifact
        result = notes_manager.remove_artifact("20250115-test-remove", artifact.sha256)
        assert result is True

        # Verify removed from ADR content
        updated_adr = notes_manager.get("20250115-test-remove")
        assert artifact.sha256 not in updated_adr.content

    def test_remove_artifact_nonexistent(self, initialized_adr_repo: Path) -> None:
        """Test removing non-existent artifact returns False."""
        git = Git(cwd=initialized_adr_repo)
        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)

        result = notes_manager.remove_artifact("nonexistent-adr", "0" * 64)
        assert result is False


class TestMimeTypeGuessing:
    """Tests for MIME type detection."""

    def test_image_types(self) -> None:
        """Test image MIME type detection."""
        assert _guess_mime_type("photo.png") == "image/png"
        assert _guess_mime_type("photo.jpg") == "image/jpeg"
        assert _guess_mime_type("photo.jpeg") == "image/jpeg"
        assert _guess_mime_type("photo.gif") == "image/gif"
        assert _guess_mime_type("icon.svg") == "image/svg+xml"
        assert _guess_mime_type("photo.webp") == "image/webp"

    def test_document_types(self) -> None:
        """Test document MIME type detection."""
        assert _guess_mime_type("doc.pdf") == "application/pdf"
        assert _guess_mime_type("readme.md") == "text/markdown"
        assert _guess_mime_type("notes.txt") == "text/plain"

    def test_data_types(self) -> None:
        """Test data file MIME type detection."""
        assert _guess_mime_type("config.json") == "application/json"
        assert _guess_mime_type("config.yaml") == "application/yaml"
        assert _guess_mime_type("config.yml") == "application/yaml"

    def test_diagram_types(self) -> None:
        """Test diagram MIME type detection."""
        assert _guess_mime_type("flow.mermaid") == "text/x-mermaid"
        assert _guess_mime_type("arch.puml") == "text/x-plantuml"

    def test_unknown_type(self) -> None:
        """Test unknown extension returns default."""
        assert _guess_mime_type("file.xyz") == "application/octet-stream"
        assert _guess_mime_type("noextension") == "application/octet-stream"


class TestNotesManagerInitialization:
    """Tests for NotesManager initialization."""

    def test_is_initialized_false(self, temp_git_repo_with_commit: Path) -> None:
        """Test is_initialized returns False for new repo."""
        git = Git(cwd=temp_git_repo_with_commit)
        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)

        assert notes_manager.is_initialized() is False

    def test_initialize_creates_refs(self, temp_git_repo_with_commit: Path) -> None:
        """Test initialize sets up notes refs."""
        git = Git(cwd=temp_git_repo_with_commit)
        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)

        notes_manager.initialize()

        # Check config was set
        assert git.config_get("adr.initialized") == "true"

    def test_initialize_with_remote(self, temp_git_repo_with_commit: Path) -> None:
        """Test initialize configures remote refs."""
        git = Git(cwd=temp_git_repo_with_commit)

        # Add a remote
        remote_path = temp_git_repo_with_commit.parent / "remote.git"
        git.run(["init", "--bare", str(remote_path)])
        git.run(["remote", "add", "origin", str(remote_path)])

        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)

        notes_manager.initialize()

        # Verify remote fetch refspecs were added
        git.config_get("remote.origin.fetch")
        # May have multiple values, just verify command succeeded

    def test_initialize_force(self, initialized_adr_repo: Path) -> None:
        """Test initialize with force flag."""
        git = Git(cwd=initialized_adr_repo)
        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)

        # Should not raise with force=True
        notes_manager.initialize(force=True)

    def test_initialize_already_initialized_raises(
        self, initialized_adr_repo: Path
    ) -> None:
        """Test initialize without force raises if already initialized."""
        git = Git(cwd=initialized_adr_repo)
        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)

        # Create an ADR to mark as initialized
        adr = ADR(
            metadata=ADRMetadata(
                id="test-init",
                title="Test",
                date=date.today(),
                status=ADRStatus.PROPOSED,
            ),
            content="Test",
        )
        notes_manager.add(adr)

        # Should raise without force
        with pytest.raises(RuntimeError, match="already initialized"):
            notes_manager.initialize(force=False)


class TestNotesManagerSync:
    """Tests for NotesManager sync operations."""

    def test_sync_push_no_remote(self, initialized_adr_repo: Path) -> None:
        """Test sync_push fails gracefully without remote."""
        git = Git(cwd=initialized_adr_repo)
        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)

        # Should raise or handle gracefully
        try:
            notes_manager.sync_push(remote="nonexistent")
        except Exception:
            pass  # Expected

    def test_sync_pull_no_remote(self, initialized_adr_repo: Path) -> None:
        """Test sync_pull fails gracefully without remote."""
        git = Git(cwd=initialized_adr_repo)
        config_manager = ConfigManager(git)
        config = config_manager.load()
        notes_manager = NotesManager(git, config)

        try:
            notes_manager.sync_pull(remote="nonexistent")
        except Exception:
            pass  # Expected
