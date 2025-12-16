---
project_id: SPEC-2025-12-15-002
project_name: "git-adr Claude Skill"
slug: git-adr-skill
status: in-progress
created: 2025-12-15T22:35:00Z
approved: null
started: 2025-12-15T23:00:00Z
completed: null
expires: 2026-03-15T22:35:00Z
superseded_by: null
tags: [skill, git-adr, adr, architecture-decision-records, claude-code]
stakeholders: []
worktree:
  branch: plan/git-adr-skill
  base_branch: main
---

# git-adr Claude Skill - Planning Project

## Overview

A Claude Code skill that provides comprehensive knowledge and capabilities for Claude to effectively utilize the git-adr tool for managing Architecture Decision Records.

**Core Purpose**: Enable Claude to help users create, manage, and query ADRs using git-adr with full understanding of ADR best practices, all available commands, and AI-assisted features.

## Status

**Current Phase**: Phase 1 - Core Skill Structure

## Specification Summary

| Metric | Value |
|--------|-------|
| Functional Requirements | 22 (P0: 15, P1: 7) |
| Implementation Tasks | 18 |
| Phases | 4 |
| ADR Formats Covered | 6 |
| Reference Files | 10 |

## Quick Links

- [REQUIREMENTS.md](REQUIREMENTS.md) - Product Requirements Document
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical Architecture
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - Phased Task Breakdown
- [DECISIONS.md](DECISIONS.md) - Architecture Decision Records
- [CHANGELOG.md](CHANGELOG.md) - Plan evolution history

## Key Decisions Made

| Decision | Resolution |
|----------|------------|
| AI Content Generation | Claude generates directly (not git-adr AI) |
| Architecture | Progressive disclosure (SKILL.md + references/) |
| Format Selection | Config-aware (reads adr.template) |
| Command Execution | Direct execution via Bash |
| Distribution | Dual (git-adr repo + user skills) |
| Scope | Comprehensive (all formats, all commands) |

## Implementation Phases

| Phase | Focus | Deliverables |
|-------|-------|--------------|
| **Phase 1** | Core Structure | SKILL.md with core instructions |
| **Phase 2** | Format Templates | All 6 ADR format templates |
| **Phase 3** | Reference Docs | Commands, config, workflows, best practices |
| **Phase 4** | Testing & Packaging | Validation, .skill package, distribution |

## Skill Structure

```
skills/git-adr/
├── SKILL.md                    # Core instructions (~400 lines)
└── references/
    ├── commands.md             # Full command reference
    ├── configuration.md        # All adr.* config options
    ├── best-practices.md       # ADR writing guidance
    ├── workflows.md            # Common workflow patterns
    └── formats/
        ├── madr.md             # MADR 4.0 template
        ├── nygard.md           # Original minimal format
        ├── y-statement.md      # Single-sentence format
        ├── alexandrian.md      # Pattern-language format
        ├── business-case.md    # Business justification
        └── planguage.md        # Quantified requirements
```

## Next Steps

1. Review specification documents
2. Approve plan with `/cs:i git-adr-skill`
3. Implement Phase 1: Core Skill Structure
