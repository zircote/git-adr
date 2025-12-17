---
project_id: SPEC-2025-12-16-001
project_name: "git-adr Skill Release Workflow"
slug: git-adr-skill-release
status: in-review
created: 2025-12-16T14:46:00Z
approved: null
started: null
completed: null
expires: 2026-03-16T14:46:00Z
superseded_by: null
tags: [skill, git-adr, release, ci-cd, github-actions, documentation]
stakeholders: []
worktree:
  branch: plan/git-adr-skill-release
  base_branch: main
---

# git-adr Skill Release Workflow - Planning Project

## Overview

Create a GitHub Actions release workflow for the Claude Code skill in `skills/git-adr/`, producing a distributable `.skill` artifact and comprehensive end-user documentation.

**Core Purpose**: Enable automated releases of the git-adr skill with proper packaging and documentation so end users can easily install and immediately understand the value proposition.

## Status

**Current Phase**: In Review - Awaiting Approval

## Specification Summary

| Metric | Value |
|--------|-------|
| Functional Requirements | 9 (P0: 6, P1: 3, P2: 2) |
| Implementation Tasks | 7 |
| Phases | 3 |
| Estimated Effort | 2-3 hours |

## Quick Links

- [REQUIREMENTS.md](REQUIREMENTS.md) - Product Requirements Document
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical Architecture
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - Phased Task Breakdown
- [CHANGELOG.md](CHANGELOG.md) - Plan evolution history

## Key Decisions Made

| Decision | Resolution |
|----------|------------|
| Release Trigger | Same as main release (v* tags) |
| Artifact Naming | `git-adr-{version}.skill` (versioned) |
| Documentation Location | README section + `docs/git-adr-skill.md` |
| Target Audience | Both Claude Code users and ADR practitioners |
| Value Props | All 4: creation, formats, git-native, commands |
| Validation | Include in CI (matches skill-spec rules) |

## Key Deliverables

1. **Validation Script** - `.github/scripts/validate-skill.py`
2. **Packaging Workflow** - New job in `release.yml`
3. **Release Artifact** - `git-adr-{version}.skill` attached to releases
4. **Documentation** - `docs/git-adr-skill.md` + README enhancement

## Implementation Phases

| Phase | Focus | Deliverables |
|-------|-------|--------------|
| **Phase 1** | Validation | Skill validation script |
| **Phase 2** | Packaging | Release workflow integration |
| **Phase 3** | Documentation | User-facing docs |

## Architecture Highlights

```
Trigger: v* tag push
    │
    ├── build (existing)
    ├── build-release-artifacts (existing)
    └── build-skill-package (NEW) ──► validates + packages
            │
            ▼
        release ──► attaches git-adr-{version}.skill
```

## Next Steps

1. Review specification documents
2. Approve plan
3. Run `/cs:i git-adr-skill-release` to begin implementation
