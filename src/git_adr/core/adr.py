"""ADR (Architecture Decision Record) model and parsing.

This module defines the core data structures for ADRs and provides
parsing/serialization using YAML frontmatter + Markdown format.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any

import frontmatter
import yaml

from git_adr.core.utils import ensure_list


class ADRStatus(str, Enum):
    """Status values for an ADR.

    Following MADR conventions with additional statuses for workflow support.
    """

    DRAFT = "draft"
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_string(cls, value: str) -> ADRStatus:
        """Parse a status string, case-insensitive.

        Args:
            value: Status string.

        Returns:
            Matching ADRStatus.

        Raises:
            ValueError: If status is not recognized.
        """
        value_lower = value.lower().strip()
        for status in cls:
            if status.value == value_lower:
                return status
        raise ValueError(f"Unknown ADR status: {value}")


@dataclass
class ADRMetadata:
    """Metadata for an Architecture Decision Record.

    This is stored in the YAML frontmatter of the ADR.
    """

    # Required fields
    id: str
    title: str
    date: date
    status: ADRStatus

    # Optional fields
    tags: list[str] = field(default_factory=list)
    deciders: list[str] = field(default_factory=list)
    consulted: list[str] = field(default_factory=list)
    informed: list[str] = field(default_factory=list)
    linked_commits: list[str] = field(default_factory=list)

    # Relationships
    supersedes: str | None = None
    superseded_by: str | None = None

    # Format metadata
    format: str = "madr"

    # Internal tracking (not serialized to frontmatter)
    note_sha: str | None = field(default=None, repr=False)

    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to dictionary for YAML serialization.

        Returns:
            Dictionary suitable for YAML frontmatter.
        """
        data: dict[str, Any] = {
            "id": self.id,
            "title": self.title,
            "date": self.date.isoformat(),
            "status": str(self.status),
        }

        # Only include optional fields if they have values
        if self.tags:
            data["tags"] = self.tags
        if self.deciders:
            data["deciders"] = self.deciders
        if self.consulted:
            data["consulted"] = self.consulted
        if self.informed:
            data["informed"] = self.informed
        if self.linked_commits:
            data["linked_commits"] = self.linked_commits
        if self.supersedes:
            data["supersedes"] = self.supersedes
        if self.superseded_by:
            data["superseded_by"] = self.superseded_by
        if self.format and self.format != "madr":
            data["format"] = self.format

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ADRMetadata:
        """Create metadata from a dictionary.

        Args:
            data: Dictionary from YAML frontmatter.

        Returns:
            ADRMetadata instance.
        """
        # Parse date
        date_value = data.get("date")
        if isinstance(date_value, str):
            parsed_date = date.fromisoformat(date_value[:10])
        elif isinstance(date_value, datetime):
            parsed_date = date_value.date()
        elif isinstance(date_value, date):
            parsed_date = date_value
        else:
            parsed_date = date.today()

        # Parse status
        status_value = data.get("status", "proposed")
        if isinstance(status_value, ADRStatus):
            status = status_value
        else:
            try:
                status = ADRStatus.from_string(str(status_value))
            except ValueError:
                status = ADRStatus.PROPOSED

        return cls(
            id=str(data.get("id", "")),
            title=str(data.get("title", "")),
            date=parsed_date,
            status=status,
            tags=ensure_list(data.get("tags")),
            # Support both 'deciders' (legacy) and 'decision-makers' (MADR 4.0)
            deciders=ensure_list(
                data.get("deciders")
                if "deciders" in data
                else data.get("decision-makers", [])
            ),
            consulted=ensure_list(data.get("consulted")),
            informed=ensure_list(data.get("informed")),
            linked_commits=ensure_list(data.get("linked_commits")),
            supersedes=data.get("supersedes"),
            superseded_by=data.get("superseded_by"),
            format=str(data.get("format", "madr")),
        )


@dataclass
class ADR:
    """Architecture Decision Record.

    An ADR consists of metadata (in YAML frontmatter) and content (Markdown).
    """

    metadata: ADRMetadata
    content: str

    @property
    def id(self) -> str:
        """Get the ADR ID."""
        return self.metadata.id

    @property
    def title(self) -> str:
        """Get the ADR title."""
        return self.metadata.title

    @property
    def status(self) -> ADRStatus:
        """Get the ADR status."""
        return self.metadata.status

    @property
    def date(self) -> date:
        """Get the ADR date."""
        return self.metadata.date

    def to_markdown(self) -> str:
        """Serialize ADR to YAML frontmatter + Markdown.

        Returns:
            Complete ADR document as string.
        """
        # Create frontmatter post
        post = frontmatter.Post(self.content)
        post.metadata = self.metadata.to_dict()

        # Serialize with frontmatter
        return frontmatter.dumps(post)

    @classmethod
    def from_markdown(cls, text: str) -> ADR:
        """Parse an ADR from YAML frontmatter + Markdown.

        Args:
            text: Complete ADR document.

        Returns:
            Parsed ADR instance.

        Raises:
            ValueError: If the document cannot be parsed.
        """
        try:
            post = frontmatter.loads(text)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML frontmatter: {e}") from e

        metadata = ADRMetadata.from_dict(dict(post.metadata))
        content = post.content

        return cls(metadata=metadata, content=content)


def generate_adr_id(title: str, existing_ids: set[str] | None = None) -> str:
    """Generate a unique ADR ID from a title.

    Format: YYYYMMDD-slug
    Example: "20251215-use-postgresql-for-persistence"

    Args:
        title: ADR title to generate ID from.
        existing_ids: Set of existing IDs to avoid collision.

    Returns:
        Unique ADR ID.
    """
    # Generate date prefix
    date_prefix = date.today().strftime("%Y%m%d")

    # Generate slug from title
    slug = _slugify(title)

    # Truncate slug to reasonable length
    max_slug_length = 50
    if len(slug) > max_slug_length:
        slug = slug[:max_slug_length].rsplit("-", 1)[0]

    base_id = f"{date_prefix}-{slug}"

    # Handle collisions
    if existing_ids is None:
        return base_id

    if base_id not in existing_ids:
        return base_id

    # Add numeric suffix for collision
    counter = 2
    while f"{base_id}-{counter}" in existing_ids:
        counter += 1

    return f"{base_id}-{counter}"


def _slugify(text: str) -> str:
    """Convert text to a URL-safe slug.

    Args:
        text: Text to slugify.

    Returns:
        Lowercase slug with hyphens.
    """
    # Convert to lowercase
    slug = text.lower()

    # Replace spaces and underscores with hyphens
    slug = re.sub(r"[\s_]+", "-", slug)

    # Remove non-alphanumeric characters (except hyphens)
    slug = re.sub(r"[^a-z0-9-]", "", slug)

    # Collapse multiple hyphens
    slug = re.sub(r"-+", "-", slug)

    # Strip leading/trailing hyphens
    slug = slug.strip("-")

    return slug


def validate_adr(adr: ADR) -> list[str]:
    """Validate an ADR and return any issues.

    Args:
        adr: ADR to validate.

    Returns:
        List of validation error messages (empty if valid).
    """
    issues: list[str] = []

    # Required fields
    if not adr.metadata.id:
        issues.append("Missing ADR ID")
    if not adr.metadata.title:
        issues.append("Missing ADR title")

    # ID format validation
    if adr.metadata.id and not re.match(r"^\d{8}-[\w-]+$", adr.metadata.id):
        issues.append(
            f"Invalid ADR ID format: {adr.metadata.id} (expected: YYYYMMDD-slug)"
        )

    # Content validation
    if not adr.content or len(adr.content.strip()) < 10:
        issues.append("ADR content is too short")

    # Status transitions (superseded should have superseded_by)
    if adr.metadata.status == ADRStatus.SUPERSEDED and not adr.metadata.superseded_by:
        issues.append("Superseded ADR should have 'superseded_by' set")

    return issues
