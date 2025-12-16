---
document_type: architecture
project_id: SPEC-2025-12-15-002
version: 1.0.0
last_updated: 2025-12-15T22:50:00Z
status: draft
---

# git-adr Claude Skill - Technical Architecture

## System Overview

The git-adr skill is a comprehensive Claude Code skill that enables Claude to manage Architecture Decision Records using the git-adr tool. It follows progressive disclosure architecture to manage context efficiently while providing complete coverage of git-adr capabilities.

### Architecture Diagram

```
git-adr-skill/
├── SKILL.md                    # Core instructions (~400 lines)
│   ├── YAML Frontmatter        # name, description, triggers
│   ├── Quick Reference         # Command cheat sheet
│   ├── Execution Patterns      # How to run commands
│   ├── Format Selection        # Config-aware template choice
│   └── Navigation Guide        # Links to references/
│
└── references/                 # Progressive disclosure content
    ├── commands.md             # Full command documentation
    ├── formats/                # ADR format templates
    │   ├── madr.md             # MADR 4.0 template
    │   ├── nygard.md           # Original minimal format
    │   ├── y-statement.md      # Single-sentence format
    │   ├── alexandrian.md      # Pattern-language format
    │   ├── business-case.md    # Business justification format
    │   └── planguage.md        # Quantified requirements format
    ├── configuration.md        # All adr.* config options
    ├── best-practices.md       # ADR writing guidance
    └── workflows.md            # Common workflow patterns
```

### Key Design Decisions

| Decision | Resolution | Rationale |
|----------|------------|-----------|
| Progressive disclosure | SKILL.md core + references/ detail | Manages context efficiently |
| Format templates | Separate files per format | Load only needed format |
| Command execution | Direct Bash tool usage | Full git-adr integration |
| Config reading | `git config --get adr.template` | Match project conventions |
| Distribution | Dual location (repo + user skills) | Maximum accessibility |

## Component Design

### Component 1: SKILL.md (Core Instructions)

- **Purpose**: Primary entry point, always loaded when skill triggers
- **Responsibilities**:
  - Define trigger conditions (description field)
  - Provide command quick-reference
  - Explain execution patterns
  - Guide to appropriate reference files
- **Size Target**: ~400 lines (under 500 limit)
- **Dependencies**: None (self-contained core)

**Content Structure**:

```markdown
# SKILL.md Structure

1. YAML Frontmatter
   - name: git-adr
   - description: Comprehensive trigger description

2. Overview
   - What git-adr does
   - Core value proposition

3. Quick Reference
   - Command table (one-liners)
   - Common workflows

4. Execution Patterns
   - How to read config
   - How to execute commands
   - Error handling

5. Format Selection
   - Default behavior
   - Config-aware selection
   - Format recommendations

6. Navigation
   - When to read commands.md
   - When to read format templates
   - When to read best-practices.md
```

### Component 2: references/commands.md

- **Purpose**: Complete command documentation
- **Responsibilities**:
  - Full syntax for every command
  - All options and flags
  - Usage examples
- **Load Condition**: When user asks about specific commands
- **Size**: ~300 lines

### Component 3: references/formats/*.md

- **Purpose**: ADR format templates for content generation
- **Responsibilities**:
  - Complete template structure
  - Section explanations
  - Example content
- **Load Condition**: When generating ADR content
- **Size**: ~100-200 lines each

**Format Files**:

| File | Format | Use Case |
|------|--------|----------|
| madr.md | MADR 4.0 | Default, option analysis |
| nygard.md | Nygard | Quick, minimal decisions |
| y-statement.md | Y-Statement | Ultra-concise documentation |
| alexandrian.md | Alexandrian | Pattern-based, forces analysis |
| business-case.md | Business Case | Stakeholder approval, ROI |
| planguage.md | Planguage | Measurable quality requirements |

### Component 4: references/configuration.md

- **Purpose**: All git-adr configuration options
- **Responsibilities**:
  - Document all adr.* keys
  - Default values
  - Configuration recipes
- **Load Condition**: When setting up or configuring git-adr
- **Size**: ~200 lines

### Component 5: references/best-practices.md

- **Purpose**: ADR writing guidance
- **Responsibilities**:
  - When to write an ADR
  - What makes a good ADR
  - Common mistakes to avoid
- **Load Condition**: When teaching ADR concepts
- **Size**: ~150 lines

### Component 6: references/workflows.md

- **Purpose**: Common workflow patterns
- **Responsibilities**:
  - New project setup
  - Team collaboration
  - Migration from file-based ADRs
  - Onboarding new members
- **Load Condition**: When helping with workflows
- **Size**: ~150 lines

## Data Flow

### ADR Creation Flow

```
User Request: "Create an ADR for using PostgreSQL"
         │
         ▼
┌─────────────────────────────────────────┐
│ 1. Read project config                  │
│    git config --get adr.template        │
│    → Returns: "madr" (or default)       │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ 2. Load appropriate format template     │
│    Read references/formats/madr.md      │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ 3. Generate ADR content                 │
│    Fill template with user's context    │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ 4. Execute git-adr command              │
│    git adr new "Use PostgreSQL"         │
│    (with generated content)             │
└─────────────────────────────────────────┘
```

### Command Execution Pattern

```python
# Pattern for executing git-adr commands

# 1. Check if git-adr is available
git adr --version

# 2. Check if in git repository
git rev-parse --is-inside-work-tree

# 3. Check if git-adr initialized (for most commands)
git notes --ref=adr list 2>/dev/null

# 4. Execute the command
git adr <command> [options]

# 5. Handle output/errors appropriately
```

### Config-Aware Format Selection

```python
# Pattern for reading project configuration

# 1. Try to read configured template
template = $(git config --get adr.template 2>/dev/null)

# 2. Fall back to default if not set
if not template:
    template = "madr"

# 3. Load corresponding format file
# Read references/formats/{template}.md
```

## Progressive Disclosure Strategy

### Level 1: Metadata (Always Loaded)

The skill description in YAML frontmatter is always in context:

```yaml
name: git-adr
description: >
  Manage Architecture Decision Records using git-adr. Execute commands
  (init, new, edit, list, show, search, sync, etc.), generate ADR content
  in any format (MADR, Nygard, Y-Statement, Alexandrian, Business Case,
  Planguage), and teach ADR best practices. Use when users ask about
  ADRs, architecture decisions, git-adr commands, or need help
  documenting technical decisions.
```

### Level 2: Core Instructions (When Skill Triggers)

SKILL.md body loaded (~400 lines) containing:
- Command quick-reference
- Execution patterns
- Navigation to references

### Level 3: Reference Files (As Needed)

| User Intent | Files Loaded |
|-------------|--------------|
| "Create an ADR" | formats/{template}.md |
| "What commands are available?" | commands.md |
| "Configure git-adr" | configuration.md |
| "What is an ADR?" | best-practices.md |
| "Set up for my team" | workflows.md |
| "Multiple questions" | Relevant subset |

## Distribution Strategy

### Location 1: git-adr Repository

```
git-adr/
└── skills/
    └── git-adr/
        ├── SKILL.md
        └── references/
            └── ...
```

**Benefits**:
- Ships with the tool
- Always matches tool version
- Available when cloning repo

### Location 2: User Skills Directory

```
~/.claude/skills/
└── git-adr/
    ├── SKILL.md
    └── references/
        └── ...
```

**Benefits**:
- Available in any project
- Works without git-adr repo
- User can customize

### Sync Strategy

The packaged `.skill` file can be installed to user skills:
- Download from git-adr releases
- Or copy from cloned repo

## Error Handling

### git-adr Not Installed

```
If `git adr --version` fails:
  → Provide installation instructions
  → Suggest: pip install git-adr
  → Or: brew tap zircote/git-adr && brew install git-adr
```

### Not in Git Repository

```
If `git rev-parse --is-inside-work-tree` fails:
  → Explain git-adr requires a git repo
  → Offer to initialize: git init && git adr init
```

### ADRs Not Initialized

```
If `git notes --ref=adr list` returns empty:
  → Suggest: git adr init
  → Explain this creates the notes namespace
```

### Invalid Format Requested

```
If template not in [madr, nygard, y-statement, alexandrian, business, planguage]:
  → List valid formats
  → Suggest closest match
  → Fall back to MADR
```

## Testing Strategy

### Unit Testing

- Verify each format template generates valid ADR structure
- Test config reading with various configurations
- Validate command syntax against git-adr docs

### Integration Testing

- Test skill with actual git-adr installation
- Verify command execution in real git repository
- Test progressive disclosure behavior

### End-to-End Testing

- Full ADR creation workflow
- Team sync workflow
- Migration workflow from file-based ADRs

## Future Considerations

### Potential Enhancements

1. **Custom template support**: Load user-defined templates from .git-adr/templates/
2. **Multi-repo ADR aggregation**: View ADRs across related repositories
3. **ADR dependency tracking**: Link related decisions
4. **Interactive ADR builder**: Step-by-step wizard for complex ADRs

### Compatibility Notes

- Design for git-adr 0.1.0+ compatibility
- Consider git-adr 1.0 breaking changes
- Template format stability expected
