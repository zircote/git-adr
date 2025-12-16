---
document_type: implementation_plan
project_id: SPEC-2025-12-15-002
version: 1.0.0
last_updated: 2025-12-15T23:50:00Z
status: draft
---

# Git Hooks & SDLC Integration - Implementation Plan

## Overview

This plan implements automatic ADR notes synchronization and SDLC integration as specified in the research report. Work is organized into 3 phases with clear deliverables.

## Phase Summary

| Phase | Focus | Key Deliverables |
|-------|-------|------------------|
| Phase 1 | Core Hook Support | hooks.py module, install/uninstall commands, init integration |
| Phase 2 | Configuration & Refspec | auto-push config, push refspecs, configurable blocking |
| Phase 3 | SDLC Integration | CI/CD templates, PR templates, governance patterns |

---

## Phase 1: Core Hook Support

**Goal**: Implement pre-push hook installation with backup-and-chain pattern

**Prerequisites**: Existing git-adr CLI, core/git.py, core/notes.py

### 1.1 Hook Manager Module

#### Task 1.1.1: Create hooks.py module
- **Description**: Implement Hook and HooksManager classes
- **File**: `src/git_adr/hooks.py`
- **Acceptance Criteria**:
  - [ ] `Hook` dataclass with type, hooks_dir, version attributes
  - [ ] `Hook.install()` method with force parameter
  - [ ] `Hook.uninstall()` method
  - [ ] `Hook.is_ours()` detection via marker comment
  - [ ] `Hook.get_version()` extracts version from script
  - [ ] `HooksManager` with install_all/uninstall_all methods
  - [ ] Unit tests for all methods
- **Dependencies**: None

#### Task 1.1.2: Implement backup-and-chain logic
- **Description**: Handle existing hooks by backing up and chaining
- **File**: `src/git_adr/hooks.py`
- **Acceptance Criteria**:
  - [ ] Detect existing non-git-adr hooks
  - [ ] Backup to `.git-adr-backup` suffix
  - [ ] Generated script calls backup hook
  - [ ] Backup restored on uninstall
  - [ ] Integration test with existing hook
- **Dependencies**: 1.1.1

#### Task 1.1.3: Implement pre-push hook script template
- **Description**: Create the shell script template for pre-push
- **File**: `src/git_adr/hooks.py`
- **Acceptance Criteria**:
  - [ ] POSIX sh compatible script
  - [ ] Version comment for upgrade detection
  - [ ] Recursion guard via `GIT_ADR_HOOK_RUNNING`
  - [ ] Skip check via `GIT_ADR_SKIP`
  - [ ] git-adr availability check (non-fatal)
  - [ ] Branch detection (skip for tags)
  - [ ] Delegation to `git adr hook pre-push`
  - [ ] Backup hook chaining
- **Dependencies**: 1.1.1

### 1.2 Hook Command Handler

#### Task 1.2.1: Create hook command module
- **Description**: Handle hook callbacks from shell scripts
- **File**: `src/git_adr/commands/hook.py`
- **Acceptance Criteria**:
  - [ ] `run_hook(hook_type, *args)` function
  - [ ] `_handle_pre_push(remote)` implementation
  - [ ] Uses NotesManager.sync_push()
  - [ ] Respects blockOnFailure config
  - [ ] Appropriate error handling
  - [ ] Unit tests
- **Dependencies**: None

#### Task 1.2.2: Register hook command in CLI
- **Description**: Add `git adr hook` command (internal)
- **File**: `src/git_adr/cli.py`
- **Acceptance Criteria**:
  - [ ] `@app.command(hidden=True)` decorator
  - [ ] Accepts hook_type and args
  - [ ] Calls run_hook()
- **Dependencies**: 1.2.1

### 1.3 Hook Management Commands

#### Task 1.3.1: Create hooks CLI module
- **Description**: User-facing hook management commands
- **File**: `src/git_adr/commands/hooks_cli.py`
- **Acceptance Criteria**:
  - [ ] `run_hooks_install(force, manual)` function
  - [ ] `run_hooks_uninstall()` function
  - [ ] `run_hooks_status()` function
  - [ ] Rich console output for status
  - [ ] Manual instructions output
- **Dependencies**: 1.1.1, 1.1.2

#### Task 1.3.2: Register hooks commands in CLI
- **Description**: Add hooks subcommands to CLI
- **File**: `src/git_adr/cli.py`
- **Acceptance Criteria**:
  - [ ] `git adr hooks install [--force] [--manual]`
  - [ ] `git adr hooks uninstall`
  - [ ] `git adr hooks status`
  - [ ] Help text for each command
- **Dependencies**: 1.3.1

#### Task 1.3.3: Export hooks functions
- **Description**: Update commands __init__.py
- **File**: `src/git_adr/commands/__init__.py`
- **Acceptance Criteria**:
  - [ ] Export run_hooks_install
  - [ ] Export run_hooks_uninstall
  - [ ] Export run_hooks_status
  - [ ] Export run_hook
- **Dependencies**: 1.2.1, 1.3.1

### 1.4 Init Integration

#### Task 1.4.1: Add interactive hook prompt to init
- **Description**: Prompt user about hook installation during init
- **File**: `src/git_adr/commands/init.py`
- **Acceptance Criteria**:
  - [ ] Prompt after config setup, before initial ADR
  - [ ] Default to "Yes" for installation
  - [ ] "Learn more" option shows explanation
  - [ ] Respects --no-input flag (skip prompt)
  - [ ] Integration test for init flow
- **Dependencies**: 1.1.1

#### Task 1.4.2: Add hook configuration defaults
- **Description**: Add hook-related config keys
- **File**: `src/git_adr/core/config.py`
- **Acceptance Criteria**:
  - [ ] `adr.hooks.blockOnFailure` default: false
  - [ ] `adr.hooks.installedVersion` tracking
  - [ ] Config validation for hook keys
- **Dependencies**: None

### 1.5 Testing & Documentation

#### Task 1.5.1: Add hook integration tests
- **Description**: End-to-end tests for hook functionality
- **File**: `tests/test_hooks.py`
- **Acceptance Criteria**:
  - [ ] Test hook installation creates executable
  - [ ] Test hook uninstall removes file
  - [ ] Test backup-and-chain with existing hook
  - [ ] Test pre-push triggers sync
  - [ ] Test GIT_ADR_SKIP bypasses hook
- **Dependencies**: 1.1.1, 1.2.1, 1.3.1

#### Task 1.5.2: Update man pages
- **Description**: Document hook commands
- **Files**: `docs/man/git-adr-hooks.1.md`
- **Acceptance Criteria**:
  - [ ] Man page for hooks command group
  - [ ] Examples for install/uninstall
  - [ ] Environment variable documentation
- **Dependencies**: 1.3.2

### Phase 1 Deliverables

- [ ] `src/git_adr/hooks.py` module
- [ ] `src/git_adr/commands/hook.py` handler
- [ ] `src/git_adr/commands/hooks_cli.py` commands
- [ ] Updated `src/git_adr/commands/init.py`
- [ ] Updated `src/git_adr/core/config.py`
- [ ] `tests/test_hooks.py`
- [ ] `docs/man/git-adr-hooks.1.md`

### Phase 1 Exit Criteria

- [ ] `git adr hooks install` creates working pre-push hook
- [ ] Hook syncs notes on `git push`
- [ ] Existing hooks are preserved via backup
- [ ] `git adr init` prompts for hook installation
- [ ] All tests pass

---

## Phase 2: Configuration & Push Refspec

**Goal**: Add configurable sync behavior and optional push refspec setup

**Prerequisites**: Phase 1 complete

### 2.1 Push Refspec Configuration

#### Task 2.1.1: Add auto-push refspec logic
- **Description**: Implement push refspec configuration in notes.py
- **File**: `src/git_adr/core/notes.py`
- **Acceptance Criteria**:
  - [ ] `_configure_remote_notes(remote, auto_push=False)`
  - [ ] Adds `refs/heads/*` push if first entry
  - [ ] Adds notes refs to push refspec
  - [ ] Idempotent (no duplicates)
  - [ ] Unit tests
- **Dependencies**: None

#### Task 2.1.2: Add --auto-push flag to init
- **Description**: Allow init to configure push refspecs
- **File**: `src/git_adr/commands/init.py`
- **Acceptance Criteria**:
  - [ ] `--auto-push` flag
  - [ ] Calls `_configure_remote_notes(auto_push=True)`
  - [ ] Config key `adr.sync.autoPush` set
  - [ ] Integration test
- **Dependencies**: 2.1.1

### 2.2 Configurable Sync Behavior

#### Task 2.2.1: Add sync configuration options
- **Description**: Implement configurable sync behavior
- **File**: `src/git_adr/core/config.py`
- **Acceptance Criteria**:
  - [ ] `adr.sync.timeout` config key (default: 5)
  - [ ] `adr.sync.autoPush` config key
  - [ ] Validation for timeout (positive integer)
- **Dependencies**: None

#### Task 2.2.2: Respect timeout in sync operations
- **Description**: Add timeout handling to sync
- **File**: `src/git_adr/core/notes.py`
- **Acceptance Criteria**:
  - [ ] Read timeout from config
  - [ ] Pass to git push/fetch subprocess
  - [ ] Graceful handling of timeout errors
- **Dependencies**: 2.2.1

### 2.3 Hook Configuration Commands

#### Task 2.3.1: Add hooks config subcommands
- **Description**: Allow configuring hook behavior via CLI
- **File**: `src/git_adr/commands/hooks_cli.py`
- **Acceptance Criteria**:
  - [ ] `git adr hooks config --block-on-failure`
  - [ ] `git adr hooks config --no-block-on-failure`
  - [ ] `git adr hooks config --show`
- **Dependencies**: 1.3.1

### Phase 2 Deliverables

- [ ] Updated `src/git_adr/core/notes.py` with auto-push
- [ ] Updated `src/git_adr/commands/init.py` with --auto-push
- [ ] Updated `src/git_adr/core/config.py` with sync config
- [ ] Hook configuration commands

### Phase 2 Exit Criteria

- [ ] `git adr init --auto-push` configures push refspecs
- [ ] `git push` without hook also syncs notes (if auto-push enabled)
- [ ] Sync timeout is configurable
- [ ] Block-on-failure is configurable

---

## Phase 3: SDLC Integration

**Goal**: Provide CI/CD templates and governance integration

**Prerequisites**: Phase 2 complete

### 3.1 Template Infrastructure

#### Task 3.1.1: Create templates directory structure
- **Description**: Set up Jinja2 templates for CI/CD
- **Files**: `src/git_adr/templates/ci/`, `src/git_adr/templates/governance/`
- **Acceptance Criteria**:
  - [ ] Directory structure created
  - [ ] Jinja2 added to dependencies
  - [ ] Template loader utility
- **Dependencies**: None

#### Task 3.1.2: Create GitHub Actions sync template
- **Description**: Workflow to sync ADRs to wiki
- **File**: `src/git_adr/templates/ci/github-actions-sync.yml.j2`
- **Acceptance Criteria**:
  - [ ] Triggers on push to main
  - [ ] Fetches notes refs
  - [ ] Runs wiki sync
  - [ ] Configurable branch
- **Dependencies**: 3.1.1

#### Task 3.1.3: Create GitLab CI sync template
- **Description**: Pipeline to sync ADRs
- **File**: `src/git_adr/templates/ci/gitlab-ci-sync.yml.j2`
- **Acceptance Criteria**:
  - [ ] Stage definition
  - [ ] Notes fetch
  - [ ] Wiki sync job
- **Dependencies**: 3.1.1

### 3.2 CI Commands

#### Task 3.2.1: Create ci command module
- **Description**: Commands to generate CI configurations
- **File**: `src/git_adr/commands/ci.py`
- **Acceptance Criteria**:
  - [ ] `run_ci_github(sync, validate)` function
  - [ ] `run_ci_gitlab(sync, validate)` function
  - [ ] Writes to appropriate locations
  - [ ] Warns if files exist
- **Dependencies**: 3.1.2, 3.1.3

#### Task 3.2.2: Register ci commands in CLI
- **Description**: Add ci subcommands
- **File**: `src/git_adr/cli.py`
- **Acceptance Criteria**:
  - [ ] `git adr ci github [--sync] [--validate]`
  - [ ] `git adr ci gitlab [--sync] [--validate]`
  - [ ] Help text
- **Dependencies**: 3.2.1

### 3.3 Governance Templates

#### Task 3.3.1: Create PR template
- **Description**: Pull request template with ADR checklist
- **File**: `src/git_adr/templates/governance/pr-template.md.j2`
- **Acceptance Criteria**:
  - [ ] Architecture impact checkbox
  - [ ] ADR reference field
  - [ ] Checklist items
- **Dependencies**: 3.1.1

#### Task 3.3.2: Create issue template
- **Description**: Issue template for ADR proposals
- **File**: `src/git_adr/templates/governance/issue-template.md.j2`
- **Acceptance Criteria**:
  - [ ] Context section
  - [ ] Proposed decision section
  - [ ] Alternatives section
  - [ ] Labels suggestion
- **Dependencies**: 3.1.1

#### Task 3.3.3: Create CODEOWNERS snippet
- **Description**: CODEOWNERS pattern for ADRs
- **File**: `src/git_adr/templates/governance/codeowners.j2`
- **Acceptance Criteria**:
  - [ ] Pattern for ADR files
  - [ ] Configurable team name
- **Dependencies**: 3.1.1

### 3.4 Templates Commands

#### Task 3.4.1: Create templates command module
- **Description**: Commands to generate governance files
- **File**: `src/git_adr/commands/templates.py`
- **Acceptance Criteria**:
  - [ ] `run_templates_pr()` function
  - [ ] `run_templates_issue()` function
  - [ ] `run_templates_codeowners(team)` function
  - [ ] Output to stdout or file
- **Dependencies**: 3.3.1, 3.3.2, 3.3.3

#### Task 3.4.2: Register templates commands in CLI
- **Description**: Add templates subcommands
- **File**: `src/git_adr/cli.py`
- **Acceptance Criteria**:
  - [ ] `git adr templates pr [--output PATH]`
  - [ ] `git adr templates issue [--output PATH]`
  - [ ] `git adr templates codeowners [--team NAME]`
- **Dependencies**: 3.4.1

### 3.5 Documentation

#### Task 3.5.1: Create SDLC integration guide
- **Description**: Documentation for CI/CD setup
- **File**: `docs/SDLC_INTEGRATION.md`
- **Acceptance Criteria**:
  - [ ] GitHub Actions setup guide
  - [ ] GitLab CI setup guide
  - [ ] Governance patterns guide
  - [ ] Examples for each platform
- **Dependencies**: 3.2.1, 3.4.1

### Phase 3 Deliverables

- [ ] `src/git_adr/templates/` directory with all templates
- [ ] `src/git_adr/commands/ci.py`
- [ ] `src/git_adr/commands/templates.py`
- [ ] `docs/SDLC_INTEGRATION.md`

### Phase 3 Exit Criteria

- [ ] `git adr ci github` generates working workflow
- [ ] `git adr ci gitlab` generates working pipeline
- [ ] `git adr templates pr` generates PR template
- [ ] Documentation complete

---

## Dependency Graph

```
Phase 1:
  1.1.1 ──┬──► 1.1.2 ──► 1.1.3
          │
          └──► 1.3.1 ──► 1.3.2
                         │
  1.2.1 ──► 1.2.2 ──────┼──► 1.3.3
                         │
  1.4.2 ──► 1.4.1 ──────┘
                         │
  1.5.1 ◄────────────────┘
  1.5.2 ◄── 1.3.2

Phase 2:
  2.1.1 ──► 2.1.2
  2.2.1 ──► 2.2.2
  1.3.1 ──► 2.3.1

Phase 3:
  3.1.1 ──┬──► 3.1.2 ──┬──► 3.2.1 ──► 3.2.2
          │            │
          ├──► 3.1.3 ──┘
          │
          ├──► 3.3.1 ──┬──► 3.4.1 ──► 3.4.2
          │            │
          ├──► 3.3.2 ──┤
          │            │
          └──► 3.3.3 ──┘
                       │
  3.5.1 ◄──────────────┘
```

## Risk Mitigation Tasks

| Risk | Mitigation Task | Phase |
|------|-----------------|-------|
| Hook conflicts with other tools | Backup-and-chain pattern | 1 |
| Platform-specific shell issues | POSIX sh compliance testing | 1 |
| CI workflow failures | Template testing in sample repos | 3 |

## Testing Checklist

- [ ] Unit tests for hooks.py
- [ ] Unit tests for hook.py command
- [ ] Integration tests for hook installation
- [ ] Integration tests for pre-push sync
- [ ] E2E test for full workflow
- [ ] Template rendering tests
- [ ] CI workflow dry-run tests

## Documentation Tasks

- [ ] Man page for hooks commands
- [ ] Update git-adr.1.md with hooks section
- [ ] SDLC integration guide
- [ ] Update README with hooks feature
- [ ] Update CONFIGURATION.md with new keys

## Launch Checklist

- [ ] All tests passing
- [ ] Documentation complete
- [ ] Man pages updated
- [ ] CHANGELOG updated
- [ ] Version bumped
- [ ] Release notes drafted
