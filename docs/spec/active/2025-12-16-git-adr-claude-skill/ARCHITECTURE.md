---
document_type: architecture
project_id: SPEC-2025-12-16-001
version: 1.0.0
last_updated: 2025-12-16
status: draft
---

# git-adr Claude Skill - Technical Architecture

## System Overview

The git-adr Claude Skill acts as a bridge between git-adr (ADR storage in git notes) and Claude Code (AI assistant), enabling ADRs to serve as persistent "machine memory" that informs AI assistance across sessions.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Claude Code Session                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐     ┌────────────────┐     ┌──────────────┐  │
│  │   SKILL.md   │────▶│  Context Loader │────▶│ ADR Context  │  │
│  │  (Entry)     │     │  (Auto-start)   │     │ (In-session) │  │
│  └──────────────┘     └────────────────┘     └──────────────┘  │
│         │                     │                      │          │
│         ▼                     ▼                      ▼          │
│  ┌──────────────┐     ┌────────────────┐     ┌──────────────┐  │
│  │  references/ │     │  Conversation   │     │   Response   │  │
│  │  (On-demand) │     │   Handlers      │     │  Generation  │  │
│  └──────────────┘     └────────────────┘     └──────────────┘  │
│                               │                                 │
└───────────────────────────────┼─────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
            ┌──────────────┐       ┌──────────────┐
            │  git-adr CLI │       │ Git Repository│
            │  (Commands)  │       │ (notes/adr)   │
            └──────────────┘       └──────────────┘
```

### Key Design Decisions

1. **Extend, Don't Replace**: Skill enhances existing git-adr CLI rather than reimplementing
2. **Progressive Loading**: Summary → Full content pattern to preserve token budget
3. **Read-Only Default**: Never modify configuration without explicit user permission
4. **Graceful Degradation**: Clear guidance when git-adr not installed or ADRs not initialized

## Component Design

### Component 1: SKILL.md (Entry Point)

- **Purpose**: Skill discovery, activation patterns, quick reference
- **Responsibilities**:
  - Define trigger phrases for skill activation
  - Provide navigation to reference files
  - Establish critical safety rules
  - Document auto-loading behavior
- **Interfaces**: Claude Code skill framework
- **Dependencies**: None (entry point)
- **Size Target**: 8-12 KB (readable in single load)

### Component 2: Context Loader (Auto-Start)

- **Purpose**: Load ADR summaries at session start
- **Responsibilities**:
  - Detect if in git repository with ADRs
  - Extract summary metadata via `git adr list`
  - Format as structured context for Claude
  - Handle errors gracefully (not installed, not initialized)
- **Interfaces**: Shell commands, SKILL.md instructions
- **Dependencies**: git-adr CLI, git
- **Output Format**:
```yaml
# Project ADRs (3 active decisions)
- id: 20251216-use-postgresql
  title: "Use PostgreSQL for Persistence"
  status: accepted
  date: 2025-12-16
  tags: [database, backend]
- id: 20251215-api-rate-limiting
  title: "API Rate Limiting Strategy"
  status: proposed
  date: 2025-12-15
  tags: [security, api]
```

### Component 3: Conversation Handlers

- **Purpose**: Process user intents and generate appropriate responses
- **Responsibilities**:
  - Parse trigger phrases (create ADR, show decision, search, etc.)
  - Route to appropriate command execution
  - Format output for conversation context
- **Interfaces**: Natural language triggers, git-adr commands
- **Dependencies**: SKILL.md navigation guide, references/

#### Handler Types

| Handler | Trigger Examples | Action |
|---------|------------------|--------|
| Hydration | "show me the database decision", "ADR-001" | `git adr show <id>` |
| Search | "what did we decide about X?", "find ADRs about Y" | `git adr search <query>` |
| Create | "record this decision", "create an ADR" | Extract context → guided prompts |
| List | "what decisions exist?", "show all ADRs" | `git adr list --format=table` |

### Component 4: Reference Files (Progressive Disclosure)

- **Purpose**: Provide detailed documentation loaded on-demand
- **Responsibilities**:
  - Command documentation with examples
  - ADR template references
  - Configuration options
  - Workflow guides
- **Interfaces**: Claude reads based on user intent
- **Dependencies**: SKILL.md navigation table
- **Size Target**: 2-5 KB per file

### Component 5: Creation Workflow

- **Purpose**: Guide ADR creation from conversation
- **Responsibilities**:
  - Extract decision context from conversation
  - Present guided prompts for MADR structure
  - Generate draft ADR
  - Allow user review before commit
- **Interfaces**: Conversation context, `git adr new`
- **Dependencies**: AI extraction capabilities, MADR template

## Data Design

### Data Models

#### ADR Summary (Auto-Load Format)
```yaml
id: string           # 20251216-use-postgresql
title: string        # "Use PostgreSQL for Persistence"
status: enum         # accepted | proposed | deprecated | superseded
date: date           # 2025-12-16
tags: string[]       # [database, backend]
supersedes?: string  # Previous ADR ID if applicable
```

#### Full ADR (Hydration Format)
```markdown
---
id: 20251216-use-postgresql
title: Use PostgreSQL for Persistence
date: 2025-12-16
status: accepted
tags: [database, backend]
deciders: [alice, bob]
format: madr
---

## Context and Problem Statement

We need a persistent data store for user accounts and application state...

## Considered Options

* PostgreSQL
* MySQL
* MongoDB
* SQLite

## Decision Outcome

Chosen option: "PostgreSQL", because...

## Consequences

### Good
* ...

### Bad
* ...
```

### Data Flow

```
Session Start
     │
     ▼
┌─────────────────┐     ┌──────────────────┐
│ Check git repo  │────▶│ Check ADRs init  │
└─────────────────┘     └──────────────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
              ┌──────────┐          ┌──────────┐
              │ Not init │          │ Has ADRs │
              │ (Suggest)│          │ (Load)   │
              └──────────┘          └──────────┘
                                         │
                                         ▼
                               ┌──────────────────┐
                               │ git adr list     │
                               │ --format=yaml    │
                               │ --status=active  │
                               └──────────────────┘
                                         │
                                         ▼
                               ┌──────────────────┐
                               │ Format summaries │
                               │ in context block │
                               └──────────────────┘
```

### Storage Strategy

- **ADR Storage**: git notes (managed by git-adr, not this skill)
- **Skill Storage**: Skill files in `~/.claude/skills/git-adr/` or project-local
- **Session Context**: Claude's in-context memory (ephemeral per session)
- **No Caching**: Always read fresh from git-adr (source of truth)

## Integration Points

### git-adr CLI Integration

| Command | Use Case | Output Processing |
|---------|----------|-------------------|
| `git adr list --format=yaml` | Auto-load summaries | Parse YAML to context block |
| `git adr show <id>` | Hydration | Include full markdown in context |
| `git adr search <query>` | Find decisions | Show matches with snippets |
| `git adr new "<title>"` | Create ADR | Launch editor or use --stdin |
| `git adr edit <id>` | Modify ADR | Launch editor |
| `git adr ai suggest <id>` | Improve ADR | Show suggestions |

### Error Handling

| Error Condition | Detection | User Message |
|-----------------|-----------|--------------|
| git-adr not installed | `which git-adr` fails | "git-adr not found. Install with: pip install git-adr" |
| Not in git repo | `git rev-parse` fails | "Not in a git repository." |
| ADRs not initialized | `git notes --ref=adr list` empty | "ADRs not initialized. Run: git adr init" |
| ADR not found | `git adr show` returns 1 | "ADR '<id>' not found. Run: git adr list" |

## Security Design

### Configuration Protection

**Critical Rule**: Never modify `git adr config` without explicit user permission.

Safe operations (read-only):
```bash
git config --get adr.template
git adr list
git adr show <id>
git adr search <query>
```

Require explicit permission:
```bash
git adr config --set <key> <value>
git adr new (creates data)
git adr edit (modifies data)
```

### Input Validation

- Sanitize ADR IDs before shell execution
- Validate search queries (no shell injection)
- Quote all parameters in shell commands

## Performance Considerations

### Token Efficiency

| Operation | Token Estimate | Strategy |
|-----------|---------------|----------|
| Summary (1 ADR) | 50-80 tokens | Structured, minimal |
| Full ADR | 300-800 tokens | Load only on request |
| 10 ADR summaries | 500-800 tokens | Acceptable for context |
| 50 ADR summaries | 2500-4000 tokens | Filter to active only |

### Optimization Strategies

1. **Status Filtering**: Only load accepted/proposed by default
2. **Tag Filtering**: Load domain-relevant ADRs when topic clear
3. **Lazy Hydration**: Never load full content unless explicitly requested
4. **Pagination**: For >20 ADRs, show first page with "more available" hint

## Skill File Structure

```
git-adr/
├── SKILL.md                    # 10 KB - Entry point + navigation
├── references/
│   ├── commands.md             # 4 KB - Command reference
│   ├── context-loading.md      # 3 KB - Auto-load behavior
│   ├── creation-workflow.md    # 4 KB - Guided ADR creation
│   ├── search-patterns.md      # 2 KB - Search syntax
│   └── configuration.md        # 3 KB - Config options
├── formats/
│   ├── madr.md                 # 2 KB - MADR template
│   ├── nygard.md               # 2 KB - Nygard template
│   ├── y-statement.md          # 1 KB - Y-statement format
│   └── alexandrian.md          # 2 KB - Pattern-based format
└── workflows/
    ├── session-start.md        # 2 KB - Context loading guide
    ├── decision-capture.md     # 3 KB - Conversation extraction
    └── decision-recall.md      # 2 KB - Finding past decisions
```

### SKILL.md Structure

```markdown
---
name: git-adr
description: >
  Manage Architecture Decision Records as machine memory. Auto-loads ADR
  context at session start, enables natural decision capture from conversations,
  and provides seamless access to project architectural history.
version: 1.0.0
---

# git-adr: ADRs as Machine Memory

## CRITICAL RULES
[Safety rules - config protection, read-only default]

## Auto-Context Loading
[Session start behavior, summary format]

## Trigger Phrases
[Create, show, search, list patterns]

## Quick Command Reference
[Table of curated commands]

## Progressive Loading Guide
[Navigation table for references/]

## Common Workflows
[Brief workflow summaries with links]
```

## Testing Strategy

### Unit Testing

| Test Area | Method |
|-----------|--------|
| Trigger phrase parsing | Pattern matching tests |
| Summary formatting | Output validation |
| Error message clarity | Expected error scenarios |

### Integration Testing

| Test Scenario | Validation |
|---------------|------------|
| Session start with ADRs | Summaries appear in context |
| Hydration request | Full ADR loads correctly |
| Search query | Relevant results returned |
| ADR creation | Draft generated, review prompted |

### End-to-End Testing

| User Journey | Success Criteria |
|--------------|------------------|
| New project, first ADR | User creates ADR via guided prompts |
| Returning to project | Claude references ADRs in responses |
| Decision recall | "What did we decide about X?" returns correct ADR |

## Deployment Considerations

### Installation

Two installation paths:

1. **Global skill** (recommended):
   ```bash
   cp -r skill-directory ~/.claude/skills/git-adr/
   ```

2. **Project-local skill**:
   ```bash
   cp -r skill-directory .claude/skills/git-adr/
   ```

### Dependencies

Pre-requisites (documented in skill):
- git-adr: `pip install git-adr` or `brew install zircote/tap/git-adr`
- Git 2.20+

### Rollout Strategy

1. **Alpha**: Manual testing in git-adr repository itself
2. **Beta**: Test with 2-3 real projects
3. **Release**: Publish to skill directory, update documentation

## Future Considerations

### Potential Enhancements

1. **MCP Server**: Expose ADR operations as MCP resources/tools
2. **Team Integration**: Slack/Teams notifications for new ADRs
3. **Visual Timeline**: ASCII diagram of decision evolution
4. **Impact Tracking**: Show code changes linked to ADRs

### Architecture Evolution

The current shell-based integration could evolve to:
- Direct Python integration (if Claude Code supports)
- MCP server for richer tool integration
- LSP-like protocol for real-time ADR awareness

These would require changes to Claude Code capabilities, not just this skill.
