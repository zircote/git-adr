---
document_type: implementation_plan
project_id: SPEC-2025-12-15-001
version: 1.0.0
last_updated: 2025-12-15T20:00:00Z
status: draft
estimated_effort: 4-6 hours
---

# Decider Display Remediation - Implementation Plan

## Overview

This plan implements stakeholder metadata display, MADR 4.0 compatibility, required deciders validation, and interactive prompts. The implementation follows a phased approach to minimize risk and enable incremental testing.

## Phase Summary

| Phase | Name | Tasks | Description |
|-------|------|-------|-------------|
| Phase 1 | Core Display Fix | 3 | Add stakeholder fields to show command output |
| Phase 2 | MADR 4.0 Compatibility | 2 | Support decision-makers alias in parsing |
| Phase 3 | CLI Enhancement | 3 | Add --deciders flag and prompts to new command |
| Phase 4 | Interactive Backfill | 2 | Add prompts for empty deciders on show |
| Phase 5 | Testing & Polish | 3 | Comprehensive tests and documentation |

---

## Phase 1: Core Display Fix

**Goal**: Display deciders, consulted, and informed in the show command's markdown panel

**Prerequisites**: None (can start immediately)

### Task 1.1: Add Stakeholder Display to _output_markdown()

- **Description**: Modify `_output_markdown()` in `show.py` to display deciders, consulted, and informed fields
- **File**: `src/git_adr/commands/show.py`
- **Acceptance Criteria**:
  - [ ] Deciders displayed after status line when non-empty
  - [ ] Consulted displayed after deciders when non-empty
  - [ ] Informed displayed after consulted when non-empty
  - [ ] Empty fields are hidden (not displayed)
  - [ ] Format matches existing style (e.g., "Deciders: name1, name2")

**Implementation Notes**:
```python
# Insert after line 98 (status display)
if adr.metadata.deciders:
    header_content.append(f"Deciders: {', '.join(adr.metadata.deciders)}")
if adr.metadata.consulted:
    header_content.append(f"Consulted: {', '.join(adr.metadata.consulted)}")
if adr.metadata.informed:
    header_content.append(f"Informed: {', '.join(adr.metadata.informed)}")
```

### Task 1.2: Verify YAML/JSON Output Unchanged

- **Description**: Ensure YAML and JSON output formats are unaffected (they already include these fields)
- **File**: `src/git_adr/commands/show.py`
- **Acceptance Criteria**:
  - [ ] `git adr show <id> --format yaml` shows deciders, consulted, informed
  - [ ] `git adr show <id> --format json` shows deciders, consulted, informed
  - [ ] No regression in existing output

### Task 1.3: Manual Testing of Display

- **Description**: Test display with various ADR configurations
- **Acceptance Criteria**:
  - [ ] ADR with all stakeholder fields displays correctly
  - [ ] ADR with partial fields (only deciders) displays correctly
  - [ ] ADR with no stakeholder fields displays correctly (no empty lines)

### Phase 1 Deliverables

- [ ] Modified `show.py` with stakeholder display
- [ ] Manual test verification

### Phase 1 Exit Criteria

- [ ] `git adr show` displays stakeholder fields when present
- [ ] Empty fields are hidden
- [ ] No regression in YAML/JSON output

---

## Phase 2: MADR 4.0 Compatibility

**Goal**: Accept `decision-makers` as alias for `deciders` in frontmatter

**Prerequisites**: Phase 1 complete

### Task 2.1: Update ADRMetadata.from_dict()

- **Description**: Modify `from_dict()` to accept both `deciders` and `decision-makers` fields
- **File**: `src/git_adr/core/adr.py`
- **Acceptance Criteria**:
  - [ ] `deciders:` field parsed correctly (existing behavior)
  - [ ] `decision-makers:` field parsed as deciders (MADR 4.0)
  - [ ] `deciders` takes precedence if both present
  - [ ] Warning logged if both fields present with different values

**Implementation Notes**:
```python
# In from_dict(), replace line 157:
deciders = ensure_list(
    data.get("deciders") or data.get("decision-makers") or []
)
```

### Task 2.2: Add MADR 4.0 Parsing Tests

- **Description**: Write tests for MADR 4.0 field parsing
- **File**: `tests/test_adr_madr4.py` (new file)
- **Acceptance Criteria**:
  - [ ] Test parsing `decision-makers` field
  - [ ] Test parsing `deciders` field (existing)
  - [ ] Test precedence when both fields present
  - [ ] Test empty field handling

### Phase 2 Deliverables

- [ ] Modified `adr.py` with MADR 4.0 alias
- [ ] New test file `test_adr_madr4.py`

### Phase 2 Exit Criteria

- [ ] MADR 4.0 templates with `decision-makers` are parsed correctly
- [ ] Tests pass

---

## Phase 3: CLI Enhancement

**Goal**: Add --deciders flag and interactive prompt to `git adr new`

**Prerequisites**: Phase 2 complete

### Task 3.1: Add --deciders Flag to new Command

- **Description**: Add CLI option for specifying deciders
- **Files**: `src/git_adr/commands/new.py`, `src/git_adr/cli.py`
- **Acceptance Criteria**:
  - [ ] `--deciders` / `-d` option available
  - [ ] Multiple values supported (`-d "Alice" -d "Bob"`)
  - [ ] Comma-separated single value supported (`-d "Alice, Bob"`)
  - [ ] CLI value merged with frontmatter (CLI takes precedence)

**Implementation Notes**:
```python
# In cli.py new command definition
deciders: Annotated[
    Optional[list[str]],
    typer.Option("--deciders", "-d", help="Decision makers")
] = None,
```

### Task 3.2: Add Pre-Editor Prompt for Deciders

- **Description**: Prompt for deciders before opening editor if not provided via CLI
- **File**: `src/git_adr/commands/new.py`
- **Acceptance Criteria**:
  - [ ] Prompt appears if `--deciders` not provided
  - [ ] Prompt skipped if stdin is not TTY (piped input)
  - [ ] Empty input allowed (user can press Enter to skip)
  - [ ] Comma-separated values parsed correctly

**Implementation Notes**:
```python
# Before opening editor
if deciders is None and sys.stdin.isatty():
    deciders_input = typer.prompt(
        "Enter deciders (comma-separated, or Enter to skip)",
        default=""
    )
    if deciders_input:
        deciders = [d.strip() for d in deciders_input.split(",") if d.strip()]
```

### Task 3.3: Add Validation for Required Deciders

- **Description**: Validate that deciders is non-empty before saving
- **File**: `src/git_adr/commands/new.py`
- **Acceptance Criteria**:
  - [ ] Error if deciders empty after all inputs (CLI, prompt, frontmatter)
  - [ ] Clear error message: "Deciders are required"
  - [ ] User can bypass with `--no-validate` flag (future, not this phase)

**Implementation Notes**:
```python
# Before creating ADR
merged_deciders = deciders or fm_deciders
if not merged_deciders:
    err_console.print("[red]Error:[/red] Deciders are required")
    raise typer.Exit(1)
```

### Phase 3 Deliverables

- [ ] Modified `new.py` with --deciders and prompt
- [ ] Modified `cli.py` with CLI option
- [ ] Validation logic implemented

### Phase 3 Exit Criteria

- [ ] `git adr new "Title" --deciders "Alice"` works
- [ ] Interactive prompt appears when --deciders omitted
- [ ] Empty deciders rejected with clear error

---

## Phase 4: Interactive Backfill

**Goal**: Prompt to add deciders when viewing an ADR with empty deciders field

**Prerequisites**: Phase 3 complete

### Task 4.1: Add Interactive Prompt to show Command

- **Description**: When showing an ADR with empty deciders, prompt user to add them
- **File**: `src/git_adr/commands/show.py`
- **Acceptance Criteria**:
  - [ ] Prompt appears: "This ADR has no deciders. Would you like to add them now? [y/N]"
  - [ ] If yes: prompt for deciders, update ADR, save
  - [ ] If no: continue with normal display
  - [ ] Prompt skipped if stdin not TTY
  - [ ] `--no-interactive` flag to suppress prompt

**Implementation Notes**:
```python
# Before displaying, check for empty deciders
if not adr.metadata.deciders and sys.stdin.isatty():
    if typer.confirm("This ADR has no deciders. Add them now?", default=False):
        deciders_input = typer.prompt("Enter deciders (comma-separated)")
        if deciders_input:
            adr.metadata.deciders = [d.strip() for d in deciders_input.split(",")]
            notes_manager.update(adr)
            console.print("[green]✓[/green] Deciders updated")
```

### Task 4.2: Add --no-interactive Flag

- **Description**: Allow suppressing interactive prompts for CI/scripting
- **Files**: `src/git_adr/commands/show.py`, `src/git_adr/cli.py`
- **Acceptance Criteria**:
  - [ ] `--no-interactive` / `-n` flag available on show command
  - [ ] Flag suppresses the deciders prompt
  - [ ] Flag also suppresses any future interactive prompts

### Phase 4 Deliverables

- [ ] Modified `show.py` with interactive prompt
- [ ] Modified `cli.py` with --no-interactive flag

### Phase 4 Exit Criteria

- [ ] Viewing ADR without deciders triggers prompt
- [ ] User can add deciders interactively
- [ ] `--no-interactive` suppresses prompt

---

## Phase 5: Testing & Polish

**Goal**: Comprehensive test coverage and documentation

**Prerequisites**: Phase 4 complete

### Task 5.1: Write Unit Tests for Display

- **Description**: Test stakeholder display in show command
- **File**: `tests/test_show_stakeholders.py` (new file)
- **Acceptance Criteria**:
  - [ ] Test display with all stakeholder fields
  - [ ] Test display with partial fields
  - [ ] Test display with no fields
  - [ ] Test interactive prompt (mocked)
  - [ ] Test --no-interactive flag

### Task 5.2: Write Unit Tests for new Command

- **Description**: Test --deciders flag and prompt in new command
- **File**: `tests/test_new_deciders.py` (new file)
- **Acceptance Criteria**:
  - [ ] Test --deciders flag single value
  - [ ] Test --deciders flag multiple values
  - [ ] Test interactive prompt (mocked)
  - [ ] Test validation error for empty deciders
  - [ ] Test frontmatter override behavior

### Task 5.3: Update Documentation and Close Issue

- **Description**: Update README and close GitHub issue
- **Acceptance Criteria**:
  - [ ] README updated with new --deciders option
  - [ ] CHANGELOG updated with changes
  - [ ] GitHub Issue #15 closed with PR reference
  - [ ] Migration note for existing ADRs

### Phase 5 Deliverables

- [ ] New test file `test_show_stakeholders.py`
- [ ] New test file `test_new_deciders.py`
- [ ] Updated README.md
- [ ] Updated CHANGELOG.md

### Phase 5 Exit Criteria

- [ ] All new tests pass
- [ ] Coverage maintained at 95%+
- [ ] Documentation complete
- [ ] Issue #15 closed

---

## Dependency Graph

```
Phase 1: Core Display Fix
   Task 1.1 ──────────────────────────────────────┐
   Task 1.2 (parallel) ──────────────────────────────> Phase 1 Complete
   Task 1.3 ──────────────────────────────────────┘
                                                       │
                                                       v
Phase 2: MADR 4.0 Compatibility
   Task 2.1 ──────────────────────────────────────┐
   Task 2.2 (depends on 2.1) ────────────────────────> Phase 2 Complete
                                                       │
                                                       v
Phase 3: CLI Enhancement
   Task 3.1 ──────────────────────────────────────┐
   Task 3.2 (depends on 3.1) ─────────────────────────> Phase 3 Complete
   Task 3.3 (depends on 3.2) ─────────────────────┘
                                                       │
                                                       v
Phase 4: Interactive Backfill
   Task 4.1 ──────────────────────────────────────┐
   Task 4.2 (parallel) ──────────────────────────────> Phase 4 Complete
                                                       │
                                                       v
Phase 5: Testing & Polish
   Task 5.1 ──────────────────────────────────────┐
   Task 5.2 (parallel) ──────────────────────────────> Phase 5 Complete
   Task 5.3 (depends on 5.1, 5.2) ─────────────────┘
```

## Risk Mitigation Tasks

| Risk | Mitigation Task | Phase |
|------|-----------------|-------|
| Breaking change for users | Add --no-interactive flag | Phase 4 |
| MADR 4.0 field conflict | Log warning if both fields present | Phase 2 |
| Test coverage drop | Dedicated test tasks | Phase 5 |

## Testing Checklist

- [ ] Unit tests for show.py stakeholder display
- [ ] Unit tests for adr.py MADR 4.0 parsing
- [ ] Unit tests for new.py --deciders flag
- [ ] Unit tests for interactive prompts (mocked input)
- [ ] Integration test: create ADR with deciders, show it
- [ ] Manual test: interactive prompt flow

## Documentation Tasks

- [ ] Update README.md with --deciders option
- [ ] Update CHANGELOG.md with version entry
- [ ] Add example in README for stakeholder usage

## Launch Checklist

- [ ] All tests passing
- [ ] Coverage at 95%+
- [ ] Documentation complete
- [ ] PR created and reviewed
- [ ] GitHub Issue #15 referenced in PR
- [ ] Merged to main

## Post-Launch

- [ ] Close GitHub Issue #15
- [ ] Backfill existing ADRs in git-adr repo with "Robert Allen <zircote@gmail.com>"
- [ ] Monitor for user feedback
