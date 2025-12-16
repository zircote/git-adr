"""SDLC Integration Templates.

This module provides Jinja2 templates for CI/CD workflows and governance
patterns to integrate git-adr into the Software Development Lifecycle.

Template Categories:
- ci/: CI/CD workflow templates (GitHub Actions, GitLab CI)
- governance/: PR templates, issue templates, CODEOWNERS patterns
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

# Template directory path
TEMPLATES_DIR = Path(__file__).parent


def get_template_environment() -> Environment:
    """Get a configured Jinja2 environment for SDLC templates.

    Returns:
        Jinja2 Environment configured with:
        - FileSystemLoader pointing to templates directory
        - Autoescape for yaml, yml, md extensions
        - Trim and lstrip blocks enabled for cleaner output
    """
    return Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["yaml", "yml", "md"]),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )


def render_template(template_path: str, **context: Any) -> str:
    """Render a template with the given context.

    Args:
        template_path: Path to template relative to templates dir
                      (e.g., "ci/github-actions-sync.yml.j2")
        **context: Template variables to substitute

    Returns:
        Rendered template content as string

    Raises:
        jinja2.TemplateNotFound: If template doesn't exist
    """
    env = get_template_environment()
    template = env.get_template(template_path)
    return template.render(**context)


def list_templates(category: str | None = None) -> list[str]:
    """List available templates.

    Args:
        category: Optional category to filter by ("ci" or "governance")

    Returns:
        List of template paths relative to templates directory
    """
    templates: list[str] = []

    if category:
        search_dir = TEMPLATES_DIR / category
        if search_dir.exists():
            for template in search_dir.glob("*.j2"):
                templates.append(f"{category}/{template.name}")
    else:
        for category_dir in ["ci", "governance"]:
            search_dir = TEMPLATES_DIR / category_dir
            if search_dir.exists():
                for template in search_dir.glob("*.j2"):
                    templates.append(f"{category_dir}/{template.name}")

    return sorted(templates)


__all__ = [
    "TEMPLATES_DIR",
    "get_template_environment",
    "render_template",
    "list_templates",
]
