# MADR Format (Markdown Any Decision Records)

MADR is a lean template for capturing architectural decisions with structured option analysis. Version 4.0 provides a comprehensive yet flexible format suitable for documenting decisions that require explicit trade-off evaluation.

## When to Use MADR

**Best suited for:**
- Decisions requiring explicit comparison of multiple options
- Complex technical choices with significant trade-offs
- Team decisions needing documented rationale for stakeholders
- Situations where rejected alternatives should be preserved

**Consider simpler formats when:**
- Quick, obvious decisions with clear single choice
- Minor implementation details
- Time-sensitive documentation needs

## Template Structure

```markdown
# [ADR-NNNN] [Short Title of Decision]

## Status

[Proposed | Accepted | Deprecated | Superseded by ADR-XXXX]

## Context

[Describe the situation, forces at play, and why a decision is needed. Include relevant constraints, requirements, and stakeholder concerns. Be specific about the problem being solved.]

## Decision

[State the decision clearly and concisely. Start with "We will..." or "We decided to..."]

## Consequences

### Positive
- [Benefit 1]
- [Benefit 2]

### Negative
- [Drawback 1]
- [Drawback 2]

### Neutral
- [Side effect that is neither clearly positive nor negative]

## Options Considered

### Option 1: [Name]

[Brief description of this option]

**Pros:**
- [Advantage 1]
- [Advantage 2]

**Cons:**
- [Disadvantage 1]
- [Disadvantage 2]

### Option 2: [Name]

[Brief description of this option]

**Pros:**
- [Advantage 1]

**Cons:**
- [Disadvantage 1]

## Decision Outcome

[Explain why the chosen option was selected. Reference specific pros/cons that drove the decision. Note any close alternatives and why they were ultimately not chosen.]

## More Information

- **Participants:** [Names or roles involved in decision]
- **Date:** [YYYY-MM-DD]
- **Related ADRs:** [Links to related decisions]
- **References:** [External documentation, RFCs, articles]
```

## Example: Database Selection

```markdown
# ADR-0012 Use PostgreSQL for Primary Data Store

## Status

Accepted

## Context

Our application requires a persistent data store for user accounts, transactions, and analytics data. We expect to handle 10,000 concurrent users with sub-100ms query latency. The team has experience with both SQL and NoSQL databases. We need ACID compliance for financial transactions but also require flexible schema for evolving analytics requirements.

## Decision

We will use PostgreSQL as our primary data store, leveraging its JSONB capabilities for semi-structured data.

## Consequences

### Positive
- ACID compliance ensures transaction integrity
- JSONB provides schema flexibility without sacrificing query performance
- Strong ecosystem with mature tooling and cloud provider support
- Team already has PostgreSQL expertise

### Negative
- Horizontal scaling requires additional architecture (read replicas, sharding)
- JSONB queries are less performant than native document stores for deeply nested data

### Neutral
- Requires dedicated DBA attention as data volume grows

## Options Considered

### Option 1: PostgreSQL

Mature relational database with strong JSONB support for semi-structured data.

**Pros:**
- ACID compliant out of the box
- Excellent query optimizer and indexing options
- JSONB provides document-store flexibility
- Large community and extensive documentation

**Cons:**
- Horizontal scaling complexity
- Less native support for time-series data

### Option 2: MongoDB

Document-oriented database designed for flexible schemas and horizontal scaling.

**Pros:**
- Native document storage with flexible schemas
- Built-in horizontal scaling via sharding
- Strong aggregation pipeline

**Cons:**
- ACID compliance only at document level (multi-document transactions added later)
- Team would need training
- Higher operational complexity for transactions

### Option 3: CockroachDB

Distributed SQL database with PostgreSQL wire compatibility.

**Pros:**
- Automatic horizontal scaling
- Strong consistency guarantees
- PostgreSQL compatible syntax

**Cons:**
- Higher latency for single-node operations
- Smaller community and ecosystem
- Higher infrastructure costs

## Decision Outcome

PostgreSQL was selected because ACID compliance for financial transactions is non-negotiable, and the team's existing expertise reduces onboarding time. The JSONB capability adequately addresses our schema flexibility needs without introducing a second data store. While horizontal scaling will require future architectural work, our projected growth timeline allows us to address this incrementally.

CockroachDB was a close second, but the latency characteristics and smaller ecosystem were concerns for our timeline.

## More Information

- **Participants:** Platform Team, Data Engineering Lead
- **Date:** 2024-03-15
- **Related ADRs:** ADR-0008 (Caching Strategy), ADR-0015 (Read Replica Architecture)
- **References:** [PostgreSQL JSONB Performance](https://www.postgresql.org/docs/current/datatype-json.html)
```

## Writing Tips

1. **Context clarity**: Describe the problem before jumping to solutions. Include constraints and non-functional requirements.

2. **Option completeness**: Document at least 2-3 options including "do nothing" when applicable. This proves due diligence.

3. **Honest consequences**: List real negatives, not just positives. Future readers need to understand trade-offs.

4. **Specific pros/cons**: Avoid generic statements. "Fast" is weak; "Sub-10ms p99 latency" is strong.

5. **Decision rationale**: The Decision Outcome section should reference specific factors from Options Considered.

6. **Keep it scannable**: Use bullet points liberally. Busy engineers will skim before deep reading.

7. **Link extensively**: Reference related ADRs, external documentation, and benchmarks to support claims.
