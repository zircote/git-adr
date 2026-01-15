"""Tests for Structured MADR format.

Tests the structured-madr format implementation including:
- Template rendering
- Format detection
- Extended metadata fields
- ADR serialization with extended fields
"""

from __future__ import annotations

from datetime import date

from git_adr.core.adr import ADR, ADRMetadata, ADRStatus
from git_adr.core.templates import TemplateContext, TemplateEngine


class TestStructuredMADRTemplate:
    """Tests for Structured MADR template rendering."""

    def test_structured_madr_in_formats_list(self) -> None:
        """Test that structured-madr is in available formats."""
        engine = TemplateEngine()
        formats = engine.list_formats()

        assert "structured-madr" in formats

    def test_render_structured_madr(self) -> None:
        """Test rendering Structured MADR template."""
        engine = TemplateEngine()
        content = engine.render_for_new(
            format_name="structured-madr",
            title="Use PostgreSQL for Primary Storage",
            adr_id="20250115-use-postgresql",
            status="proposed",
            deciders=["Architecture Team"],
        )

        # Check header format
        assert (
            "ADR-20250115-use-postgresql: Use PostgreSQL for Primary Storage" in content
        )
        assert "## Status" in content
        assert "proposed" in content

        # Check structured-madr specific sections
        assert "## Decision Drivers" in content
        assert "### Primary Drivers" in content
        assert "### Secondary Drivers" in content
        assert "## Considered Options" in content
        assert "Risk Assessment" in content
        assert "## Consequences" in content
        assert "### Positive" in content
        assert "### Negative" in content
        assert "### Neutral" in content
        assert "## Decision Outcome" in content
        assert "## Related Decisions" in content
        assert "## Links" in content
        assert "## Audit" in content
        assert "### Compliance Review" in content
        assert "### Findings" in content

    def test_render_structured_madr_with_deciders(self) -> None:
        """Test rendering Structured MADR with deciders/author."""
        engine = TemplateEngine()
        content = engine.render_for_new(
            format_name="structured-madr",
            title="Test Decision",
            adr_id="20250115-test",
            status="accepted",
            deciders=["John Doe", "Jane Smith"],
        )

        assert "John Doe, Jane Smith" in content


class TestStructuredMADRFormatDetection:
    """Tests for Structured MADR format detection."""

    def test_detect_structured_madr_with_audit_and_drivers(self) -> None:
        """Test detecting structured-madr from audit and decision drivers."""
        engine = TemplateEngine()

        content = """# ADR-001: Use Kubernetes

## Status

accepted

## Decision Drivers

### Primary Drivers

- Scalability needs
- Team expertise

## Context

We need container orchestration.

## Audit

### Compliance Review

| Date | Status |
|------|--------|
| 2025-01-15 | Reviewed |
"""
        detected = engine.detect_format(content)
        assert detected == "structured-madr"

    def test_detect_structured_madr_with_risk_assessment(self) -> None:
        """Test detecting structured-madr from risk assessment."""
        engine = TemplateEngine()

        content = """# Test ADR

## Decision Drivers

Some factors here.

## Considered Options

### Option A

Risk Assessment:

| Technical | Medium |
"""
        detected = engine.detect_format(content)
        assert detected == "structured-madr"

    def test_detect_structured_madr_header_format(self) -> None:
        """Test detecting structured-madr from ADR-{id}: header format."""
        engine = TemplateEngine()

        content = """# ADR-20250115-test: Some Decision

## Status

proposed

## Context

Something.

## Audit

Stuff here.
"""
        detected = engine.detect_format(content)
        assert detected == "structured-madr"

    def test_distinguish_from_regular_madr(self) -> None:
        """Test structured-madr is distinct from regular MADR."""
        engine = TemplateEngine()

        # Regular MADR content - no audit section
        madr_content = """# Test Decision

## Status

accepted

## Options Considered

### Option 1

Good option.

## Decision Outcome

Chose option 1.
"""
        detected = engine.detect_format(madr_content)
        assert detected == "madr"  # Should NOT be structured-madr


class TestStructuredMADRMetadata:
    """Tests for Structured MADR extended metadata fields."""

    def test_metadata_extended_fields_defaults(self) -> None:
        """Test ADRMetadata extended fields have defaults."""
        metadata = ADRMetadata(
            id="test-id",
            title="Test",
            date=date.today(),
            status=ADRStatus.PROPOSED,
        )

        assert metadata.description is None
        assert metadata.adr_type is None
        assert metadata.category is None
        assert metadata.project is None
        assert metadata.technologies == []
        assert metadata.audience == []
        assert metadata.related == []
        assert metadata.author is None
        assert metadata.updated is None

    def test_metadata_extended_fields_set(self) -> None:
        """Test ADRMetadata with extended fields populated."""
        metadata = ADRMetadata(
            id="20250115-use-postgres",
            title="Use PostgreSQL",
            date=date(2025, 1, 15),
            status=ADRStatus.PROPOSED,
            format="structured-madr",
            description="Decision to adopt PostgreSQL as primary database",
            adr_type="adr",
            category="architecture",
            project="my-application",
            technologies=["postgresql", "python"],
            audience=["developers", "architects"],
            related=["20250101-database-strategy"],
            author="Architecture Team",
            updated=date(2025, 1, 15),
        )

        assert (
            metadata.description == "Decision to adopt PostgreSQL as primary database"
        )
        assert metadata.adr_type == "adr"
        assert metadata.category == "architecture"
        assert metadata.project == "my-application"
        assert metadata.technologies == ["postgresql", "python"]
        assert metadata.audience == ["developers", "architects"]
        assert metadata.related == ["20250101-database-strategy"]
        assert metadata.author == "Architecture Team"
        assert metadata.updated == date(2025, 1, 15)

    def test_metadata_to_dict_extended_fields(self) -> None:
        """Test serialization of extended metadata fields."""
        metadata = ADRMetadata(
            id="test-id",
            title="Test",
            date=date(2025, 1, 15),
            status=ADRStatus.PROPOSED,
            format="structured-madr",
            description="A test decision",
            adr_type="adr",
            category="testing",
            project="test-project",
            technologies=["python"],
            audience=["developers"],
            related=["other-adr"],
            author="Test Author",
            updated=date(2025, 1, 15),
        )

        data = metadata.to_dict()

        assert data["description"] == "A test decision"
        assert data["type"] == "adr"
        assert data["category"] == "testing"
        assert data["project"] == "test-project"
        assert data["technologies"] == ["python"]
        assert data["audience"] == ["developers"]
        assert data["related"] == ["other-adr"]
        assert data["author"] == "Test Author"
        assert data["updated"] == "2025-01-15"

    def test_metadata_from_dict_extended_fields(self) -> None:
        """Test parsing extended metadata fields from dict."""
        data = {
            "id": "test-id",
            "title": "Test",
            "date": "2025-01-15",
            "status": "proposed",
            "format": "structured-madr",
            "description": "A test decision",
            "type": "adr",
            "category": "testing",
            "project": "test-project",
            "technologies": ["python", "postgresql"],
            "audience": ["developers"],
            "related": ["adr-001", "adr-002"],
            "author": "Test Author",
            "updated": "2025-01-15",
        }

        metadata = ADRMetadata.from_dict(data)

        assert metadata.description == "A test decision"
        assert metadata.adr_type == "adr"
        assert metadata.category == "testing"
        assert metadata.project == "test-project"
        assert metadata.technologies == ["python", "postgresql"]
        assert metadata.audience == ["developers"]
        assert metadata.related == ["adr-001", "adr-002"]
        assert metadata.author == "Test Author"
        assert metadata.updated == date(2025, 1, 15)


class TestStructuredMADRADRSerialization:
    """Tests for ADR serialization with structured-madr fields."""

    def test_adr_to_markdown_extended_fields(self) -> None:
        """Test ADR serialization includes extended fields."""
        metadata = ADRMetadata(
            id="20250115-test",
            title="Test Decision",
            date=date(2025, 1, 15),
            status=ADRStatus.PROPOSED,
            format="structured-madr",
            description="Test description",
            category="architecture",
            technologies=["python"],
        )

        adr = ADR(
            metadata=metadata,
            content="# Test\n\nContent here.",
        )

        markdown = adr.to_markdown()

        assert "description: Test description" in markdown
        assert "category: architecture" in markdown
        assert "technologies:" in markdown
        assert "- python" in markdown

    def test_adr_from_markdown_extended_fields(self) -> None:
        """Test ADR parsing includes extended fields."""
        markdown = """---
id: 20250115-test
title: Test Decision
date: 2025-01-15
status: proposed
format: structured-madr
description: Test description
type: adr
category: architecture
project: test-project
technologies:
  - python
  - postgresql
audience:
  - developers
related:
  - adr-001
author: Test Author
updated: 2025-01-15
---
# Test

Content here.
"""
        adr = ADR.from_markdown(markdown)

        assert adr.metadata.description == "Test description"
        assert adr.metadata.adr_type == "adr"
        assert adr.metadata.category == "architecture"
        assert adr.metadata.project == "test-project"
        assert adr.metadata.technologies == ["python", "postgresql"]
        assert adr.metadata.audience == ["developers"]
        assert adr.metadata.related == ["adr-001"]
        assert adr.metadata.author == "Test Author"
        assert adr.metadata.updated == date(2025, 1, 15)


class TestTemplateContextExtendedFields:
    """Tests for TemplateContext with extended fields."""

    def test_template_context_extended_fields(self) -> None:
        """Test TemplateContext supports extended fields."""
        context = TemplateContext(
            id="test-id",
            title="Test",
            date=date(2025, 1, 15),
            status="proposed",
            tags=["tag1", "tag2"],
            deciders=["Alice", "Bob"],
            description="A description",
            adr_type="adr",
            category="testing",
            project="my-project",
            technologies=["python"],
            audience=["devs"],
            related=["adr-001"],
            author="Author",
        )

        data = context.to_dict()

        assert data["description"] == "A description"
        assert data["type"] == "adr"
        assert data["category"] == "testing"
        assert data["project"] == "my-project"
        assert data["technologies"] == "python"
        assert data["audience"] == "devs"
        assert data["related"] == "adr-001"
        assert data["author"] == "Author"

    def test_template_context_default_type(self) -> None:
        """Test TemplateContext default type is 'adr'."""
        context = TemplateContext(
            id="test",
            title="Test",
            date=date.today(),
            status="proposed",
            tags=[],
            deciders=[],
        )

        data = context.to_dict()
        assert data["type"] == "adr"


class TestStructuredMADRConversion:
    """Tests for converting to/from Structured MADR."""

    def test_convert_madr_to_structured_madr(self) -> None:
        """Test converting regular MADR to Structured MADR."""
        engine = TemplateEngine()

        adr = ADR(
            metadata=ADRMetadata(
                id="20250115-test",
                title="Test Decision",
                date=date(2025, 1, 15),
                status=ADRStatus.ACCEPTED,
            ),
            content="""# Test Decision

## Status

accepted

## Context

Some context.

## Decision

The decision.

## Consequences

Some consequences.
""",
        )

        converted = engine.convert(adr, "structured-madr")

        assert converted is not None
        assert "## Decision Drivers" in converted
        assert "## Audit" in converted
        assert "## Related Decisions" in converted
