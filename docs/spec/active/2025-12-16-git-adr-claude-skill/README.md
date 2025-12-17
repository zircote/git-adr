---
project_id: SPEC-2025-12-16-001
project_name: "git-adr Claude Skill"
slug: git-adr-claude-skill
status: in-review
created: 2025-12-16T00:00:00Z
approved: null
started: null
completed: null
expires: 2026-03-16T00:00:00Z
superseded_by: null
tags: [claude-skill, git-adr, adr, machine-memory, developer-experience]
stakeholders: []
worktree:
  branch: plan/git-adr-claude-skill
  base_branch: main
---

# git-adr Claude Skill

A Claude Code skill for seamless Architecture Decision Record management using git-adr, enabling ADRs to serve as persistent machine memory for project context.

## Quick Links

- [Requirements](./REQUIREMENTS.md)
- [Architecture](./ARCHITECTURE.md)
- [Implementation Plan](./IMPLEMENTATION_PLAN.md)
- [Research Notes](./RESEARCH_NOTES.md)
- [Decisions](./DECISIONS.md)

## Status

**Current Phase**: In Review (Awaiting Approval)

## Summary

This skill transforms git-adr ADRs into persistent "machine memory" for Claude Code, addressing the problem of context loss between sessions. Key capabilities:

### Core Features
- **Auto-Load Context**: ADR summaries loaded automatically at session start
- **On-Demand Hydration**: Full ADR content when explicitly requested
- **Natural Search**: Find decisions by topic, keyword, or tag
- **Conversation Capture**: Create ADRs from ongoing discussions

### Technical Approach
- Extends existing git-adr skill (not replace)
- Shell-based integration with git-adr CLI
- Progressive loading for token efficiency
- Read-only configuration by default

### Command Scope (Curated Subset)
| Command | Purpose |
|---------|---------|
| `git adr list` | Load ADR summaries |
| `git adr show` | Full ADR content |
| `git adr new` | Create ADR |
| `git adr edit` | Modify ADR |
| `git adr search` | Find decisions |
| `git adr ai suggest` | AI improvements |

### Success Criteria
- Claude naturally references ADRs in responses
- Past decisions inform current recommendations
- Reduced context re-explanation across sessions

### Non-Goals
- Wiki sync (handled by git-adr)
- Export formats (handled by git-adr)
- Team approval workflows

### Estimated Effort
2-3 days across 4 phases: Foundation → Core Features → Enhanced Workflows → Polish
