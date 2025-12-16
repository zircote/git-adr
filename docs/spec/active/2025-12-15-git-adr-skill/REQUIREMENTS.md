---
document_type: requirements
project_id: SPEC-2025-12-15-002
version: 1.0.0
last_updated: 2025-12-15T22:45:00Z
status: draft
---

# git-adr Claude Skill - Product Requirements Document

## Executive Summary

Create a comprehensive Claude Code skill that enables Claude to effectively utilize the git-adr tool for managing Architecture Decision Records. The skill provides Claude with complete knowledge of git-adr commands, ADR formats, best practices, and the ability to execute commands directly while generating ADR content tailored to project configurations.

## Problem Statement

### The Problem

Claude lacks specialized knowledge about git-adr, a powerful git extension for managing Architecture Decision Records using git notes. Without this skill, Claude cannot:
- Execute git-adr commands with proper syntax and options
- Generate ADR content in the correct format for a project
- Guide users through ADR workflows and best practices
- Help teams adopt ADR practices effectively

### Impact

- Users must manually reference git-adr documentation
- ADR content generation doesn't match project conventions
- Inconsistent guidance on ADR best practices
- Missed opportunities for AI-assisted architecture documentation

### Current State

- git-adr has comprehensive documentation but no Claude skill
- Users get generic ADR advice not tailored to git-adr's capabilities
- No integration between Claude and git-adr's git notes-based storage

## Goals and Success Criteria

### Primary Goal

Enable Claude to be a comprehensive git-adr assistant that can execute commands, generate properly-formatted ADR content, and teach ADR best practices to users of all skill levels.

### Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Command coverage | 100% of git-adr commands | Skill audit vs. COMMANDS.md |
| Format coverage | All 6 ADR formats | Template verification |
| Config-awareness | Reads adr.template | Integration testing |
| Execution capability | Direct command execution | Functional testing |

### Non-Goals (Explicit Exclusions)

- Creating a new ADR format (uses existing 6 formats)
- Replacing git-adr's built-in AI features
- Managing ADRs in non-git repositories
- Providing ADR workflow automation scripts

## User Analysis

### Primary Users

**1. ADR Beginners**
- **Who**: Developers new to Architecture Decision Records
- **Needs**: Learn what ADRs are, when to write them, how to use git-adr
- **Context**: Onboarding to projects that use ADRs

**2. git-adr Newcomers**
- **Who**: Teams familiar with ADRs but new to git-adr
- **Needs**: Understand git notes storage, command syntax, configuration
- **Context**: Migrating from file-based ADR tools or starting fresh

**3. Advanced Users**
- **Who**: Experienced git-adr users wanting AI assistance
- **Needs**: Quick command execution, content generation, format conversion
- **Context**: Daily ADR workflows, team onboarding, analytics

### User Stories

1. As a **developer new to ADRs**, I want Claude to explain what ADRs are and when to write them, so that I understand the value before learning the tool.

2. As a **developer setting up git-adr**, I want Claude to initialize git-adr in my repo and configure it for my team, so that we can start documenting decisions.

3. As an **architect creating an ADR**, I want Claude to generate ADR content in my project's configured format, so that my ADRs are consistent with existing decisions.

4. As a **team lead onboarding new members**, I want Claude to run `git adr onboard` and explain our architecture decisions, so that new hires understand our system.

5. As a **developer searching for context**, I want Claude to search and show relevant ADRs, so that I understand why decisions were made.

6. As an **architect superseding a decision**, I want Claude to create a superseding ADR with proper links, so that decision history is preserved.

7. As a **devops engineer syncing ADRs**, I want Claude to push/pull ADR notes with the team, so that decisions are shared across the organization.

## Functional Requirements

### Must Have (P0)

| ID | Requirement | Rationale | Acceptance Criteria |
|----|-------------|-----------|---------------------|
| FR-001 | Execute all core git-adr commands | Enable direct workflow assistance | Claude can run init, new, edit, list, show, search, rm, supersede, link, log |
| FR-002 | Execute sync commands | Team collaboration essential | Claude can run sync push, sync pull, sync |
| FR-003 | Execute artifact commands | Complete feature coverage | Claude can run attach, artifacts, artifact-get, artifact-rm |
| FR-004 | Execute analytics commands | Reporting capability | Claude can run stats, report, metrics |
| FR-005 | Execute import/export commands | Migration workflows | Claude can run export, import, convert |
| FR-006 | Execute config commands | Setup assistance | Claude can run config list, config get, config set |
| FR-007 | Read project's adr.template config | Match project conventions | Claude reads and uses configured template |
| FR-008 | Generate ADR content in MADR format | Most common format | Complete MADR template generation |
| FR-009 | Generate ADR content in Nygard format | Original minimal format | Complete Nygard template generation |
| FR-010 | Generate ADR content in Y-Statement format | Quick documentation | Complete Y-Statement generation |
| FR-011 | Generate ADR content in Alexandrian format | Pattern-based decisions | Complete Alexandrian generation |
| FR-012 | Generate ADR content in Business Case format | Stakeholder decisions | Complete Business Case generation |
| FR-013 | Generate ADR content in Planguage format | Measurable requirements | Complete Planguage generation |
| FR-014 | Explain ADR concepts to beginners | All skill levels supported | Clear explanations of what/when/why |
| FR-015 | Guide through git-adr setup | Onboarding workflow | Step-by-step initialization guidance |

### Should Have (P1)

| ID | Requirement | Rationale | Acceptance Criteria |
|----|-------------|-----------|---------------------|
| FR-101 | Execute wiki commands | Wiki sync capability | Claude can run wiki init, wiki sync |
| FR-102 | Suggest appropriate ADR format | Context-aware assistance | Recommends format based on decision type |
| FR-103 | Validate ADR content structure | Quality assurance | Checks for required sections |
| FR-104 | Link ADRs to commits automatically | Traceability | Associates ADRs with implementation commits |
| FR-105 | Search and retrieve relevant ADRs | Context discovery | Full-text search with filtering |
| FR-106 | Explain configuration options | Setup guidance | Document all adr.* config keys |
| FR-107 | Generate ADR from conversation | Content elicitation | Socratic questioning to gather context |

### Nice to Have (P2)

| ID | Requirement | Rationale | Acceptance Criteria |
|----|-------------|-----------|---------------------|
| FR-201 | Multi-ADR comparison | Decision analysis | Compare alternatives across ADRs |
| FR-202 | ADR health scoring | Quality metrics | Assess completeness and clarity |
| FR-203 | Timeline visualization | Decision history | Chronological decision view |
| FR-204 | Custom template support | Organization needs | Support user-defined templates |

## Non-Functional Requirements

### Performance

- Skill loading should add minimal latency (<100ms)
- Progressive disclosure reduces context usage
- Reference files loaded only when needed

### Usability

- Clear trigger phrases in skill description
- Intuitive command suggestions
- Helpful error messages with corrections

### Maintainability

- Skill updates when git-adr adds commands
- Template updates when formats change
- Version tracking for compatibility

### Compatibility

- Works with git-adr 0.1.0+
- Supports all configured AI providers
- Works in any git repository

## Technical Constraints

- Must follow Claude Code skill specification
- SKILL.md required with YAML frontmatter
- Progressive disclosure via references/ directory
- No external dependencies beyond git-adr

## Dependencies

### Internal Dependencies

- git-adr tool installed in user's environment
- Git repository initialized
- Git notes support (standard git feature)

### External Dependencies

- None (git-adr handles AI provider integration)

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| git-adr command changes | Low | Medium | Version-aware skill with update process |
| Format template changes | Low | Low | Reference git-adr docs for authoritative templates |
| Config reading failures | Medium | Low | Fallback to MADR default |
| Large skill context usage | Medium | Medium | Progressive disclosure architecture |

## Open Questions

- [x] Primary use case priority → All equally important
- [x] Target audience → All skill levels
- [x] AI feature handling → Claude generates directly
- [x] Distribution location → Both git-adr repo and user skills
- [x] Format selection → Match project config
- [x] Template inclusion → Include all 6 formats
- [x] Command execution → Direct execution
- [x] Size trade-off → Comprehensive

## Appendix

### Glossary

| Term | Definition |
|------|------------|
| ADR | Architecture Decision Record - document capturing a significant decision |
| git notes | Git feature for attaching metadata to commits without modifying history |
| MADR | Markdown Any Decision Records - popular ADR format |
| Nygard | Original minimal ADR format by Michael Nygard |
| Planguage | Planning Language - quantified requirements format |
| Skill | Claude Code extension providing specialized knowledge |

### References

- [git-adr README](../../README.md)
- [git-adr Commands Reference](../../COMMANDS.md)
- [git-adr Configuration](../../CONFIGURATION.md)
- [ADR Format Guide](../../ADR_FORMATS.md)
- [ADR Primer](../../ADR_PRIMER.md)
- [Claude Code Skill Specification](~/.claude/skills/agent_skills_spec.md)
- [Skill Creator Guide](~/.claude/skills/skill-creator/SKILL.md)
