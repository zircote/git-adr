---
document_type: implementation_plan
project_id: SPEC-2025-12-16-001
version: 1.0.0
last_updated: 2025-12-16
status: draft
estimated_effort: 2-3 days
---

# git-adr Claude Skill - Implementation Plan

## Overview

Implementation proceeds in four phases: Foundation (skill structure), Core Features (context loading + commands), Enhanced Workflows (creation + search), and Polish (testing + documentation).

## Phase Summary

| Phase | Key Deliverables |
|-------|------------------|
| Phase 1: Foundation | Skill scaffold, SKILL.md, basic references |
| Phase 2: Core Features | Auto-load context, command handlers, hydration |
| Phase 3: Enhanced Workflows | Guided creation, search patterns, error handling |
| Phase 4: Polish | Testing, documentation, installation guide |

---

## Phase 1: Foundation

**Goal**: Establish skill structure with proper metadata and navigation

**Prerequisites**: Understanding of Claude skill patterns (completed in research)

### Tasks

#### Task 1.1: Create Skill Directory Structure
- **Description**: Create `git-adr/` directory with subdirectories
- **Acceptance Criteria**:
  - [x] `git-adr/SKILL.md` created with frontmatter
  - [x] `git-adr/references/` directory exists
  - [x] `git-adr/formats/` directory exists (at references/formats/)
  - [x] `git-adr/workflows/` directory exists

#### Task 1.2: Write SKILL.md Entry Point
- **Description**: Core skill file with metadata, critical rules, and navigation
- **Acceptance Criteria**:
  - [x] Frontmatter with name, description, version
  - [x] CRITICAL RULES section (config protection)
  - [x] Auto-Context Loading section
  - [x] Trigger Phrases section
  - [x] Quick Command Reference table
  - [x] Progressive Loading Guide (navigation table)
  - [x] File size: 8-12 KB (10.4 KB)

#### Task 1.3: Create Command Reference
- **Description**: `references/commands.md` with curated command documentation
- **Dependencies**: Task 1.1
- **Acceptance Criteria**:
  - [x] Commands: list, show, new, edit, search, ai suggest
  - [x] Each command: syntax, options, examples
  - [x] File size: 3-5 KB (7.7 KB - exceeded, more comprehensive)

#### Task 1.4: Create Format Templates
- **Description**: Format reference files for MADR and alternatives
- **Dependencies**: Task 1.1
- **Acceptance Criteria**:
  - [x] `formats/madr.md` with full template
  - [x] `formats/nygard.md` with template
  - [x] `formats/y-statement.md` with template
  - [x] Each file: 1-3 KB (2-6 KB, plus alexandrian, business-case, planguage)

### Phase 1 Deliverables
- [x] Skill directory structure
- [x] SKILL.md with navigation
- [x] references/commands.md
- [x] formats/ directory with templates

### Phase 1 Exit Criteria
- [x] Skill is discoverable by Claude Code
- [x] SKILL.md loads without errors
- [x] Navigation links resolve to existing files

---

## Phase 2: Core Features

**Goal**: Implement context auto-loading and core command handlers

**Prerequisites**: Phase 1 complete

### Tasks

#### Task 2.1: Context Loading Instructions
- **Description**: Write `workflows/session-start.md` with auto-load behavior
- **Acceptance Criteria**:
  - [ ] Detection logic (git repo? ADRs init?)
  - [ ] Summary format specification
  - [ ] Error handling for common issues
  - [ ] Example output block

#### Task 2.2: Hydration Handler
- **Description**: Document on-demand full ADR loading in SKILL.md
- **Dependencies**: Task 2.1
- **Acceptance Criteria**:
  - [ ] Trigger phrases documented
  - [ ] ID/title/keyword matching explained
  - [ ] `git adr show` command integration
  - [ ] Example conversation flow

#### Task 2.3: Search Handler
- **Description**: Write `references/search-patterns.md` for decision lookup
- **Acceptance Criteria**:
  - [ ] Search syntax documentation
  - [ ] Natural language → query mapping
  - [ ] Status/tag filtering
  - [ ] Example search scenarios

#### Task 2.4: List Handler
- **Description**: Document list command with format options
- **Dependencies**: Task 1.3
- **Acceptance Criteria**:
  - [ ] Format options: table, yaml, oneline
  - [ ] Filter options: status, tag, date range
  - [ ] Output examples

### Phase 2 Deliverables
- [ ] workflows/session-start.md
- [ ] Search patterns documentation
- [ ] Hydration trigger documentation
- [ ] List command documentation

### Phase 2 Exit Criteria
- [ ] Context loads at session start (manual test)
- [ ] `show me ADR-001` triggers hydration
- [ ] Search returns relevant results

---

## Phase 3: Enhanced Workflows

**Goal**: Implement ADR creation and advanced search capabilities

**Prerequisites**: Phase 2 complete

### Tasks

#### Task 3.1: Guided Creation Workflow
- **Description**: Write `workflows/decision-capture.md` for conversation extraction
- **Acceptance Criteria**:
  - [ ] Trigger phrase documentation
  - [ ] Context extraction prompts
  - [ ] MADR-guided question flow
  - [ ] Draft review step
  - [ ] `git adr new` integration

#### Task 3.2: AI Suggest Integration
- **Description**: Document `git adr ai suggest` in commands.md
- **Dependencies**: Task 1.3
- **Acceptance Criteria**:
  - [ ] When to use AI suggest
  - [ ] Required setup (AI provider config)
  - [ ] Example improvement flow

#### Task 3.3: Decision Recall Workflow
- **Description**: Write `workflows/decision-recall.md` for finding past decisions
- **Acceptance Criteria**:
  - [ ] "What did we decide about X?" handling
  - [ ] Keyword → ADR mapping
  - [ ] Related ADRs suggestions
  - [ ] Example recall scenarios

#### Task 3.4: Error Handling Enhancement
- **Description**: Comprehensive error messages in SKILL.md
- **Acceptance Criteria**:
  - [ ] Not installed: install command
  - [ ] Not initialized: init command
  - [ ] ADR not found: list suggestion
  - [ ] Permission denied: explanation

### Phase 3 Deliverables
- [ ] workflows/decision-capture.md
- [ ] workflows/decision-recall.md
- [ ] Enhanced error handling
- [ ] AI suggest documentation

### Phase 3 Exit Criteria
- [ ] "Record this decision" triggers creation workflow
- [ ] "What did we decide about caching?" finds relevant ADRs
- [ ] All error conditions have clear guidance

---

## Phase 4: Polish

**Goal**: Testing, documentation completion, installation guide

**Prerequisites**: Phase 3 complete

### Tasks

#### Task 4.1: Integration Testing
- **Description**: Test skill in real git-adr repository
- **Acceptance Criteria**:
  - [ ] Session start loads context
  - [ ] All trigger phrases work
  - [ ] Error conditions handled gracefully
  - [ ] No shell injection vulnerabilities

#### Task 4.2: Configuration Reference
- **Description**: Write `references/configuration.md` with all options
- **Acceptance Criteria**:
  - [ ] git-adr config options
  - [ ] AI provider setup
  - [ ] Template selection
  - [ ] Read-only emphasis

#### Task 4.3: Installation Guide
- **Description**: Add installation instructions to SKILL.md
- **Acceptance Criteria**:
  - [ ] pip install command
  - [ ] brew install command
  - [ ] Skill installation paths
  - [ ] Verification steps

#### Task 4.4: Final Review
- **Description**: Quality check all documentation
- **Acceptance Criteria**:
  - [ ] All links valid
  - [ ] Code examples tested
  - [ ] Consistent formatting
  - [ ] Size targets met

### Phase 4 Deliverables
- [ ] references/configuration.md
- [ ] Installation guide
- [ ] Tested, polished skill

### Phase 4 Exit Criteria
- [ ] Skill passes all integration tests
- [ ] Documentation complete and accurate
- [ ] Ready for user adoption

---

## Dependency Graph

```
Phase 1:
  Task 1.1 (Structure) ─┬──▶ Task 1.2 (SKILL.md)
                        │
                        ├──▶ Task 1.3 (Commands)
                        │
                        └──▶ Task 1.4 (Formats)

Phase 2:
  Phase 1 Complete ─┬──▶ Task 2.1 (Context Loading)
                    │
                    ├──▶ Task 2.2 (Hydration) ──▶ depends on 2.1
                    │
                    ├──▶ Task 2.3 (Search)
                    │
                    └──▶ Task 2.4 (List)

Phase 3:
  Phase 2 Complete ─┬──▶ Task 3.1 (Guided Creation)
                    │
                    ├──▶ Task 3.2 (AI Suggest)
                    │
                    ├──▶ Task 3.3 (Decision Recall)
                    │
                    └──▶ Task 3.4 (Error Handling)

Phase 4:
  Phase 3 Complete ─┬──▶ Task 4.1 (Testing)
                    │
                    ├──▶ Task 4.2 (Configuration)
                    │
                    ├──▶ Task 4.3 (Installation)
                    │
                    └──▶ Task 4.4 (Final Review) ──▶ depends on all above
```

## Risk Mitigation Tasks

| Risk | Mitigation Task | Phase |
|------|-----------------|-------|
| git-adr not installed | Task 3.4: Clear install instructions | Phase 3 |
| Token budget exceeded | Task 2.1: Summary format optimization | Phase 2 |
| AI extraction errors | Task 3.1: User review step | Phase 3 |
| Config modification | Task 1.2: Critical rules section | Phase 1 |

## Testing Checklist

- [ ] Skill loads in Claude Code
- [ ] Trigger phrases activate correctly
- [ ] Context loading works at session start
- [ ] Hydration loads full ADR
- [ ] Search finds relevant ADRs
- [ ] Creation workflow guides user
- [ ] All error conditions have messages
- [ ] No shell injection vulnerabilities
- [ ] File sizes within targets

## Documentation Tasks

- [ ] SKILL.md complete and navigable
- [ ] All reference files written
- [ ] All workflow files written
- [ ] Format templates included
- [ ] Configuration documented
- [ ] Installation guide included

## Launch Checklist

- [ ] All tests passing
- [ ] Documentation complete
- [ ] Skill file sizes within targets
- [ ] Tested in git-adr repository
- [ ] README updated (if applicable)
- [ ] Version tagged in metadata

## Post-Launch

- [ ] Monitor user feedback
- [ ] Track common issues
- [ ] Consider MCP server enhancement
- [ ] Update based on git-adr changes
