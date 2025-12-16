---
document_type: requirements
project_id: SPEC-2025-12-16-001
version: 1.0.0
last_updated: 2025-12-16T00:00:00Z
status: draft
---

# Git ADR Issue CLI - Product Requirements Document

## Executive Summary

Add a `git adr issue` command to create GitHub issues from the command line using project-defined issue templates. The command provides a hybrid UX where users can supply values via flags for speed, or be prompted interactively for any missing fields. Issues can be saved locally as markdown files or submitted directly to GitHub when the `gh` CLI is available and authenticated.

## Problem Statement

### The Problem

Creating GitHub issues currently requires:
1. Navigating to the web interface
2. Selecting a template
3. Filling out form fields
4. Submitting

This interrupts developer workflow, especially when already working in the terminal on ADR-related tasks.

### Impact

- **Developers** lose context switching between terminal and browser
- **Issue quality** suffers when templates aren't easily accessible
- **Consistency** decreases when developers skip templates due to friction

### Current State

Users must leave the CLI workflow, open GitHub in a browser, and manually create issues. There is no way to create structured issues from the command line using project templates.

## Goals and Success Criteria

### Primary Goal

Enable developers to create well-structured GitHub issues without leaving the terminal.

### Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Issue creation time | <60 seconds | Manual timing tests |
| Template compliance | 100% | Issues match template structure |
| CLI consistency | High | Code review against existing patterns |

### Non-Goals (Explicit Exclusions)

- Editing existing issues
- Commenting on issues
- Issue listing/search
- PR creation
- Supporting non-GitHub issue trackers
- Supporting GitHub Enterprise (initial release)

## User Analysis

### Primary Users

- **git-adr CLI users**: Developers already using git-adr for architecture decisions
- **Context**: Working in terminal, want to report bugs or request features without context switching

### User Stories

1. As a developer using git-adr, I want to report a bug from the CLI so I don't have to switch to the browser
2. As a developer, I want to request a new feature using the project's template so my request includes all required information
3. As a maintainer, I want issue submitters to use templates so I receive consistent, actionable issues
4. As a developer without gh installed, I want to draft an issue locally so I can submit it later

## Functional Requirements

### Must Have (P0)

| ID | Requirement | Rationale | Acceptance Criteria |
|----|-------------|-----------|---------------------|
| FR-001 | Bundle default templates as static assets | Works offline/air-gapped without project setup | `bug_report.md`, `feature_request.md`, `documentation.md` in package resources |
| FR-002 | Parse markdown templates (`.md`) | Core functionality - read template structure | Templates with YAML frontmatter correctly parsed |
| FR-003 | Parse YAML form templates (`.yml`) | Support modern GitHub form templates | All form element types correctly handled |
| FR-004 | Template resolution: project overrides bundled | Allow customization while maintaining defaults | Project's `.github/ISSUE_TEMPLATE/` overrides bundled when present |
| FR-005 | Auto-discover available templates | Users shouldn't need to know exact filenames | `--type` shows available options if invalid type given |
| FR-006 | Map `--type` aliases to templates | UX convenience | `bug` maps to `bug_report.md`, `feat` to `feature_request.md`, `docs` to `documentation.md` |
| FR-007 | Interactive prompts for template sections | Guide users through template fields | Each section header displayed with hint text |
| FR-008 | Flag-based input for all fields | Power user efficiency | `--title`, `--description`, etc. skip prompts for those fields |
| FR-009 | Preview before submission | Catch errors before creating | Rendered markdown shown with confirm/edit/cancel options |
| FR-010 | Local file output | Works without gh CLI | Creates `.github/issues/YYYY-MM-DD-title.md` (or configurable path) |
| FR-011 | GitHub submission via gh CLI | Primary workflow | Issue created, URL returned |
| FR-012 | Detect gh installation and auth | Graceful degradation | Clear message if gh missing or not authenticated |

### Should Have (P1)

| ID | Requirement | Rationale | Acceptance Criteria |
|----|-------------|-----------|---------------------|
| FR-101 | Edit in $EDITOR before submit | Power user control | Opens editor with rendered content, resumes after save |
| FR-102 | Label auto-population from template | Use template metadata | Labels from frontmatter auto-applied |
| FR-103 | Assignee support | Template metadata | `--assignee` flag and template `assignees` field |

### Nice to Have (P2)

| ID | Requirement | Rationale | Acceptance Criteria |
|----|-------------|-----------|---------------------|
| FR-201 | `--dry-run` flag | Testing/scripting | Shows what would be created without actually creating |
| FR-202 | Issue draft saving | Resume interrupted work | Saves partial input, offers to resume |
| FR-203 | Template caching | Performance | Templates cached, refreshed on git pull |
| FR-204 | Custom template directory | Flexibility | `adr.issue.template_dir` config option |

## Non-Functional Requirements

### Performance

- Template parsing: <100ms
- Interactive prompt display: <50ms latency
- GitHub submission: <5s (network dependent)

### Security

- No credential storage (delegates to gh CLI)
- No execution of arbitrary code from templates
- Input sanitization for shell command construction

### Maintainability

- Follow existing git-adr CLI patterns (Typer, Rich, command structure)
- Unit tests for template parsing
- Integration tests for gh CLI interaction

### Reliability

- Graceful handling of missing gh CLI
- Clear error messages for common failures
- No data loss on submission failure (local draft preserved)

## Technical Constraints

- Python 3.11+ (match existing git-adr requirements)
- Use existing dependencies where possible (python-frontmatter, pyyaml, rich)
- Must work on macOS, Linux (Windows support: best effort)
- gh CLI integration is optional (not a hard dependency)

## Dependencies

### Internal Dependencies

- git-adr core: Git class, ConfigManager, console utilities
- Existing patterns: Typer app structure, Rich formatting, error handling

### External Dependencies

- python-frontmatter (existing): Parse markdown template frontmatter
- pyyaml (existing): Parse YAML form templates
- rich (existing): Terminal UI, prompts, tables
- gh CLI (optional, external): GitHub API access

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| gh CLI not installed | High | Med | Local file fallback with helpful message |
| gh CLI not authenticated | Med | Med | Clear error message, auth instructions |
| Template format changes by GitHub | Low | Med | Version-pinned parsing, graceful degradation |
| Template parsing edge cases | Med | Low | Comprehensive test suite, fallback to basic fields |
| Large template bodies exceed shell limits | Low | Low | Use --body-file - (stdin) pattern |

## Open Questions

- [x] Should docs template be created? → **Yes, as part of implementation**
- [x] UX for multi-select fields in YAML forms? → **Follow checkbox pattern, prompt for each option**

## Appendix

### Glossary

| Term | Definition |
|------|------------|
| YAML frontmatter | Metadata block at start of markdown file, delimited by `---` |
| YAML issue forms | GitHub's newer template format using `.yml` files with structured fields |
| gh CLI | GitHub's official command-line tool |

### Command Examples

```bash
# Interactive bug report
git adr issue --type bug

# Feature request with flags
git adr issue --type feat --title "Add dark mode" --description "Support dark color scheme"

# Documentation request
git adr issue --type docs

# Auto-discover available types
git adr issue --type invalid
# Error: Unknown type 'invalid'. Available: bug, feat, docs

# Dry run (preview only)
git adr issue --type bug --dry-run

# Save locally without submitting
git adr issue --type bug --local-only

# Specify repo explicitly
git adr issue --type bug --repo zircote/git-adr
```

### Template Type Aliases

| Alias | Maps To | Notes |
|-------|---------|-------|
| `bug` | `bug_report.md` | Standard bug report |
| `feat` | `feature_request.md` | Feature/enhancement request |
| `feature` | `feature_request.md` | Alternative alias |
| `docs` | `documentation.md` | Documentation issue |
| `doc` | `documentation.md` | Alternative alias |

Additional templates discovered in `.github/ISSUE_TEMPLATE/` are available by filename (without extension).

### References

- [GitHub Issue Templates Documentation](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository)
- [GitHub Issue Forms Schema](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms)
- [gh CLI Manual - issue create](https://cli.github.com/manual/gh_issue_create)
