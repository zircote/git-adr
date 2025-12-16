"""Issue Template models and parsing.

This module defines data structures for GitHub issue templates and provides
parsing for both Markdown (.md) and YAML form (.yml) templates.

Supports:
- Markdown templates with YAML frontmatter + section-based body
- YAML form templates with structured input elements

Template Resolution:
1. Project's `.github/ISSUE_TEMPLATE/` (user customizations)
2. Bundled templates in package resources (offline/air-gapped support)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import frontmatter
import yaml


class FormElementType(str, Enum):
    """Types of form elements in YAML issue templates.

    These correspond to GitHub's issue form schema types.
    """

    MARKDOWN = "markdown"
    INPUT = "input"
    TEXTAREA = "textarea"
    DROPDOWN = "dropdown"
    CHECKBOXES = "checkboxes"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_string(cls, value: str) -> FormElementType:
        """Parse an element type string, case-insensitive.

        Args:
            value: Element type string.

        Returns:
            Matching FormElementType.

        Raises:
            ValueError: If type is not recognized.
        """
        value_lower = value.lower().strip()
        for element_type in cls:
            if element_type.value == value_lower:
                return element_type
        raise ValueError(f"Unknown form element type: {value}")


@dataclass
class FormElement:
    """A single form element in a YAML issue template.

    Represents input, textarea, dropdown, checkboxes, or markdown elements.
    """

    type: FormElementType
    id: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    validations: dict[str, Any] = field(default_factory=dict)

    @property
    def label(self) -> str:
        """Get the display label for this element."""
        return str(self.attributes.get("label", self.id or ""))

    @property
    def required(self) -> bool:
        """Check if this field is required."""
        return bool(self.validations.get("required", False))

    @property
    def placeholder(self) -> str | None:
        """Get the placeholder text for this element."""
        return self.attributes.get("placeholder")

    @property
    def description(self) -> str | None:
        """Get the description/hint for this element."""
        return self.attributes.get("description")

    @property
    def options(self) -> list[str]:
        """Get options for dropdown or checkboxes elements."""
        return self.attributes.get("options", [])

    @property
    def default_value(self) -> str | None:
        """Get the default/render value for this element."""
        return self.attributes.get("value") or self.attributes.get("render")

    @property
    def is_promptable(self) -> bool:
        """Check if this element should be prompted to the user.

        Markdown elements are display-only and shouldn't be prompted.
        """
        return self.type != FormElementType.MARKDOWN

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FormElement:
        """Create a FormElement from a dictionary.

        Args:
            data: Dictionary from YAML body element.

        Returns:
            FormElement instance.
        """
        type_str = data.get("type", "input")
        try:
            element_type = FormElementType.from_string(type_str)
        except ValueError:
            element_type = FormElementType.INPUT

        return cls(
            type=element_type,
            id=data.get("id"),
            attributes=dict(data.get("attributes", {})),
            validations=dict(data.get("validations", {})),
        )


@dataclass
class TemplateSection:
    """A section in a markdown issue template.

    Extracted from ## headers in the template body.
    """

    header: str
    hint: str = ""
    required: bool = True

    @property
    def id(self) -> str:
        """Generate a lowercase ID from the header."""
        return self.header.lower().replace(" ", "_")

    @classmethod
    def from_markdown(cls, header: str, content: str) -> TemplateSection:
        """Create a TemplateSection from markdown header and content.

        Args:
            header: Section header text (without ##).
            content: Section body content.

        Returns:
            TemplateSection instance.
        """
        # Use the content as hint text, stripping placeholder markers
        hint = content.strip()
        if hint.startswith("<!--") and hint.endswith("-->"):
            hint = hint[4:-3].strip()
        elif not hint:
            hint = f"Enter {header.lower()}"

        return cls(
            header=header,
            hint=hint,
            required=True,  # Default to required; can be overridden
        )


@dataclass
class IssueTemplate:
    """A GitHub issue template.

    Supports both Markdown (.md) and YAML form (.yml) templates.
    """

    # Metadata (from frontmatter or top-level YAML keys)
    name: str
    about: str = ""
    title: str = ""
    labels: list[str] = field(default_factory=list)
    assignees: list[str] = field(default_factory=list)

    # Content (mutually exclusive - one or the other)
    sections: list[TemplateSection] = field(default_factory=list)  # For .md templates
    body: list[FormElement] = field(default_factory=list)  # For .yml templates

    # Source metadata
    source_path: Path | None = None
    is_yaml_form: bool = False

    @property
    def promptable_fields(self) -> list[FormElement | TemplateSection]:
        """Get all fields that should be prompted to the user.

        Returns form elements (excluding markdown) or template sections.
        """
        if self.is_yaml_form:
            return [el for el in self.body if el.is_promptable]
        return list(self.sections)

    @property
    def has_fields(self) -> bool:
        """Check if the template has any promptable fields."""
        return len(self.promptable_fields) > 0

    def get_field_by_id(self, field_id: str) -> FormElement | TemplateSection | None:
        """Get a field by its ID.

        Args:
            field_id: The field ID to look up.

        Returns:
            The matching field, or None if not found.
        """
        for template_field in self.promptable_fields:
            if (
                isinstance(template_field, FormElement)
                and template_field.id == field_id
            ):
                return template_field
            if (
                isinstance(template_field, TemplateSection)
                and template_field.id == field_id
            ):
                return template_field
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert template metadata to dictionary.

        Returns:
            Dictionary suitable for serialization.
        """
        data: dict[str, Any] = {
            "name": self.name,
        }

        if self.about:
            data["about"] = self.about
        if self.title:
            data["title"] = self.title
        if self.labels:
            data["labels"] = self.labels
        if self.assignees:
            data["assignees"] = self.assignees

        return data


# =============================================================================
# Parsing Functions
# =============================================================================


def parse_markdown_template(path: Path) -> IssueTemplate:
    """Parse a Markdown issue template (.md) with YAML frontmatter.

    Args:
        path: Path to the template file.

    Returns:
        Parsed IssueTemplate.

    Raises:
        ValueError: If the template cannot be parsed.
    """
    try:
        text = path.read_text()
    except OSError as e:
        raise ValueError(f"Cannot read template file: {e}") from e

    return parse_markdown_template_string(text, source_path=path)


def parse_markdown_template_string(
    text: str, source_path: Path | None = None
) -> IssueTemplate:
    """Parse a Markdown issue template from string content.

    Args:
        text: Template content as string.
        source_path: Optional source path for metadata.

    Returns:
        Parsed IssueTemplate.

    Raises:
        ValueError: If the template cannot be parsed.
    """
    try:
        post = frontmatter.loads(text)
    except yaml.YAMLError as e:
        msg = "Invalid YAML frontmatter"
        if source_path:
            msg += f" in '{source_path}'"
        msg += f": {e}"
        raise ValueError(msg) from e

    # Extract frontmatter metadata
    metadata = dict(post.metadata)
    name = str(metadata.get("name", source_path.stem if source_path else "Untitled"))
    about = str(metadata.get("about", ""))
    title = str(metadata.get("title", ""))

    # Parse labels (can be string or list)
    labels_raw = metadata.get("labels", [])
    if isinstance(labels_raw, str):
        labels = [lbl.strip() for lbl in labels_raw.split(",") if lbl.strip()]
    else:
        labels = list(labels_raw) if labels_raw else []

    # Parse assignees (can be string or list)
    assignees_raw = metadata.get("assignees", [])
    if isinstance(assignees_raw, str):
        assignees = [a.strip() for a in assignees_raw.split(",") if a.strip()]
    else:
        assignees = list(assignees_raw) if assignees_raw else []

    # Extract sections from markdown body
    sections = _extract_markdown_sections(post.content)

    return IssueTemplate(
        name=name,
        about=about,
        title=title,
        labels=labels,
        assignees=assignees,
        sections=sections,
        source_path=source_path,
        is_yaml_form=False,
    )


def _extract_markdown_sections(content: str) -> list[TemplateSection]:
    """Extract sections from markdown content.

    Args:
        content: Markdown body content.

    Returns:
        List of TemplateSection instances.
    """
    import re

    sections: list[TemplateSection] = []
    current_header = ""
    current_content: list[str] = []

    for line in content.split("\n"):
        # Check for ## header
        header_match = re.match(r"^##\s+(.+)$", line)
        if header_match:
            # Save previous section
            if current_header:
                section = TemplateSection.from_markdown(
                    current_header, "\n".join(current_content)
                )
                sections.append(section)

            current_header = header_match.group(1).strip()
            current_content = []
        else:
            current_content.append(line)

    # Save last section
    if current_header:
        section = TemplateSection.from_markdown(
            current_header, "\n".join(current_content)
        )
        sections.append(section)

    return sections


def parse_yaml_form(path: Path) -> IssueTemplate:
    """Parse a YAML issue form template (.yml).

    Args:
        path: Path to the template file.

    Returns:
        Parsed IssueTemplate.

    Raises:
        ValueError: If the template cannot be parsed.
    """
    try:
        text = path.read_text()
    except OSError as e:
        raise ValueError(f"Cannot read template file: {e}") from e

    return parse_yaml_form_string(text, source_path=path)


def parse_yaml_form_string(text: str, source_path: Path | None = None) -> IssueTemplate:
    """Parse a YAML issue form template from string content.

    Args:
        text: Template content as string.
        source_path: Optional source path for metadata.

    Returns:
        Parsed IssueTemplate.

    Raises:
        ValueError: If the template cannot be parsed.
    """
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        if source_path:
            raise ValueError(f"Invalid YAML in {source_path}: {e}") from e
        else:
            raise ValueError(f"Invalid YAML: {e}") from e

    if not isinstance(data, dict):
        raise ValueError("YAML template must be a mapping")

    # Extract top-level metadata
    name = str(data.get("name", source_path.stem if source_path else "Untitled"))
    description = str(data.get("description", ""))
    title = str(data.get("title", ""))

    # Parse labels (can be list or comma-separated string)
    labels_raw = data.get("labels", [])
    if isinstance(labels_raw, str):
        labels = [lbl.strip() for lbl in labels_raw.split(",") if lbl.strip()]
    else:
        labels = list(labels_raw) if labels_raw else []

    # Parse assignees
    assignees_raw = data.get("assignees", [])
    if isinstance(assignees_raw, str):
        assignees = [a.strip() for a in assignees_raw.split(",") if a.strip()]
    else:
        assignees = list(assignees_raw) if assignees_raw else []

    # Parse body elements
    body_raw = data.get("body", [])
    body: list[FormElement] = []
    for element_data in body_raw:
        if isinstance(element_data, dict):
            element = FormElement.from_dict(element_data)
            body.append(element)

    return IssueTemplate(
        name=name,
        about=description,
        title=title,
        labels=labels,
        assignees=assignees,
        body=body,
        source_path=source_path,
        is_yaml_form=True,
    )


def parse_template(path: Path) -> IssueTemplate:
    """Parse an issue template from file, auto-detecting format.

    Args:
        path: Path to the template file.

    Returns:
        Parsed IssueTemplate.

    Raises:
        ValueError: If the template format is not recognized or cannot be parsed.
    """
    suffix = path.suffix.lower()

    if suffix in (".yml", ".yaml"):
        return parse_yaml_form(path)
    elif suffix == ".md":
        return parse_markdown_template(path)
    else:
        raise ValueError(f"Unsupported template format: {suffix}")


# =============================================================================
# Template Manager
# =============================================================================

# Type aliases: short names mapping to template filenames
TYPE_ALIASES: dict[str, str] = {
    "bug": "bug_report",
    "feat": "feature_request",
    "feature": "feature_request",
    "docs": "documentation",
    "doc": "documentation",
}


class TemplateManager:
    """Manages issue template discovery and resolution.

    Discovers templates from:
    1. Bundled package resources (always available, offline/air-gapped)
    2. Project's `.github/ISSUE_TEMPLATE/` directory (user customizations)

    Project templates override bundled templates with the same name.
    """

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize the TemplateManager.

        Args:
            project_root: Path to the project root. If None, uses current directory.
        """
        self._project_root = project_root or Path.cwd()
        self._templates: dict[str, IssueTemplate] = {}
        self._loaded = False

    @property
    def project_template_dir(self) -> Path:
        """Get the project's issue template directory."""
        return self._project_root / ".github" / "ISSUE_TEMPLATE"

    def _ensure_loaded(self) -> None:
        """Ensure templates are loaded (lazy loading)."""
        if not self._loaded:
            self._templates = self.discover_templates()
            self._loaded = True

    def get_bundled_templates(self) -> dict[str, IssueTemplate]:
        """Load bundled templates from package resources.

        Returns:
            Dictionary mapping template names to IssueTemplate instances.
        """
        templates: dict[str, IssueTemplate] = {}

        try:
            # Use importlib.resources for Python 3.9+ style
            import importlib.resources as pkg_resources

            # Navigate to the templates/issues directory
            try:
                # Python 3.11+ style
                files = pkg_resources.files("git_adr") / "templates" / "issues"
                for item in files.iterdir():
                    if item.name.endswith((".md", ".yml", ".yaml")):
                        # Read the file content
                        content = item.read_text()
                        name = item.name.rsplit(".", 1)[0]

                        # Parse based on extension
                        if item.name.endswith(".md"):
                            template = parse_markdown_template_string(content)
                        else:
                            template = parse_yaml_form_string(content)

                        templates[name] = template
            except (TypeError, AttributeError):
                # Fallback for older Python or missing package data
                pass
        except ImportError:
            # importlib.resources not available
            pass

        return templates

    def get_project_templates(self) -> dict[str, IssueTemplate]:
        """Load templates from project's .github/ISSUE_TEMPLATE/ directory.

        Returns:
            Dictionary mapping template names to IssueTemplate instances.
        """
        templates: dict[str, IssueTemplate] = {}
        template_dir = self.project_template_dir

        if not template_dir.exists():
            return templates

        # Find all template files
        for path in template_dir.iterdir():
            if path.is_file() and path.suffix.lower() in (".md", ".yml", ".yaml"):
                # Skip config.yml - it's GitHub's template chooser config
                if path.name.lower() == "config.yml":
                    continue

                try:
                    template = parse_template(path)
                    name = path.stem
                    templates[name] = template
                except ValueError:
                    # Skip templates that can't be parsed
                    continue

        return templates

    def discover_templates(self) -> dict[str, IssueTemplate]:
        """Discover all available templates.

        Resolution order (highest priority first):
        1. Project templates (user customizations)
        2. Bundled templates (always available)

        Returns:
            Dictionary mapping template names to IssueTemplate instances.
        """
        # Start with bundled templates
        templates = self.get_bundled_templates()

        # Override with project templates
        templates.update(self.get_project_templates())

        return templates

    def get_template(self, type_or_name: str) -> IssueTemplate | None:
        """Get a template by type alias or filename.

        Args:
            type_or_name: Type alias (bug, feat, docs) or template filename (without extension).

        Returns:
            Matching IssueTemplate, or None if not found.
        """
        self._ensure_loaded()

        # Resolve alias if present
        resolved_name = TYPE_ALIASES.get(type_or_name.lower(), type_or_name.lower())

        return self._templates.get(resolved_name)

    def get_available_types(self) -> list[str]:
        """Get list of available template types/names.

        Returns:
            Sorted list of available template names.
        """
        self._ensure_loaded()
        return sorted(self._templates.keys())

    def get_type_aliases(self) -> dict[str, str]:
        """Get the mapping of type aliases to template names.

        Returns:
            Dictionary of alias -> template name.
        """
        return dict(TYPE_ALIASES)

    def get_aliases_for_type(self, template_name: str) -> list[str]:
        """Get all aliases that map to a template name.

        Args:
            template_name: The template name to find aliases for.

        Returns:
            List of aliases (may be empty).
        """
        return [alias for alias, name in TYPE_ALIASES.items() if name == template_name]

    def format_available_types_message(self) -> str:
        """Format a user-friendly message listing available types.

        Returns:
            Formatted string for display.
        """
        self._ensure_loaded()

        lines = ["Available issue types:"]

        for name in self.get_available_types():
            template = self._templates[name]
            aliases = self.get_aliases_for_type(name)

            if aliases:
                alias_str = ", ".join(aliases)
                lines.append(f"  {name} (aliases: {alias_str})")
            else:
                lines.append(f"  {name}")

            if template.about:
                lines.append(f"    {template.about}")

        return "\n".join(lines)

    def reload(self) -> None:
        """Force reload of all templates."""
        self._loaded = False
        self._templates = {}
        self._ensure_loaded()
