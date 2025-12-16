---
document_type: decisions
project_id: SPEC-2025-12-16-001
---

# Git ADR Issue CLI - Architecture Decision Records

## ADR-001: Use Typer for CLI Framework

**Date**: 2025-12-16
**Status**: Accepted
**Deciders**: User, Claude

### Context

The git-adr project needs a CLI framework for the new `issue` command. The project already uses Typer for all existing commands.

### Decision

Use Typer (the existing CLI framework) for the `issue` command, following established patterns in `cli.py` and `commands/*.py`.

### Consequences

**Positive:**
- Consistent with existing codebase
- No new dependencies
- Developers familiar with patterns can contribute easily
- Rich integration already configured

**Negative:**
- None identified

**Neutral:**
- Must follow existing Annotated type hint patterns

### Alternatives Considered

1. **Click (directly)**: Typer is built on Click, but using Click directly would break consistency
2. **argparse**: Standard library but less ergonomic and inconsistent with project

---

## ADR-002: Hybrid Input Model (Flags + Interactive Prompts)

**Date**: 2025-12-16
**Status**: Accepted
**Deciders**: User

### Context

Users need a way to provide input when creating issues. Options include:
- Fully interactive (prompt for everything)
- Fully flag-based (require all values via CLI flags)
- Hybrid (flags for optional override, prompts for missing)

### Decision

Implement a hybrid model where:
- Any field can be provided via flag (e.g., `--title`, `--description`)
- Missing fields are prompted interactively
- Power users can skip all prompts with flags
- Casual users get guided experience

### Consequences

**Positive:**
- Flexible for both scripting and interactive use
- No learning curve for either user type
- Can pipe in values or use interactively

**Negative:**
- More complex implementation than single mode
- Must handle partial input state

**Neutral:**
- Testing requires covering both modes

### Alternatives Considered

1. **Interactive only**: Would frustrate power users and break scripting
2. **Flags only**: Would require memorizing all options, lose template guidance

---

## ADR-003: Optional gh CLI Dependency with Local Fallback

**Date**: 2025-12-16
**Status**: Accepted
**Deciders**: User

### Context

The command needs to submit issues to GitHub. Options:
- Require gh CLI (hard dependency)
- Use GitHub REST API directly with token
- Make submission optional, support local files

### Decision

Make gh CLI optional with local file fallback:
- If gh is installed and authenticated → submit to GitHub
- If gh unavailable or --local-only → save as local markdown
- Clear messaging about what's happening

### Consequences

**Positive:**
- Works offline
- No credential management in our code
- Delegates auth complexity to gh CLI
- Users without gh can still use the command

**Negative:**
- Local files require manual submission later
- Two code paths to maintain

**Neutral:**
- gh CLI becomes a recommended but optional dependency

### Alternatives Considered

1. **Require gh CLI**: Would exclude users without it installed
2. **Direct API with token**: Credential management complexity, security concerns
3. **PyGithub library**: Extra dependency, still need credential handling

---

## ADR-004: Bundle Default Templates as Static Assets

**Date**: 2025-12-16
**Status**: Accepted
**Deciders**: User

### Context

Need to decide where issue templates come from:
- Only from project's `.github/ISSUE_TEMPLATE/`
- Only bundled with git-adr package
- Both, with resolution order

User requirement: Must work in offline/air-gapped environments.

### Decision

Bundle default templates as static assets within the git-adr package, with project templates overriding when present:

1. **Bundled templates** in `src/git_adr/templates/issues/` (bug, feat, docs)
2. **Project templates** in `.github/ISSUE_TEMPLATE/` override bundled
3. Bundled templates loaded via `importlib.resources`

### Consequences

**Positive:**
- Works offline/air-gapped without project setup
- Consistent baseline experience across all projects
- Users can customize per-project by adding templates
- No network dependency for basic functionality

**Negative:**
- Package size slightly larger
- Must maintain bundled templates alongside code
- Version coupling between templates and code

**Neutral:**
- Users may not realize templates can be customized

### Alternatives Considered

1. **Project templates only**: Would fail in air-gapped/offline scenarios, requires setup
2. **Bundled templates only**: No customization, forces git-adr's template format on all users
3. **Download templates on first use**: Requires network, breaks offline use

---

## ADR-005: Auto-Discovery of Templates with Type Aliases

**Date**: 2025-12-16
**Status**: Accepted
**Deciders**: User

### Context

Need to map user's `--type` input to actual template files. Options:
- Hardcoded mapping (bug → bug_report.md)
- Full filename requirement (bug_report)
- Auto-discovery with aliases

### Decision

Auto-discover templates from bundled package resources and optionally `.github/ISSUE_TEMPLATE/` with built-in aliases:
- Load bundled templates from package resources (always available)
- Scan project's `.github/ISSUE_TEMPLATE/` for overrides
- Maintain alias map: `bug` → `bug_report`, `feat` → `feature_request`, `docs` → `documentation`
- Allow direct filename reference (without extension)
- Show available types on invalid input

### Consequences

**Positive:**
- Works with any project's custom templates
- Short aliases for common types
- Extensible as project adds templates

**Negative:**
- Must handle edge cases (missing dir, no templates)
- Alias maintenance if conventions change

**Neutral:**
- First-time users see helpful error with available options

### Alternatives Considered

1. **Hardcoded only**: Would break with custom templates
2. **Filename only**: Requires knowing exact names, poor UX
3. **Template selection menu**: More complex, still needs type shortcut for scripting

---

## ADR-006: Pass Issue Body via stdin to gh CLI

**Date**: 2025-12-16
**Status**: Accepted
**Deciders**: Technical research

### Context

When submitting via gh CLI, the issue body must be passed safely. Options:
- `--body "content"` (shell escaping required)
- `--body-file /path/to/file` (temp file required)
- `--body-file -` (stdin, no temp file)

### Decision

Use `--body-file -` to pass body content via stdin using subprocess `input` parameter.

```python
subprocess.run(
    ["gh", "issue", "create", "--title", title, "--body-file", "-"],
    input=body_content,
    text=True,
    ...
)
```

### Consequences

**Positive:**
- No shell escaping issues
- No temp files to clean up
- Handles any content (special chars, newlines, etc.)

**Negative:**
- Slightly more complex subprocess invocation

**Neutral:**
- Standard pattern for gh CLI automation

### Alternatives Considered

1. **--body with escaping**: Error-prone, can fail on special characters
2. **Temp file**: Extra cleanup, potential race conditions
