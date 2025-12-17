---
document_type: research
project_id: SPEC-2025-12-16-001
last_updated: 2025-12-16
---

# git-adr Claude Skill - Research Notes

## Research Summary

This skill enables Claude Code to treat git-adr ADRs as persistent "machine memory" - automatically loading ADR context at session start and enabling natural ADR creation from conversations.

### Key Findings

1. **git-adr architecture is ideal for tiered context**: IndexManager provides metadata-only queries, NotesManager handles full content - perfect for "summaries + on-demand hydration"
2. **Existing git-adr skill is functional but basic**: Focuses on CLI wrapper, doesn't address context-as-memory use case
3. **Claude skill patterns favor progressive disclosure**: Reference files loaded on-demand, not monolithic SKILL.md

---

## Codebase Analysis

### Relevant git-adr Components for Integration

| Component | Location | Relevance |
|-----------|----------|-----------|
| IndexManager | `src/git_adr/core/index.py` | Metadata queries without full content (perfect for summaries) |
| NotesManager | `src/git_adr/core/notes.py` | Full ADR retrieval for hydration |
| ADR dataclass | `src/git_adr/core/adr.py` | Model structure: id, title, date, status, tags, etc. |
| AIService | `src/git_adr/ai/service.py` | draft_adr(), suggest_improvements() for AI features |
| ConfigManager | `src/git_adr/core/config.py` | Template, AI provider, namespace settings |

### Index Entry Structure (Ideal for Summaries)

```python
@dataclass
class IndexEntry:
    id: str                      # 20251216-use-postgresql
    title: str                   # "Use PostgreSQL for Persistence"
    date: date                   # 2025-12-16
    status: ADRStatus           # accepted, proposed, deprecated, etc.
    tags: tuple[str, ...]       # (database, backend)
    linked_commits: tuple[str, ...]
    supersedes: str | None
    superseded_by: str | None
```

This maps directly to the "structured metadata" format the user requested for auto-loaded summaries.

### Full ADR Content (For Hydration)

YAML frontmatter + Markdown body:
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
...

## Decision Outcome
Chosen option: "PostgreSQL"
...
```

### Command Surface (Curated Subset)

| Command | Purpose | Claude Integration |
|---------|---------|-------------------|
| `git adr list` | List ADRs with filters | Context loading (summaries) |
| `git adr show <id>` | Display single ADR | On-demand hydration |
| `git adr new "<title>"` | Create ADR | From guided prompts or conversation |
| `git adr edit <id>` | Modify ADR | After review/feedback |
| `git adr search <query>` | Full-text search | Find relevant decisions |
| `git adr ai suggest <id>` | AI improvements | Polish draft ADRs |

### AI Integration Points

```python
# From ai/service.py
class AIService:
    draft_adr(title, context, options, drivers) -> AIResponse
    suggest_improvements(adr: ADR) -> AIResponse
```

Can leverage existing AI scaffolding for:
- Drafting from conversation context
- Improving drafted ADRs
- Summarizing decisions

---

## Claude Skill Patterns

### Standard Skill Structure

```
skill-name/
├── SKILL.md                    # Entry point + navigation
├── references/                 # Progressive disclosure
│   ├── commands.md
│   ├── configuration.md
│   ├── best-practices.md
│   └── formats/               # Template variants
│       ├── madr.md
│       └── ...
└── resources/                  # Additional content
```

### Critical Design Patterns

1. **Progressive Loading Guide** - Tell Claude what file to load based on user intent:
   ```markdown
   | User Intent | Load File |
   |-------------|-----------|
   | "Create ADR" | references/creation-workflow.md |
   | "What decisions exist?" | (run git adr list) |
   ```

2. **Safety Rules** - Configuration protection:
   ```markdown
   ## CRITICAL RULES
   **NEVER modify user configuration without explicit permission.**
   ```

3. **Context-Efficient Summaries** - Don't load full ADRs when summaries suffice

### Existing git-adr Skill Gap Analysis

Current skill (`~/.claude/skills/git-adr/`) provides:
- ✅ Command reference
- ✅ Format templates
- ✅ Configuration guidance
- ✅ Safety rules

Missing for "machine memory" use case:
- ❌ Auto-load ADR context at session start
- ❌ Conversation-to-ADR extraction
- ❌ Tiered loading (summary → full)
- ❌ Decision recall guidance ("what did we decide about X?")

---

## Technical Research

### Best Practices for Context Loading

**Pattern: Structured Metadata First**

At session start, load concise ADR index:
```yaml
# ADR Context (4 active decisions)
- ADR-001: Use PostgreSQL [accepted, 2025-12-10] #database #backend
- ADR-002: MADR Template Format [accepted, 2025-12-08] #process
- ADR-003: API Rate Limiting [proposed, 2025-12-15] #security #api
- ADR-004: Monorepo Structure [deprecated, 2025-11-20] #architecture
```

Token cost: ~50 tokens per ADR vs ~500+ for full content.

**Pattern: Hydration on Demand**

When user asks "tell me more about the database decision":
1. Parse reference to ADR-001 or "database" tag
2. Load full ADR content via `git adr show ADR-001`
3. Include in response context

**Pattern: Search for Relevance**

When discussing a topic that might have an ADR:
1. Run `git adr search "<topic>"`
2. If matches found, suggest checking relevant ADRs
3. Load if user confirms interest

---

## Integration Point Analysis

### Context Auto-Loading (Session Start)

**Trigger**: Claude Code session starts in a git repo with ADRs initialized

**Action**:
```bash
# Check if ADRs exist
git notes --ref=adr list 2>/dev/null | head -1
# If yes, load summary
git adr list --format=oneline --status=accepted,proposed
```

**Output Format**:
```
📋 Project ADRs (3 active):
• 20251216-use-postgresql: Use PostgreSQL [accepted] #database
• 20251215-api-rate-limiting: API Rate Limiting Strategy [proposed] #api
• 20251210-madr-format: Use MADR Template Format [accepted] #process

Run `git adr show <id>` for full context.
```

### Conversation-to-ADR Extraction

**Trigger Phrases**:
- "record this decision"
- "create an ADR for this"
- "we should document this decision"
- "capture this as an ADR"

**Extraction Flow**:
1. Identify decision context from recent conversation
2. Extract: title, context, options considered, decision, rationale
3. Generate draft using MADR template
4. Present for user review before creating

### On-Demand Hydration

**Trigger Phrases**:
- "tell me more about ADR-XXX"
- "what was the rationale for X?"
- "show me the database decision"

**Flow**:
1. Map natural language to ADR ID (by title keyword, tag, or explicit ID)
2. Run `git adr show <id>`
3. Include full content in response

---

## Competitive Analysis

### Similar Memory/Context Patterns

| Approach | Strengths | Weaknesses | Applicability |
|----------|-----------|------------|---------------|
| CLAUDE.md | Always loaded | Manual maintenance | Project-level docs |
| Git notes | Portable, versioned | Requires tool | ADR storage |
| Session summaries | Low overhead | Lost on restart | Ephemeral |
| MCP resources | Structured | Complex setup | External systems |

**Why ADRs are ideal for machine memory**:
- Versioned with code history
- Structured format (parseable)
- Already capture architectural decisions
- Don't pollute working tree
- Sync with remote automatically

---

## Open Questions Resolved

1. **How to avoid loading all ADRs?** → Index-based queries return metadata only
2. **How to identify relevant ADRs?** → Status filters (accepted, proposed) + search
3. **How to extract from conversation?** → AI draft with conversation context
4. **How to maintain coherence?** → Link new decisions to superseded ones

---

## Sources

- git-adr source code: `src/git_adr/`
- Existing git-adr skill: `~/.claude/skills/git-adr/`
- Claude skill patterns: `~/.claude/skills/` (66+ skills examined)
- Frontend-development skill: Progressive loading pattern example
- DevOps skill: Multi-platform reference organization
