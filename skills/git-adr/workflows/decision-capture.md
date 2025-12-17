# Decision Capture Workflow

Guided workflow for extracting architecture decisions from conversation context.

## Trigger Phrases

- "Record this decision"
- "Create an ADR for..."
- "Document this architecture decision"
- "We decided to..."
- "Let's record that we're using..."
- "ADR for {topic}"

## Capture Flow

```
Trigger Detected
    │
    ▼
┌─────────────────────────┐
│ Extract decision context│
│ from conversation       │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│ Read adr.template config│
│ (default: madr)         │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│ Ask clarifying questions│
│ if context insufficient │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│ Generate ADR draft      │
│ in configured format    │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│ Present for user review │
│ "Does this capture it?" │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│ Execute: git adr new    │
└─────────────────────────┘
```

## Context Extraction Questions

### Essential (always gather)

1. **What is the decision?** (one sentence)
2. **Why was this decided?** (context/constraints)
3. **What alternatives were considered?** (if any)

### Format-Specific (based on adr.template)

**MADR format:**
- What options were evaluated?
- What are the pros/cons of each?

**Business Case format:**
- Who are the stakeholders?
- What is the estimated cost/benefit?

**Alexandrian format:**
- What forces led to this decision?
- What is the resulting context?

## Draft Presentation Format

```markdown
## Draft ADR Preview

**Title:** {Generated title}
**Status:** proposed
**Date:** {today}

### Context
{Extracted from conversation}

### Decision
{Core decision statement}

### Consequences
{Positive, negative, neutral}

---
✅ Create this ADR?
✏️ Edit first?
❌ Cancel?
```

## User Confirmation Commands

After presenting draft:

| User Response | Action |
|---------------|--------|
| "yes" / "create" / "looks good" | `git adr new "{title}" --file draft.md` |
| "edit" / "change" | Ask what to modify |
| "cancel" / "no" | Abort creation |

## Example Conversation

**User:** "We just discussed using PostgreSQL instead of MySQL. Record this decision."

**Assistant:** "I'll create an ADR for this decision. Let me ask a few questions:

1. **Context**: What prompted this database choice? (e.g., existing infrastructure, team expertise)
2. **Alternatives**: Did you consider any options besides PostgreSQL and MySQL?
3. **Consequences**: Any concerns with PostgreSQL? (licensing, complexity, etc.)

Or I can draft based on our conversation and you can edit."

**User:** "Just draft it from what we discussed."

**Assistant:** [Generates draft, presents for review]

## Implementation Command

Once user approves:

```bash
# Create ADR with drafted content
git adr new "Use PostgreSQL for primary database" --batch << 'EOF'
---
title: Use PostgreSQL for primary database
date: 2025-01-15
status: proposed
---

## Context
...
EOF
```

## Notes

- Always present draft before creating
- Respect configured template format
- Link to relevant commits if discussed (`git adr link`)
- Suggest `proposed` status unless user confirms acceptance
