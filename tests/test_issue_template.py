"""Tests for issue template parsing and management."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from git_adr.core.issue_template import (
    FormElement,
    FormElementType,
    IssueTemplate,
    TemplateManager,
    TemplateSection,
    TYPE_ALIASES,
    parse_markdown_template_string,
    parse_yaml_form_string,
)


class TestFormElementType:
    """Tests for FormElementType enum."""

    def test_all_types_defined(self) -> None:
        """Test all expected form element types exist."""
        assert FormElementType.MARKDOWN.value == "markdown"
        assert FormElementType.INPUT.value == "input"
        assert FormElementType.TEXTAREA.value == "textarea"
        assert FormElementType.DROPDOWN.value == "dropdown"
        assert FormElementType.CHECKBOXES.value == "checkboxes"

    def test_from_string_valid(self) -> None:
        """Test parsing valid type strings."""
        assert FormElementType.from_string("input") == FormElementType.INPUT
        assert FormElementType.from_string("INPUT") == FormElementType.INPUT
        assert FormElementType.from_string("Textarea") == FormElementType.TEXTAREA

    def test_from_string_invalid(self) -> None:
        """Test parsing invalid type string raises ValueError."""
        with pytest.raises(ValueError, match="Unknown form element type"):
            FormElementType.from_string("invalid")


class TestFormElement:
    """Tests for FormElement dataclass."""

    def test_create_basic_element(self) -> None:
        """Test creating a basic form element."""
        element = FormElement(
            type=FormElementType.INPUT,
            id="test-field",
        )
        assert element.type == FormElementType.INPUT
        assert element.id == "test-field"
        assert element.attributes == {}
        assert element.validations == {}

    def test_element_properties(self) -> None:
        """Test form element property accessors."""
        element = FormElement(
            type=FormElementType.INPUT,
            id="description",
            attributes={
                "label": "Description",
                "placeholder": "Enter description",
                "description": "A helpful hint",
            },
            validations={"required": True},
        )
        assert element.label == "Description"
        assert element.placeholder == "Enter description"
        assert element.description == "A helpful hint"
        assert element.required is True

    def test_element_options_dropdown(self) -> None:
        """Test options property for dropdown elements."""
        element = FormElement(
            type=FormElementType.DROPDOWN,
            id="severity",
            attributes={
                "label": "Severity",
                "options": ["Low", "Medium", "High"],
            },
        )
        assert element.options == ["Low", "Medium", "High"]

    def test_element_is_promptable(self) -> None:
        """Test is_promptable property."""
        input_element = FormElement(type=FormElementType.INPUT, id="test")
        markdown_element = FormElement(type=FormElementType.MARKDOWN)

        assert input_element.is_promptable is True
        assert markdown_element.is_promptable is False

    def test_from_dict(self) -> None:
        """Test creating element from dictionary."""
        data = {
            "type": "textarea",
            "id": "description",
            "attributes": {
                "label": "Description",
                "placeholder": "Enter description",
            },
            "validations": {"required": True},
        }
        element = FormElement.from_dict(data)
        assert element.type == FormElementType.TEXTAREA
        assert element.id == "description"
        assert element.label == "Description"
        assert element.required is True


class TestTemplateSection:
    """Tests for TemplateSection dataclass."""

    def test_create_section(self) -> None:
        """Test creating a template section."""
        section = TemplateSection(
            header="Description",
            hint="A clear description of the bug",
            required=True,
        )
        assert section.header == "Description"
        assert section.hint == "A clear description of the bug"
        assert section.required is True

    def test_section_id_generation(self) -> None:
        """Test ID is generated from header."""
        section = TemplateSection(header="Steps to Reproduce")
        assert section.id == "steps_to_reproduce"

    def test_from_markdown(self) -> None:
        """Test creating section from markdown content."""
        section = TemplateSection.from_markdown(
            "Description",
            "\n<!-- Describe the bug -->\n",
        )
        assert section.header == "Description"
        assert section.hint == "Describe the bug"

    def test_from_markdown_with_content(self) -> None:
        """Test section with non-comment content."""
        section = TemplateSection.from_markdown(
            "Environment",
            "\n- OS: [e.g., macOS]\n- Python: [e.g., 3.12]\n",
        )
        assert section.header == "Environment"
        assert "OS:" in section.hint


class TestIssueTemplate:
    """Tests for IssueTemplate dataclass."""

    def test_create_markdown_template(self) -> None:
        """Test creating a markdown template."""
        template = IssueTemplate(
            name="Bug Report",
            about="Report a bug",
            title="[BUG] ",
            labels=["bug"],
            sections=[
                TemplateSection(header="Description"),
                TemplateSection(header="Steps to Reproduce"),
            ],
        )
        assert template.name == "Bug Report"
        assert template.labels == ["bug"]
        assert len(template.sections) == 2
        assert template.is_yaml_form is False

    def test_promptable_fields_markdown(self) -> None:
        """Test promptable_fields for markdown template."""
        template = IssueTemplate(
            name="Test",
            sections=[
                TemplateSection(header="Description"),
                TemplateSection(header="Steps"),
            ],
        )
        fields = template.promptable_fields
        assert len(fields) == 2
        assert all(isinstance(f, TemplateSection) for f in fields)

    def test_promptable_fields_yaml(self) -> None:
        """Test promptable_fields for YAML form template."""
        template = IssueTemplate(
            name="Test",
            is_yaml_form=True,
            body=[
                FormElement(type=FormElementType.MARKDOWN),  # Not promptable
                FormElement(type=FormElementType.INPUT, id="title"),
                FormElement(type=FormElementType.TEXTAREA, id="desc"),
            ],
        )
        fields = template.promptable_fields
        assert len(fields) == 2  # Markdown element excluded

    def test_get_field_by_id(self) -> None:
        """Test looking up fields by ID."""
        template = IssueTemplate(
            name="Test",
            sections=[
                TemplateSection(header="Description"),
                TemplateSection(header="Steps"),
            ],
        )
        field = template.get_field_by_id("description")
        assert field is not None
        assert field.header == "Description"

        assert template.get_field_by_id("nonexistent") is None


class TestMarkdownTemplateParsing:
    """Tests for markdown template parsing."""

    def test_parse_basic_template(self) -> None:
        """Test parsing a basic markdown template."""
        content = """---
name: Bug Report
about: Report a bug
title: "[BUG] "
labels: bug
assignees: ""
---

## Description

A clear description of the bug.

## Steps to Reproduce

1. Step one
2. Step two
"""
        template = parse_markdown_template_string(content)
        assert template.name == "Bug Report"
        assert template.about == "Report a bug"
        assert template.title == "[BUG] "
        assert template.labels == ["bug"]
        assert len(template.sections) == 2
        assert template.sections[0].header == "Description"
        assert template.sections[1].header == "Steps to Reproduce"

    def test_parse_template_with_multiple_labels(self) -> None:
        """Test parsing template with comma-separated labels."""
        content = """---
name: Test
labels: bug, priority
---

## Description

Test
"""
        template = parse_markdown_template_string(content)
        assert template.labels == ["bug", "priority"]

    def test_parse_template_with_list_labels(self) -> None:
        """Test parsing template with YAML list labels."""
        content = """---
name: Test
labels:
  - bug
  - priority
---

## Description

Test
"""
        template = parse_markdown_template_string(content)
        assert template.labels == ["bug", "priority"]


class TestYAMLFormParsing:
    """Tests for YAML form template parsing."""

    def test_parse_basic_form(self) -> None:
        """Test parsing a basic YAML form template."""
        content = """
name: Bug Report
description: Report a bug
title: "[BUG]: "
labels: ["bug"]
body:
  - type: input
    id: title
    attributes:
      label: Bug Title
      placeholder: Enter a title
    validations:
      required: true
  - type: textarea
    id: description
    attributes:
      label: Description
"""
        template = parse_yaml_form_string(content)
        assert template.name == "Bug Report"
        assert template.about == "Report a bug"
        assert template.is_yaml_form is True
        assert len(template.body) == 2
        assert template.body[0].type == FormElementType.INPUT
        assert template.body[0].required is True
        assert template.body[1].type == FormElementType.TEXTAREA

    def test_parse_form_with_dropdown(self) -> None:
        """Test parsing form with dropdown element."""
        content = """
name: Test
body:
  - type: dropdown
    id: severity
    attributes:
      label: Severity
      options:
        - Low
        - Medium
        - High
"""
        template = parse_yaml_form_string(content)
        assert template.body[0].type == FormElementType.DROPDOWN
        assert template.body[0].options == ["Low", "Medium", "High"]


class TestTemplateManager:
    """Tests for TemplateManager class."""

    def test_type_aliases_defined(self) -> None:
        """Test that type aliases are defined."""
        assert TYPE_ALIASES["bug"] == "bug_report"
        assert TYPE_ALIASES["feat"] == "feature_request"
        assert TYPE_ALIASES["feature"] == "feature_request"
        assert TYPE_ALIASES["docs"] == "documentation"
        assert TYPE_ALIASES["doc"] == "documentation"

    def test_manager_with_project_templates(self) -> None:
        """Test manager finds project templates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create template directory
            template_dir = Path(tmpdir) / ".github" / "ISSUE_TEMPLATE"
            template_dir.mkdir(parents=True)

            # Create a template
            template_file = template_dir / "bug_report.md"
            template_file.write_text("""---
name: Bug Report
about: Report a bug
labels: bug
---

## Description

Describe the bug
""")

            manager = TemplateManager(Path(tmpdir))
            templates = manager.get_project_templates()

            assert "bug_report" in templates
            assert templates["bug_report"].name == "Bug Report"

    def test_manager_type_resolution(self) -> None:
        """Test template resolution by type alias."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_dir = Path(tmpdir) / ".github" / "ISSUE_TEMPLATE"
            template_dir.mkdir(parents=True)

            # Create bug_report template
            (template_dir / "bug_report.md").write_text("""---
name: Bug Report
---

## Description

Test
""")

            manager = TemplateManager(Path(tmpdir))

            # Test alias resolution
            template = manager.get_template("bug")
            assert template is not None
            assert template.name == "Bug Report"

            # Test direct name
            template = manager.get_template("bug_report")
            assert template is not None

    def test_manager_available_types(self) -> None:
        """Test getting available types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_dir = Path(tmpdir) / ".github" / "ISSUE_TEMPLATE"
            template_dir.mkdir(parents=True)

            (template_dir / "bug_report.md").write_text(
                "---\nname: Bug\n---\n## Test\n"
            )
            (template_dir / "feature.md").write_text(
                "---\nname: Feature\n---\n## Test\n"
            )

            manager = TemplateManager(Path(tmpdir))
            types = manager.get_available_types()

            assert "bug_report" in types
            assert "feature" in types

    def test_manager_skips_config_yml(self) -> None:
        """Test that config.yml is not parsed as a template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_dir = Path(tmpdir) / ".github" / "ISSUE_TEMPLATE"
            template_dir.mkdir(parents=True)

            # Create config.yml (GitHub template chooser config)
            (template_dir / "config.yml").write_text("blank_issues_enabled: false\n")
            (template_dir / "bug.md").write_text("---\nname: Bug\n---\n## Test\n")

            manager = TemplateManager(Path(tmpdir))
            templates = manager.get_project_templates()

            assert "config" not in templates
            assert "bug" in templates

    def test_manager_get_aliases_for_type(self) -> None:
        """Test getting aliases for a template name."""
        manager = TemplateManager()
        aliases = manager.get_aliases_for_type("bug_report")
        assert "bug" in aliases

        aliases = manager.get_aliases_for_type("feature_request")
        assert "feat" in aliases
        assert "feature" in aliases

    def test_manager_format_available_types_message(self) -> None:
        """Test formatting available types message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_dir = Path(tmpdir) / ".github" / "ISSUE_TEMPLATE"
            template_dir.mkdir(parents=True)

            (template_dir / "bug_report.md").write_text("""---
name: Bug Report
about: Report a bug
---
## Test
""")

            manager = TemplateManager(Path(tmpdir))
            message = manager.format_available_types_message()

            assert "bug_report" in message
            assert "Report a bug" in message
