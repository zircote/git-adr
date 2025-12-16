---
document_type: requirements
project_id: SPEC-2025-12-16-001
version: 1.0.0
last_updated: 2025-12-16T15:00:00Z
status: draft
---

# git-adr Skill Release Workflow - Product Requirements Document

## Executive Summary

This project adds automated release infrastructure for the git-adr Claude Code skill, producing versioned `.skill` packages as GitHub release artifacts alongside comprehensive end-user documentation. The goal is to make skill installation trivial while clearly communicating the value proposition to both Claude Code users and ADR practitioners.

## Problem Statement

### The Problem

The git-adr Claude Code skill exists in `skills/git-adr/` but lacks:
1. **Automated packaging** - No CI/CD produces distributable `.skill` files
2. **Release artifacts** - Skill not included in GitHub releases
3. **Dedicated documentation** - README section exists but lacks installation details and value proposition clarity

### Impact

- Users must manually copy the skill directory instead of downloading a packaged artifact
- No versioning alignment between the skill and the main git-adr tool
- First-time users don't immediately understand why they would use the skill

### Current State

- Skill source exists at `skills/git-adr/SKILL.md` with `references/` directory
- Main `release.yml` workflow builds Python packages and release artifacts but ignores the skill
- README has a brief "Claude Code Skill" section (lines 420-454) with basic instructions

## Goals and Success Criteria

### Primary Goal

Automate skill packaging and release with documentation that enables users to install the skill in under 60 seconds and immediately understand its value.

### Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Installation time | < 60 seconds from release page to working skill | Manual testing |
| Documentation completeness | All 4 value propositions clearly explained | Content review |
| Release artifact size | < 50 KB for .skill file | CI artifact check |
| Validation coverage | 100% of skill-spec rules checked | Validation script output |

### Non-Goals (Explicit Exclusions)

- Skill content changes (handled by existing SPEC-2025-12-15-002)
- Multiple skill variants or platform-specific builds
- Skill marketplace integration (future consideration)
- Automated skill testing in CI (beyond validation)

## User Analysis

### Primary Users

1. **Claude Code Users**
   - **Who**: Developers using Claude Code who want ADR capabilities
   - **Needs**: Quick installation, immediate productivity
   - **Context**: Discover skill via git-adr repo, releases, or documentation

2. **ADR Practitioners**
   - **Who**: Engineers who already use or want to use ADRs
   - **Needs**: Understand how Claude + git-adr improves their workflow
   - **Context**: Evaluating git-adr as ADR tooling, looking for AI assistance

### User Stories

1. As a Claude Code user, I want to download a `.skill` file from GitHub releases so that I can install the git-adr skill without cloning the repository
2. As a developer, I want the skill version to match the git-adr version so that I know they're compatible
3. As an ADR practitioner, I want to understand what the skill enables so that I can decide if it's valuable for my workflow
4. As a new user, I want clear installation instructions so that I can start using the skill immediately

## Functional Requirements

### Must Have (P0)

| ID | Requirement | Rationale | Acceptance Criteria |
|----|-------------|-----------|---------------------|
| FR-001 | Skill validation in CI | Catch skill-spec violations before release | Validation runs on v* tags, blocks release on failure |
| FR-002 | Skill packaging into .skill file | Required for distribution | ZIP archive created with skill directory structure |
| FR-003 | Versioned artifact naming | Track compatibility with git-adr | `git-adr-{version}.skill` naming pattern |
| FR-004 | GitHub release attachment | Primary distribution channel | .skill file appears in release assets |
| FR-005 | README skill section enhancement | Entry point for many users | Expanded section with installation + value props |
| FR-006 | Dedicated docs/git-adr-skill.md | Comprehensive documentation | Full guide with all 4 value propositions |

### Should Have (P1)

| ID | Requirement | Rationale | Acceptance Criteria |
|----|-------------|-----------|---------------------|
| FR-101 | Skill validation on PR | Catch issues early | Validation runs on skills/** changes in PRs |
| FR-102 | Release notes skill section | Visibility in release | Template includes skill download instructions |
| FR-103 | Quick start example in docs | Reduce time to value | Working example within first 30 seconds of reading |

### Nice to Have (P2)

| ID | Requirement | Rationale | Acceptance Criteria |
|----|-------------|-----------|---------------------|
| FR-201 | Skill checksum in release | Integrity verification | SHA256 hash published alongside artifact |
| FR-202 | Installation script for skill | One-liner install | curl/bash script similar to binary installer |

## Non-Functional Requirements

### Performance

- Skill packaging job completes in < 30 seconds
- No impact on existing release workflow duration

### Security

- No secrets required for skill packaging
- Validation prevents malformed YAML injection

### Reliability

- Skill packaging failure does not block Python package release (continue-on-error)
- Validation failure DOES block release (catches real issues)

### Maintainability

- Validation logic matches skill-creator's quick_validate.py rules
- Single source of truth for validation (embedded or imported)

## Technical Constraints

- Must integrate with existing GitHub Actions workflows
- Must use existing artifact upload/download patterns
- Skill package format must be ZIP with .skill extension (per skill-spec)
- Python 3.11+ available in CI runners

## Dependencies

### Internal Dependencies

- `skills/git-adr/` directory with valid SKILL.md
- Existing `.github/workflows/release.yml` structure
- Existing `docs/` directory for documentation

### External Dependencies

- `actions/upload-artifact@v6` and `actions/download-artifact@v6`
- `softprops/action-gh-release@v2` for release creation
- Python + PyYAML for validation script

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Skill content changes break validation | Medium | Low | Validation provides clear error messages |
| Release workflow complexity increases | Low | Medium | Skill job runs in parallel, minimal coupling |
| Users confused by .skill vs .tar.gz | Low | Low | Clear documentation distinguishes purposes |

## Open Questions

- [x] Include validation in CI? **Decision: Yes, include validation**
- [x] Artifact naming pattern? **Decision: git-adr-{version}.skill**
- [x] Documentation location? **Decision: README section + docs/git-adr-skill.md**

## Appendix

### Glossary

| Term | Definition |
|------|------------|
| .skill file | ZIP archive containing a skill directory, per Claude Code skill-spec |
| skill-spec | Agent Skills Spec v1.0 defining skill structure requirements |
| SKILL.md | Required entry point file for any Claude Code skill |
| YAML frontmatter | Metadata block at top of SKILL.md with name and description |

### References

- Agent Skills Spec: `~/.claude/skills/agent_skills_spec.md`
- skill-creator validation: `~/.claude/skills/skill-creator/scripts/quick_validate.py`
- Existing release workflow: `.github/workflows/release.yml`
