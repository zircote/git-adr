"""Issue model and building utilities.

This module provides the core Issue data model and IssueBuilder for
constructing issues from templates and user input.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

import frontmatter

if TYPE_CHECKING:
    from git_adr.core.issue_template import (
        FormElement,
        IssueTemplate,
        TemplateSection,
    )


@dataclass
class Issue:
    """A GitHub issue ready for submission or local storage.

    Contains all the data needed to create a GitHub issue:
    - title: Issue title
    - body: Rendered markdown body
    - labels: List of label names
    - assignees: List of GitHub usernames
    """

    title: str
    body: str
    labels: list[str] = field(default_factory=list)
    assignees: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Serialize issue to markdown with YAML frontmatter.

        The frontmatter contains metadata (labels, assignees) and the
        body becomes the markdown content.

        Returns:
            Complete issue document as string.
        """
        post = frontmatter.Post(self.body)
        post.metadata = {
            "title": self.title,
        }

        if self.labels:
            post.metadata["labels"] = self.labels
        if self.assignees:
            post.metadata["assignees"] = self.assignees

        return frontmatter.dumps(post)

    @classmethod
    def from_markdown(cls, text: str) -> Issue:
        """Parse an issue from markdown with YAML frontmatter.

        Args:
            text: Complete issue document.

        Returns:
            Parsed Issue instance.

        Raises:
            ValueError: If the document cannot be parsed.
        """
        try:
            post = frontmatter.loads(text)
        except Exception as e:
            raise ValueError(f"Invalid issue document: {e}") from e

        metadata = dict(post.metadata)

        return cls(
            title=str(metadata.get("title", "")),
            body=post.content,
            labels=list(metadata.get("labels", [])),
            assignees=list(metadata.get("assignees", [])),
        )

    @classmethod
    def from_template(
        cls,
        template: IssueTemplate,
        values: dict[str, str],
        title: str | None = None,
    ) -> Issue:
        """Create an issue from a template and field values.

        Args:
            template: The IssueTemplate to use.
            values: Dictionary mapping field IDs to user-provided values.
            title: Optional override for the issue title.

        Returns:
            Issue instance with rendered body.
        """
        # Determine title
        final_title = title or template.title or ""

        # Build body from template sections/fields
        body_parts: list[str] = []

        if template.is_yaml_form:
            # YAML form: render each element
            for element in template.body:
                if element.id and element.id in values:
                    body_parts.append(f"## {element.label}")
                    body_parts.append("")
                    body_parts.append(values[element.id])
                    body_parts.append("")
        else:
            # Markdown template: render each section
            for section in template.sections:
                section_id = section.id
                value = values.get(section_id, "")

                body_parts.append(f"## {section.header}")
                body_parts.append("")
                body_parts.append(value if value else section.hint)
                body_parts.append("")

        return cls(
            title=final_title,
            body="\n".join(body_parts).strip(),
            labels=list(template.labels),
            assignees=list(template.assignees),
        )


class IssueBuilder:
    """Builder for constructing issues from templates interactively.

    Provides a fluent interface for setting field values and validating
    that all required fields are filled before building.
    """

    def __init__(self, template: IssueTemplate) -> None:
        """Initialize the builder with a template.

        Args:
            template: The IssueTemplate to build from.
        """
        self._template = template
        self._title: str = template.title
        self._values: dict[str, str] = {}
        self._labels: list[str] = list(template.labels)
        self._assignees: list[str] = list(template.assignees)

    @property
    def template(self) -> IssueTemplate:
        """Get the template being used."""
        return self._template

    @property
    def title(self) -> str:
        """Get the current title."""
        return self._title

    def set_title(self, title: str) -> IssueBuilder:
        """Set the issue title.

        Args:
            title: The issue title.

        Returns:
            Self for method chaining.
        """
        self._title = title
        return self

    def set_field(self, field_id: str, value: str) -> IssueBuilder:
        """Set a field value.

        Args:
            field_id: The field ID (section header ID or form element ID).
            value: The value for this field.

        Returns:
            Self for method chaining.
        """
        self._values[field_id] = value
        return self

    def get_field(self, field_id: str) -> str | None:
        """Get the current value of a field.

        Args:
            field_id: The field ID.

        Returns:
            The field value, or None if not set.
        """
        return self._values.get(field_id)

    def add_label(self, label: str) -> IssueBuilder:
        """Add a label.

        Args:
            label: Label name to add.

        Returns:
            Self for method chaining.
        """
        if label not in self._labels:
            self._labels.append(label)
        return self

    def remove_label(self, label: str) -> IssueBuilder:
        """Remove a label.

        Args:
            label: Label name to remove.

        Returns:
            Self for method chaining.
        """
        if label in self._labels:
            self._labels.remove(label)
        return self

    def set_assignees(self, assignees: list[str]) -> IssueBuilder:
        """Set the assignees list.

        Args:
            assignees: List of GitHub usernames.

        Returns:
            Self for method chaining.
        """
        self._assignees = list(assignees)
        return self

    def is_complete(self) -> bool:
        """Check if all required fields are filled.

        Returns:
            True if all required fields have values.
        """
        return len(self.missing_required_fields()) == 0

    def missing_required_fields(self) -> list[str]:
        """Get list of required fields that are missing values.

        Returns:
            List of field IDs that need values.
        """
        missing: list[str] = []

        # Title is always required
        if not self._title or not self._title.strip():
            missing.append("title")

        # Check template fields
        for template_field in self._template.promptable_fields:
            field_id = self._get_field_id(template_field)
            is_required = self._is_field_required(template_field)

            if is_required and not self._values.get(field_id, "").strip():
                missing.append(field_id)

        return missing

    def _get_field_id(self, field: FormElement | TemplateSection) -> str:
        """Get the ID for a field."""
        from git_adr.core.issue_template import FormElement, TemplateSection

        if isinstance(field, FormElement):
            return field.id or ""
        if isinstance(field, TemplateSection):
            return field.id
        return ""

    def _is_field_required(self, field: FormElement | TemplateSection) -> bool:
        """Check if a field is required."""
        from git_adr.core.issue_template import FormElement, TemplateSection

        if isinstance(field, FormElement):
            return field.required
        if isinstance(field, TemplateSection):
            return field.required
        return False

    def build(self) -> Issue:
        """Build the final Issue.

        Returns:
            Completed Issue instance.

        Raises:
            ValueError: If required fields are missing.
        """
        missing = self.missing_required_fields()
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        return Issue.from_template(
            self._template,
            self._values,
            title=self._title,
        )

    def preview(self) -> str:
        """Generate a preview of the issue body.

        Returns markdown preview even if not all fields are complete.

        Returns:
            Rendered markdown preview.
        """
        body_parts: list[str] = []

        # Add title preview
        title_display = self._title if self._title else "[Title not set]"
        body_parts.append(f"# {title_display}")
        body_parts.append("")

        # Add labels if present
        if self._labels:
            labels_str = ", ".join(f"`{label}`" for label in self._labels)
            body_parts.append(f"**Labels:** {labels_str}")
            body_parts.append("")

        # Add assignees if present
        if self._assignees:
            assignees_str = ", ".join(f"@{a}" for a in self._assignees)
            body_parts.append(f"**Assignees:** {assignees_str}")
            body_parts.append("")

        body_parts.append("---")
        body_parts.append("")

        # Add fields
        if self._template.is_yaml_form:
            for element in self._template.body:
                if element.id:
                    value = self._values.get(element.id, "")
                    body_parts.append(f"## {element.label}")
                    body_parts.append("")
                    body_parts.append(
                        value if value else f"*[{element.label} not provided]*"
                    )
                    body_parts.append("")
        else:
            for section in self._template.sections:
                value = self._values.get(section.id, "")
                body_parts.append(f"## {section.header}")
                body_parts.append("")
                body_parts.append(
                    value if value else f"*[{section.header} not provided]*"
                )
                body_parts.append("")

        return "\n".join(body_parts).strip()


# =============================================================================
# Local File Storage
# =============================================================================


def generate_issue_filename(title: str) -> str:
    """Generate a filename for a local issue file.

    Format: YYYY-MM-DD-slug.md

    Args:
        title: The issue title.

    Returns:
        Generated filename.
    """
    date_prefix = date.today().strftime("%Y-%m-%d")
    slug = _slugify(title)

    # Truncate slug to reasonable length
    max_slug_length = 50
    if len(slug) > max_slug_length:
        slug = slug[:max_slug_length].rsplit("-", 1)[0]

    return f"{date_prefix}-{slug}.md"


def _slugify(text: str) -> str:
    """Convert text to a URL-safe slug.

    Args:
        text: Text to slugify.

    Returns:
        Lowercase slug with hyphens.
    """
    # Remove title prefixes like [BUG], [FEATURE], etc.
    text = re.sub(r"^\[[A-Z]+\]\s*", "", text)

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

    return slug or "untitled"


def save_local_issue(
    issue: Issue,
    output_dir: Path | None = None,
    filename: str | None = None,
) -> Path:
    """Save an issue as a local markdown file.

    Args:
        issue: The Issue to save.
        output_dir: Directory to save to. Defaults to `.github/issues/`.
        filename: Optional custom filename. If None, generates from title.

    Returns:
        Path to the saved file.

    Raises:
        OSError: If the file cannot be written.
    """
    # Default output directory
    if output_dir is None:
        output_dir = Path.cwd() / ".github" / "issues"

    # Create directory if needed
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename if not provided
    if filename is None:
        filename = generate_issue_filename(issue.title)

    # Ensure .md extension
    if not filename.endswith(".md"):
        filename = f"{filename}.md"

    # Write file
    output_path = output_dir / filename
    output_path.write_text(issue.to_markdown())

    return output_path
