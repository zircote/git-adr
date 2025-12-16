"""Tests for Issue model and IssueBuilder."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from git_adr.core.issue import (
    Issue,
    IssueBuilder,
    generate_issue_filename,
    save_local_issue,
)
from git_adr.core.issue_template import (
    IssueTemplate,
    TemplateSection,
)


class TestIssue:
    """Tests for Issue dataclass."""

    def test_create_basic_issue(self) -> None:
        """Test creating a basic issue."""
        issue = Issue(
            title="Test Issue",
            body="This is the body",
        )
        assert issue.title == "Test Issue"
        assert issue.body == "This is the body"
        assert issue.labels == []
        assert issue.assignees == []

    def test_create_full_issue(self) -> None:
        """Test creating issue with all fields."""
        issue = Issue(
            title="Bug: Something broken",
            body="## Description\n\nIt's broken",
            labels=["bug", "priority"],
            assignees=["alice", "bob"],
        )
        assert issue.labels == ["bug", "priority"]
        assert issue.assignees == ["alice", "bob"]

    def test_to_markdown(self) -> None:
        """Test serializing issue to markdown with frontmatter."""
        issue = Issue(
            title="Test Issue",
            body="## Description\n\nTest body",
            labels=["bug"],
        )
        markdown = issue.to_markdown()

        assert "title: Test Issue" in markdown
        assert "labels:" in markdown
        assert "bug" in markdown
        assert "## Description" in markdown

    def test_from_markdown(self) -> None:
        """Test parsing issue from markdown."""
        markdown = """---
title: Test Issue
labels:
  - bug
  - urgent
assignees:
  - alice
---
## Description

This is a test issue.
"""
        issue = Issue.from_markdown(markdown)

        assert issue.title == "Test Issue"
        assert issue.labels == ["bug", "urgent"]
        assert issue.assignees == ["alice"]
        assert "## Description" in issue.body

    def test_from_template(self) -> None:
        """Test creating issue from template and values."""
        template = IssueTemplate(
            name="Bug Report",
            title="[BUG] ",
            labels=["bug"],
            sections=[
                TemplateSection(header="Description", hint="Describe the bug"),
                TemplateSection(header="Steps", hint="Steps to reproduce"),
            ],
        )

        issue = Issue.from_template(
            template=template,
            values={
                "description": "The app crashes",
                "steps": "1. Click button\n2. See crash",
            },
            title="[BUG] App crashes",
        )

        assert issue.title == "[BUG] App crashes"
        assert issue.labels == ["bug"]
        assert "## Description" in issue.body
        assert "The app crashes" in issue.body
        assert "## Steps" in issue.body


class TestIssueBuilder:
    """Tests for IssueBuilder class."""

    @pytest.fixture
    def template(self) -> IssueTemplate:
        """Create a test template."""
        return IssueTemplate(
            name="Bug Report",
            title="[BUG] ",
            labels=["bug"],
            sections=[
                TemplateSection(header="Description", hint="Describe", required=True),
                TemplateSection(header="Steps", hint="Steps to reproduce", required=True),
                TemplateSection(header="Notes", hint="Additional notes", required=False),
            ],
        )

    def test_builder_creation(self, template: IssueTemplate) -> None:
        """Test creating a builder."""
        builder = IssueBuilder(template)
        assert builder.template == template
        assert builder.title == "[BUG] "

    def test_set_title(self, template: IssueTemplate) -> None:
        """Test setting title."""
        builder = IssueBuilder(template)
        result = builder.set_title("My Bug")
        assert builder.title == "My Bug"
        assert result is builder  # Fluent interface

    def test_set_field(self, template: IssueTemplate) -> None:
        """Test setting field values."""
        builder = IssueBuilder(template)
        builder.set_field("description", "Bug description")
        assert builder.get_field("description") == "Bug description"
        assert builder.get_field("nonexistent") is None

    def test_add_remove_label(self, template: IssueTemplate) -> None:
        """Test label manipulation."""
        builder = IssueBuilder(template)

        # Initially has template labels
        builder.add_label("urgent")
        builder.add_label("bug")  # Duplicate, shouldn't add again

        # Build to check labels
        builder.set_title("Test")
        builder.set_field("description", "test")
        builder.set_field("steps", "test")

        # Remove a label
        builder.remove_label("urgent")
        issue = builder.build()
        assert "urgent" not in issue.labels

    def test_is_complete(self, template: IssueTemplate) -> None:
        """Test completion check."""
        builder = IssueBuilder(template)

        # Initially incomplete
        assert builder.is_complete() is False

        # Set title
        builder.set_title("Bug Report")
        assert builder.is_complete() is False

        # Set required fields
        builder.set_field("description", "A bug")
        assert builder.is_complete() is False  # Still missing steps

        builder.set_field("steps", "1. Click button")
        assert builder.is_complete() is True

    def test_missing_required_fields(self, template: IssueTemplate) -> None:
        """Test getting missing required fields."""
        builder = IssueBuilder(template)
        builder.set_title("")  # Empty title

        missing = builder.missing_required_fields()
        assert "title" in missing
        assert "description" in missing
        assert "steps" in missing
        assert "notes" not in missing  # Not required

    def test_build_success(self, template: IssueTemplate) -> None:
        """Test successful build."""
        builder = IssueBuilder(template)
        builder.set_title("Bug Report")
        builder.set_field("description", "Bug description")
        builder.set_field("steps", "1. Do something")

        issue = builder.build()
        assert issue.title == "Bug Report"
        assert "Bug description" in issue.body

    def test_build_fails_incomplete(self, template: IssueTemplate) -> None:
        """Test build fails when incomplete."""
        builder = IssueBuilder(template)
        builder.set_title("Test")
        # Missing required fields

        with pytest.raises(ValueError, match="Missing required fields"):
            builder.build()

    def test_preview(self, template: IssueTemplate) -> None:
        """Test preview generation."""
        builder = IssueBuilder(template)
        builder.set_title("Test Bug")
        builder.set_field("description", "A bug happened")

        preview = builder.preview()

        assert "# Test Bug" in preview
        assert "## Description" in preview
        assert "A bug happened" in preview
        assert "bug" in preview.lower()  # Label


class TestIssueFilename:
    """Tests for filename generation."""

    def test_basic_filename(self) -> None:
        """Test basic filename generation."""
        filename = generate_issue_filename("Add dark mode")
        assert filename.endswith(".md")
        assert "add-dark-mode" in filename

    def test_strips_prefix(self) -> None:
        """Test that [BUG]/[FEATURE] prefixes are stripped."""
        filename = generate_issue_filename("[BUG] App crashes")
        assert "bug" not in filename.lower()
        assert "app-crashes" in filename

    def test_truncates_long_titles(self) -> None:
        """Test that long titles are truncated."""
        long_title = "This is a very long title that should be truncated " * 5
        filename = generate_issue_filename(long_title)
        assert len(filename) < 100


class TestLocalFileSaving:
    """Tests for local issue file saving."""

    def test_save_basic_issue(self) -> None:
        """Test saving an issue to local file."""
        issue = Issue(
            title="Test Issue",
            body="Test body",
            labels=["bug"],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = save_local_issue(issue, output_dir=Path(tmpdir))

            assert path.exists()
            assert path.suffix == ".md"

            content = path.read_text()
            assert "title: Test Issue" in content

    def test_creates_directory(self) -> None:
        """Test that output directory is created if needed."""
        issue = Issue(title="Test", body="Test")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "new" / "nested" / "dir"
            path = save_local_issue(issue, output_dir=output_dir)

            assert output_dir.exists()
            assert path.exists()

    def test_custom_filename(self) -> None:
        """Test saving with custom filename."""
        issue = Issue(title="Test", body="Test")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = save_local_issue(
                issue,
                output_dir=Path(tmpdir),
                filename="my-custom-name",
            )

            assert path.name == "my-custom-name.md"
