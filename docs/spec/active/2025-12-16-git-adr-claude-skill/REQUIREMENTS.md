---
document_type: requirements
project_id: SPEC-2025-12-16-001
version: 1.0.0
last_updated: 2025-12-16
status: draft
---

# git-adr Claude Skill - Product Requirements Document

## Executive Summary

Create a Claude Code skill that transforms Architecture Decision Records (ADRs) into persistent "machine memory" - enabling Claude to automatically load project architectural context at session start, recall past decisions during conversations, and capture new decisions from natural dialogue.

This skill bridges the gap between git-adr (which stores ADRs in git notes) and Claude Code (which lacks persistent project context across sessions), creating a seamless experience where architectural decisions inform AI assistance throughout a project's lifecycle.

## Problem Statement

### The Problem

Claude Code loses architectural context between sessions. Despite projects having well-documented ADRs via git-adr, Claude cannot:
- Know what technologies were chosen and why
- Recall past architectural decisions when making recommendations
- Suggest code patterns consistent with established decisions
- Understand the rationale behind existing implementations

This leads to recommendations that contradict established decisions, repeated explanations of architectural choices, and suggestions that ignore project constraints.

### Impact

- **Solo developers**: Waste time re-explaining decisions every session
- **Team developers**: Get inconsistent recommendations that don't align with team decisions
- **Claude Code**: Provides less valuable assistance without historical context

### Current State

- git-adr stores ADRs in git notes (invisible in working tree, portable with history)
- ADRs contain valuable context: decisions, rationale, alternatives considered, consequences
- Claude Code cannot access this context without explicit user prompting
- Users must manually paste ADR content into conversations

## Goals and Success Criteria

### Primary Goal

Enable Claude Code to automatically leverage project ADRs as persistent context, making architectural decisions inform AI assistance without manual intervention.

### Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Context availability | ADR summaries loaded in >90% of sessions | Skill activation tracking |
| Decision recall | Claude references relevant ADRs in responses | User feedback / conversation analysis |
| ADR creation ease | <2 minutes from "capture this" to draft | Time-to-draft measurement |
| Context loss reduction | Users report Claude "remembers" decisions | Qualitative feedback |

### Non-Goals (Explicit Exclusions)

- **Wiki sync**: No GitHub/GitLab wiki integration (handled by git-adr directly)
- **Export formats**: No DOCX/PDF export (handled by git-adr directly)
- **Team workflows**: No approval/review workflow features
- **Multi-repo ADRs**: Single repository focus only

## User Analysis

### Primary Users

#### Solo Developers
- **Who**: Individual developers using Claude Code on personal/side projects
- **Needs**: Consistent AI assistance that remembers project decisions
- **Context**: Working across multiple sessions over weeks/months

#### Team Developers
- **Who**: Engineers on teams with shared ADR practices
- **Needs**: AI recommendations aligned with team architectural decisions
- **Context**: Onboarding to existing codebases, maintaining consistency

#### Claude Code (AI Consumer)
- **Who**: The AI assistant itself, consuming ADRs for context
- **Needs**: Structured, accessible decision history
- **Context**: Every conversation where code/architecture is discussed

### User Stories

1. As a **developer**, I want Claude to know our technology choices so that it doesn't suggest alternatives we've already rejected.

2. As a **developer**, I want to quickly capture architectural decisions from our conversation so that they're preserved for future sessions.

3. As a **developer returning after a break**, I want Claude to remind me of recent architectural decisions so that I can resume work with full context.

4. As a **new team member**, I want Claude to explain why certain technologies were chosen so that I understand the project's architectural foundation.

5. As a **developer debugging**, I want Claude to recall relevant past decisions so that it can suggest fixes consistent with our architecture.

6. As a **developer making a new decision**, I want Claude to show me related past decisions so that I can maintain consistency.

## Functional Requirements

### Must Have (P0)

| ID | Requirement | Rationale | Acceptance Criteria |
|----|-------------|-----------|---------------------|
| FR-001 | Auto-load ADR summaries at session start | Core value proposition - context without manual effort | ADR summaries appear in Claude's context when session starts in git repo with ADRs |
| FR-002 | On-demand ADR hydration | Full content only when needed, preserves token budget | `show me the database decision` loads full ADR content |
| FR-003 | ADR search by natural language | Find relevant decisions without knowing exact IDs | `what did we decide about caching?` returns matching ADRs |
| FR-004 | Create ADR from conversation | Capture decisions naturally | `record this decision` extracts context and generates draft |
| FR-005 | Expose curated git-adr commands | Direct CLI access for power users | list, show, new, edit, search, ai suggest accessible |

### Should Have (P1)

| ID | Requirement | Rationale | Acceptance Criteria |
|----|-------------|-----------|---------------------|
| FR-101 | Guided ADR creation workflow | Structured prompts for quality ADRs | Skill walks through title, context, options, decision, consequences |
| FR-102 | Decision linking suggestions | Connect new decisions to related ADRs | When creating ADR, suggest supersedes/relates-to links |
| FR-103 | Status-aware context loading | Focus on active decisions | Only accepted/proposed ADRs in auto-load; deprecated/superseded on request |
| FR-104 | Tag-based filtering | Group decisions by domain | Load only `#security` ADRs when discussing security |

### Nice to Have (P2)

| ID | Requirement | Rationale | Acceptance Criteria |
|----|-------------|-----------|---------------------|
| FR-201 | Decision timeline view | Understand evolution | Show ADR history chronologically |
| FR-202 | Impact analysis | Understand decision scope | Show commits linked to each ADR |
| FR-203 | ADR templates preview | Help choose format | Show template examples before creation |

## Non-Functional Requirements

### Performance

- **Context loading**: ADR summaries loaded in <1 second
- **Full ADR hydration**: Complete content in <2 seconds
- **Search**: Results in <3 seconds for repositories with <100 ADRs

### Token Efficiency

- **Summary format**: <100 tokens per ADR in summary mode
- **Progressive loading**: Only load full content when explicitly requested
- **Caching hint**: Suggest Claude cache repeated ADR content within session

### Reliability

- **Graceful degradation**: Skill works even if git-adr not installed (shows install guidance)
- **Error recovery**: Clear messages for common issues (not in git repo, ADRs not initialized)
- **Config safety**: Never modify user configuration without explicit permission

### Maintainability

- **Documentation**: Complete reference files for all features
- **Progressive disclosure**: Load only relevant reference content
- **Version tracking**: Skill version in SKILL.md metadata

## Technical Constraints

### Required Dependencies

- git-adr CLI installed and accessible in PATH
- Git repository with ADR tracking initialized (`git adr init`)
- Claude Code (skill execution environment)

### Integration Points

| System | Integration Type | Purpose |
|--------|-----------------|---------|
| git-adr CLI | Shell subprocess | Execute ADR commands |
| Git repository | Working directory | ADR storage in git notes |
| Claude Code | Skill framework | Context injection, conversation handling |

### Compatibility

- git-adr version: 0.2.0+
- Claude Code: Current version
- Git: 2.20+ (for notes features)

## Dependencies

### Internal Dependencies

- Existing git-adr skill (can extend or replace)
- Shell access for git-adr commands

### External Dependencies

| Dependency | Purpose | Risk |
|------------|---------|------|
| git-adr CLI | ADR operations | User must install; mitigate with install guidance |
| Git | Repository and notes | Assumed present in dev environment |

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| git-adr not installed | Medium | High | Detect and provide install instructions |
| Large ADR count overwhelming context | Low | Medium | Pagination, status filtering, tag filtering |
| AI extracts wrong context from conversation | Medium | Medium | User review step before ADR creation |
| Configuration accidentally modified | Low | High | Read-only config access; explicit permission for writes |
| Token budget exceeded | Low | Medium | Progressive loading, summary-first approach |

## Open Questions

- [x] ~~What format for auto-loaded summaries?~~ → Structured metadata (YAML-like)
- [x] ~~Which commands to include?~~ → Curated: list, show, new, edit, search, ai suggest
- [x] ~~How to handle large ADR counts?~~ → Status filters + pagination
- [ ] Should skill replace or extend existing git-adr skill? (TBD in architecture)

## Appendix

### Glossary

| Term | Definition |
|------|------------|
| ADR | Architecture Decision Record - documented architectural decision |
| git notes | Git feature for attaching metadata to objects without changing history |
| Hydration | Loading full content after initially showing summary |
| Machine memory | Persistent context that survives across Claude sessions |
| MADR | Markdown Any Decision Records - common ADR template format |

### References

- [git-adr repository](https://github.com/zircote/git-adr)
- [MADR template](https://adr.github.io/madr/)
- [Claude Code Skills documentation](https://docs.anthropic.com/claude-code/skills)
- Research notes: `./RESEARCH_NOTES.md`
