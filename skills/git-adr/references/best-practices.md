# ADR Best Practices Guide

Reference for teaching users effective Architecture Decision Record practices.

---

## What is an ADR?

An **Architecture Decision Record** (ADR) is a short document capturing a significant decision, its context, and consequences. Each ADR answers three questions:

1. **What was the situation?** (Context)
2. **What did we decide?** (Decision)
3. **What happens because of this decision?** (Consequences)

ADRs preserve institutional knowledge so future team members understand not just *what* was decided, but *why*.

---

## When to Write an ADR

### Good Candidates

Write an ADR when the decision is **significant**, **structural**, or **hard to reverse**.

| Category | Examples |
|----------|----------|
| Technology Choices | Database, language, cloud provider, framework |
| Architecture Patterns | Monolith vs microservices, REST vs GraphQL |
| Design Decisions | Auth strategy, caching, multi-tenancy, API versioning |
| Trade-offs | Consistency vs availability, build vs buy, tech debt |

### When NOT to Write an ADR

Skip ADRs for decisions that are trivial, easily reversible, or temporary:
- Variable naming or code formatting (use a linter)
- Which utility package to use for minor tasks
- Quick fixes you plan to replace soon
- Personal preferences (IDE, local setup)

**Heuristic**: If reversing takes less than a day and affects only one developer, skip it. If it takes a week and requires coordination, write one.

---

## What Makes a Good ADR

### Clear Context

Explain the situation: problem, constraints, stakeholders, timeline.

**Poor**: "We need a database."
**Good**: "We're building an e-commerce platform expecting 10K DAU. Team has strong SQL experience. Need ACID compliance for orders."

### Explicit Decision

Be specific and actionable.

**Vague**: "We'll use a modern approach."
**Explicit**: "We will use PostgreSQL 15 on AWS RDS with Multi-AZ deployment."

### Documented Consequences

| Type | Question |
|------|----------|
| Positive | What do we gain? What becomes easier? |
| Negative | What do we lose? What becomes harder? |
| Neutral | What changes without clear good/bad value? |

### Alternatives Considered

Document options evaluated and why rejected. This prevents relitigating and helps others understand the decision space.

---

## Common Mistakes

### Too Detailed

**Problem**: 20-page specification with implementation details, API contracts, schemas.

**Signs**: Takes 15+ minutes to read. Code samples over 10 lines. Documents endpoints or columns.

**Fix**: Focus on decision and rationale. Target 1-2 pages. Save details for design docs.

### Too Brief

**Problem**: Decision with no context or reasoning.

```markdown
# Use Redis
## Decision
We will use Redis.
```

**Signs**: One-sentence context. No alternatives. Reader asks "But why?"

**Fix**: Always include context, alternatives, and reasoning.

### Not Updating Status

**Problem**: ADRs stay "Accepted" when obsolete or replaced.

**Fix**: Review ADRs during architectural changes. Update when decommissioning systems.

### Writing After the Fact

**Problem**: Decisions in meetings/chat, ADRs written weeks later.

**Fix**: Write ADR during decision-making. Use "Proposed" status during research.

---

## ADR Lifecycle

### Status Transitions

```
             Proposed
                |
        +-------+-------+
        |               |
    Accepted        Rejected
        |
        +-------+-------+
        |               |
   Deprecated      Superseded
```

### Status Definitions

| Status | Meaning |
|--------|---------|
| Proposed | Under discussion, not yet approved |
| Accepted | Team agreed, official approach |
| Rejected | Not accepted, kept for history |
| Deprecated | No longer relevant, tech removed |
| Superseded | Replaced by newer decision |

### Deprecate vs Supersede

**Deprecated**: Feature/technology no longer exists; not replacing with a new decision.
*Example*: "Use Flash" - deprecated because Flash is gone.

**Superseded**: Making new decision about same topic; old was valid but circumstances changed.
*Example*: "Use MySQL" superseded by "Use PostgreSQL" during migration.

**Supersession process**:
1. Create new ADR
2. Update old: "Superseded by ADR-XXX"
3. New includes: "Supersedes ADR-YYY"

```bash
git adr supersede 20240101-use-mysql "Migrate to PostgreSQL"
```

---

## Quality Checklist

Before finalizing an ADR:

- [ ] Context explains situation and constraints
- [ ] Decision is explicit and actionable
- [ ] Consequences categorized (positive/negative/neutral)
- [ ] 2-3 alternatives considered
- [ ] Status is appropriate
- [ ] Title clearly identifies subject
- [ ] Length is 1-2 pages

---

## Teaching Tips

When helping users write ADRs:

1. **Start with the problem**: What are they solving?
2. **Explore constraints**: Deadlines, team skills, existing systems
3. **Surface alternatives**: What else was considered?
4. **Probe consequences**: What becomes harder or easier?
5. **Check completeness**: Run through quality checklist

**Common questions**:
- "What should I include?" - Quality checklist
- "Is this too detailed?" - Focus on decision, not implementation
- "Should I write an ADR?" - Apply the heuristic
- "How do I update old decisions?" - Deprecate vs supersede
