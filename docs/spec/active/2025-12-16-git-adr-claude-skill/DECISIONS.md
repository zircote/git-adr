---
document_type: decisions
project_id: SPEC-2025-12-16-001
---

# git-adr Claude Skill - Architecture Decision Records

## ADR-001: Extend Rather Than Replace Existing Skill

**Date**: 2025-12-16
**Status**: Accepted
**Deciders**: Project author

### Context

An existing `git-adr` skill exists in `~/.claude/skills/git-adr/` that provides CLI command documentation. The new "machine memory" capability could either:
1. Replace the existing skill entirely
2. Extend it with new features
3. Create a separate skill with different name

### Decision

Extend the existing skill by enhancing it with machine memory capabilities while preserving existing functionality.

### Consequences

**Positive:**
- Single skill to maintain
- Existing users get new features automatically
- Consistent experience

**Negative:**
- Must be careful not to break existing functionality
- Skill file grows larger

**Neutral:**
- May need versioning to track changes

### Alternatives Considered

1. **Replace entirely**: Would lose proven patterns, risky
2. **Separate skill (git-adr-memory)**: Confusing to have two similar skills

---

## ADR-002: Shell-Based git-adr Integration

**Date**: 2025-12-16
**Status**: Accepted
**Deciders**: Project author

### Context

The skill needs to interact with git-adr. Options:
1. Direct shell subprocess calls to `git adr` commands
2. Python import of git-adr modules (if skill supports)
3. MCP server wrapping git-adr

### Decision

Use shell subprocess calls to git-adr CLI commands.

### Consequences

**Positive:**
- Works with Claude Code's current capabilities
- No dependency on internal git-adr APIs
- Easy to test and debug
- Users see familiar commands

**Negative:**
- Shell parsing overhead
- Must handle shell escaping carefully
- Limited by CLI output formats

**Neutral:**
- May evolve to MCP server if Claude Code adds support

### Alternatives Considered

1. **Python import**: Claude Code skills don't support arbitrary Python imports
2. **MCP server**: More complex, requires additional infrastructure

---

## ADR-003: Structured YAML for ADR Summaries

**Date**: 2025-12-16
**Status**: Accepted
**Deciders**: Project author, user input

### Context

Auto-loaded ADR summaries need a format that:
- Minimizes token usage
- Is parseable by Claude
- Contains enough context to be useful
- Is human-readable

Options considered:
- Title + status only (minimal)
- Title + one-liner (brief)
- Structured metadata (YAML-like)
- Mini-markdown

### Decision

Use structured YAML-like format with key metadata fields.

### Consequences

**Positive:**
- Programmatically parseable
- Clear field semantics
- Compact but informative
- ~50-80 tokens per ADR

**Negative:**
- Slightly more verbose than minimal options
- Requires parsing logic in skill instructions

**Neutral:**
- Matches git-adr's `--format=yaml` output

### Alternatives Considered

1. **Title only**: Too minimal, loses status/tags
2. **One-liner**: Harder to parse programmatically
3. **Mini-markdown**: Higher token cost

---

## ADR-004: Progressive Loading Architecture

**Date**: 2025-12-16
**Status**: Accepted
**Deciders**: Project author

### Context

Skills can contain extensive documentation. Loading everything wastes tokens. Need a strategy for efficient context loading.

### Decision

Implement progressive loading:
1. SKILL.md contains navigation table
2. Reference files loaded on-demand based on user intent
3. ADR content loaded only when explicitly requested

### Consequences

**Positive:**
- Token-efficient
- Faster initial load
- Only relevant content in context

**Negative:**
- More complex skill structure
- Must maintain accurate navigation table

**Neutral:**
- Standard pattern in well-designed Claude skills

### Alternatives Considered

1. **Monolithic SKILL.md**: Simple but wasteful
2. **Always load everything**: Token-inefficient

---

## ADR-005: Read-Only Configuration Default

**Date**: 2025-12-16
**Status**: Accepted
**Deciders**: Project author

### Context

The skill could modify git-adr configuration to help users set up AI providers, templates, etc. However, modifying user config without permission is dangerous.

### Decision

Make all configuration access read-only by default. Any configuration changes require explicit user permission stated in the conversation.

### Consequences

**Positive:**
- Prevents accidental config corruption
- Builds user trust
- Follows principle of least privilege

**Negative:**
- Slightly less convenient for setup

**Neutral:**
- Users can still configure via direct `git adr config` commands

### Alternatives Considered

1. **Allow helpful config changes**: Too risky for surprising behavior
2. **No config access at all**: Would break features that read config

---

## ADR-006: Curated Command Subset

**Date**: 2025-12-16
**Status**: Accepted
**Deciders**: Project author, user input

### Context

git-adr has 30+ commands. Including all would:
- Overwhelm skill documentation
- Dilute focus on "machine memory" use case
- Add maintenance burden

### Decision

Expose a curated subset of commands most relevant to Claude Code workflow:
- `list`, `show` (read)
- `new`, `edit` (write)
- `search` (find)
- `ai suggest` (improve)

### Consequences

**Positive:**
- Focused documentation
- Clear use cases
- Easier maintenance

**Negative:**
- Power users may want more commands
- Must document how to access other commands directly

**Neutral:**
- Can expand subset based on user feedback

### Alternatives Considered

1. **Full CLI wrapper**: Too complex, dilutes focus
2. **Read-only subset**: Misses creation workflow value
