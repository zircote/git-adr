# Session Start: Auto-Context Loading

Load ADR context at the beginning of every session in a git-adr repository.

## Detection Flow

```
Session Start
    │
    ▼
┌─────────────────────────┐
│ Is this a git repo?     │──No──► Skip (not applicable)
└─────────────────────────┘
    │ Yes
    ▼
┌─────────────────────────┐
│ Is git-adr initialized? │──No──► Note: "ADRs not initialized"
│ (git notes --ref=adr)   │
└─────────────────────────┘
    │ Yes
    ▼
┌─────────────────────────┐
│ Load ADR summary        │
│ (git adr list --oneline)│
└─────────────────────────┘
    │
    ▼
Present context to conversation
```

## Auto-Load Commands

Execute at session start (silently, don't print to user):

```bash
# Step 1: Check if initialized
git notes --ref=adr list &>/dev/null && echo "INITIALIZED" || echo "NOT_INITIALIZED"

# Step 2: If initialized, get summary
git adr list --format oneline 2>/dev/null
```

## Context Summary Format

Present ADR context in this format:

```
📋 ADR Context Loaded
━━━━━━━━━━━━━━━━━━━━━
Repository has {N} Architecture Decision Records:

Recent Decisions:
• {ID} [{STATUS}] {Title} ({date})
• {ID} [{STATUS}] {Title} ({date})
• {ID} [{STATUS}] {Title} ({date})

Use "show me ADR {ID}" or "what did we decide about {topic}" to explore.
```

## Example Summary

```
📋 ADR Context Loaded
━━━━━━━━━━━━━━━━━━━━━
Repository has 5 Architecture Decision Records:

Recent Decisions:
• 20250115-use-postgresql [accepted] Use PostgreSQL for primary database (2025-01-15)
• 20250110-rest-api [accepted] REST API over GraphQL (2025-01-10)
• 20250105-typescript [proposed] Migrate to TypeScript (2025-01-05)

Use "show me ADR 20250115-use-postgresql" or "what did we decide about databases" to explore.
```

## When Context is Empty

If no ADRs exist:

```
📋 ADR Context Loaded
━━━━━━━━━━━━━━━━━━━━━
Repository has 0 Architecture Decision Records.

Ready to capture decisions. Say "record decision about {topic}" to start.
```

## Error Handling

### git-adr not installed

```
⚠️ git-adr is not installed
Install with:
  pip install git-adr
  # or
  brew tap zircote/git-adr && brew install git-adr
```

### Not in a git repository

Skip silently - git-adr not applicable.

### ADRs not initialized

```
ℹ️ ADR tracking not initialized in this repository.
Run `git adr init` to start tracking architecture decisions.
```

## Memory Optimization

- Load **oneline format** only (minimal tokens)
- Limit to **recent 5-10 ADRs** in summary
- Full content loaded **on-demand** via hydration (see decision-recall.md)

## Implementation Notes

This workflow runs automatically when the skill detects a git-adr repository. The summary provides awareness of existing decisions without consuming excessive context.

For full ADR content, use the hydration pattern:
- "Show me ADR {id}" → `git adr show {id}`
- "What did we decide about X" → `git adr search "X"`
