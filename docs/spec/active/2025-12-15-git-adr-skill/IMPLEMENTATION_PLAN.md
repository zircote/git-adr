---
document_type: implementation_plan
project_id: SPEC-2025-12-15-002
version: 1.0.0
last_updated: 2025-12-15T22:55:00Z
status: draft
---

# git-adr Claude Skill - Implementation Plan

## Overview

This plan implements a comprehensive Claude Code skill for git-adr, following the progressive disclosure architecture defined in ARCHITECTURE.md.

## Phase Summary

| Phase | Focus | Key Deliverables |
|-------|-------|------------------|
| Phase 1 | Core Skill Structure | SKILL.md with core instructions |
| Phase 2 | ADR Format Templates | All 6 format template files |
| Phase 3 | Reference Documentation | Commands, config, workflows |
| Phase 4 | Testing & Packaging | Validation, packaging, distribution |

---

## Phase 1: Core Skill Structure

**Goal**: Create the foundational SKILL.md and directory structure

**Prerequisites**: None

### Task 1.1: Create Skill Directory

- **Description**: Initialize the skill directory structure in git-adr repo
- **Acceptance Criteria**:
  - [ ] `skills/git-adr/` directory created
  - [ ] `skills/git-adr/references/` directory created
  - [ ] `skills/git-adr/references/formats/` directory created

### Task 1.2: Create SKILL.md Frontmatter

- **Description**: Write YAML frontmatter with name and comprehensive description
- **Acceptance Criteria**:
  - [ ] `name: git-adr` defined
  - [ ] Description includes all trigger phrases
  - [ ] Description mentions all capabilities

### Task 1.3: Write Core Instructions

- **Description**: Write the main SKILL.md body with quick reference and patterns
- **Acceptance Criteria**:
  - [ ] Overview section explaining git-adr
  - [ ] Quick reference command table
  - [ ] Config-aware format selection pattern
  - [ ] Command execution patterns
  - [ ] Navigation guide to references/

### Task 1.4: Write Execution Patterns

- **Description**: Document how Claude should execute git-adr commands
- **Acceptance Criteria**:
  - [ ] git-adr availability check pattern
  - [ ] Git repository verification
  - [ ] ADR initialization check
  - [ ] Error handling patterns

### Phase 1 Deliverables

- [ ] `skills/git-adr/SKILL.md` (core ~400 lines)
- [ ] Directory structure in place

### Phase 1 Exit Criteria

- [ ] SKILL.md passes frontmatter validation
- [ ] All sections documented
- [ ] Under 500 line limit

---

## Phase 2: ADR Format Templates

**Goal**: Create all 6 ADR format template files

**Prerequisites**: Phase 1 complete

### Task 2.1: Create MADR Template

- **Description**: Full MADR 4.0 template with all sections
- **File**: `references/formats/madr.md`
- **Acceptance Criteria**:
  - [ ] Complete template structure
  - [ ] All MADR sections (Status, Context, Decision, Consequences, Options)
  - [ ] Example content for each section
  - [ ] Guidance on when to use

### Task 2.2: Create Nygard Template

- **Description**: Original minimal ADR format
- **File**: `references/formats/nygard.md`
- **Acceptance Criteria**:
  - [ ] Minimal 4-section structure
  - [ ] Status, Context, Decision, Consequences
  - [ ] Example content
  - [ ] Best use cases documented

### Task 2.3: Create Y-Statement Template

- **Description**: Ultra-concise single-statement format
- **File**: `references/formats/y-statement.md`
- **Acceptance Criteria**:
  - [ ] Y-Statement pattern documented
  - [ ] "In the context of... facing... we decided... to achieve... accepting..."
  - [ ] Example statements
  - [ ] When to use guidance

### Task 2.4: Create Alexandrian Template

- **Description**: Pattern-language format with Forces
- **File**: `references/formats/alexandrian.md`
- **Acceptance Criteria**:
  - [ ] Context, Forces, Problem, Solution, Resulting Context
  - [ ] Forces section guidance
  - [ ] Pattern-thinking explanation
  - [ ] Example content

### Task 2.5: Create Business Case Template

- **Description**: Business justification format with ROI
- **File**: `references/formats/business-case.md`
- **Acceptance Criteria**:
  - [ ] Executive Summary section
  - [ ] Financial Impact table
  - [ ] Risk Assessment section
  - [ ] Approval tracking section
  - [ ] Example content

### Task 2.6: Create Planguage Template

- **Description**: Quantified requirements format
- **File**: `references/formats/planguage.md`
- **Acceptance Criteria**:
  - [ ] Scale, Meter, Past, Must, Plan, Wish sections
  - [ ] Measurement guidance
  - [ ] Example with metrics
  - [ ] When to use guidance

### Phase 2 Deliverables

- [ ] `references/formats/madr.md`
- [ ] `references/formats/nygard.md`
- [ ] `references/formats/y-statement.md`
- [ ] `references/formats/alexandrian.md`
- [ ] `references/formats/business-case.md`
- [ ] `references/formats/planguage.md`

### Phase 2 Exit Criteria

- [ ] All 6 format templates complete
- [ ] Each template has example content
- [ ] Templates match git-adr ADR_FORMATS.md

---

## Phase 3: Reference Documentation

**Goal**: Create comprehensive reference files for commands, config, and workflows

**Prerequisites**: Phase 2 complete

### Task 3.1: Create Commands Reference

- **Description**: Full documentation of all git-adr commands
- **File**: `references/commands.md`
- **Acceptance Criteria**:
  - [ ] All core commands (init, new, edit, list, show, search, rm, supersede, link, log)
  - [ ] All sync commands (sync, sync push, sync pull)
  - [ ] All artifact commands (attach, artifacts, artifact-get, artifact-rm)
  - [ ] All analytics commands (stats, report, metrics)
  - [ ] All export/import commands (export, import, convert)
  - [ ] All config commands (config list, config get, config set)
  - [ ] Wiki commands (wiki init, wiki sync)
  - [ ] Onboard command
  - [ ] Full syntax and options for each
  - [ ] Usage examples

### Task 3.2: Create Configuration Reference

- **Description**: Document all git-adr configuration options
- **File**: `references/configuration.md`
- **Acceptance Criteria**:
  - [ ] All adr.* config keys documented
  - [ ] Default values specified
  - [ ] Type and valid values listed
  - [ ] Common configuration recipes

### Task 3.3: Create Best Practices Guide

- **Description**: ADR writing guidance and common mistakes
- **File**: `references/best-practices.md`
- **Acceptance Criteria**:
  - [ ] What makes a good ADR
  - [ ] When to write an ADR
  - [ ] When NOT to write an ADR
  - [ ] Common mistakes to avoid
  - [ ] ADR lifecycle guidance

### Task 3.4: Create Workflows Guide

- **Description**: Common workflow patterns
- **File**: `references/workflows.md`
- **Acceptance Criteria**:
  - [ ] New project setup workflow
  - [ ] Team collaboration workflow
  - [ ] Migration from file-based ADRs
  - [ ] Onboarding new team members
  - [ ] Superseding decisions workflow

### Phase 3 Deliverables

- [ ] `references/commands.md`
- [ ] `references/configuration.md`
- [ ] `references/best-practices.md`
- [ ] `references/workflows.md`

### Phase 3 Exit Criteria

- [ ] All reference files complete
- [ ] Content matches git-adr documentation
- [ ] Cross-references between files work

---

## Phase 4: Testing & Packaging

**Goal**: Validate skill and package for distribution

**Prerequisites**: Phase 3 complete

### Task 4.1: Validate Skill Structure

- **Description**: Run skill validation checks
- **Acceptance Criteria**:
  - [ ] YAML frontmatter valid
  - [ ] All referenced files exist
  - [ ] No broken internal links
  - [ ] SKILL.md under 500 lines

### Task 4.2: Functional Testing

- **Description**: Test skill with Claude Code
- **Acceptance Criteria**:
  - [ ] Skill triggers on appropriate prompts
  - [ ] Commands execute correctly
  - [ ] Format templates generate valid ADRs
  - [ ] Config reading works
  - [ ] Progressive disclosure works

### Task 4.3: Package Skill

- **Description**: Create distributable .skill package
- **Acceptance Criteria**:
  - [ ] Package script runs successfully
  - [ ] .skill file created
  - [ ] All files included in package

### Task 4.4: Update Documentation

- **Description**: Update git-adr docs to reference skill
- **Acceptance Criteria**:
  - [ ] README mentions skill availability
  - [ ] Installation instructions added
  - [ ] Link to skill in documentation

### Task 4.5: Distribution Setup

- **Description**: Set up dual distribution
- **Acceptance Criteria**:
  - [ ] Skill in git-adr repo at skills/git-adr/
  - [ ] Instructions for copying to ~/.claude/skills/
  - [ ] Release packaging considered

### Phase 4 Deliverables

- [ ] Validated skill
- [ ] Packaged .skill file
- [ ] Updated documentation
- [ ] Distribution ready

### Phase 4 Exit Criteria

- [ ] All tests pass
- [ ] Skill works in both locations
- [ ] Documentation complete

---

## Dependency Graph

```
Phase 1: Core Structure
    │
    ├── Task 1.1 (directory) ──┐
    ├── Task 1.2 (frontmatter) ┼──> Task 1.3 (instructions) ──> Task 1.4 (patterns)
    └───────────────────────────┘
         │
         ▼
Phase 2: Format Templates (can run in parallel)
    │
    ├── Task 2.1 (MADR) ────────┐
    ├── Task 2.2 (Nygard) ──────┤
    ├── Task 2.3 (Y-Statement) ─┤
    ├── Task 2.4 (Alexandrian) ─┼──> Phase 2 Complete
    ├── Task 2.5 (Business) ────┤
    └── Task 2.6 (Planguage) ───┘
         │
         ▼
Phase 3: References (can run in parallel)
    │
    ├── Task 3.1 (commands) ────┐
    ├── Task 3.2 (config) ──────┼──> Phase 3 Complete
    ├── Task 3.3 (practices) ───┤
    └── Task 3.4 (workflows) ───┘
         │
         ▼
Phase 4: Testing & Packaging
    │
    ├── Task 4.1 (validate) ──> Task 4.2 (test) ──> Task 4.3 (package)
    │                                                    │
    └── Task 4.4 (docs) ─────────────────────────────────┴──> Task 4.5 (distribute)
```

## Risk Mitigation Tasks

| Risk | Mitigation Task | Phase |
|------|-----------------|-------|
| SKILL.md too large | Monitor line count, split if needed | Phase 1 |
| Format mismatch | Cross-reference with ADR_FORMATS.md | Phase 2 |
| Command syntax drift | Verify against current git-adr --help | Phase 3 |
| Packaging failure | Test with init_skill.py first | Phase 4 |

## Testing Checklist

- [ ] Skill triggers on "git adr" mentions
- [ ] Skill triggers on "ADR" and "architecture decision" mentions
- [ ] Commands execute without errors
- [ ] MADR format generates correctly
- [ ] Nygard format generates correctly
- [ ] Y-Statement format generates correctly
- [ ] Alexandrian format generates correctly
- [ ] Business Case format generates correctly
- [ ] Planguage format generates correctly
- [ ] Config reading works with set template
- [ ] Config reading falls back to MADR default
- [ ] References load on demand

## Documentation Tasks

- [ ] Update git-adr README with skill section
- [ ] Add skill installation instructions
- [ ] Document skill capabilities

## Launch Checklist

- [ ] All phases complete
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Skill packaged
- [ ] Distribution locations verified
