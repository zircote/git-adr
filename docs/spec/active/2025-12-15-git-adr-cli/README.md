---
project_id: SPEC-2025-12-15-001
project_name: "git-adr CLI"
slug: git-adr-cli
status: in-progress
created: 2025-12-15T00:20:00Z
approved: 2025-12-15T02:00:00Z
started: 2025-12-15T02:00:00Z
completed: null
expires: 2026-03-15T00:20:00Z
superseded_by: null
tags: [cli, git, adr, architecture-decision-records, git-notes]
stakeholders: []
worktree:
  branch: plan/git-adr-cli
  base_branch: main
---

# git-adr CLI - Planning Project

## Overview

A command-line tool implemented as a git extension that manages Architecture Decision Records (ADRs) by storing them in git notes rather than traditional file-based storage.

**Core Differentiator**: Git notes-based storage - ADRs are invisible in the working tree but visible in history.

## Status

**Current Phase**: Implementation (Phase 1: Core MVP)

## Specification Summary

| Metric | Value |
|--------|-------|
| Functional Requirements | 60+ |
| Implementation Tasks | 80+ |
| Phases | 4 (MVP → v1.0.0) |
| ADR Formats Supported | 6 + custom |
| AI Providers | 7 |

## Quick Links

- [Product Brief](../../../git-adr-product-brief.md) - Original feature specification
- [REQUIREMENTS.md](REQUIREMENTS.md) - Product Requirements Document
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical Architecture
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - Phased Task Breakdown
- [DECISIONS.md](DECISIONS.md) - Architecture Decision Records
- [RESEARCH_NOTES.md](RESEARCH_NOTES.md) - Research Findings

## Key Decisions Made

| Decision | Resolution |
|----------|------------|
| Git operations | subprocess to git binary (industry standard) |
| Note attachment | Root tree object (survives rebase) |
| CLI framework | typer (migrate from click) |
| Python version | 3.11+ |
| AI provider priority | OpenAI → Anthropic → Others → Ollama |
| Storage format | YAML frontmatter + Markdown |

## Implementation Phases

| Phase | Focus | Deliverables |
|-------|-------|--------------|
| **Phase 1** | Core MVP (v0.5.0) | Git notes storage, 11 core commands, 6 formats |
| **Phase 2** | Integration (v0.8.0) | AI features, wiki sync, analytics |
| **Phase 3** | Onboarding (v0.9.0) | Interactive wizard, export/import |
| **Phase 4** | Polish (v1.0.0) | Documentation, CI/CD, final QA |

## Next Steps

1. Complete Phase 1 tasks (see [PROGRESS.md](PROGRESS.md))
2. Start with Task 1.1.1: Migrate CLI from click to typer
3. Track progress using `/cs:i git-adr-cli`
