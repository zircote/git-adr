"""Template Engine for ADR formats.

This module provides template rendering and format conversion for
various ADR formats:
- MADR 4.0 (default) - Full template with options analysis
- Nygard - Original minimal format
- Y-Statement - Single-sentence decision format
- Alexandrian - Pattern-language inspired
- Business Case - Extended business justification
- Planguage - Quality-focused measurable format
- Custom - User-provided templates
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from git_adr.core.adr import ADR

# =============================================================================
# Template Definitions
# =============================================================================

MADR_TEMPLATE = """# {title}

## Status

{status}

## Context

<!-- Describe the context and problem statement -->

## Decision

<!-- Describe the decision that was made -->

## Consequences

### Positive

<!-- List positive consequences -->

### Negative

<!-- List negative consequences -->

### Neutral

<!-- List neutral consequences -->

## Options Considered

### Option 1: [Name]

<!-- Description, pros, cons -->

### Option 2: [Name]

<!-- Description, pros, cons -->

## Decision Outcome

Chosen option: "[option name]", because [justification].

## More Information

<!-- Links, references, related ADRs -->
"""

NYGARD_TEMPLATE = """# {title}

## Status

{status}

## Context

<!-- What is the issue that we're seeing that is motivating this decision or change? -->

## Decision

<!-- What is the change that we're proposing and/or doing? -->

## Consequences

<!-- What becomes easier or more difficult to do because of this change? -->
"""

Y_STATEMENT_TEMPLATE = """# {title}

## Status

{status}

## Decision

In the context of [context],
facing [concern],
we decided [decision],
to achieve [goal],
accepting [tradeoff].

## More Information

<!-- Additional context or references -->
"""

ALEXANDRIAN_TEMPLATE = """# {title}

## Status

{status}

## Context

<!-- The situation that gives rise to the need for this decision -->

## Forces

<!-- The competing constraints and concerns -->

## Problem

<!-- The specific problem or question being addressed -->

## Solution

<!-- The decision or approach chosen -->

## Resulting Context

<!-- The situation after applying the solution -->

## Related Patterns

<!-- Links to related ADRs or patterns -->
"""

BUSINESS_CASE_TEMPLATE = """# {title}

## Status

{status}

## Executive Summary

<!-- Brief overview for stakeholders -->

## Business Context

<!-- Business drivers and strategic alignment -->

## Problem Statement

<!-- Clear description of the problem -->

## Proposed Solution

<!-- The recommended approach -->

## Options Analysis

### Option 1: [Name]

**Cost:** [estimate]
**Time:** [estimate]
**Risk:** [Low/Medium/High]

**Pros:**
-

**Cons:**
-

### Option 2: [Name]

**Cost:** [estimate]
**Time:** [estimate]
**Risk:** [Low/Medium/High]

**Pros:**
-

**Cons:**
-

## Financial Impact

<!-- Cost/benefit analysis, ROI -->

## Risk Assessment

<!-- Identified risks and mitigation strategies -->

## Implementation Plan

<!-- High-level implementation approach -->

## Approval

| Role | Name | Date | Decision |
|------|------|------|----------|
| Sponsor | | | |
| Architect | | | |
| Tech Lead | | | |
"""

PLANGUAGE_TEMPLATE = """# {title}

## Status

{status}

## Tag

{id}

## Gist

<!-- One-sentence summary of the decision -->

## Background

<!-- Context and motivation -->

## Scale

<!-- Measurement scale for success -->

## Meter

<!-- How success will be measured -->

## Past

<!-- Current state/baseline -->

## Must

<!-- Minimum acceptable level (hard constraint) -->

## Plan

<!-- Target level (expected outcome) -->

## Wish

<!-- Ideal level (stretch goal) -->

## Assumptions

<!-- Key assumptions underlying this decision -->

## Risks

<!-- Potential risks and mitigation -->
"""


# =============================================================================
# Template Registry
# =============================================================================

TEMPLATES: dict[str, str] = {
    "madr": MADR_TEMPLATE,
    "nygard": NYGARD_TEMPLATE,
    "y-statement": Y_STATEMENT_TEMPLATE,
    "alexandrian": ALEXANDRIAN_TEMPLATE,
    "business": BUSINESS_CASE_TEMPLATE,
    "planguage": PLANGUAGE_TEMPLATE,
}

TEMPLATE_DESCRIPTIONS: dict[str, str] = {
    "madr": "MADR 4.0 - Full template with options analysis (default)",
    "nygard": "Nygard - Original minimal ADR format",
    "y-statement": "Y-Statement - Single-sentence decision format",
    "alexandrian": "Alexandrian - Pattern-language inspired format",
    "business": "Business Case - Extended business justification",
    "planguage": "Planguage - Quality-focused measurable format",
}


# =============================================================================
# Template Engine
# =============================================================================


@dataclass
class TemplateContext:
    """Context for template rendering.

    Contains all the variables available for substitution in templates.
    """

    id: str
    title: str
    date: date
    status: str
    tags: list[str]
    deciders: list[str]
    supersedes: str | None = None

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary for template substitution.

        Returns:
            Dictionary with string values.
        """
        return {
            "id": self.id,
            "title": self.title,
            "date": self.date.isoformat(),
            "status": self.status,
            "tags": ", ".join(self.tags) if self.tags else "",
            "deciders": ", ".join(self.deciders) if self.deciders else "",
            "supersedes": self.supersedes or "",
        }


class TemplateEngine:
    """Engine for rendering and converting ADR templates.

    Supports built-in formats and custom templates loaded from files.
    """

    def __init__(self, custom_templates_dir: Path | None = None) -> None:
        """Initialize the template engine.

        Args:
            custom_templates_dir: Directory containing custom templates.
        """
        self._templates = dict(TEMPLATES)
        self._custom_dir = custom_templates_dir

        # Load custom templates if directory exists
        if custom_templates_dir and custom_templates_dir.exists():
            self._load_custom_templates(custom_templates_dir)

    def _load_custom_templates(self, directory: Path) -> None:
        """Load custom templates from a directory.

        Custom templates should be named {format_name}.md

        Args:
            directory: Directory containing template files.
        """
        for template_file in directory.glob("*.md"):
            format_name = template_file.stem
            try:
                template_content = template_file.read_text()
                self._templates[format_name] = template_content
            except OSError:
                continue

    def list_formats(self) -> list[str]:
        """List all available format names.

        Returns:
            List of format names.
        """
        return sorted(self._templates.keys())

    def get_template(self, format_name: str) -> str | None:
        """Get a template by format name.

        Args:
            format_name: Name of the format.

        Returns:
            Template string, or None if not found.
        """
        return self._templates.get(format_name)

    def render(
        self,
        format_name: str,
        context: TemplateContext,
    ) -> str:
        """Render a template with the given context.

        Args:
            format_name: Name of the format to render.
            context: Template context with values.

        Returns:
            Rendered template content.

        Raises:
            ValueError: If format is not found.
        """
        template = self.get_template(format_name)
        if template is None:
            available = ", ".join(self.list_formats())
            raise ValueError(f"Unknown format: {format_name}. Available: {available}")

        # Substitute context values
        content = template.format(**context.to_dict())

        return content

    def render_for_new(
        self,
        format_name: str,
        title: str,
        adr_id: str,
        status: str = "proposed",
        tags: list[str] | None = None,
        deciders: list[str] | None = None,
        supersedes: str | None = None,
    ) -> str:
        """Render a template for a new ADR.

        Convenience method that creates the context and renders.

        Args:
            format_name: Format name.
            title: ADR title.
            adr_id: Generated ADR ID.
            status: Initial status.
            tags: Optional tags.
            deciders: Optional deciders.
            supersedes: ID of superseded ADR.

        Returns:
            Rendered template content.
        """
        context = TemplateContext(
            id=adr_id,
            title=title,
            date=date.today(),
            status=status,
            tags=tags or [],
            deciders=deciders or [],
            supersedes=supersedes,
        )

        return self.render(format_name, context)

    def detect_format(self, content: str) -> str:
        """Detect the format of an existing ADR.

        Uses heuristics to identify the format based on content structure.

        Args:
            content: ADR content (without frontmatter).

        Returns:
            Detected format name, or "unknown".
        """
        content_lower = content.lower()

        # Check for distinctive sections
        if "## options considered" in content_lower:
            return "madr"
        if "## decision outcome" in content_lower:
            return "madr"

        if "in the context of" in content_lower and "we decided" in content_lower:
            return "y-statement"

        if "## forces" in content_lower and "## resulting context" in content_lower:
            return "alexandrian"

        if "## financial impact" in content_lower or "## approval" in content_lower:
            return "business"

        if "## scale" in content_lower and "## meter" in content_lower:
            return "planguage"

        # Default to nygard if has basic structure
        if "## context" in content_lower and "## decision" in content_lower:
            return "nygard"

        return "unknown"

    def convert(
        self,
        adr: ADR,
        target_format: str,
    ) -> str:
        """Convert an ADR to a different format.

        Attempts to preserve content while restructuring to the target format.

        Args:
            adr: Source ADR.
            target_format: Target format name.

        Returns:
            Converted content.

        Raises:
            ValueError: If target format is not found.
        """
        template = self.get_template(target_format)
        if template is None:
            raise ValueError(f"Unknown format: {target_format}")

        # Extract sections from source content
        sections = self._extract_sections(adr.content)

        # Create context from metadata
        context = TemplateContext(
            id=adr.metadata.id,
            title=adr.metadata.title,
            date=adr.metadata.date,
            status=str(adr.metadata.status),
            tags=adr.metadata.tags,
            deciders=adr.metadata.deciders,
            supersedes=adr.metadata.supersedes,
        )

        # Render base template
        content = self.render(target_format, context)

        # Merge extracted sections into the new format
        content = self._merge_sections(content, sections, target_format)

        return content

    def _extract_sections(self, content: str) -> dict[str, str]:
        """Extract sections from ADR content.

        Args:
            content: ADR markdown content.

        Returns:
            Dictionary mapping section name to content.
        """
        import re

        sections: dict[str, str] = {}
        current_section = ""
        current_content: list[str] = []

        for line in content.split("\n"):
            # Check for section header
            header_match = re.match(r"^##\s+(.+)$", line)
            if header_match:
                # Save previous section
                if current_section:
                    sections[current_section.lower()] = "\n".join(
                        current_content
                    ).strip()

                current_section = header_match.group(1)
                current_content = []
            else:
                current_content.append(line)

        # Save last section
        if current_section:
            sections[current_section.lower()] = "\n".join(current_content).strip()

        return sections

    def _merge_sections(
        self,
        template_content: str,
        sections: dict[str, str],
        target_format: str,
    ) -> str:
        """Merge extracted sections into a template.

        Args:
            template_content: Rendered template.
            sections: Extracted sections from source.
            target_format: Target format name.

        Returns:
            Content with sections merged.
        """
        import re

        # Define section mappings for common sections
        # Maps source section names to target section names
        mappings: dict[str, list[str]] = {
            "context": ["context", "background", "business context"],
            "decision": ["decision", "proposed solution", "solution"],
            "consequences": ["consequences", "resulting context"],
            "problem": ["problem", "problem statement"],
            "options": ["options considered", "options analysis"],
        }

        result = template_content

        for source_name, source_content in sections.items():
            if not source_content or "<!--" in source_content:
                continue

            # Find matching target section
            for canonical, targets in mappings.items():
                if source_name in targets or canonical in source_name:
                    # Try to replace placeholder content in target
                    for target_name in targets:
                        pattern = (
                            rf"(## {re.escape(target_name.title())}.*?\n)(<!-- .+? -->)"
                        )
                        replacement = rf"\1{source_content}"
                        result, count = re.subn(
                            pattern,
                            replacement,
                            result,
                            flags=re.IGNORECASE | re.DOTALL,
                        )
                        if count > 0:
                            break

        return result


def get_default_template_engine() -> TemplateEngine:
    """Get the default template engine.

    Returns:
        TemplateEngine with built-in templates.
    """
    return TemplateEngine()


def render_initial_adr(
    adr_id: str = "00000000-use-adrs",
    title: str = "Use Architecture Decision Records",
) -> str:
    """Render the initial ADR created during init.

    This ADR documents the decision to use ADRs for the project.

    Args:
        adr_id: ADR ID.
        title: ADR title.

    Returns:
        Rendered ADR content.
    """
    return f"""# {title}

## Status

accepted

## Context

We need to record the architectural decisions made on this project.

## Decision

We will use Architecture Decision Records (ADRs) stored in git notes,
as described by git-adr. This approach:

- Keeps ADRs invisible in the working tree but visible in history
- Eliminates merge conflicts from sequential numbering
- Associates decisions with implementing commits
- Syncs automatically with regular git operations

## Consequences

### Positive

- Decisions are documented and searchable
- Context is preserved for future team members
- ADRs don't clutter the repository file tree
- Natural integration with git workflow

### Negative

- Team members need to learn git-adr commands
- Git notes require configuration for remote sync

### Neutral

- Existing file-based ADRs can be imported
"""
