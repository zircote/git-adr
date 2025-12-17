# Decision Recall Workflow

Find and hydrate past architecture decisions on demand.

## Trigger Phrases

### Direct Recall (by ID)
- "Show me ADR {id}"
- "What's in ADR {id}"
- "Pull up {id}"
- "Display ADR {id}"

### Topic Search
- "What did we decide about {topic}"
- "Find decisions about {topic}"
- "Any ADRs for {topic}"
- "Search ADRs for {topic}"

### Status-Based
- "What decisions are proposed"
- "Show accepted ADRs"
- "List deprecated decisions"

## Recall Flow

```
Trigger Detected
    │
    ▼
┌─────────────────────────────┐
│ Classify query type:        │
│ - Direct ID? → show command │
│ - Topic? → search command   │
│ - Status? → list + filter   │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│ Execute appropriate command │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│ Present results with context│
└─────────────────────────────┘
```

## Command Mapping

| Query Type | Command |
|------------|---------|
| Direct ID | `git adr show {id}` |
| Topic search | `git adr search "{topic}"` |
| Status filter | `git adr list --status {status}` |
| Tag filter | `git adr list --tag {tag}` |
| Recent | `git adr list --limit 5` |

## Hydration Pattern

### Summary → Full Content

Session start loads **summary only**. When user requests specific ADR:

```
Summary (loaded at start):
• 20250115-use-postgresql [accepted] Use PostgreSQL (2025-01-15)

User: "Show me the PostgreSQL decision"

Full hydration:
git adr show 20250115-use-postgresql
```

### Search Results → Detail

```
User: "What did we decide about databases?"

Step 1 - Search:
git adr search "database"
→ Returns matching ADRs with snippets

Step 2 - Follow-up (if needed):
git adr show {selected-id}
→ Returns full content
```

## Response Format

### Single ADR

```
📄 ADR: 20250115-use-postgresql
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Title:** Use PostgreSQL for primary database
**Status:** accepted
**Date:** 2025-01-15

## Context
{full context section}

## Decision
{decision statement}

## Consequences
{consequences list}

---
Related: `git adr show 20250115-use-postgresql`
```

### Search Results

```
🔍 ADRs matching "database"
━━━━━━━━━━━━━━━━━━━━━━━━━━

Found 3 matching decisions:

1. **20250115-use-postgresql** [accepted]
   Use PostgreSQL for primary database
   > "...chose PostgreSQL for its **database** features..."

2. **20250110-redis-cache** [accepted]
   Use Redis for caching layer
   > "...separate from primary **database**..."

3. **20241220-schema-migrations** [superseded]
   Use Flyway for database migrations
   > "...managing **database** schema changes..."

Say "show me {id}" for full details.
```

## Fuzzy Matching

When user reference is ambiguous:

```
User: "Show me the postgres decision"

Search: git adr search "postgres"
→ Found: 20250115-use-postgresql

Response: "Found one ADR about PostgreSQL:
[Shows full content]"
```

```
User: "What about the API decision?"

Search: git adr search "API"
→ Found multiple:
  - 20250110-rest-api
  - 20250108-api-versioning
  - 20241215-api-authentication

Response: "Found 3 ADRs about APIs:
[Lists summaries]
Which one would you like to see in full?"
```

## Related ADRs

When showing an ADR, note relationships:

```
📄 ADR: 20250120-migrate-to-aurora
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Supersedes:** 20250115-use-postgresql
**Status:** accepted

...

Related decisions:
• Supersedes: 20250115-use-postgresql (Use PostgreSQL)
```

## Error Handling

### No Results

```
🔍 No ADRs matching "{query}"

Try:
• `git adr list` - see all ADRs
• `git adr search "{alternative-term}"`
• Check spelling or use broader terms
```

### ADR Not Found

```
❌ ADR "{id}" not found

Available ADRs:
• 20250115-use-postgresql
• 20250110-rest-api
...

Did you mean one of these?
```
