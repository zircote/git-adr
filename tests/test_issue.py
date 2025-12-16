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
                TemplateSection(
                    header="Steps", hint="Steps to reproduce", required=True
                ),
                TemplateSection(
                    header="Notes", hint="Additional notes", required=False
                ),
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


class TestIssueFromMarkdownErrors:
    """Tests for Issue.from_markdown error handling."""

    def test_invalid_frontmatter_raises(self) -> None:
        """Test that invalid YAML frontmatter raises ValueError."""
        invalid_markdown = """---
title: [invalid yaml
labels: - broken
---
Body content
"""
        with pytest.raises(ValueError, match="Invalid issue document"):
            Issue.from_markdown(invalid_markdown)

    def test_missing_title_returns_empty(self) -> None:
        """Test missing title defaults to empty string."""
        markdown = """---
labels:
  - bug
---
Body content
"""
        issue = Issue.from_markdown(markdown)
        assert issue.title == ""


class TestIssueFromTemplateYaml:
    """Tests for Issue.from_template with YAML form templates."""

    def test_yaml_form_body_rendering(self) -> None:
        """Test creating issue from YAML form template."""
        from git_adr.core.issue_template import FormElement, FormElementType

        template = IssueTemplate(
            name="Feature Request",
            title="[FEATURE] ",
            labels=["enhancement"],
            is_yaml_form=True,
            body=[
                FormElement(
                    type=FormElementType.INPUT,
                    id="feature_name",
                    attributes={"label": "Feature Name"},
                ),
                FormElement(
                    type=FormElementType.TEXTAREA,
                    id="description",
                    attributes={"label": "Description"},
                ),
            ],
        )

        issue = Issue.from_template(
            template=template,
            values={
                "feature_name": "Dark Mode",
                "description": "Add a dark mode option",
            },
        )

        # Uses template title when no override given
        assert issue.title == "[FEATURE] "
        assert "## Feature Name" in issue.body
        assert "Dark Mode" in issue.body
        assert "## Description" in issue.body
        assert "Add a dark mode option" in issue.body

    def test_yaml_form_missing_value(self) -> None:
        """Test YAML form with missing value skips the field."""
        from git_adr.core.issue_template import FormElement, FormElementType

        template = IssueTemplate(
            name="Bug Report",
            is_yaml_form=True,
            body=[
                FormElement(
                    type=FormElementType.INPUT,
                    id="title",
                    attributes={"label": "Bug Title"},
                ),
            ],
        )

        # When no value provided for 'title', the field is skipped in rendering
        issue = Issue.from_template(template=template, values={})

        # Since no values provided, body is empty (only fields with values are rendered)
        assert issue.body == ""


class TestIssueBuilderYamlForm:
    """Tests for IssueBuilder with YAML form templates."""

    @pytest.fixture
    def yaml_template(self) -> IssueTemplate:
        """Create a YAML form template."""
        from git_adr.core.issue_template import FormElement, FormElementType

        return IssueTemplate(
            name="Feature Request",
            title="",
            labels=["enhancement"],
            is_yaml_form=True,
            body=[
                FormElement(
                    type=FormElementType.INPUT,
                    id="feature_name",
                    attributes={"label": "Feature Name"},
                    validations={"required": True},
                ),
                FormElement(
                    type=FormElementType.TEXTAREA,
                    id="description",
                    attributes={"label": "Description"},
                    validations={"required": False},
                ),
                FormElement(
                    type=FormElementType.MARKDOWN,
                    id=None,
                    attributes={"value": "Some markdown content"},
                ),
            ],
        )

    def test_missing_required_yaml_fields(self, yaml_template: IssueTemplate) -> None:
        """Test missing required fields detection for YAML form."""
        builder = IssueBuilder(yaml_template)
        builder.set_title("My Feature")

        missing = builder.missing_required_fields()
        assert "feature_name" in missing
        assert "description" not in missing  # Not required

    def test_preview_yaml_form(self, yaml_template: IssueTemplate) -> None:
        """Test preview generation for YAML form."""
        builder = IssueBuilder(yaml_template)
        builder.set_title("My Feature")
        builder.set_field("feature_name", "Dark Mode")

        preview = builder.preview()

        assert "# My Feature" in preview
        assert "## Feature Name" in preview
        assert "Dark Mode" in preview
        assert "## Description" in preview
        assert "[Description not provided]" in preview

    def test_build_yaml_form(self, yaml_template: IssueTemplate) -> None:
        """Test building issue from YAML form."""
        builder = IssueBuilder(yaml_template)
        builder.set_title("My Feature")
        builder.set_field("feature_name", "Dark Mode")

        issue = builder.build()
        assert issue.title == "My Feature"
        assert "## Feature Name" in issue.body
        assert "Dark Mode" in issue.body

    def test_set_assignees(self, yaml_template: IssueTemplate) -> None:
        """Test setting assignees updates builder state and preview."""
        builder = IssueBuilder(yaml_template)
        result = builder.set_assignees(["user1", "user2"])

        # Check fluent interface
        assert result is builder

        # Verify preview shows the assignees
        builder.set_title("Test")
        builder.set_field("feature_name", "test")
        preview = builder.preview()
        assert "@user1" in preview
        assert "@user2" in preview


class TestIssueToMarkdownEdgeCases:
    """Edge case tests for Issue.to_markdown."""

    def test_to_markdown_no_labels_or_assignees(self) -> None:
        """Test to_markdown without labels or assignees."""
        issue = Issue(
            title="Simple Issue",
            body="Just the body",
        )
        markdown = issue.to_markdown()

        assert "title: Simple Issue" in markdown
        assert "labels:" not in markdown
        assert "assignees:" not in markdown

    def test_to_markdown_with_assignees(self) -> None:
        """Test to_markdown with assignees."""
        issue = Issue(
            title="Issue",
            body="Body",
            assignees=["alice", "bob"],
        )
        markdown = issue.to_markdown()

        assert "assignees:" in markdown
        assert "alice" in markdown
        assert "bob" in markdown


class TestIssueBuilderRemoveNonexistentLabel:
    """Test removing a label that doesn't exist."""

    def test_remove_label_not_present(self) -> None:
        """Test removing a label that was never added."""
        template = IssueTemplate(
            name="Test",
            labels=["bug"],
            sections=[
                TemplateSection(header="Desc", hint="", required=True),
            ],
        )
        builder = IssueBuilder(template)

        # Remove a label that doesn't exist - should not raise
        builder.remove_label("nonexistent")

        # Original labels still there
        builder.set_title("Test")
        builder.set_field("desc", "test")
        issue = builder.build()
        assert "bug" in issue.labels


class TestIssueBuilderPreviewMetadata:
    """Test preview method metadata display."""

    def test_preview_shows_assignees(self) -> None:
        """Test that preview shows assignees when set."""
        template = IssueTemplate(
            name="Test",
            labels=["bug"],
            assignees=["alice"],
            sections=[
                TemplateSection(header="Desc", hint=""),
            ],
        )
        builder = IssueBuilder(template)
        builder.set_title("Test Issue")

        preview = builder.preview()

        assert "@alice" in preview
        assert "`bug`" in preview

    def test_preview_no_title(self) -> None:
        """Test preview when title not set."""
        template = IssueTemplate(
            name="Test",
            title="",
            sections=[
                TemplateSection(header="Desc", hint=""),
            ],
        )
        builder = IssueBuilder(template)

        preview = builder.preview()

        assert "[Title not set]" in preview
