---
document_type: decisions
project_id: SPEC-2025-12-15-001
---

# git-adr CLI - Architecture Decision Records

## ADR-001: Use subprocess to git binary for git operations

**Date**: 2025-12-15
**Status**: Accepted
**Deciders**: User, Claude (Planning)

### Context

git-adr needs to perform git operations including notes management. Options include:
1. `subprocess` to git binary (shell out)
2. `pygit2` (libgit2 bindings)
3. `GitPython` (Python git wrapper)

### Decision

Use subprocess to the git binary for all git operations.

### Consequences

**Positive:**
- Industry standard approach (5 of 6 major git extensions use this)
- Zero additional dependencies
- Full feature parity with git CLI including all notes operations
- Inherits user's git configuration and credentials automatically
- No GPL license concerns (pygit2/libgit2 is GPLv2)
- Simple, well-understood model

**Negative:**
- Process spawning overhead (negligible for our use case)
- Must parse text output
- Requires git to be installed

**Neutral:**
- Same approach used by git-lfs, git-flow, git-crypt, GitHub CLI

### Alternatives Considered

1. **pygit2**: High performance but adds libgit2 dependency, installation complexity, GPLv2 license, overkill for ADR operations
2. **GitPython**: Still shells out internally (no performance benefit), Windows reliability issues, recent security vulnerabilities

---

## ADR-002: Attach ADRs to root tree object, not specific commits

**Date**: 2025-12-15
**Status**: Accepted
**Deciders**: User, Claude (Planning)

### Context

Git notes can be attached to any git object. ADRs need a stable attachment point that survives rebase and amendment operations.

### Decision

Attach ADRs to the repository root tree object, with related commit SHAs stored in ADR metadata.

### Consequences

**Positive:**
- ADRs survive rebase/amend operations
- ADRs exist independently of specific commits
- Supports ADRs that precede or span multiple commits
- Bidirectional tracking via metadata

**Negative:**
- Requires index to map ADR IDs to notes
- Slightly more complex lookup

**Neutral:**
- Related commits tracked in `linked-commits` metadata field

---

## ADR-003: Use typer for CLI framework

**Date**: 2025-12-15
**Status**: Accepted
**Deciders**: User

### Context

The existing skeleton uses click. The product brief suggested typer.

### Decision

Migrate from click to typer.

### Consequences

**Positive:**
- Type hints provide better IDE support
- Automatic shell completion generation
- Built-in rich integration for formatting
- Less boilerplate than click
- Built on click (same underlying engine)

**Negative:**
- Migration effort from existing click code
- Additional dependency (though click is a transitive dep)

---

## ADR-004: Support Python 3.11+

**Date**: 2025-12-15
**Status**: Accepted
**Deciders**: User

### Context

The existing pyproject.toml required Python 3.12+. Broader compatibility was requested.

### Decision

Lower minimum Python version to 3.11+.

### Consequences

**Positive:**
- Broader user base (3.11 still widely used)
- Longer support window

**Negative:**
- Cannot use 3.12+ only features (few relevant ones)
- Must include tomllib fallback for 3.10 (not needed for 3.11+)

---

## ADR-005: AI provider priority order

**Date**: 2025-12-15
**Status**: Accepted
**Deciders**: User

### Context

Multiple AI providers are supported. Need to prioritize implementation and testing.

### Decision

Priority order: OpenAI → Anthropic → Other providers → Ollama

### Consequences

**Positive:**
- OpenAI has largest user base, gets most attention
- Anthropic as strong secondary option
- Ollama last (local use, no API key needed)

**Neutral:**
- All providers supported via langchain abstraction

---

## ADR-006: Use YAML frontmatter + Markdown for ADR storage format

**Date**: 2025-12-15
**Status**: Accepted
**Deciders**: Planning (based on product brief)

### Context

ADRs stored in git notes need a format that is:
- Human-readable in `git log`
- Machine-parseable for indexing
- Merge-friendly for concurrent changes

### Decision

Use YAML frontmatter followed by Markdown body.

### Consequences

**Positive:**
- Human-readable in terminal
- Structured metadata for programmatic access
- Compatible with `union` merge strategy
- Standard format (matches file-based ADR tools)

**Negative:**
- YAML parsing adds dependency

---

## ADR-007: Separate namespace for binary artifacts

**Date**: 2025-12-15
**Status**: Accepted
**Deciders**: Planning (based on product brief)

### Context

ADRs may include diagrams and images. These shouldn't bloat the main notes namespace.

### Decision

Store artifacts in `refs/notes/adr-artifacts` with content-addressed references in ADR metadata.

### Consequences

**Positive:**
- Main ADR notes stay small and text-based
- Content deduplication via SHA256 addressing
- Size limits enforceable separately

**Negative:**
- Additional namespace to sync
- More complex artifact retrieval

---

## ADR-008: Editor integration with multiple input modes

**Date**: 2025-12-15
**Status**: Accepted
**Deciders**: User

### Context

Users need flexibility in how they provide ADR content:
- Interactive editing (terminal or GUI editors)
- Scripted/automated creation
- Pre-written content from files

### Decision

Support multiple input modes for `git adr new`:

1. **Editor mode** (default): Opens configured editor
   - Fallback chain: `$EDITOR` → `$VISUAL` → `vim` → `nano` → `vi`
   - Auto-detects GUI editors and adds `--wait` flag (VS Code, Sublime, Atom)

2. **File input**: `git adr new "Title" --file path/to/content.md`

3. **Stdin input**: `cat file.md | git adr new "Title"`

4. **Preview mode**: `git adr new "Title" --preview` (shows template without creating)

### Consequences

**Positive:**
- Works with any editor (terminal or GUI)
- Enables scripting and automation
- No editor lock-in
- Template preview helps users understand formats

**Negative:**
- More complex input handling logic
- Must detect stdin vs interactive mode

---

## ADR-009: AI draft uses interactive elicitation by default

**Date**: 2025-12-15
**Status**: Accepted
**Deciders**: User

### Context

`git adr draft` needs to help users create ADRs with AI assistance. Two modes are possible:
1. **Batch**: AI generates from commits/context in one shot
2. **Interactive**: AI guides user through Socratic questioning

### Decision

When AI is enabled, `git adr draft` defaults to **interactive elicitation mode**.

The AI asks sequential questions:
1. "What problem are you solving?"
2. "What options have you considered?"
3. "What's driving this decision?"
4. "What are the trade-offs/consequences?"

Then synthesizes answers into a complete ADR.

`--batch` flag available for scripted/automated usage.

### Consequences

**Positive:**
- AI acts as collaborative partner, not just generator
- Ensures users think through all decision aspects
- Higher quality ADRs through guided reflection
- Natural for users unfamiliar with ADR structure

**Negative:**
- More complex implementation (conversation state)
- Slower than one-shot generation
- Requires terminal interactivity (not pure stdin/stdout)

---

## ADR-010: Auto-configure notes sync in `git adr init`

**Date**: 2025-12-15
**Status**: Accepted
**Deciders**: Planning (risk mitigation)

### Context

Git notes are NOT pushed or fetched by default. Users will lose ADRs if they don't configure remotes.

### Decision

`git adr init` automatically configures:
- `remote.origin.fetch` to include notes refs
- `remote.origin.push` to include notes refs
- `notes.rewriteRef` for rebase safety
- `notes.rewrite.rebase` and `notes.rewrite.amend`

### Consequences

**Positive:**
- Users don't lose ADRs due to misconfiguration
- Notes automatically sync with regular push/pull

**Negative:**
- Modifies user's git config (expected behavior for init)
- May conflict with existing notes configuration (handle gracefully)

---

## ADR-011: Add `git adr rm` command (Late Addition)

**Date**: 2025-12-15
**Status**: Accepted
**Deciders**: User
**Type**: Scope Creep

### Context

During implementation, the user needed to remove an ADR from git notes. The original specification (REQUIREMENTS.md) did not include a `rm` command - only artifact removal (`artifact-rm`) was planned.

### Decision

Add `git adr rm <id> [--force]` command to remove ADRs from git notes.

### Implementation

- Interactive confirmation by default showing ADR title, status, and warnings
- `--force` flag to skip confirmation (for scripting)
- Warnings displayed for:
  - ADRs with linked commits (traceability will be lost)
  - ADRs that supersede others (chain will be broken)
  - ADRs superseded by others (reference becomes stale)

### Consequences

**Positive:**
- Users can remove ADRs without direct git notes manipulation
- Consistent UX with other ADR management commands
- Safe defaults (confirmation required)

**Negative:**
- Scope increase (~5 hours of work including tests and docs)
- Not recoverable without git reflog knowledge

### Classification

This is **acceptable scope creep** because:
1. Aligns with tool's philosophy (manage ADRs without raw git notes)
2. User-requested based on real need
3. Similar pattern to existing `artifact-rm` command

---

## ADR-012: git-lfs Style Distribution (Late Addition)

**Date**: 2025-12-15
**Status**: Accepted
**Deciders**: User
**Type**: Scope Creep

### Context

Original spec assumed PyPI-only distribution. User requested distribution patterns following git-lfs conventions for git extensions.

### Decision

Implement git-lfs style distribution with:
- Makefile for build/install/release targets
- install.sh script for tarball installation
- release.yml GitHub Actions workflow for automated releases

### Implementation

- `Makefile` with targets: build, install, install-bin, install-man, install-completions, release
- `script/install.sh` following git-lfs pattern with uv/pip fallback
- `.github/workflows/release.yml` creating tarballs with man pages + completions

### Consequences

**Positive:**
- Familiar pattern for git extension users
- Single tarball contains all artifacts
- Works without PyPI access

**Negative:**
- Significant scope increase (~10 hours of work)
- More complex release process

### Classification

This is **acceptable scope creep** because:
1. Follows established git extension conventions
2. Improves distribution flexibility
3. User explicitly requested

---

## ADR-013: Coverage Target 95% (Late Addition)

**Date**: 2025-12-15
**Status**: Accepted
**Deciders**: PR Requirements
**Type**: Scope Creep

### Context

Original REQUIREMENTS.md specified 90% test coverage. The PR CI configuration required 95%.

### Decision

Raise coverage target from 90% to 95% and add tests to meet it.

### Implementation

- Added `tests/test_completion.py` (12 tests) for shell completion code
- Added `tests/test_rm_command.py` (14 tests) for new rm command
- Final coverage: 95.19%

### Consequences

**Positive:**
- Higher code quality assurance
- Better coverage of edge cases
- Shell completion code now tested

**Negative:**
- Additional test development time
- Coverage requirement more strict than planned

### Classification

This is **acceptable scope creep** because:
1. Higher quality is always beneficial
2. CI already enforced this requirement
3. Tests caught real issues during development
