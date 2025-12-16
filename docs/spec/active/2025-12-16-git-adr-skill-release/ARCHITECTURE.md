---
document_type: architecture
project_id: SPEC-2025-12-16-001
version: 1.0.0
last_updated: 2025-12-16T15:00:00Z
status: draft
---

# git-adr Skill Release Workflow - Technical Architecture

## System Overview

This architecture adds skill packaging and documentation to the existing git-adr release infrastructure. The design follows the principle of minimal coupling - the skill release runs in parallel with existing jobs and does not block core functionality.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          GitHub Actions: release.yml                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Trigger: push tags v*  OR  workflow_dispatch                               │
│                                                                              │
│  ┌──────────────┐  ┌────────────────────┐  ┌──────────────────────┐         │
│  │    build     │  │ build-release-     │  │ build-skill-package │ (NEW)   │
│  │              │  │ artifacts          │  │                     │         │
│  │  • Python    │  │  • Man pages       │  │  • Validate skill   │         │
│  │    wheel     │  │  • Completions     │  │  • Package .skill   │         │
│  │  • sdist     │  │  • Tarball         │  │  • Upload artifact  │         │
│  └──────┬───────┘  └─────────┬──────────┘  └──────────┬──────────┘         │
│         │                    │                        │                     │
│         └────────────────────┼────────────────────────┘                     │
│                              │                                              │
│                              ▼                                              │
│                    ┌──────────────────┐                                     │
│                    │     release      │                                     │
│                    │                  │                                     │
│                    │  • Download all  │                                     │
│                    │    artifacts     │                                     │
│                    │  • Create GitHub │                                     │
│                    │    release       │                                     │
│                    │  • Attach files  │                                     │
│                    └────────┬─────────┘                                     │
│                             │                                               │
│                             ▼                                               │
│                    ┌──────────────────┐                                     │
│                    │     publish      │                                     │
│                    │                  │                                     │
│                    │  • PyPI upload   │                                     │
│                    └────────┬─────────┘                                     │
│                             │                                               │
│                             ▼                                               │
│                    ┌──────────────────┐                                     │
│                    │ update-homebrew  │                                     │
│                    │                  │                                     │
│                    │  • Formula sync  │                                     │
│                    └──────────────────┘                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Resolution | Rationale |
|----------|------------|-----------|
| Parallel execution | Skill job runs alongside build jobs | No dependencies, faster total time |
| Validation blocking | Validation failure stops skill packaging | Catch issues before release |
| Validation non-blocking release | Skill failure uses continue-on-error | Don't block Python release |
| Embedded validation | Python script in .github/scripts/ | No external dependency on skill-creator |
| ZIP format | .skill is a ZIP archive | Per skill-spec v1.0 |

## Component Design

### Component 1: Skill Validation Script

- **Purpose**: Validate SKILL.md against skill-spec rules before packaging
- **Location**: `.github/scripts/validate-skill.py`
- **Responsibilities**:
  - Check SKILL.md exists
  - Parse and validate YAML frontmatter
  - Enforce naming conventions (hyphen-case)
  - Enforce length limits (name: 64, description: 1024)
  - Check for disallowed characters
- **Interface**: CLI with exit code 0 (pass) or 1 (fail)
- **Dependencies**: Python 3.11+, PyYAML

### Component 2: Skill Packaging Job

- **Purpose**: Create versioned .skill package and upload as artifact
- **Location**: `.github/workflows/release.yml` (new job)
- **Responsibilities**:
  - Checkout repository
  - Extract version from tag/input
  - Run validation script
  - Create ZIP archive with skill directory
  - Upload artifact for release job
- **Interface**: GitHub Actions job with artifact output
- **Dependencies**: actions/checkout@v6, actions/upload-artifact@v6

### Component 3: Release Job Updates

- **Purpose**: Include skill package in GitHub release
- **Location**: `.github/workflows/release.yml` (existing job, modified)
- **Responsibilities**:
  - Download skill artifact (new step)
  - Include in release files (updated glob)
  - Add skill section to release body (updated template)
- **Dependencies**: actions/download-artifact@v6, softprops/action-gh-release@v2

### Component 4: Documentation Files

- **Purpose**: Explain skill value and installation
- **Files**:
  - `docs/git-adr-skill.md` - Comprehensive skill guide (new)
  - `README.md` - Enhanced skill section (existing, modified)
- **Responsibilities**:
  - Value proposition (4 key benefits)
  - Installation instructions (multiple methods)
  - Quick start example
  - Feature overview

## Data Design

### Skill Package Structure

The .skill file is a ZIP archive containing:

```
git-adr/                        # Skill directory (matches name in frontmatter)
├── SKILL.md                    # Entry point with frontmatter
└── references/                 # Supporting documentation
    ├── commands.md             # Command reference
    ├── configuration.md        # Configuration options
    ├── best-practices.md       # ADR guidance
    ├── workflows.md            # Workflow patterns
    └── formats/                # ADR format templates
        ├── madr.md
        ├── nygard.md
        ├── y-statement.md
        ├── alexandrian.md
        ├── business-case.md
        └── planguage.md
```

### Version Extraction Logic

```bash
# From tag (e.g., v0.2.0)
VERSION="${REF_NAME#v}"  # → 0.2.0

# From workflow_dispatch input (e.g., 0.2.0)
VERSION="${INPUT_VERSION}"  # → 0.2.0
```

### Artifact Flow

| Stage | Artifact Name | Contents |
|-------|---------------|----------|
| build-skill-package | `skill-package` | `git-adr-{version}.skill` |
| release | (downloaded) | Attached to GitHub release |

## Integration Points

### Internal Integrations

| System | Integration Type | Purpose |
|--------|-----------------|---------|
| release.yml | Workflow job | Add skill packaging job |
| release.yml | Release template | Include skill in release body |
| README.md | Documentation | Enhanced skill section |

### External Integrations

| Service | Integration Type | Purpose |
|---------|-----------------|---------|
| GitHub Releases | Artifact attachment | Distribute .skill file |
| GitHub Actions | CI/CD execution | Automated packaging |

## Validation Design

### Validation Rules (from skill-spec)

```python
VALIDATION_RULES = {
    "file_exists": "SKILL.md must exist",
    "frontmatter_present": "Must start with ---",
    "frontmatter_valid_yaml": "YAML must parse successfully",
    "frontmatter_is_dict": "Must be a YAML dictionary",
    "allowed_keys_only": "Only name, description, license, allowed-tools, metadata",
    "name_required": "name field must be present",
    "name_format": "lowercase letters, digits, hyphens only",
    "name_no_boundary_hyphens": "Cannot start/end with hyphen",
    "name_no_consecutive_hyphens": "Cannot contain --",
    "name_max_length": "64 characters maximum",
    "description_required": "description field must be present",
    "description_no_angle_brackets": "Cannot contain < or >",
    "description_max_length": "1024 characters maximum",
}
```

### Validation Script Interface

```bash
# Usage
python .github/scripts/validate-skill.py skills/git-adr

# Output (success)
✅ skills/git-adr: Valid

# Output (failure)
❌ skills/git-adr: Name 'Git-ADR' must be hyphen-case (lowercase, digits, hyphens only)

# Exit codes
# 0 = Valid
# 1 = Invalid or error
```

## Packaging Design

### ZIP Creation Logic

```bash
# Create versioned .skill file
VERSION="0.2.0"
SKILL_DIR="skills/git-adr"
OUTPUT="git-adr-${VERSION}.skill"

# Package (from skill parent directory to maintain structure)
cd skills
zip -r "../${OUTPUT}" git-adr/
```

The archive structure ensures that extracting to `~/.claude/skills/` creates:
```
~/.claude/skills/git-adr/SKILL.md
~/.claude/skills/git-adr/references/...
```

## Documentation Design

### docs/git-adr-skill.md Structure

```markdown
# git-adr Claude Code Skill

## Why Use This Skill?
[4 value propositions with examples]

## Installation
[3 methods: download, copy, extract]

## Quick Start
[30-second working example]

## Features
[Detailed capabilities]

## Configuration
[Optional customization]
```

### README.md Skill Section Enhancement

Current (lines 420-454):
- Basic installation
- Skill structure listing

Enhanced:
- Value proposition summary
- Multiple installation methods
- Link to full documentation
- Quick example

## Reliability & Operations

### Failure Modes

| Failure | Impact | Recovery |
|---------|--------|----------|
| Validation fails | Skill not packaged | Fix SKILL.md, re-release |
| Packaging fails | Skill not in release | Manual packaging or re-run |
| Artifact upload fails | Skill not in release | Re-run workflow |
| Release job fails | No release | Standard release debugging |

### Monitoring

- GitHub Actions workflow status
- Release asset verification (manual check)

## Testing Strategy

### Validation Script Testing

- Unit tests for each validation rule
- Edge cases (empty fields, max lengths, special characters)

### Workflow Testing

- Manual workflow_dispatch with test version
- Verify artifact contents

### Documentation Testing

- Install from packaged .skill file
- Follow quick start instructions

## Deployment Considerations

### Rollout Strategy

1. Add validation script (no impact on existing workflow)
2. Add skill packaging job (parallel, non-blocking)
3. Update release job to include skill
4. Add documentation files
5. Test with next release

### Rollback Plan

- Remove skill-related steps from release.yml
- Skill packaging is additive; removal is safe

## Future Considerations

- Skill marketplace integration when available
- Automated skill testing (beyond validation)
- Multiple skill variants if needed
- Skill dependency management
