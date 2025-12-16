---
document_type: requirements
project_id: SPEC-2025-12-15-002
version: 1.0.0
last_updated: 2025-12-15T23:30:00Z
status: draft
---

# Git Hooks & SDLC Integration - Product Requirements Document

## Executive Summary

This specification defines the requirements for automatic ADR notes synchronization via git hooks and integration of git-adr into the Software Development Lifecycle (SDLC). The implementation provides defense-in-depth through three complementary mechanisms: pre-push hooks (active enforcement), push refspec configuration (passive sync), and CI/CD integration (centralized validation).

**Based on**: Research Report - Git Hooks for Ref Sync & SDLC Integration

## Problem Statement

### The Problem

Currently, git-adr requires users to manually run `git adr sync --push` to synchronize ADR notes with remote repositories. This creates a gap between local and remote state, leading to:

1. **Lost decisions** - ADRs created locally but never pushed become invisible to the team
2. **Divergence** - Multiple developers may have different views of architectural decisions
3. **No enforcement** - No mechanism ensures ADRs are reviewed before merging
4. **Manual overhead** - Users must remember an extra step in their workflow

### Impact

| Stakeholder | Impact |
|-------------|--------|
| Individual developers | Must remember extra sync command; risk losing work |
| Teams | Inconsistent ADR visibility; review gaps |
| Organizations | Governance/compliance risks; architectural drift |

### Current State

The existing implementation configures:
- ✅ Fetch refspecs for automatic pull of notes on `git fetch`
- ✅ `notes.rewriteRef` for rebase/amend safety
- ❌ No push refspecs - requires explicit `git adr sync --push`
- ❌ No pre-push hooks for automatic sync
- ❌ No CI/CD integration for validation
- ❌ No governance templates (PR templates, CODEOWNERS)

## Goals and Success Criteria

### Primary Goal

Ensure ADR notes are automatically synchronized with remote repositories without user intervention, while providing organizational governance mechanisms for teams.

### Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Auto-sync adoption | 80% of users enable hooks | Config telemetry (opt-in) |
| Sync failure rate | < 1% of pushes | Hook exit code monitoring |
| Notes divergence | 0 repos with local-only ADRs | CI validation check |
| User friction | No increase in push time | Performance benchmarking |

### Non-Goals (Explicit Exclusions)

- Bi-directional sync (editing ADRs in remote UI) - out of scope
- Cross-repository ADR management - deferred to future version
- Real-time sync (WebSocket/polling) - git operations only
- Hook installation for all git operations (only pre-push initially)

## User Analysis

### Primary Users

**1. Individual Developers**
- **Needs**: Convenience, automatic sync, minimal configuration
- **Context**: Working on personal or small team projects
- **Pain points**: Forgetting to sync, losing ADR work

**2. Enterprise Teams**
- **Needs**: Governance, review workflows, compliance enforcement
- **Context**: Large organizations with formal architecture review processes
- **Pain points**: No visibility into ADR creation, no review gates

### User Stories

#### Developer Convenience (P0)

1. As a developer, I want ADR notes to sync automatically when I push code, so that I don't have to remember a separate sync command.

2. As a developer, I want to be prompted during `git adr init` about hook installation, so that I can make an informed choice.

3. As a developer, I want hook failures to be non-fatal by default, so that my push isn't blocked by sync issues.

#### Team Governance (P1)

4. As a tech lead, I want a GitHub Actions workflow to validate ADR structure in PRs, so that malformed ADRs are caught before merge.

5. As an architect, I want a CODEOWNERS pattern for ADRs, so that architecture team review is required.

6. As a team member, I want a PR template that asks about architectural impact, so that ADR requirements are visible.

#### Configuration (P1)

7. As a user, I want to configure whether sync failures block pushes, so that I can choose my risk tolerance.

8. As a user, I want to chain git-adr hooks with my existing hooks, so that I don't lose my custom automation.

9. As a user, I want to skip hooks temporarily via environment variable, so that I can bypass in emergencies.

## Functional Requirements

### Must Have (P0)

| ID | Requirement | Rationale | Acceptance Criteria |
|----|-------------|-----------|---------------------|
| FR-001 | Pre-push hook auto-syncs ADR notes to remote | Primary mechanism for automatic sync | Hook pushes `refs/notes/adr` and `refs/notes/adr-artifacts` on branch push |
| FR-002 | Interactive prompt during `git adr init` for hook installation | User opted for interactive install | Prompt displays options: Install hooks / Skip / Learn more |
| FR-003 | `git adr hooks install` command | Explicit hook management for existing repos | Installs pre-push hook with version tracking |
| FR-004 | `git adr hooks uninstall` command | Remove hooks without manual intervention | Removes git-adr hooks, restores backups if present |
| FR-005 | Recursion guard prevents infinite loops | Essential safety mechanism | Environment variable `GIT_ADR_HOOK_RUNNING` checked |
| FR-006 | Chain with existing hooks (backup-and-chain) | User requested chaining approach | Existing hook backed up to `.git-adr-backup`, called after git-adr logic |
| FR-007 | Skip hook via `GIT_ADR_SKIP=1` | Emergency bypass capability | Hook exits early if env var set |
| FR-008 | Non-fatal by default, configurable to block | Configurable failure mode | Config key `adr.hooks.blockOnFailure` (default: false) |

### Should Have (P1)

| ID | Requirement | Rationale | Acceptance Criteria |
|----|-------------|-----------|---------------------|
| FR-101 | `--auto-push` option in `git adr init` | Passive sync via refspec config | Adds push refspec to `.git/config` for notes refs |
| FR-102 | `git adr hooks status` command | Check current hook state | Shows installed hooks, versions, backup status |
| FR-103 | GitHub Actions workflow template | CI/CD integration | `git adr ci github` generates `.github/workflows/adr-sync.yml` |
| FR-104 | GitLab CI workflow template | CI/CD integration | `git adr ci gitlab` generates `.gitlab-ci.yml` snippet |
| FR-105 | PR template generation | Governance integration | `git adr templates pr` generates PR template with ADR checklist |
| FR-106 | CODEOWNERS snippet generation | Review enforcement | `git adr templates codeowners` outputs CODEOWNERS pattern |
| FR-107 | Issue template for ADR proposals | Workflow integration | `git adr templates issue` generates GitHub/GitLab issue template |
| FR-108 | `--manual` flag for merge instructions | Handle complex hook setups | Shows snippet to add to existing hooks |

### Nice to Have (P2)

| ID | Requirement | Rationale | Acceptance Criteria |
|----|-------------|-----------|---------------------|
| FR-201 | ADR structure validation in CI | Centralized validation | Workflow validates required sections present |
| FR-202 | Hook version auto-upgrade | Seamless updates | Detects old git-adr hooks, offers upgrade |
| FR-203 | Generic CI template (Jenkins, CircleCI) | Broader platform support | Documentation + example scripts |
| FR-204 | Post-commit hook option | Alternative sync point | Optional hook that syncs on commit |
| FR-205 | Commit-msg hook for ADR linking | Auto-link commits to ADRs | Parse commit message for ADR references |

## Non-Functional Requirements

### Performance

- Hook execution adds < 500ms to push time in normal conditions
- Network failures timeout after 5 seconds (configurable)
- Hook script size < 100 lines

### Security

- No credentials stored in hook scripts
- Hooks use existing git credential chain
- Backup files not executable
- No remote code execution vectors

### Reliability

- Sync failures are logged but non-blocking by default
- Partial failures (artifacts fail, ADRs succeed) are handled gracefully
- Hooks are idempotent (safe to run multiple times)

### Maintainability

- Hook scripts include version number for upgrade detection
- Clear separation between hook script and git-adr logic
- Backup files follow consistent naming (.git-adr-backup suffix)

### Compatibility

- Supports Git 2.20+ (for notes operations)
- Works with GitHub, GitLab, Bitbucket, and generic Git remotes
- Compatible with other hook managers (Husky, pre-commit) via chaining
- Shell script hooks (POSIX sh) for maximum portability

## Technical Constraints

- Python 3.11+ (matches git-adr requirement)
- Typer CLI framework (matches existing)
- Subprocess-based git operations (matches existing pattern)
- No additional runtime dependencies for hooks (pure shell)

## Dependencies

### Internal Dependencies

- `core/git.py` - Git subprocess operations
- `core/config.py` - Configuration management
- `core/notes.py` - Notes push/pull operations
- `commands/init.py` - Hook installation integration

### External Dependencies

- Git 2.20+ binary
- Shell interpreter (sh/bash)
- GitHub/GitLab API (optional, for CI templates)

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Hook conflicts with existing tools | Medium | Medium | Backup-and-chain pattern; --manual flag |
| Push blocking causes user frustration | Medium | High | Non-blocking default; GIT_ADR_SKIP escape hatch |
| Platform-specific shell issues | Low | Medium | POSIX sh compliance; test on multiple platforms |
| Hook version fragmentation | Low | Low | Version tracking; auto-upgrade mechanism |

## Open Questions

- [x] Hook installation opt-in vs opt-out? → **Interactive prompt**
- [x] How to handle existing pre-push hooks? → **Chain (append with backup)**
- [x] Should auto-push be default behavior? → **No, explicit opt-in**
- [x] Sync failure blocking behavior? → **Configurable, default non-blocking**

## Appendix

### Glossary

| Term | Definition |
|------|------------|
| Pre-push hook | Git hook that runs before push completes |
| Refspec | Git reference specification for push/fetch operations |
| Notes ref | Git reference for notes (`refs/notes/adr`) |
| Backup-and-chain | Pattern where existing hook is backed up and called from new hook |

### References

- [Research Report](/Users/AllenR1_1/Projects/zircote/git-adr/docs/research/RESEARCH_REPORT.md)
- [Git Hooks Documentation](https://git-scm.com/docs/githooks)
- [git-lfs Hook Implementation](https://github.com/git-lfs/git-lfs/blob/main/lfs/hook.go)
- [git-adr CLI Spec](../2025-12-15-git-adr-cli/README.md)
