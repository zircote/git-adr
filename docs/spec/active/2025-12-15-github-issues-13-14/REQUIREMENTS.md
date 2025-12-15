---
document_type: requirements
project_id: SPEC-2025-12-15-001
version: 1.0.0
last_updated: 2025-12-15T00:00:00Z
status: draft
github_issues:
  - number: 14
    title: "[FEATURE] homebrew release"
    url: https://github.com/zircote/git-adr/issues/14
  - number: 13
    title: "[FEATURE] docs do not include configuration items"
    url: https://github.com/zircote/git-adr/issues/13
---

# GitHub Issues #13 & #14 - Product Requirements Document

## Executive Summary

This project addresses two enhancement requests for git-adr:

1. **Issue #14 - Homebrew Release**: Enable `brew install git-adr` by creating a personal Homebrew tap with automated formula updates on release.

2. **Issue #13 - Documentation Improvements**: Create comprehensive configuration documentation and an ADR format guide for users unfamiliar with Architecture Decision Records.

Both enhancements improve developer experience (DX) - #14 simplifies installation, #13 reduces the learning curve.

## Problem Statement

### The Problem

**Distribution Gap (#14)**: Users cannot install git-adr via Homebrew, the dominant package manager for macOS developers. Current installation requires pip/uv knowledge and manual setup of shell completions and man pages.

**Documentation Gap (#13)**: The existing documentation assumes familiarity with ADRs and doesn't comprehensively cover:
- All configuration options with examples
- ADR format alternatives (MADR is shown but others exist)
- Concepts for ADR beginners

### Impact

| User Segment | Problem | Severity |
|--------------|---------|----------|
| macOS developers | Must use pip instead of familiar `brew install` | Medium |
| ADR beginners | No concept explanations, steep learning curve | High |
| Power users | Can't discover all configuration options | Medium |

### Current State

**Installation Methods Today:**
- `pip install git-adr` or `uv tool install git-adr` (requires Python knowledge)
- GitHub release tarball with `install.sh` (requires manual download)
- From source via Makefile (requires dev environment)

**Documentation Today:**
- README.md: Good quickstart, lists commands
- docs/COMMANDS.md: Command reference
- Man pages: 5 pages covering main commands
- Missing: Complete config reference, ADR format guide, beginner concepts

## Goals and Success Criteria

### Primary Goals

1. **Homebrew**: Users can run `brew tap zircote/git-adr && brew install git-adr` successfully
2. **Documentation**: Users can find answers to "what does config X do?" and "what ADR formats exist?"

### Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Homebrew formula works | 100% | Automated CI tests on macOS |
| Config options documented | 100% | Audit against config.py |
| ADR formats documented | 6 formats | Count in format guide |
| Time to first ADR (new user) | < 5 min | User testing |

### Non-Goals (Explicit Exclusions)

- Submission to homebrew-core (future consideration after tap is stable)
- Linux package managers (apt, dnf, etc.)
- Windows package managers (chocolatey, winget)
- Video tutorials or interactive documentation
- Internationalization/translation

## User Analysis

### Primary Users

| User Type | Description | Key Needs |
|-----------|-------------|-----------|
| macOS Developer | Uses Homebrew for tooling | `brew install` workflow, man pages in standard location |
| ADR Beginner | New to Architecture Decision Records | Concept explanations, format examples, guided setup |
| Power User | Experienced with git-adr | Discoverable config options, advanced customization |

### User Stories

#### Homebrew (#14)

1. As a macOS developer, I want to install git-adr via `brew install` so that I can use my familiar package management workflow.

2. As a Homebrew user, I want man pages installed to `/usr/local/share/man` so that `man git-adr` works after installation.

3. As a user upgrading git-adr, I want `brew upgrade git-adr` to work so that I get new features automatically.

#### Documentation (#13)

4. As an ADR beginner, I want to understand what ADRs are and why they matter so that I can evaluate if git-adr fits my needs.

5. As a user choosing an ADR format, I want to see examples of all supported formats so that I can pick the one that fits my team's style.

6. As a power user, I want a comprehensive config reference so that I can customize git-adr behavior without reading source code.

7. As a user setting up AI features, I want clear documentation of AI configuration options so that I can integrate with my LLM provider.

## Functional Requirements

### Must Have (P0)

#### FR-001: Personal Homebrew Tap Repository

**Description**: Create `homebrew-git-adr` repository under zircote GitHub account.

**Rationale**: Personal tap allows rapid iteration without homebrew-core approval process.

**Acceptance Criteria**:
- [ ] Repository exists at `github.com/zircote/homebrew-git-adr`
- [ ] Contains valid `Formula/git-adr.rb`
- [ ] `brew tap zircote/git-adr` succeeds
- [ ] README explains installation and uninstallation

---

#### FR-002: Homebrew Formula for git-adr

**Description**: Create Ruby formula that installs git-adr, man pages, and shell completions.

**Rationale**: Formula is the standard Homebrew packaging unit.

**Acceptance Criteria**:
- [ ] Formula downloads from PyPI sdist (or GitHub release tarball)
- [ ] Installs `git-adr` binary to libexec using virtualenv pattern
- [ ] Creates bin shim that invokes libexec binary
- [ ] Installs man pages to `share/man/man1/`
- [ ] Installs bash/zsh/fish completions to appropriate locations
- [ ] Passes `brew audit --strict --online`
- [ ] Passes `brew test git-adr`

---

#### FR-003: Automated Formula Updates on Release

**Description**: GitHub Action updates formula SHA and version when new release is tagged.

**Rationale**: Manual formula updates are error-prone and create delays.

**Acceptance Criteria**:
- [ ] Release workflow triggers formula update
- [ ] Formula version and SHA256 are updated automatically
- [ ] PR or direct push to tap repository
- [ ] CI validates formula before merge

---

#### FR-004: Configuration Reference Documentation

**Description**: Document all git config keys used by git-adr with types, defaults, and examples.

**Rationale**: Issue #13 specifically requests this.

**Acceptance Criteria**:
- [ ] All 15+ config keys documented (from config.py audit)
- [ ] Each entry includes: key, type, default, description, example
- [ ] Grouped by category (core, sync, AI, wiki)
- [ ] Available via `docs/CONFIGURATION.md` and man page reference

**Configuration Keys to Document** (from codebase analysis):

| Key | Type | Default |
|-----|------|---------|
| `adr.namespace` | string | `adr` |
| `adr.artifacts_namespace` | string | `adr-artifacts` |
| `adr.template` | string | `madr` |
| `adr.editor` | string | (system default) |
| `adr.artifact_warn_size` | int | 1048576 (1MB) |
| `adr.artifact_max_size` | int | 10485760 (10MB) |
| `adr.sync.auto_push` | bool | false |
| `adr.sync.auto_pull` | bool | true |
| `adr.sync.merge_strategy` | string | `union` |
| `adr.ai.provider` | string | (none) |
| `adr.ai.model` | string | (provider default) |
| `adr.ai.temperature` | float | 0.7 |
| `adr.wiki.platform` | string | (auto-detect) |
| `adr.wiki.auto_sync` | bool | false |

---

#### FR-005: ADR Format Guide

**Description**: Document all supported ADR templates with full examples and use case guidance.

**Rationale**: Issue #13 requests removing "overly deterministic" MADR-only focus.

**Acceptance Criteria**:
- [ ] All 6 built-in templates documented: madr, nygard, y-statement, alexandrian, business, planguage
- [ ] Each format includes: description, when to use, full example, pros/cons
- [ ] Comparison table for quick selection
- [ ] Instructions for custom templates
- [ ] Available via `docs/ADR_FORMATS.md`

---

#### FR-006: ADR Concepts for Beginners

**Description**: Add introductory content explaining what ADRs are and why they matter.

**Rationale**: User selected "ADR beginners" as target audience.

**Acceptance Criteria**:
- [ ] "What is an ADR?" section
- [ ] Benefits of documenting decisions
- [ ] When to write an ADR
- [ ] Common anti-patterns
- [ ] Links to seminal resources (Nygard blog post, MADR spec)
- [ ] Available via `docs/ADR_PRIMER.md` or README expansion

### Should Have (P1)

#### FR-101: Formula Test Block

**Description**: Homebrew formula includes test block that validates installation.

**Rationale**: Enables `brew test git-adr` and CI validation.

**Acceptance Criteria**:
- [ ] Test verifies `git-adr --version` output
- [ ] Test verifies `git-adr --help` works
- [ ] Test runs in sandboxed Homebrew environment

---

#### FR-102: Homebrew Caveats

**Description**: Formula displays post-install instructions for git alias setup.

**Rationale**: Users may not know to configure `git adr` alias.

**Acceptance Criteria**:
- [ ] Caveat explains `git config --global alias.adr '!git-adr'`
- [ ] Caveat displays on install and `brew info`

---

#### FR-103: Man Page Updates

**Description**: Update man pages to reference new configuration documentation.

**Rationale**: Man pages should be the authoritative reference for terminal users.

**Acceptance Criteria**:
- [ ] `git-adr.1` references config section
- [ ] Config man page or section added
- [ ] Format examples in relevant man pages

---

#### FR-104: Documentation Navigation

**Description**: Add documentation index/TOC linking all guides.

**Rationale**: Users need clear paths to find relevant documentation.

**Acceptance Criteria**:
- [ ] README links to all documentation files
- [ ] docs/INDEX.md or docs/README.md as hub
- [ ] Consistent navigation across docs

### Nice to Have (P2)

#### FR-201: Shell Completion via Homebrew

**Description**: Homebrew automatically enables shell completions without manual sourcing.

**Rationale**: Improved DX for Homebrew users.

**Acceptance Criteria**:
- [ ] Completions installed to Homebrew's completion directories
- [ ] Works automatically for bash/zsh with standard Homebrew setup
- [ ] Fish completions work with standard setup

---

#### FR-202: Homebrew Bottle (Pre-built Binary)

**Description**: Pre-build bottles for common macOS versions.

**Rationale**: Faster installation, no build dependencies needed.

**Acceptance Criteria**:
- [ ] Bottles for macOS Ventura (13), Sonoma (14), Sequoia (15)
- [ ] ARM64 (Apple Silicon) and x86_64 support
- [ ] CI builds and uploads bottles on release

---

#### FR-203: Interactive Config Wizard

**Description**: `git adr config wizard` command for guided configuration.

**Rationale**: Beginners may not know which options to set.

**Acceptance Criteria**:
- [ ] Prompts for common settings
- [ ] Explains each option
- [ ] Writes to git config

## Non-Functional Requirements

### Performance

- Formula installation should complete in < 60 seconds on standard broadband
- Documentation pages should render in < 3 seconds on GitHub

### Compatibility

- Homebrew formula must support macOS 12+ (Monterey and later)
- Documentation must render correctly in GitHub, man, and common terminals

### Maintainability

- Formula updates should be automated (no manual SHA editing)
- Documentation should be source-controlled alongside code
- DRY principle: Config defaults defined once (in code), documented via generation if possible

### Security

- Formula must download from HTTPS sources only
- SHA256 verification for downloaded archives
- No credential storage in formula

## Technical Constraints

### Homebrew Formula

- Must use Python virtualenv pattern (Homebrew requirement for Python tools)
- Must specify Python version dependency
- Must declare all PyPI dependencies in formula
- Source: PyPI sdist preferred (homebrew-core policy) or GitHub release tarball

### Documentation

- Markdown format for GitHub rendering
- Compatible with pandoc for man page generation
- No external hosting dependencies (self-contained in repo)

## Dependencies

### Internal Dependencies

| Dependency | Purpose |
|------------|---------|
| Existing release workflow | Triggers formula update |
| pyproject.toml | Source of version, dependencies |
| docs/man/*.md | Source for man page content |
| src/git_adr/core/templates.py | Source for format documentation |
| src/git_adr/core/config.py | Source for config documentation |

### External Dependencies

| Dependency | Purpose | Risk |
|------------|---------|------|
| PyPI | Package source for formula | Low (stable) |
| GitHub Actions | CI/CD | Low (stable) |
| Homebrew | Package manager | Low (stable) |
| homebrew-releaser action | Formula automation | Medium (third-party) |

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Formula rejected by brew audit | Low | Medium | Test locally with `brew audit --strict` |
| PyPI unavailable during install | Very Low | Low | Formula can fall back to GitHub tarball |
| homebrew-releaser action breaks | Low | Medium | Can update formula manually; fork action if needed |
| Documentation becomes stale | Medium | Medium | Generate docs from source where possible |
| Apple Silicon compatibility issues | Low | Medium | Test on ARM64 CI runners |

## Open Questions

- [ ] Should we generate config docs from source code to prevent staleness?
- [ ] Should ADR_FORMATS.md include community templates beyond built-in 6?
- [ ] Is there appetite for a `brew tap --cask` GUI application in the future?

## Appendix

### Glossary

| Term | Definition |
|------|------------|
| ADR | Architecture Decision Record - a document capturing a significant decision |
| MADR | Markdown Any Decision Records - popular ADR template format |
| Tap | A third-party Homebrew repository |
| Formula | A Homebrew package definition (Ruby file) |
| Bottle | Pre-built binary package for Homebrew |
| Caveats | Post-install messages displayed by Homebrew |

### References

- [Homebrew Formula Cookbook](https://docs.brew.sh/Formula-Cookbook)
- [Homebrew Python for Formula Authors](https://docs.brew.sh/Python-for-Formula-Authors)
- [Simon Willison: Packaging Python CLI for Homebrew](https://til.simonwillison.net/homebrew/packaging-python-cli-for-homebrew)
- [Michael Nygard: Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- [MADR Specification](https://adr.github.io/madr/)
- [git-lfs Homebrew Formula](https://github.com/Homebrew/homebrew-core/blob/master/Formula/g/git-lfs.rb)
