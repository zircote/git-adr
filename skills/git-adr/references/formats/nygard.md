# Nygard ADR Format

The original Architecture Decision Record format, created by Michael Nygard in 2011.
A minimal, four-section structure designed for quick documentation of architectural decisions.

## When to Use Nygard Format

- **Quick decisions**: Document decisions efficiently without ceremony
- **Small teams**: Where extensive option analysis is discussed verbally
- **Simple context**: When the problem space is well understood
- **Iteration speed**: When you need to capture many decisions quickly
- **Retrofitting**: Documenting past decisions that are already implemented

Nygard is ideal when the decision is clear and you want to record it without overhead.

## Template

```markdown
# ADR-{ID}: {Title}

## Status

{Proposed | Accepted | Deprecated | Superseded by ADR-XXX}

## Context

{Describe the situation and forces at play. What is the issue? Why does it matter?
Keep this concise - focus on the essential facts that drive the decision.}

## Decision

{State what you have decided to do. Use active voice: "We will..."
Be specific about what is being adopted, built, or changed.}

## Consequences

{List the results of the decision - both positive and negative.
Include technical, organizational, and process implications.}
```

## Example

```markdown
# ADR-0003: Use PostgreSQL for Primary Database

## Status

Accepted

## Context

We need a relational database for our core application data. The team has
experience with both MySQL and PostgreSQL. Our data model includes JSON
documents and geographic queries. We anticipate moderate scale with complex
query patterns.

## Decision

We will use PostgreSQL as our primary database.

## Consequences

- Native JSON support simplifies our document storage needs
- PostGIS extension enables geographic queries without additional services
- Team members familiar with MySQL will need PostgreSQL training
- We gain access to advanced features like CTEs and window functions
- Hosting costs are comparable to MySQL alternatives
```

## Tips for Effective Nygard ADRs

1. **Context**: Focus on forces, not history. Answer "why now?" not "how we got here"
2. **Decision**: One sentence is ideal. If you need paragraphs, consider MADR format
3. **Consequences**: Include negatives - every decision has tradeoffs
4. **Status**: Update when decisions change; link to superseding ADRs
5. **Length**: A good Nygard ADR fits on one screen (under 30 lines of content)

## Comparison with Other Formats

| Aspect | Nygard | MADR |
|--------|--------|------|
| Sections | 4 | 8+ |
| Options analysis | Implicit | Explicit |
| Best for | Quick capture | Deliberation |
| Typical length | 15-30 lines | 50-100 lines |

Use Nygard when speed matters; switch to MADR when you need to document option analysis.
