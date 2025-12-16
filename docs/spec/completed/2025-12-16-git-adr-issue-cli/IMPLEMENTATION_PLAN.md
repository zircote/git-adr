---
document_type: implementation_plan
project_id: SPEC-2025-12-16-001
version: 1.0.0
last_updated: 2025-12-16T00:00:00Z
status: draft
estimated_effort: ~4-6 hours
---

# Git ADR Issue CLI - Implementation Plan

## Overview

Implementation of `git adr issue` command in 4 phases:
1. **Foundation** - Core data models and template parsing
2. **Core Logic** - Issue building and gh CLI integration
3. **CLI Interface** - Typer command with interactive prompts
4. **Polish** - Documentation template, tests, and refinements

## Phase Summary

| Phase | Key Deliverables |
|-------|------------------|
| Phase 1: Foundation | IssueTemplate, FormElement, TemplateManager |
| Phase 2: Core Logic | Issue, IssueBuilder, GitHubIssueClient |
| Phase 3: CLI Interface | `git adr issue` command, interactive prompts |
| Phase 4: Polish | docs template, tests, integration, docs |

---

## Phase 1: Foundation

**Goal**: Establish data models and template parsing capabilities

**Prerequisites**: None (starting from existing codebase patterns)

### Task 1.1: Create issue template data models

- **Description**: Create `src/git_adr/core/issue_template.py` with dataclasses for `FormElement`, `TemplateSection`, and `IssueTemplate`
- **Dependencies**: None
- **Acceptance Criteria**:
  - [ ] `FormElement` dataclass with type, id, attributes, validations
  - [ ] `TemplateSection` dataclass with header, hint, required
  - [ ] `IssueTemplate` dataclass with all metadata fields
  - [ ] Properties for label, required, placeholder on FormElement
  - [ ] Property for promptable_fields on IssueTemplate

### Task 1.2: Implement markdown template parsing

- **Description**: Add `_parse_markdown_template()` method to parse `.md` templates with YAML frontmatter
- **Dependencies**: Task 1.1
- **Acceptance Criteria**:
  - [ ] Parse YAML frontmatter (name, about, title, labels, assignees)
  - [ ] Extract sections from markdown body (## headers)
  - [ ] Handle hint text from section content
  - [ ] Use python-frontmatter library (existing dependency)

### Task 1.3: Implement YAML form parsing

- **Description**: Add `_parse_yaml_form()` method to parse `.yml` issue form templates
- **Dependencies**: Task 1.1
- **Acceptance Criteria**:
  - [ ] Parse top-level keys (name, description, title, labels, assignees, body)
  - [ ] Convert body elements to FormElement instances
  - [ ] Handle all element types (markdown, input, textarea, dropdown, checkboxes)
  - [ ] Use pyyaml library (existing dependency)

### Task 1.4: Create bundled issue templates

- **Description**: Create `src/git_adr/templates/issues/` with default templates as static assets
- **Dependencies**: None
- **Acceptance Criteria**:
  - [ ] `bug_report.md` - default bug report template
  - [ ] `feature_request.md` - default feature request template
  - [ ] `documentation.md` - default documentation request template
  - [ ] Templates included as package data in pyproject.toml
  - [ ] Work offline/air-gapped without project templates

### Task 1.5: Implement TemplateManager

- **Description**: Create `TemplateManager` class to discover and manage templates (bundled + project)
- **Dependencies**: Tasks 1.2, 1.3, 1.4
- **Acceptance Criteria**:
  - [ ] `get_bundled_templates()` loads from package resources via importlib.resources
  - [ ] `get_project_templates()` finds templates in `.github/ISSUE_TEMPLATE/`
  - [ ] `discover_templates()` merges both (project overrides bundled)
  - [ ] `get_template(type_or_name)` resolves type aliases
  - [ ] `get_available_types()` returns list of available types
  - [ ] Type alias mapping: bug→bug_report, feat→feature_request, docs→documentation

### Phase 1 Deliverables

- [ ] `src/git_adr/templates/issues/` with bundled templates (bug, feat, docs)
- [ ] `src/git_adr/core/issue_template.py` with complete implementation
- [ ] Updated `pyproject.toml` with package data configuration
- [ ] Unit tests in `tests/test_issue_template.py`

### Phase 1 Exit Criteria

- [ ] All template parsing tests pass
- [ ] Can load bundled templates via importlib.resources
- [ ] Project templates override bundled when present

---

## Phase 2: Core Logic

**Goal**: Build issue construction and GitHub submission capabilities

**Prerequisites**: Phase 1 complete

### Task 2.1: Create Issue data model

- **Description**: Create `src/git_adr/core/issue.py` with `Issue` dataclass
- **Dependencies**: None (parallel with Phase 1)
- **Acceptance Criteria**:
  - [ ] `Issue` dataclass with title, body, labels, assignees
  - [ ] `to_markdown()` method for local file output
  - [ ] `from_template()` class method for creating from template + values

### Task 2.2: Implement IssueBuilder

- **Description**: Create `IssueBuilder` class for constructing issues from template and user input
- **Dependencies**: Task 2.1, Phase 1
- **Acceptance Criteria**:
  - [ ] `set_title()`, `set_field()` methods with fluent interface
  - [ ] `is_complete()` checks all required fields filled
  - [ ] `missing_required_fields()` returns list of missing required fields
  - [ ] `build()` returns completed Issue or raises validation error
  - [ ] `preview()` returns rendered markdown preview

### Task 2.3: Implement GitHubIssueClient

- **Description**: Create `src/git_adr/core/gh_client.py` for gh CLI integration
- **Dependencies**: None (parallel task)
- **Acceptance Criteria**:
  - [ ] `is_available()` classmethod checks gh installation
  - [ ] `is_authenticated()` classmethod checks auth status
  - [ ] `create_issue()` method submits via subprocess
  - [ ] `IssueCreateResult` dataclass for return type
  - [ ] Body passed via stdin (--body-file -)
  - [ ] Proper error handling for common failure modes

### Task 2.4: Implement local file storage

- **Description**: Add `save_local_issue()` function for draft storage
- **Dependencies**: Task 2.1
- **Acceptance Criteria**:
  - [ ] Generate timestamped filename from title
  - [ ] Write markdown with YAML frontmatter
  - [ ] Create draft directory if needed
  - [ ] Return path to saved file

### Phase 2 Deliverables

- [ ] `src/git_adr/core/issue.py` with Issue and IssueBuilder
- [ ] `src/git_adr/core/gh_client.py` with GitHubIssueClient
- [ ] Unit tests in `tests/test_issue.py` and `tests/test_gh_client.py`

### Phase 2 Exit Criteria

- [ ] Can build Issue from template and values
- [ ] Can submit issue via gh CLI (tested with mock)
- [ ] Can save issue locally as markdown

---

## Phase 3: CLI Interface

**Goal**: Implement the `git adr issue` command with full UX

**Prerequisites**: Phases 1 and 2 complete

### Task 3.1: Add CLI command skeleton

- **Description**: Add `@app.command("issue")` to `cli.py` and create `commands/issue.py`
- **Dependencies**: Phases 1, 2
- **Acceptance Criteria**:
  - [ ] Command registered in cli.py
  - [ ] All options defined with Typer annotations
  - [ ] Help text follows existing patterns
  - [ ] `run_issue()` function structure in place

### Task 3.2: Implement type resolution and template loading

- **Description**: Add logic to resolve --type to template and handle errors
- **Dependencies**: Task 3.1
- **Acceptance Criteria**:
  - [ ] Valid type loads corresponding template
  - [ ] Invalid type shows available types and exits
  - [ ] Missing template directory handled gracefully
  - [ ] Rich formatted error messages

### Task 3.3: Implement interactive prompting

- **Description**: Add interactive field prompts for template sections
- **Dependencies**: Task 3.2
- **Acceptance Criteria**:
  - [ ] Each section shows header and hint
  - [ ] Text input for simple fields
  - [ ] Multi-line input for textarea fields
  - [ ] Selection for dropdown fields
  - [ ] Checkbox selection for checkboxes fields
  - [ ] Skip fields provided via flags

### Task 3.4: Implement preview and confirmation flow

- **Description**: Add preview display and edit/submit/cancel options
- **Dependencies**: Task 3.3
- **Acceptance Criteria**:
  - [ ] Rendered markdown preview in Rich panel
  - [ ] Confirm prompt with options: Submit / Edit / Cancel
  - [ ] Edit opens $EDITOR with content
  - [ ] Resumes after editor closes
  - [ ] --no-edit flag skips preview

### Task 3.5: Implement submission flow

- **Description**: Add gh CLI submission or local save based on availability
- **Dependencies**: Task 3.4
- **Acceptance Criteria**:
  - [ ] Check gh availability before prompting
  - [ ] Submit to GitHub if available and authenticated
  - [ ] Save locally if --local-only or gh unavailable
  - [ ] Display issue URL on success
  - [ ] Display file path for local save
  - [ ] Proper exit codes for all scenarios

### Phase 3 Deliverables

- [ ] `src/git_adr/commands/issue.py` with complete implementation
- [ ] Updated `src/git_adr/cli.py` with command registration
- [ ] Integration tests in `tests/test_issue_integration.py`

### Phase 3 Exit Criteria

- [ ] `git adr issue --type bug` works interactively
- [ ] `git adr issue --type bug --title "Test" --dry-run` works non-interactively
- [ ] `git adr issue --type bug --local-only` creates local file
- [ ] Error handling works for all edge cases

---

## Phase 4: Polish

**Goal**: Comprehensive tests and final polish

**Prerequisites**: Phase 3 complete

### Task 4.1: Add comprehensive unit tests

- **Description**: Expand test coverage for all components
- **Dependencies**: Phase 3
- **Acceptance Criteria**:
  - [ ] Template parsing edge cases (malformed YAML, missing fields)
  - [ ] Issue builder validation
  - [ ] gh client error handling
  - [ ] Coverage target: 80%+

### Task 4.2: Add integration tests

- **Description**: End-to-end tests with temp git repos
- **Dependencies**: Task 4.1
- **Acceptance Criteria**:
  - [ ] Full interactive flow (mocked input)
  - [ ] Flag-based flow
  - [ ] Local-only flow
  - [ ] Dry-run flow
  - [ ] gh unavailable flow

### Task 4.3: Update documentation

- **Description**: Update README and add command help
- **Dependencies**: Phase 3
- **Acceptance Criteria**:
  - [ ] README.md section for `git adr issue`
  - [ ] Example usage in help text
  - [ ] Configuration options documented

### Task 4.4: Final review and cleanup

- **Description**: Code review, linting, type checking
- **Dependencies**: All previous tasks
- **Acceptance Criteria**:
  - [ ] `ruff check` passes
  - [ ] `mypy` passes
  - [ ] No TODO comments left
  - [ ] Consistent code style with rest of project

### Phase 4 Deliverables

- [ ] Complete test suite with 80%+ coverage
- [ ] Updated README.md
- [ ] All quality checks passing

### Phase 4 Exit Criteria

- [ ] All tests pass
- [ ] All linters pass
- [ ] Feature complete and documented

---

## Dependency Graph

```
Phase 1:
  Task 1.1 (models) ──┬──► Task 1.2 (md parse) ──┐
                      │                          ├──► Task 1.5 (manager)
                      └──► Task 1.3 (yml parse) ─┤
                                                 │
  Task 1.4 (bundled templates) ──────────────────┘

Phase 2:
  Task 2.1 (Issue) ────┬──► Task 2.2 (builder) ──┐
                       │                          │
  Task 2.3 (gh client) ─┴──► Task 2.4 (local) ───┴──► Phase 3

Phase 3:
  Task 3.1 (skeleton) ──► Task 3.2 (type) ──► Task 3.3 (prompts)
                                                  │
                                                  ▼
                         Task 3.4 (preview) ──► Task 3.5 (submit)

Phase 4:
  Task 4.1 (unit) ─────┐
                       ├──► Task 4.4 (review)
  Task 4.2 (integ) ────┤
                       │
  Task 4.3 (docs) ─────┘
```

## Risk Mitigation Tasks

| Risk | Mitigation Task | Phase |
|------|-----------------|-------|
| gh CLI not installed | Implement local fallback early | Phase 2 |
| Template format edge cases | Comprehensive parsing tests | Phase 1 |
| Shell escaping issues | Use stdin for body content | Phase 2 |

## Testing Checklist

- [ ] Unit tests for IssueTemplate parsing (.md)
- [ ] Unit tests for IssueTemplate parsing (.yml)
- [ ] Unit tests for TemplateManager type resolution
- [ ] Unit tests for IssueBuilder validation
- [ ] Unit tests for GitHubIssueClient (mocked subprocess)
- [ ] Integration tests for full command flow
- [ ] Integration tests for error scenarios
- [ ] Manual testing with real gh CLI

## Documentation Tasks

- [ ] Add `git adr issue` section to README.md
- [ ] Add help text to all CLI options
- [ ] Document configuration options in README
- [ ] Add examples to command docstring

## Launch Checklist

- [ ] All P0 requirements implemented
- [ ] All P1 requirements implemented (or documented as future)
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Code review completed
- [ ] Merged to main branch
