# Changelog

## [Unreleased]

### Implemented (2025-12-15)

#### Phase 1: Core Display Fix
- Added deciders, consulted, informed display to `git adr show` markdown output
- Stakeholder fields appear after status in the panel header

#### Phase 2: MADR 4.0 Compatibility
- Added `decision-makers` field alias in `ADRMetadata.from_dict()`
- `deciders` field takes precedence if both are present
- Added unit tests in test_core.py

#### Phase 3: CLI Enhancement
- Added `--deciders/-d` flag to `git adr new` command
- Supports comma-separated values and repeated flags
- Interactive prompt when deciders not provided (TTY only)
- Deciders are now REQUIRED - error if empty after all sources checked
- Updated 10+ test files to provide deciders

#### Phase 4: Interactive Backfill
- Added `_prompt_for_deciders()` function in show.py
- Added `--no-interactive` flag to suppress prompts
- Prompts user when viewing ADR with empty deciders
- Saves updated deciders via `NotesManager.update()`

### Scope Decisions
- Deciders will be REQUIRED for new ADRs (not auto-populated from git)
- Interactive prompt will appear when viewing ADRs with empty deciders
- MADR 4.0 `decision-makers` field will be supported as alias
- Format: "Name <email>" style for deciders display

### Status
- Implementation complete
- All 1489 tests passing
- Ready for final documentation and issue closure

## [COMPLETED] - 2025-12-15

### Project Closed
- Final status: **Success**
- Actual effort: ~5 hours (within 4-6 hour estimate)
- Moved to: docs/spec/completed/2025-12-15-decider-display-remediation

### Retrospective Summary
- **What went well**: Comprehensive planning, test coverage (95.03%), MADR 4.0 compatibility, documentation
- **What to improve**: Anticipate breaking change scope upfront, add coverage tests before CI
- **Key learning**: Making deciders required (vs optional with fallback) was the right architectural decision for accountability
