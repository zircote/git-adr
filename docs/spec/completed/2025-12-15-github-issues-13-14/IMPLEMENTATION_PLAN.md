---
document_type: implementation_plan
project_id: SPEC-2025-12-15-001
version: 1.0.0
last_updated: 2025-12-15T00:00:00Z
status: draft
---

# GitHub Issues #13 & #14 - Implementation Plan

## Overview

This plan implements Homebrew distribution (#14) and documentation improvements (#13) for git-adr. Work is organized into 4 phases, with Homebrew and documentation tracks proceeding in parallel after initial setup.

## Phase Summary

| Phase | Description | Key Deliverables |
|-------|-------------|------------------|
| Phase 1: Setup | Create tap repo, initial formula, docs scaffold | Working `brew install` |
| Phase 2: Automation | Release workflow integration, CI | Automated updates |
| Phase 3: Documentation | Complete all documentation files | Full config & format docs |
| Phase 4: Polish | Man pages, navigation, final testing | Production-ready |

---

## Phase 1: Foundation

**Goal**: Working Homebrew installation and documentation scaffold

**Prerequisites**: GitHub account access, ability to create repositories

### Task 1.1: Create Homebrew Tap Repository

- **Description**: Create `zircote/homebrew-git-adr` repository on GitHub
- **Dependencies**: None
- **Acceptance Criteria**:
  - [x] Repository created at `github.com/zircote/homebrew-git-adr`
  - [x] MIT LICENSE file added
  - [x] README.md with installation instructions
  - [x] .gitignore for common patterns
- **Notes**: Use GitHub web UI or `gh repo create`

---

### Task 1.2: Generate PyPI Dependency List

- **Description**: Extract all dependencies with URLs and SHA256 for formula resources
- **Dependencies**: None
- **Acceptance Criteria**:
  - [x] List all runtime dependencies from pyproject.toml
  - [x] Fetch PyPI URLs for each package
  - [x] Calculate SHA256 for each download
  - [x] Format as Homebrew resource blocks
- **Notes**: Use `poet` tool: `pip install homebrew-pypi-poet && poet git-adr`

---

### Task 1.3: Create Initial Homebrew Formula

- **Description**: Write `Formula/git-adr.rb` with virtualenv pattern
- **Dependencies**: Task 1.1, Task 1.2
- **Acceptance Criteria**:
  - [x] Formula class with virtualenv mixin
  - [x] All dependencies as resource blocks
  - [x] Man page installation
  - [x] Shell completion generation
  - [x] Caveats for git alias
  - [x] Test block with version check
  - [ ] Passes `brew audit --strict`
- **Notes**: Reference Simon Willison's llm formula as template

---

### Task 1.4: Test Formula Locally

- **Description**: Verify formula installs and works on macOS
- **Dependencies**: Task 1.3
- **Acceptance Criteria**:
  - [ ] `brew install --build-from-source ./Formula/git-adr.rb` succeeds (blocked: needs PyPI release)
  - [ ] `git-adr --version` works (blocked: needs install)
  - [ ] `git-adr --help` works (blocked: needs install)
  - [ ] `man git-adr` works (blocked: needs install)
  - [ ] Shell completion works (bash/zsh) (blocked: needs install)
  - [x] `brew audit --strict` passes (1 expected error: URL needs PyPI)
- **Notes**: Test on both Intel and Apple Silicon if possible

---

### Task 1.5: Create Documentation Scaffold

- **Description**: Create empty documentation files with structure
- **Dependencies**: None
- **Acceptance Criteria**:
  - [x] docs/CONFIGURATION.md created with section headers
  - [x] docs/ADR_FORMATS.md created with section headers
  - [x] docs/ADR_PRIMER.md created with section headers
  - [x] docs/README.md (index) created
- **Notes**: Scaffold enables parallel work on content

### Phase 1 Deliverables

- [ ] `zircote/homebrew-git-adr` repository
- [ ] Working formula (local test only)
- [ ] Documentation file scaffold

### Phase 1 Exit Criteria

- [ ] `brew install --build-from-source` works
- [ ] All acceptance criteria for Tasks 1.1-1.5 met

---

## Phase 2: Automation

**Goal**: Automated formula updates on release

**Prerequisites**: Phase 1 complete, repository secrets configured

### Task 2.1: Create Tap CI Workflow

- **Description**: Add GitHub Actions workflow to test formula in tap repo
- **Dependencies**: Task 1.3
- **Acceptance Criteria**:
  - [ ] `.github/workflows/test.yml` in tap repo
  - [ ] Runs on push and PR
  - [ ] Tests formula installation
  - [ ] Tests `brew audit`
  - [ ] Tests `brew test`
  - [ ] Uses macOS runner
- **Notes**: Keep simple - just validation, not releases

---

### Task 2.2: Create Homebrew Update Token

- **Description**: Generate PAT for automated formula updates
- **Dependencies**: Task 1.1
- **Acceptance Criteria**:
  - [ ] PAT created with `repo` scope
  - [ ] Scoped to `homebrew-git-adr` repository only (fine-grained)
  - [ ] Added as `HOMEBREW_TAP_TOKEN` secret in `git-adr` repo
- **Notes**: Use fine-grained PAT if possible for minimal scope

---

### Task 2.3: Update Release Workflow

- **Description**: Add Homebrew formula update job to release.yml
- **Dependencies**: Task 2.2
- **Acceptance Criteria**:
  - [ ] New job `update-homebrew` in release.yml
  - [ ] Runs after PyPI publish
  - [ ] Uses bump-homebrew-formula-action or custom script
  - [ ] Updates version and SHA256 in formula
  - [ ] Creates commit in tap repo
- **Notes**: Consider Simon Willison's Python script approach as alternative

---

### Task 2.4: Test Release Automation

- **Description**: Verify end-to-end release flow updates formula
- **Dependencies**: Task 2.3
- **Acceptance Criteria**:
  - [ ] Create test release (or use existing workflow_dispatch)
  - [ ] Formula in tap repo is updated
  - [ ] SHA256 matches PyPI sdist
  - [ ] Version matches release tag
  - [ ] `brew update && brew upgrade git-adr` works
- **Notes**: May need to create a patch release to test

### Phase 2 Deliverables

- [ ] Tap repo CI workflow
- [ ] Automated formula updates on release

### Phase 2 Exit Criteria

- [ ] Release automatically updates formula
- [ ] CI validates formula on changes

---

## Phase 3: Documentation

**Goal**: Complete all documentation content

**Prerequisites**: Phase 1 scaffold complete

### Task 3.1: Write Configuration Reference

- **Description**: Document all configuration options with examples
- **Dependencies**: Task 1.5
- **Acceptance Criteria**:
  - [ ] All 14+ config keys documented
  - [ ] Each has: key, type, default, description, example
  - [ ] Grouped by category
  - [ ] Common recipes section
  - [ ] Linked from README
- **Notes**: Reference config.py for accuracy

**Configuration Keys to Document**:
```
Core: namespace, artifacts_namespace, template, editor
Artifacts: artifact_warn_size, artifact_max_size
Sync: sync.auto_push, sync.auto_pull, sync.merge_strategy
AI: ai.provider, ai.model, ai.temperature
Wiki: wiki.platform, wiki.auto_sync
```

---

### Task 3.2: Write ADR Format Guide

- **Description**: Document all built-in ADR formats with examples
- **Dependencies**: Task 1.5
- **Acceptance Criteria**:
  - [ ] Introduction to ADR formats
  - [ ] Comparison table for quick selection
  - [ ] Full documentation for each format:
    - MADR
    - Nygard
    - Y-Statement
    - Alexandrian
    - Business Case
    - Planguage
  - [ ] Each includes: when to use, full example, pros/cons
  - [ ] Custom template instructions
- **Notes**: Extract examples from templates.py

---

### Task 3.3: Write ADR Primer

- **Description**: Create beginner-friendly ADR introduction
- **Dependencies**: Task 1.5
- **Acceptance Criteria**:
  - [ ] "What is an ADR?" explained simply
  - [ ] Benefits section (onboarding, history, etc.)
  - [ ] "When to write" guidance
  - [ ] Lifecycle explanation
  - [ ] Common mistakes/anti-patterns
  - [ ] 5-minute quick start tutorial
  - [ ] Links to canonical resources
- **Notes**: Target audience is someone who has never heard of ADRs

---

### Task 3.4: Update Documentation Index

- **Description**: Create docs hub and update README links
- **Dependencies**: Tasks 3.1-3.3
- **Acceptance Criteria**:
  - [ ] docs/README.md links to all docs
  - [ ] Main README.md documentation section updated
  - [ ] Consistent navigation across all docs
- **Notes**: Keep navigation simple and discoverable

### Phase 3 Deliverables

- [ ] Complete CONFIGURATION.md
- [ ] Complete ADR_FORMATS.md
- [ ] Complete ADR_PRIMER.md
- [ ] Updated documentation index

### Phase 3 Exit Criteria

- [ ] All documentation files complete
- [ ] Cross-links working
- [ ] Technical accuracy verified

---

## Phase 4: Polish

**Goal**: Production-ready release

**Prerequisites**: Phases 1-3 complete

### Task 4.1: Update Man Pages

- **Description**: Add config reference to man pages
- **Dependencies**: Task 3.1
- **Acceptance Criteria**:
  - [ ] git-adr.1.md references configuration
  - [ ] Config section or see-also links added
  - [ ] Man pages regenerate correctly
- **Notes**: Keep man pages focused, link to full docs

---

### Task 4.2: Add Homebrew Installation to README

- **Description**: Update README with Homebrew installation option
- **Dependencies**: Phase 1-2 complete
- **Acceptance Criteria**:
  - [ ] Homebrew option in installation section
  - [ ] Correct tap and install commands
  - [ ] Note about automatic updates
- **Notes**: Position as primary macOS installation method

---

### Task 4.3: End-to-End Testing

- **Description**: Complete user journey testing
- **Dependencies**: All previous tasks
- **Acceptance Criteria**:
  - [ ] Fresh macOS install test
  - [ ] `brew tap && brew install` flow works
  - [ ] All documentation renders on GitHub
  - [ ] Man pages display correctly
  - [ ] Shell completions work
  - [ ] Config examples work as documented
- **Notes**: Consider testing on multiple macOS versions

---

### Task 4.4: Close GitHub Issues

- **Description**: Close issues #13 and #14 with references
- **Dependencies**: All tasks complete
- **Acceptance Criteria**:
  - [ ] Issue #14 closed with link to tap repo
  - [ ] Issue #13 closed with link to new docs
  - [ ] Both reference this implementation
- **Notes**: Include links to specific commits/PRs

### Phase 4 Deliverables

- [ ] Updated man pages
- [ ] Updated README
- [ ] Verified end-to-end experience
- [ ] Closed GitHub issues

### Phase 4 Exit Criteria

- [ ] All tasks complete
- [ ] User can `brew install` and have working git-adr
- [ ] User can find all config options documented
- [ ] Issues #13 and #14 closed

---

## Dependency Graph

```
Phase 1 (Foundation):
  Task 1.1 ──────────────────────┬──────────────────────────────────────┐
  Task 1.2 ──────────────────────┼─── Task 1.3 ─── Task 1.4             │
  Task 1.5 (parallel) ───────────┴──────────────────────────────────────┤
                                                                        │
Phase 2 (Automation):                                                   │
  Task 2.1 ◄── Task 1.3                                                 │
  Task 2.2 ◄── Task 1.1                                                 │
  Task 2.3 ◄── Task 2.2 ─── Task 2.4                                    │
                                                                        │
Phase 3 (Documentation, can run parallel with Phase 2):                 │
  Task 3.1 ◄── Task 1.5                                                 │
  Task 3.2 ◄── Task 1.5                                                 │
  Task 3.3 ◄── Task 1.5                                                 │
  Task 3.4 ◄── Tasks 3.1-3.3                                            │
                                                                        │
Phase 4 (Polish):                                                       │
  Task 4.1 ◄── Task 3.1                                                 │
  Task 4.2 ◄── Phases 1-2                                               │
  Task 4.3 ◄── All previous                                             │
  Task 4.4 ◄── Task 4.3                                                 │
```

## Risk Mitigation Tasks

| Risk | Mitigation Task | Phase |
|------|-----------------|-------|
| Formula fails audit | Local testing before push (Task 1.4) | 1 |
| PyPI unavailable | Consider GitHub tarball fallback | 1 |
| Action breaks | Document manual update procedure | 2 |
| Docs become stale | Add doc review to release checklist | 4 |

## Testing Checklist

- [ ] Formula passes `brew audit --strict`
- [ ] Formula passes `brew test`
- [ ] Man pages generate from markdown
- [ ] Shell completions work (bash, zsh, fish)
- [ ] All documentation links resolve
- [ ] Examples in docs are executable
- [ ] Config docs match actual defaults in code

## Documentation Tasks

- [ ] Update README.md with Homebrew section
- [ ] Create docs/CONFIGURATION.md
- [ ] Create docs/ADR_FORMATS.md
- [ ] Create docs/ADR_PRIMER.md
- [ ] Create docs/README.md (index)
- [ ] Update man pages with config references

## Launch Checklist

- [ ] Tap repository created and public
- [ ] Formula passes all tests
- [ ] Automation verified on test release
- [ ] All documentation complete
- [ ] README updated with Homebrew instructions
- [ ] Man pages updated
- [ ] Issues #13 and #14 closed

## Post-Launch

- [ ] Monitor Homebrew installation reports
- [ ] Gather documentation feedback
- [ ] Consider homebrew-core submission (after 3+ successful releases)
- [ ] Add bottles for faster installation (P2)
