---
document_type: requirements
project_id: SPEC-2025-12-15-001
version: 1.0.0
last_updated: 2025-12-15T19:30:00Z
status: draft
---

# Decider Display Remediation - Product Requirements Document

## Executive Summary

This project addresses GitHub Issue #15: stakeholder metadata (deciders, consulted, informed) is not displayed in the `git adr show` command's markdown output. The scope has been expanded to include making deciders a required field, adding CLI support, implementing interactive prompts for empty fields, and adding MADR 4.0 compatibility.

## Problem Statement

### The Problem

When using `git adr show <id>`, the rich markdown panel displays tags, linked commits, and supersession relationships, but **omits** the stakeholder metadata fields (deciders, consulted, informed) even though these fields are:
1. Fully modeled in `ADRMetadata` dataclass
2. Properly serialized to/from YAML frontmatter
3. Displayed correctly in `--format yaml` and `--format json` output

Additionally, the deciders field is optional, which leads to ADRs being created without proper attribution of who made the decision.

### Impact

- Users cannot see who made a decision without switching to YAML/JSON format
- ADRs lack accountability - no record of decision-makers
- Historical ADRs have no decider information
- Non-compliance with MADR best practices which emphasize stakeholder tracking

### Current State

The `_output_markdown()` function in `show.py` (lines 93-116) displays:
- Title, ID, Date, Status (always)
- Tags (if non-empty)
- Linked commits (if non-empty)
- Supersedes/Superseded by (if set)

Missing:
- Deciders
- Consulted
- Informed

## Goals and Success Criteria

### Primary Goal

Ensure stakeholder metadata is visible, required, and properly tracked for all ADRs.

### Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Deciders display | 100% visible | All ADRs with deciders show them in `git adr show` |
| New ADR compliance | 100% | All new ADRs created have non-empty deciders |
| Migration coverage | 100% | All existing ADRs in project have deciders set |
| MADR 4.0 support | Full | Both `deciders` and `decision-makers` fields accepted |

### Non-Goals (Explicit Exclusions)

- Automatic git author fallback (rejected - deciders must be explicitly provided)
- Validation of decider format (emails, names) - accept any string
- Integration with external identity systems
- Changes to `consulted` or `informed` field requirements (remain optional)

## User Analysis

### Primary Users

- **Who**: Software architects and developers using git-adr for decision tracking
- **Needs**: Clear visibility of who made decisions; accountability for decisions
- **Context**: Reviewing ADRs during code reviews, audits, or onboarding

### User Stories

1. As an architect, I want to see who made a decision when viewing an ADR so that I know who to consult for clarification
2. As a developer, I want to be prompted to specify deciders when creating an ADR so that decisions have proper attribution
3. As a team lead, I want ADRs without deciders to prompt for completion so that historical records can be improved
4. As a user of MADR 4.0 templates, I want my `decision-makers` field to be recognized so that I don't have to modify my workflow

## Functional Requirements

### Must Have (P0)

| ID | Requirement | Rationale | Acceptance Criteria |
|----|-------------|-----------|---------------------|
| FR-001 | Display deciders in markdown panel | Core bug fix - Issue #15 | `git adr show <id>` displays "Deciders: name1, name2" when field is non-empty |
| FR-002 | Display consulted in markdown panel | Stakeholder visibility | `git adr show <id>` displays "Consulted: name1, name2" when field is non-empty |
| FR-003 | Display informed in markdown panel | Stakeholder visibility | `git adr show <id>` displays "Informed: name1, name2" when field is non-empty |
| FR-004 | Hide empty stakeholder fields | UX consistency | Fields with empty values are not displayed (matches tags behavior) |
| FR-005 | Add --deciders flag to `new` command | CLI support | `git adr new --deciders "Alice, Bob" "Title"` sets deciders |
| FR-006 | Prompt for deciders during creation | Required field enforcement | If --deciders not provided, prompt user before opening editor |
| FR-007 | Interactive prompt on show for empty deciders | Backfill support | When viewing ADR with empty deciders, ask "Would you like to add deciders now?" |
| FR-008 | Support MADR 4.0 `decision-makers` alias | Compatibility | Accept `decision-makers:` in frontmatter as alias for `deciders:` |

### Should Have (P1)

| ID | Requirement | Rationale | Acceptance Criteria |
|----|-------------|-----------|---------------------|
| FR-101 | Validation error for empty deciders on new ADRs | Enforcement | `git adr new` fails if deciders would be empty after all prompts |
| FR-102 | Format: Name + Email display | User preference | Deciders displayed as "John Doe <john@example.com>" format |
| FR-103 | Template emphasis for deciders | User guidance | MADR template highlights deciders field with instructions |

### Nice to Have (P2)

| ID | Requirement | Rationale | Acceptance Criteria |
|----|-------------|-----------|---------------------|
| FR-201 | Migration command | Bulk backfill | `git adr migrate-deciders` command to set deciders on multiple ADRs |
| FR-202 | --consulted and --informed flags | Parity | CLI flags for other stakeholder fields |

## Non-Functional Requirements

### Performance

- Display of stakeholder fields should add < 1ms to show command latency
- Interactive prompt should appear within 100ms of command execution

### Security

- No sensitive data handling changes
- Decider values stored in git notes (same security as other ADR metadata)

### Maintainability

- Follow existing code patterns in show.py
- Add unit tests for all new functionality
- Update existing tests to cover new display fields

## Technical Constraints

- Must work with existing git notes storage mechanism
- Must be backward compatible with ADRs created without deciders
- Must integrate with existing Rich console output
- Python 3.9+ compatibility required

## Dependencies

### Internal Dependencies

- `ADRMetadata.deciders` field (already exists)
- `ADRMetadata.consulted` field (already exists)
- `ADRMetadata.informed` field (already exists)
- `NotesManager.update()` for prompt-and-save flow

### External Dependencies

- `rich` library for console output
- `typer` for CLI prompts
- `python-frontmatter` for MADR 4.0 field parsing

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking change for users with empty deciders | Medium | Low | Interactive prompt is non-blocking; validation only on new ADRs |
| MADR 4.0 field conflict | Low | Medium | Prefer `deciders` if both fields present; warn on conflict |
| User annoyance with prompts | Medium | Low | Provide --no-interactive flag to skip prompts |

## Open Questions

- [x] Should git author be used as fallback? **NO - deciders must be explicit**
- [x] Should deciders be required? **YES - for new ADRs**
- [x] How to handle existing ADRs? **Interactive prompt on access**
- [ ] Should --no-interactive flag suppress the prompt?

## Appendix

### Glossary

| Term | Definition |
|------|------------|
| Deciders | People who made the decision (RACI: Responsible/Accountable) |
| Consulted | Subject matter experts whose input was sought (RACI: Consulted) |
| Informed | Stakeholders kept up-to-date (RACI: Informed) |
| MADR | Markdown Any Decision Record - template format |
| MADR 4.0 | Latest MADR version using `decision-makers` instead of `deciders` |

### References

- [GitHub Issue #15](https://github.com/zircote/git-adr/issues/15)
- [MADR 4.0 Template](https://adr.github.io/madr/)
- [ADR Organization](https://adr.github.io/)

### Migration Plan for This Project

All existing ADRs in this project (git-adr repository) with empty deciders should be backfilled with:
- **Decider**: Robert Allen <zircote@gmail.com>
