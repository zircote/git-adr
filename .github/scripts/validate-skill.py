#!/usr/bin/env python3
"""
Skill validation script for CI/CD.

Validates Claude Code skills against the Agent Skills Spec v1.0.
Based on skill-creator's quick_validate.py validation rules.

Usage:
    python validate-skill.py <skill_directory>

Exit codes:
    0 = Valid
    1 = Invalid or error
"""

import re
import sys
from pathlib import Path

import yaml


def validate_skill(skill_path: str) -> tuple[bool, str]:
    """
    Validate a skill directory against skill-spec rules.

    Args:
        skill_path: Path to the skill directory

    Returns:
        Tuple of (is_valid, message)
    """
    skill_path = Path(skill_path)

    # Check skill directory exists
    if not skill_path.exists():
        return False, f"Skill directory not found: {skill_path}"

    if not skill_path.is_dir():
        return False, f"Path is not a directory: {skill_path}"

    # Check SKILL.md exists
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return False, f"SKILL.md not found in {skill_path}"

    # Read content (explicit UTF-8 for cross-platform consistency)
    content = skill_md.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return False, "No YAML frontmatter found (must start with ---)"

    # Extract frontmatter
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return False, "Invalid frontmatter format (must have closing ---)"

    frontmatter_text = match.group(1)

    # Parse YAML frontmatter
    try:
        frontmatter = yaml.safe_load(frontmatter_text)
        if not isinstance(frontmatter, dict):
            return False, "Frontmatter must be a YAML dictionary"
    except yaml.YAMLError as e:
        return False, f"Invalid YAML in frontmatter: {e}"

    # Define allowed properties (per Agent Skills Spec v1.0)
    allowed_properties = {"name", "description", "license", "allowed-tools", "metadata"}

    # Check for unexpected properties
    unexpected_keys = set(frontmatter.keys()) - allowed_properties
    if unexpected_keys:
        return False, (
            f"Unexpected key(s) in frontmatter: {', '.join(sorted(unexpected_keys))}. "
            f"Allowed: {', '.join(sorted(allowed_properties))}"
        )

    # Check required fields
    if "name" not in frontmatter:
        return False, "Missing required 'name' field in frontmatter"
    if "description" not in frontmatter:
        return False, "Missing required 'description' field in frontmatter"

    # Validate name
    name = frontmatter.get("name", "")
    if not isinstance(name, str):
        return False, f"Name must be a string, got {type(name).__name__}"
    name = name.strip()

    if not name:
        return False, "Name cannot be empty"

    # Name must be hyphen-case (lowercase letters, digits, hyphens)
    if not re.match(r"^[a-z0-9-]+$", name):
        return False, (
            f"Name '{name}' must be hyphen-case "
            "(lowercase letters, digits, and hyphens only)"
        )

    # No boundary or consecutive hyphens
    if name.startswith("-") or name.endswith("-") or "--" in name:
        return False, (
            f"Name '{name}' cannot start/end with hyphen or contain consecutive hyphens"
        )

    # Max 64 characters
    if len(name) > 64:
        return False, f"Name too long ({len(name)} chars). Maximum is 64 characters."

    # Validate description
    description = frontmatter.get("description", "")
    if not isinstance(description, str):
        return False, f"Description must be a string, got {type(description).__name__}"
    description = description.strip()

    if not description:
        return False, "Description cannot be empty"

    # No angle brackets (avoid markup conflicts)
    if "<" in description or ">" in description:
        return False, "Description cannot contain angle brackets (< or >)"

    # Max 1024 characters
    if len(description) > 1024:
        return False, (
            f"Description too long ({len(description)} chars). Maximum is 1024 characters."
        )

    return True, f"Valid: {skill_path.name}"


def main() -> int:
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python validate-skill.py <skill_directory>")
        print("\nValidates a Claude Code skill against Agent Skills Spec v1.0")
        return 1

    skill_path = sys.argv[1]

    print(f"Validating skill: {skill_path}")

    valid, message = validate_skill(skill_path)

    if valid:
        print(f"✅ {message}")
        return 0
    else:
        print(f"❌ {message}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
