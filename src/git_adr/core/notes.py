"""Notes Manager for git-adr.

This module provides the high-level interface for ADR storage in git notes.
ADRs are attached to the repository's root tree object, which provides
stability across rebase and amend operations.
"""

from __future__ import annotations

import contextlib
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from git_adr.core.adr import ADR, ADRMetadata
from git_adr.core.git import GitError

if TYPE_CHECKING:
    from git_adr.core.config import Config
    from git_adr.core.git import Git


# Special object ID for the ADR index note
INDEX_OBJECT_ID = "0" * 40  # Null SHA as index anchor


@dataclass
class ArtifactInfo:
    """Information about an attached artifact.

    Attributes:
        name: Filename of the artifact.
        sha256: Content hash for deduplication.
        size: Size in bytes.
        mime_type: MIME type of the artifact.
        alt_text: Alternative text (for images).
    """

    name: str
    sha256: str
    size: int
    mime_type: str = "application/octet-stream"
    alt_text: str = ""


class NotesManager:
    """High-level manager for ADR notes operations.

    This class provides the primary interface for storing and retrieving
    ADRs from git notes. It handles:
    - ADR storage in refs/notes/adr
    - Artifact storage in refs/notes/adr-artifacts
    - Index management for fast queries
    """

    def __init__(self, git: Git, config: Config) -> None:
        """Initialize the notes manager.

        Args:
            git: Git executor instance.
            config: Configuration instance.
        """
        self._git = git
        self._config = config

    @property
    def adr_ref(self) -> str:
        """Get the git notes reference for ADRs."""
        return self._config.notes_ref

    @property
    def artifacts_ref(self) -> str:
        """Get the git notes reference for artifacts."""
        return self._config.artifacts_ref

    # =========================================================================
    # Initialization
    # =========================================================================

    def is_initialized(self) -> bool:
        """Check if git-adr is initialized in this repository.

        Checks the adr.initialized config flag set by `git adr init`.
        This is more reliable than checking for notes existence because:
        - A freshly initialized repo has no notes yet
        - Notes may not be fetched from remote yet

        Returns:
            True if initialized, False otherwise.
        """
        # Check the initialization marker set by init command
        initialized = self._git.config_get("adr.initialized")
        return initialized == "true"

    def initialize(self, *, force: bool = False) -> None:
        """Initialize git-adr in the repository.

        This sets up:
        - Notes namespace configuration
        - Fetch/push refspecs for notes sync
        - Notes rewrite configuration for rebase safety

        Args:
            force: If True, reinitialize even if already initialized.

        Raises:
            RuntimeError: If already initialized and force=False.
        """
        if self.is_initialized() and not force:
            raise RuntimeError(
                "git-adr is already initialized. Use --force to reinitialize."
            )

        # Configure notes fetch/push for remotes
        remotes = self._git.get_remotes()
        for remote in remotes:
            self._configure_remote_notes(remote)

        # Configure notes rewrite behavior for rebase safety
        self._git.config_set("notes.rewriteRef", self.adr_ref)
        self._git.config_set("notes.rewrite.rebase", "true")
        self._git.config_set("notes.rewrite.amend", "true")

        # Store initialization marker
        self._git.config_set("adr.initialized", "true")

    def _configure_remote_notes(self, remote: str) -> None:
        """Configure a remote for notes fetch.

        This method is idempotent - it checks for existing configuration
        before adding to prevent duplicate entries.

        Note: We only configure fetch refspecs, not push. Push refspecs cause
        bare `git push` to fail if the notes refs don't exist locally yet.
        The `git adr sync push` command handles pushes explicitly.

        Args:
            remote: Remote name to configure.
        """
        fetch_key = f"remote.{remote}.fetch"

        # Get all existing values for idempotent configuration
        existing_fetch = self._git.config_get_all(fetch_key)

        # Add fetch refspec for ADR notes (if not already present)
        fetch_spec = f"+{self.adr_ref}:{self.adr_ref}"
        if fetch_spec not in existing_fetch:
            self._git.config_add(fetch_key, fetch_spec)

        # Add fetch refspec for artifacts (if not already present)
        artifacts_fetch_spec = f"+{self.artifacts_ref}:{self.artifacts_ref}"
        if artifacts_fetch_spec not in existing_fetch:
            self._git.config_add(fetch_key, artifacts_fetch_spec)

    # =========================================================================
    # ADR Operations
    # =========================================================================

    def add(self, adr: ADR, *, update_index: bool = True) -> str:
        """Add a new ADR to git notes.

        Args:
            adr: ADR to store.
            update_index: If True, update the index after adding.

        Returns:
            The ADR ID.
        """
        # Get root tree as attachment point
        self._git.get_root_tree()

        # Generate note object ID from ADR ID
        obj_id = self._adr_id_to_object(adr.id)

        # Serialize ADR to markdown
        content = adr.to_markdown()

        # Store the note
        self._git.notes_add(
            message=content,
            obj=obj_id,
            ref=self.adr_ref,
            force=True,  # Allow update if exists
        )

        if update_index:
            self._update_index(adr.metadata, action="add")

        return adr.id

    def get(self, adr_id: str) -> ADR | None:
        """Get an ADR by ID.

        Args:
            adr_id: ADR ID to retrieve.

        Returns:
            ADR instance, or None if not found.
        """
        obj_id = self._adr_id_to_object(adr_id)
        content = self._git.notes_show(obj_id, ref=self.adr_ref)

        if content is None:
            return None

        try:
            adr = ADR.from_markdown(content)
            return adr
        except ValueError:
            return None

    def update(self, adr: ADR, *, update_index: bool = True) -> None:
        """Update an existing ADR.

        Args:
            adr: ADR with updated content.
            update_index: If True, update the index after updating.
        """
        # Same as add since notes_add with force=True overwrites
        self.add(adr, update_index=update_index)

    def remove(self, adr_id: str, *, update_index: bool = True) -> bool:
        """Remove an ADR.

        Args:
            adr_id: ADR ID to remove.
            update_index: If True, update the index after removing.

        Returns:
            True if removed, False if ADR didn't exist.
        """
        obj_id = self._adr_id_to_object(adr_id)
        result = self._git.notes_remove(obj_id, ref=self.adr_ref)

        if result and update_index:
            self._update_index_remove(adr_id)

        return result

    def list_all(self) -> list[ADR]:
        """List all ADRs.

        Uses batch fetching to retrieve all ADR content in a single
        subprocess call, reducing N+1 subprocess overhead to O(2).

        Returns:
            List of all ADRs in the repository.
        """
        notes = self._git.notes_list(self.adr_ref)

        # Filter out index and collect note SHAs for batch retrieval
        note_shas = [
            note_sha for note_sha, obj_sha in notes if obj_sha != INDEX_OBJECT_ID
        ]

        if not note_shas:
            return []

        # Batch fetch all note contents in a single subprocess call
        contents = self._git.cat_file_batch(note_shas)

        adrs: list[ADR] = []
        for note_sha in note_shas:
            content = contents.get(note_sha)
            if content:
                try:
                    adr = ADR.from_markdown(content)
                    adrs.append(adr)
                except ValueError:
                    continue

        return adrs

    def exists(self, adr_id: str) -> bool:
        """Check if an ADR exists.

        Args:
            adr_id: ADR ID to check.

        Returns:
            True if exists, False otherwise.
        """
        obj_id = self._adr_id_to_object(adr_id)
        content = self._git.notes_show(obj_id, ref=self.adr_ref)
        return content is not None

    # =========================================================================
    # Artifact Operations
    # =========================================================================

    def attach_artifact(
        self,
        adr_id: str,
        file_path: Path,
        *,
        name: str | None = None,
        alt_text: str = "",
    ) -> ArtifactInfo:
        """Attach a file artifact to an ADR.

        Args:
            adr_id: ADR ID to attach to.
            file_path: Path to the file to attach.
            name: Override filename (default: original filename).
            alt_text: Alt text for images.

        Returns:
            Artifact info with hash and size.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the file is too large.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Check size limits
        size = file_path.stat().st_size
        if size > self._config.artifact_max_size:
            max_mb = self._config.artifact_max_size / (1024 * 1024)
            raise ValueError(f"File too large. Maximum size: {max_mb:.1f}MB")

        # Calculate content hash
        content = file_path.read_bytes()
        sha256 = hashlib.sha256(content).hexdigest()

        # Determine filename
        filename = name or file_path.name

        # Determine MIME type (basic detection)
        mime_type = _guess_mime_type(filename)

        # Create artifact info
        artifact = ArtifactInfo(
            name=filename,
            sha256=sha256,
            size=size,
            mime_type=mime_type,
            alt_text=alt_text,
        )

        # Store artifact in artifacts namespace
        # Key is the SHA256 hash for deduplication
        artifact_obj = self._artifact_hash_to_object(sha256)

        # Store as base64-encoded for binary safety
        import base64

        encoded = base64.b64encode(content).decode("ascii")

        artifact_note = (
            f"name: {filename}\n"
            f"sha256: {sha256}\n"
            f"size: {size}\n"
            f"mime_type: {mime_type}\n"
            f"alt_text: {alt_text}\n"
            f"---\n"
            f"{encoded}"
        )

        self._git.notes_add(
            message=artifact_note,
            obj=artifact_obj,
            ref=self.artifacts_ref,
            force=True,
        )

        # Update ADR metadata with artifact reference
        adr = self.get(adr_id)
        if adr:
            # Add artifact to ADR content (as markdown reference)
            artifact_ref = f"\n![{alt_text or filename}](artifact:{sha256})\n"
            if artifact_ref not in adr.content:
                adr = ADR(
                    metadata=adr.metadata,
                    content=adr.content + artifact_ref,
                )
                self.update(adr, update_index=False)

        return artifact

    def get_artifact(self, sha256: str) -> tuple[ArtifactInfo, bytes] | None:
        """Get an artifact by its content hash.

        Args:
            sha256: Content hash of the artifact.

        Returns:
            Tuple of (artifact_info, content), or None if not found.
        """
        import base64

        artifact_obj = self._artifact_hash_to_object(sha256)
        note_content = self._git.notes_show(artifact_obj, ref=self.artifacts_ref)

        if note_content is None:
            return None

        # Parse artifact note
        lines = note_content.split("\n")
        metadata: dict[str, str] = {}
        content_start = 0

        for i, line in enumerate(lines):
            if line == "---":
                content_start = i + 1
                break
            if ":" in line:
                key, _, value = line.partition(":")
                metadata[key.strip()] = value.strip()

        # Decode content
        encoded_content = "\n".join(lines[content_start:])
        content = base64.b64decode(encoded_content)

        artifact = ArtifactInfo(
            name=metadata.get("name", "unknown"),
            sha256=metadata.get("sha256", sha256),
            size=int(metadata.get("size", len(content))),
            mime_type=metadata.get("mime_type", "application/octet-stream"),
            alt_text=metadata.get("alt_text", ""),
        )

        return artifact, content

    def list_artifacts(self, adr_id: str) -> list[ArtifactInfo]:
        """List artifacts attached to an ADR.

        Args:
            adr_id: ADR ID.

        Returns:
            List of artifact info.
        """
        adr = self.get(adr_id)
        if adr is None:
            return []

        # Find artifact references in content
        import re

        artifact_refs = re.findall(r"artifact:([a-f0-9]{64})", adr.content)

        artifacts: list[ArtifactInfo] = []
        for sha256 in artifact_refs:
            result = self.get_artifact(sha256)
            if result:
                artifacts.append(result[0])

        return artifacts

    def remove_artifact(self, adr_id: str, sha256: str) -> bool:
        """Remove an artifact reference from an ADR.

        Note: The artifact blob remains in git (garbage collected later).

        Args:
            adr_id: ADR ID.
            sha256: Artifact content hash.

        Returns:
            True if removed, False if not found.
        """
        import re

        adr = self.get(adr_id)
        if adr is None:
            return False

        # Remove artifact references from content
        pattern = rf"!\[[^\]]*\]\(artifact:{sha256}\)\n?"
        new_content = re.sub(pattern, "", adr.content)

        if new_content != adr.content:
            adr = ADR(metadata=adr.metadata, content=new_content)
            self.update(adr, update_index=False)
            return True

        return False

    # =========================================================================
    # Sync Operations
    # =========================================================================

    def sync_push(
        self,
        remote: str = "origin",
        *,
        force: bool = False,
        timeout: int | None = None,
    ) -> None:
        """Push ADR notes to a remote.

        Args:
            remote: Remote name.
            force: If True, force push.
            timeout: Optional timeout in seconds for the push operation.
        """
        # Convert int timeout to float for git operations
        timeout_float = float(timeout) if timeout is not None else None

        # Push ADR notes (must exist)
        self._git.push_notes(remote, self.adr_ref, force=force, timeout=timeout_float)

        # Only push artifacts ref if it exists locally
        try:
            self._git.run(["rev-parse", "--verify", self.artifacts_ref], check=True)
            self._git.push_notes(
                remote, self.artifacts_ref, force=force, timeout=timeout_float
            )
        except GitError:
            # Artifacts ref doesn't exist yet - nothing to push
            pass

    def sync_pull(
        self,
        remote: str = "origin",
        *,
        merge_strategy: str = "union",
    ) -> None:
        """Pull ADR notes from a remote.

        Args:
            remote: Remote name.
            merge_strategy: Strategy for merging conflicts.
        """
        # Fetch ADR notes
        self._git.fetch_notes(remote, self.adr_ref)

        # Try to fetch artifacts ref (may not exist on remote)
        with contextlib.suppress(GitError):
            self._git.fetch_notes(remote, self.artifacts_ref)

        # Notes are automatically merged by git during fetch
        # The strategy is configured via notes.mergeStrategy

    # =========================================================================
    # Internal Helpers
    # =========================================================================

    def _adr_id_to_object(self, adr_id: str) -> str:
        """Convert an ADR ID to a git object ID for notes.

        We use a deterministic hash of the ADR ID to create a stable
        object reference that can hold the note.

        Args:
            adr_id: ADR ID.

        Returns:
            Object ID for the note.
        """
        # Hash the ADR ID to create a pseudo-object ID.
        # We use SHA1 here for git compatibility (git uses SHA1 for object IDs).
        # Security note: This is NOT used for cryptographic security, only for
        # generating unique, deterministic identifiers. Collision resistance is
        # not critical since we control the input format (adr_id is validated).
        hash_input = f"git-adr:{adr_id}".encode()
        return hashlib.sha1(hash_input, usedforsecurity=False).hexdigest()

    def _artifact_hash_to_object(self, sha256: str) -> str:
        """Convert an artifact hash to a git object ID for notes.

        We use a deterministic hash of the artifact's SHA-256 to create a stable
        object reference that can hold the artifact note in git.

        Args:
            sha256: Content hash (SHA-256) of the artifact.

        Returns:
            Object ID for the artifact note (SHA-1 hash, 40-char hex).
        """
        # Hash the artifact SHA-256 to create a pseudo-object ID.
        # We use SHA1 here for git compatibility (git uses SHA1 for object IDs).
        # Security note: This is NOT used for cryptographic security, only for
        # generating unique, deterministic identifiers. Collision resistance is
        # not critical since the input is already a SHA-256 hash (64 hex chars).
        # The artifact content itself is verified using SHA-256 (line 309).
        hash_input = f"git-adr-artifact:{sha256}".encode()
        return hashlib.sha1(hash_input, usedforsecurity=False).hexdigest()

    def _update_index(
        self,
        metadata: ADRMetadata,
        action: str = "add",
    ) -> None:
        """Update the ADR index with new/updated metadata.

        The index is stored as a special note for fast listing.

        Args:
            metadata: ADR metadata to index.
            action: "add" or "update".
        """
        # For now, we don't maintain a separate index - list_all reads all notes
        # This could be optimized later with a dedicated index note
        pass

    def _update_index_remove(self, adr_id: str) -> None:
        """Remove an ADR from the index.

        Args:
            adr_id: ADR ID to remove.
        """
        # Placeholder for index optimization
        pass


def _guess_mime_type(filename: str) -> str:
    """Guess MIME type from filename.

    Args:
        filename: Filename to check.

    Returns:
        MIME type string.
    """
    extension = Path(filename).suffix.lower()
    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
        ".webp": "image/webp",
        ".pdf": "application/pdf",
        ".md": "text/markdown",
        ".txt": "text/plain",
        ".json": "application/json",
        ".yaml": "application/yaml",
        ".yml": "application/yaml",
        ".mermaid": "text/x-mermaid",
        ".puml": "text/x-plantuml",
    }
    return mime_types.get(extension, "application/octet-stream")
