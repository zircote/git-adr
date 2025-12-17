---
document_type: implementation_plan
project_id: SPEC-2025-12-16-001
version: 1.0.0
last_updated: 2025-12-16T15:00:00Z
status: draft
estimated_effort: 2-3 hours
---

# git-adr Skill Release Workflow - Implementation Plan

## Overview

This plan implements automated skill packaging, release artifact generation, and end-user documentation in 3 focused phases. The implementation is designed to be completed in a single session with minimal disruption to the existing release workflow.

## Phase Summary

| Phase | Focus | Key Deliverables |
|-------|-------|------------------|
| Phase 1: Validation | CI quality gate | `.github/scripts/validate-skill.py` |
| Phase 2: Packaging | Release workflow | `build-skill-package` job in release.yml |
| Phase 3: Documentation | User-facing docs | `docs/git-adr-skill.md`, README updates |

---

## Phase 1: Validation Infrastructure

**Goal**: Create reusable skill validation script that enforces skill-spec rules

**Prerequisites**: None

### Task 1.1: Create Validation Script

- **Description**: Create Python script that validates SKILL.md against skill-spec rules
- **File**: `.github/scripts/validate-skill.py`
- **Acceptance Criteria**:
  - [ ] Validates SKILL.md existence
  - [ ] Parses YAML frontmatter
  - [ ] Checks required fields (name, description)
  - [ ] Validates name format (hyphen-case, 64 char max)
  - [ ] Validates description (no angle brackets, 1024 char max)
  - [ ] Checks only allowed keys in frontmatter
  - [ ] Returns exit code 0 on success, 1 on failure
  - [ ] Provides clear error messages
- **Notes**: Based on skill-creator's quick_validate.py but standalone

### Task 1.2: Test Validation Script Locally

- **Description**: Run validation script against skills/git-adr to verify it passes
- **Acceptance Criteria**:
  - [ ] Script runs without errors
  - [ ] Current skill passes validation
  - [ ] Invalid skills produce clear error messages (test with modified copy)

### Phase 1 Deliverables

- [ ] `.github/scripts/validate-skill.py` - Skill validation script

### Phase 1 Exit Criteria

- [ ] Validation script exists and is executable
- [ ] Current skill passes validation
- [ ] Error messages are clear and actionable

---

## Phase 2: Release Workflow Integration

**Goal**: Add skill packaging job to release.yml and include artifact in releases

**Prerequisites**: Phase 1 complete (validation script exists)

### Task 2.1: Add build-skill-package Job

- **Description**: Add new job to .github/workflows/release.yml that validates and packages the skill
- **Location**: Insert after `build-release-artifacts` job (around line 116)
- **Acceptance Criteria**:
  - [ ] Job runs in parallel with other build jobs
  - [ ] Extracts version from tag/input
  - [ ] Runs validation script
  - [ ] Creates `git-adr-{version}.skill` ZIP file
  - [ ] Uploads artifact as `skill-package`
- **Notes**: Use existing patterns for version extraction and artifact upload

### Task 2.2: Update release Job Dependencies

- **Description**: Modify release job to download skill artifact and include in release
- **Acceptance Criteria**:
  - [ ] `needs` includes `build-skill-package`
  - [ ] Downloads `skill-package` artifact
  - [ ] Skill file included in release `files` glob
- **Notes**: Use `continue-on-error: true` on skill job to not block main release

### Task 2.3: Update Release Body Template

- **Description**: Add skill installation section to release notes template
- **Location**: Lines 168-213 in release.yml
- **Acceptance Criteria**:
  - [ ] Skill section added after existing installation options
  - [ ] Includes download link with version placeholder
  - [ ] Includes extraction command
  - [ ] Matches existing documentation style

### Phase 2 Deliverables

- [ ] Modified `.github/workflows/release.yml` with skill packaging

### Phase 2 Exit Criteria

- [ ] Workflow syntax is valid (run `act` or create test PR)
- [ ] Job structure follows existing patterns
- [ ] Release body includes skill section

---

## Phase 3: Documentation

**Goal**: Create comprehensive documentation for skill installation and usage

**Prerequisites**: None (can be done in parallel with Phase 2)

### Task 3.1: Create Dedicated Skill Documentation

- **Description**: Create comprehensive skill documentation page
- **File**: `docs/git-adr-skill.md`
- **Acceptance Criteria**:
  - [x] Value proposition section with 4 key benefits:
    - Automatic ADR creation from natural language
    - Multi-format support (6 ADR formats)
    - Git-native storage (non-intrusive)
    - Direct command execution
  - [x] Installation section with 3 methods:
    - Download from GitHub release
    - Copy from repository
    - Extract from .skill package
  - [x] Quick start section (30-second example)
  - [x] Feature overview with examples
  - [x] Link to main git-adr documentation
- **Notes**: Target both Claude Code users and ADR practitioners

### Task 3.2: Enhance README Skill Section

- **Description**: Expand existing README skill section (lines 420-454)
- **File**: `README.md`
- **Acceptance Criteria**:
  - [x] Brief value proposition (1-2 sentences per benefit)
  - [x] Multiple installation methods (release download, copy, skill package)
  - [x] Quick example of skill in action
  - [x] Link to full documentation (`docs/git-adr-skill.md`)
- **Notes**: Keep README section concise; detailed info in docs/

### Phase 3 Deliverables

- [x] `docs/git-adr-skill.md` - Comprehensive skill documentation
- [x] Updated README.md skill section

### Phase 3 Exit Criteria

- [x] Documentation covers all 4 value propositions
- [x] Installation instructions are clear and complete
- [x] Quick start example works when followed

---

## Dependency Graph

```
Phase 1 ─────────────────────────────────────────┐
                                                 │
  Task 1.1 (Validation Script)                   │
       │                                         │
       ▼                                         │
  Task 1.2 (Test Script)                         │
       │                                         │
       ▼                                         │
Phase 2 ────────────────────────┐                │
                                │                │
  Task 2.1 (Package Job) ───────┤                │
                                │                │
  Task 2.2 (Release Deps) ──────┤                │
                                │                │
  Task 2.3 (Release Body) ──────┘                │
                                                 │
Phase 3 (Parallel) ──────────────────────────────┤
                                                 │
  Task 3.1 (Skill Docs) ─────────────────────────┤
                                                 │
  Task 3.2 (README Update) ──────────────────────┘
```

Phase 3 can run in parallel with Phase 2 since documentation has no dependencies on workflow implementation.

## Risk Mitigation Tasks

| Risk | Mitigation Task | Phase |
|------|-----------------|-------|
| Validation rules mismatch | Compare with quick_validate.py line-by-line | Phase 1 |
| Workflow syntax errors | Validate with yamllint before commit | Phase 2 |
| Skill package structure wrong | Test extraction manually | Phase 2 |
| Documentation unclear | Test with fresh user perspective | Phase 3 |

## Testing Checklist

- [ ] Validation script passes current skill
- [ ] Validation script fails on intentionally broken skill
- [ ] Workflow YAML syntax valid
- [ ] Local skill packaging creates correct ZIP structure
- [ ] Documentation installation steps work
- [ ] Quick start example produces expected result

## Documentation Tasks

- [ ] Create docs/git-adr-skill.md
- [ ] Update README.md skill section
- [ ] Update release body template with skill section

## Launch Checklist

- [ ] All validation tests passing
- [ ] Workflow syntax verified
- [ ] Documentation complete and reviewed
- [ ] Spec documents finalized (REQUIREMENTS.md, ARCHITECTURE.md, this file)

## Post-Launch

- [ ] Monitor first release with skill packaging
- [ ] Verify skill artifact in release assets
- [ ] Test download and installation from release
- [ ] Gather user feedback on documentation clarity
