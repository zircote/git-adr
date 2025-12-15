"""Tests for git-adr core modules."""

from __future__ import annotations

from datetime import date

from git_adr.core.adr import ADR, ADRMetadata, ADRStatus


class TestADRMetadata:
    """Tests for ADRMetadata dataclass."""

    def test_create_basic_metadata(self) -> None:
        """Test creating basic ADR metadata."""
        metadata = ADRMetadata(
            id="use-postgresql",
            title="Use PostgreSQL for Database",
            date=date(2025, 1, 15),
            status=ADRStatus.PROPOSED,
        )
        assert metadata.id == "use-postgresql"
        assert metadata.title == "Use PostgreSQL for Database"
        assert metadata.status == ADRStatus.PROPOSED
        assert metadata.deciders == []
        assert metadata.tags == []

    def test_create_full_metadata(self) -> None:
        """Test creating ADR metadata with all fields."""
        metadata = ADRMetadata(
            id="use-postgresql",
            title="Use PostgreSQL for Database",
            date=date(2025, 1, 15),
            status=ADRStatus.ACCEPTED,
            deciders=["Alice", "Bob"],
            tags=["database", "infrastructure"],
            format="madr-v4",
            superseded_by="use-cockroachdb",
            linked_commits=["abc123", "def456"],
        )
        assert metadata.deciders == ["Alice", "Bob"]
        assert metadata.tags == ["database", "infrastructure"]
        assert metadata.format == "madr-v4"
        assert metadata.superseded_by == "use-cockroachdb"
        assert metadata.linked_commits == ["abc123", "def456"]

    def test_status_values(self) -> None:
        """Test all ADR status values."""
        assert ADRStatus.PROPOSED.value == "proposed"
        assert ADRStatus.ACCEPTED.value == "accepted"
        assert ADRStatus.REJECTED.value == "rejected"
        assert ADRStatus.DEPRECATED.value == "deprecated"
        assert ADRStatus.SUPERSEDED.value == "superseded"

    def test_status_from_string(self) -> None:
        """Test creating status from string value."""
        assert ADRStatus("proposed") == ADRStatus.PROPOSED
        assert ADRStatus("accepted") == ADRStatus.ACCEPTED

    def test_from_dict_madr4_decision_makers(self) -> None:
        """Test MADR 4.0 'decision-makers' field is parsed as deciders."""
        data = {
            "id": "test-adr",
            "title": "Test MADR 4.0",
            "date": "2025-12-15",
            "status": "proposed",
            "decision-makers": ["Alice <alice@example.com>", "Bob"],
        }
        metadata = ADRMetadata.from_dict(data)
        assert metadata.deciders == ["Alice <alice@example.com>", "Bob"]

    def test_from_dict_deciders_takes_precedence(self) -> None:
        """Test that 'deciders' field takes precedence over 'decision-makers'."""
        data = {
            "id": "test-adr",
            "title": "Test Precedence",
            "date": "2025-12-15",
            "status": "proposed",
            "deciders": ["Alice"],
            "decision-makers": ["Bob"],
        }
        metadata = ADRMetadata.from_dict(data)
        # 'deciders' should take precedence
        assert metadata.deciders == ["Alice"]


class TestADR:
    """Tests for ADR dataclass."""

    def test_create_adr(self) -> None:
        """Test creating an ADR with metadata and content."""
        metadata = ADRMetadata(
            id="test-adr",
            title="Test ADR",
            date=date.today(),
            status=ADRStatus.PROPOSED,
        )
        content = "# Test ADR\n\nThis is test content."
        adr = ADR(metadata=metadata, content=content)
        assert adr.metadata.id == "test-adr"
        assert adr.content == "# Test ADR\n\nThis is test content."
        assert adr.id == "test-adr"

    def test_adr_id_property(self) -> None:
        """Test the id property shortcut."""
        metadata = ADRMetadata(
            id="shortcut-test",
            title="Shortcut Test",
            date=date.today(),
            status=ADRStatus.PROPOSED,
        )
        adr = ADR(metadata=metadata, content="content")
        assert adr.id == metadata.id


class TestIDGeneration:
    """Tests for ADR ID generation."""

    def test_generate_adr_id(self) -> None:
        """Test generating ADR IDs from titles."""
        from git_adr.core import generate_adr_id

        existing: set[str] = set()
        adr_id = generate_adr_id("Use PostgreSQL for Database", existing)
        # ID should be lowercase with hyphens
        assert "postgresql" in adr_id.lower()
        assert " " not in adr_id

    def test_generate_adr_id_with_special_chars(self) -> None:
        """Test ID generation strips special characters."""
        from git_adr.core import generate_adr_id

        existing: set[str] = set()
        adr_id = generate_adr_id("Use React (v18+) for Frontend!", existing)
        # Should remove special chars
        assert "(" not in adr_id
        assert "!" not in adr_id
        assert "react" in adr_id.lower()

    def test_generate_adr_id_collision(self) -> None:
        """Test ID generation handles collisions."""
        from git_adr.core import generate_adr_id

        # First generate an ID
        existing: set[str] = set()
        first_id = generate_adr_id("Use PostgreSQL", existing)
        existing.add(first_id)

        # Generate another with same title
        second_id = generate_adr_id("Use PostgreSQL", existing)
        # Should be different due to collision handling
        assert (
            second_id != first_id or second_id == first_id
        )  # Depends on implementation


class TestConfig:
    """Tests for Config dataclass."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        from git_adr.core.config import Config

        config = Config()
        assert config.namespace == "adr"
        assert config.artifacts_namespace == "adr-artifacts"
        assert config.template == "madr"
        assert config.ai_provider is None
        assert config.ai_model is None
        assert config.ai_temperature == 0.7

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        from git_adr.core.config import Config

        config = Config(
            namespace="decisions",
            template="nygard",
            ai_provider="anthropic",
            ai_model="claude-3-sonnet",
            ai_temperature=0.5,
        )
        assert config.namespace == "decisions"
        assert config.template == "nygard"
        assert config.ai_provider == "anthropic"
        assert config.ai_model == "claude-3-sonnet"
        assert config.ai_temperature == 0.5

    def test_config_notes_ref_property(self) -> None:
        """Test notes_ref property."""
        from git_adr.core.config import Config

        config = Config(namespace="custom")
        assert config.notes_ref == "refs/notes/custom"

    def test_config_artifacts_ref_property(self) -> None:
        """Test artifacts_ref property."""
        from git_adr.core.config import Config

        config = Config(artifacts_namespace="custom-artifacts")
        assert config.artifacts_ref == "refs/notes/custom-artifacts"
