---
document_type: decisions
project_id: SPEC-2025-12-15-002
---

# git-adr Claude Skill - Architecture Decision Records

## ADR-001: Claude Generates ADR Content Directly

**Date**: 2025-12-15
**Status**: Accepted
**Deciders**: User (via requirements elicitation)

### Context

git-adr has built-in AI features (`git adr ai draft`, `git adr ai suggest`, `git adr ai ask`) that use configured AI providers (OpenAI, Anthropic, etc.) to generate content. The skill could either teach users how to use these features or have Claude generate content directly.

### Decision

Claude will generate ADR content directly rather than delegating to git-adr's AI features.

### Consequences

**Positive:**
- Consistent experience regardless of git-adr AI configuration
- No dependency on external AI provider setup
- Claude can apply its full capabilities to content generation
- Works even when git-adr AI features aren't configured

**Negative:**
- git-adr's AI features may be underutilized
- Content generation style may differ from git-adr AI
- Users may not learn about git-adr's AI capabilities

**Neutral:**
- Claude still documents git-adr AI features for users who prefer them

---

## ADR-002: Progressive Disclosure Architecture

**Date**: 2025-12-15
**Status**: Accepted
**Deciders**: Architecture review

### Context

The skill needs to cover 30+ commands, 6 ADR formats, extensive configuration, and best practices. Loading all content at once would overwhelm context limits. The skill-creator framework recommends progressive disclosure.

### Decision

Implement three-level progressive disclosure:
1. **Metadata** (~100 tokens): Always in context via YAML description
2. **SKILL.md body** (~400 lines): Core instructions when skill triggers
3. **references/** (unlimited): Loaded on-demand per user intent

### Consequences

**Positive:**
- Efficient context usage
- Faster skill loading
- Content scales without penalty
- Users get relevant information only

**Negative:**
- Additional file management
- Potential for missing cross-references
- More complex navigation

**Neutral:**
- Follows established skill-creator patterns

### Alternatives Considered

1. **Single large SKILL.md**: Simple but would exceed recommended limits
2. **Minimal skill + external docs**: Lean but requires internet access
3. **Multiple focused skills**: Modular but fragments the experience

---

## ADR-003: Config-Aware Format Selection

**Date**: 2025-12-15
**Status**: Accepted
**Deciders**: User (via requirements elicitation)

### Context

When Claude generates ADR content, it needs to know which of the 6 formats to use. Options include always asking the user, using a default, or reading the project's configuration.

### Decision

Read the project's `adr.template` configuration and use that format. Fall back to MADR if not configured.

### Consequences

**Positive:**
- ADRs match project conventions automatically
- Less friction for users
- Consistent with team's chosen format
- Respects project autonomy

**Negative:**
- Requires git config access
- May fail in non-git contexts
- Users may not realize format was auto-selected

**Neutral:**
- MADR fallback is sensible default

---

## ADR-004: Direct Command Execution

**Date**: 2025-12-15
**Status**: Accepted
**Deciders**: User (via requirements elicitation)

### Context

The skill could either execute git-adr commands directly (using Claude's Bash tool) or advise users on what commands to run.

### Decision

Execute git-adr commands directly when in a git repository with git-adr available.

### Consequences

**Positive:**
- Seamless user experience
- Full workflow automation
- Immediate results
- Reduces user friction

**Negative:**
- Requires git-adr installation
- May need error handling for missing dependencies
- User must trust Claude with file system access

**Neutral:**
- Standard pattern for Claude Code tools

---

## ADR-005: Dual Distribution Strategy

**Date**: 2025-12-15
**Status**: Accepted
**Deciders**: User (via requirements elicitation)

### Context

The skill needs to be available to users. Options include shipping only with git-adr repo, only in user's skills directory, or both.

### Decision

Distribute in both locations:
1. `git-adr/skills/git-adr/` - Ships with the tool
2. `~/.claude/skills/git-adr/` - User-installed standalone

### Consequences

**Positive:**
- Maximum accessibility
- Works with or without git-adr repo cloned
- Users can customize their copy
- Version in repo matches tool version

**Negative:**
- Potential version drift between locations
- Two places to maintain
- Installation instructions more complex

**Neutral:**
- .skill package simplifies user installation

---

## ADR-006: Comprehensive Over Lean

**Date**: 2025-12-15
**Status**: Accepted
**Deciders**: User (via requirements elicitation)

### Context

Skills can be lean (minimal SKILL.md, external references) or comprehensive (include everything). Trade-off between context usage and completeness.

### Decision

Build a comprehensive skill that includes all 6 format templates, full command reference, and complete documentation. Accept larger size in exchange for complete coverage.

### Consequences

**Positive:**
- Works offline/without external references
- Complete feature coverage
- Self-contained package
- No broken links to external docs

**Negative:**
- Larger skill size
- More maintenance burden
- Potential for drift from git-adr docs

**Neutral:**
- Progressive disclosure mitigates context impact

### Alternatives Considered

1. **Lean core + external references**: Smaller but requires git-adr docs access
2. **Minimal viable**: Fast to build but incomplete
3. **Comprehensive**: Chosen - complete coverage with progressive disclosure
