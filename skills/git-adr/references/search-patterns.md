# Search Patterns

Natural language to git-adr search query mapping.

## Basic Search Syntax

```bash
# Full-text search
git adr search "query"

# With filters
git adr search "query" --status accepted
git adr search "query" --tag infrastructure

# Case-sensitive
git adr search "PostgreSQL" --case-sensitive

# Regex
git adr search "data.*base" --regex
```

## Natural Language Mapping

| User Says | Command |
|-----------|---------|
| "Find ADRs about X" | `git adr search "X"` |
| "What did we decide about X" | `git adr search "X"` |
| "Decisions mentioning X" | `git adr search "X"` |
| "ADRs containing X" | `git adr search "X"` |

### With Status

| User Says | Command |
|-----------|---------|
| "Accepted decisions about X" | `git adr search "X" --status accepted` |
| "Proposed ADRs for X" | `git adr search "X" --status proposed` |
| "Deprecated decisions" | `git adr list --status deprecated` |

### With Tags

| User Says | Command |
|-----------|---------|
| "Security-related decisions" | `git adr list --tag security` |
| "Infrastructure ADRs" | `git adr list --tag infrastructure` |
| "Frontend decisions" | `git adr list --tag frontend` |

## Search Context Options

```bash
# Lines of context around matches
git adr search "database" --context 3

# Match output snippets
git adr search "database" --context 2
```

## Common Search Queries

### Technology Decisions

```bash
# Database choices
git adr search "database OR postgres OR mysql OR mongo"

# API decisions
git adr search "API OR REST OR GraphQL"

# Framework decisions
git adr search "framework OR library"
```

### Architecture Patterns

```bash
# Microservices
git adr search "microservice OR service OR monolith"

# Caching
git adr search "cache OR redis OR memcached"

# Authentication
git adr search "auth OR authentication OR OAuth"
```

### Status Queries

```bash
# All active decisions
git adr list --status accepted

# Decisions needing review
git adr list --status proposed

# Historical decisions
git adr list --status superseded
```

## Regex Patterns

When users need complex matching:

```bash
# Multiple terms
git adr search "post.*SQL|MySQL" --regex

# Specific patterns
git adr search "version.*[0-9]+\.[0-9]+" --regex

# Word boundaries
git adr search "\bAPI\b" --regex
```

## Search Result Interpretation

### Single Match

```
Found 1 ADR matching "postgresql":

• 20250115-use-postgresql [accepted]
  Use PostgreSQL for primary database
  > "...chose **PostgreSQL** for its robust JSONB support..."
```

### Multiple Matches

```
Found 3 ADRs matching "database":

• 20250115-use-postgresql [accepted] - primary database
• 20250110-redis-cache [accepted] - caching layer
• 20241220-schema-migrations [superseded] - migrations

Show specific ADR: `git adr show {id}`
```

### No Matches

```
No ADRs matching "kubernetes"

Suggestions:
• Try broader terms: "container", "orchestration"
• Check spelling
• List all: `git adr list`
```

## Advanced Filters

### Date Range

```bash
# Recent decisions (list only)
git adr list --since 2025-01-01

# Specific period
git adr list --since 2024-06-01 --until 2024-12-31
```

### Combined Filters

```bash
# Accepted security decisions
git adr list --status accepted --tag security

# Recent proposed
git adr list --status proposed --since 2025-01-01
```

## Tips

1. **Start broad**, narrow with filters
2. Use **synonyms**: "database" or "data store" or "persistence"
3. **Quote phrases**: `git adr search "REST API"` vs individual words
4. Use **--context** to see surrounding text
5. Follow up with `show` for full content
