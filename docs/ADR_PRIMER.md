# ADR Primer: Introduction to Architecture Decision Records

This guide introduces Architecture Decision Records (ADRs) for those new to the concept, explaining what they are, why they matter, and how to use them effectively with git-adr.

## Table of Contents

- [What are Architecture Decision Records?](#what-are-architecture-decision-records)
- [Why Document Decisions?](#why-document-decisions)
- [When to Write an ADR](#when-to-write-an-adr)
- [ADR Lifecycle](#adr-lifecycle)
- [Common Mistakes](#common-mistakes)
- [Quick Start with git-adr](#quick-start-with-git-adr)
- [Further Reading](#further-reading)

---

## What are Architecture Decision Records?

An **Architecture Decision Record** (ADR) is a short document that captures a significant decision made during a project, along with the context and consequences of that decision.

Think of ADRs like a **captain's log** or **project logbook**. Just as a ship's captain records important events, course changes, and the reasoning behind navigation decisions, ADRs record the important choices your team makes about how to build your software.

Each ADR answers three fundamental questions:

1. **What was the situation?** (Context)
2. **What did we decide?** (Decision)
3. **What happens because of this decision?** (Consequences)

Here is a simple example:

```markdown
# Use PostgreSQL for Primary Database

## Status
Accepted

## Context
We need a database for our new e-commerce application. We expect
moderate traffic initially but want room to grow. Our team has
experience with relational databases.

## Decision
We will use PostgreSQL as our primary database.

## Consequences
- We get ACID compliance and strong data integrity
- The team can leverage existing SQL knowledge
- We need to manage database backups and scaling ourselves
- Switching to a NoSQL database later would require migration effort
```

ADRs exist because software projects accumulate decisions over time. Six months from now, no one will remember why you chose one approach over another. ADRs preserve that institutional knowledge.

---

## Why Document Decisions?

### Onboarding New Team Members

When a new developer joins your team, they face a mountain of questions: Why is the code structured this way? Why did we pick this framework? Why not use that popular library everyone talks about?

Without ADRs, new team members must either:
- Interrupt senior developers with endless questions
- Make assumptions that may be wrong
- Repeat research that was already done

With ADRs, they can read the decision records and understand the reasoning. Instead of "That's just how we do things here," you can point them to ADR-007 where the team documented the trade-offs.

**Example conversation without ADRs:**
> "Why do we use message queues instead of direct API calls between services?"
> "I don't know, it was like that when I joined."

**Example conversation with ADRs:**
> "Why do we use message queues instead of direct API calls?"
> "Check ADR-012. We chose async messaging for resilience during the payment service outage in March. Direct calls were cascading failures across services."

### Understanding Historical Context

Software is full of decisions that seem strange in hindsight. A workaround that made sense two years ago might look like bad code today. Without context, developers may "fix" something that was actually intentional, reintroducing bugs that were already solved.

ADRs preserve the **why** behind decisions:

- Why we accepted a known limitation
- What constraints existed at the time
- What alternatives we considered and rejected
- What we expected to change in the future

This historical context transforms "Who wrote this garbage?" into "Oh, this was a deliberate trade-off because of deadline pressure for the product launch."

### Preventing Decision Repetition

Have you ever been in a meeting where someone proposes an idea, and three people say "We discussed this before"—but no one can remember what was decided or why?

ADRs prevent this cycle of relitigating settled decisions. When someone asks "Why don't we switch to GraphQL?", you can reference the existing ADR that evaluated GraphQL, REST, and gRPC. Maybe the decision should be revisited—circumstances change—but at least you are starting from a documented baseline rather than from scratch.

This saves enormous amounts of time and meeting fatigue. It also creates a clear path for changing decisions: rather than endlessly debating, you can write a new ADR that supersedes the old one.

---

## When to Write an ADR

### Good Candidates for ADRs

Write an ADR when the decision is **significant**, **structural**, or **hard to reverse**. Here are common categories:

**Technology Choices**
- Which database to use (PostgreSQL vs. MongoDB vs. DynamoDB)
- Which programming language for a new service
- Which cloud provider (AWS vs. GCP vs. Azure)
- Which web framework (Django vs. FastAPI vs. Flask)

**Architecture Patterns**
- Monolith vs. microservices
- Event-driven vs. request-response
- REST vs. GraphQL vs. gRPC
- Serverless vs. containers vs. VMs

**Design Decisions**
- Authentication strategy (JWT vs. sessions vs. OAuth)
- Caching approach (Redis vs. Memcached vs. in-memory)
- How to handle file uploads
- Multi-tenancy approach

**Trade-off Decisions**
- Consistency vs. availability (CAP theorem)
- Build vs. buy for a component
- Technical debt acceptance for deadline
- Performance optimization vs. code simplicity

**Standards and Conventions**
- API versioning strategy
- Error handling patterns
- Logging and observability approach
- Testing strategy

### Not Every Decision Needs an ADR

ADRs are for **significant** decisions. Do not document every small choice—that creates noise that obscures the important decisions.

**Skip ADRs for:**

- **Trivial choices**: Variable naming, code formatting (use a linter), file organization within a module
- **Easily reversible decisions**: Which npm package to use for date formatting, which icon set to pick
- **Temporary solutions**: Quick fixes you plan to replace soon (though you might document the "real" solution)
- **Personal preferences**: IDE choice, local development setup
- **Well-established patterns**: Following your language's standard conventions

**A useful heuristic**: If reversing the decision would take less than a day and affect only one developer, you probably do not need an ADR. If reversing it would take a week and require coordinating multiple people, you probably do.

---

## ADR Lifecycle

ADRs are not static documents. They have a lifecycle that reflects how decisions evolve over time.

### Status Transitions

```
                    +------------+
                    |  Proposed  |
                    +-----+------+
                          |
            +-------------+-------------+
            |                           |
            v                           v
     +------+------+            +-------+------+
     |   Accepted  |            |   Rejected   |
     +------+------+            +--------------+
            |
            |  (time passes, circumstances change)
            |
     +------+------+---------------+
     |                             |
     v                             v
+----+-------+            +--------+-----+
| Deprecated |            |  Superseded  |
+------------+            +--------------+
```

### Status Definitions

**Proposed**
The decision is under discussion. The ADR documents what is being considered but has not been approved yet. This status is useful for getting feedback before committing to a direction.

**Accepted**
The team has agreed to this decision. It is now the official approach. Most ADRs will spend the majority of their life in this status.

**Rejected**
The proposed decision was not accepted. Keeping rejected ADRs is valuable—they document paths you deliberately chose not to take, so future team members do not waste time re-evaluating them.

**Deprecated**
The decision is no longer relevant or recommended. Perhaps the project no longer uses this technology, or the feature was removed. The ADR remains as historical context.

**Superseded**
A newer decision has replaced this one. The superseding ADR should link back to this one, and this one should link forward to the new ADR. This creates a clear chain of how decisions evolved.

### When to Deprecate vs. Supersede

**Use Deprecated when:**
- The feature or technology no longer exists in your system
- The decision became irrelevant due to external changes
- You are not replacing it with a different decision

Example: "Use Flash for interactive components" becomes deprecated because Flash no longer exists.

**Use Superseded when:**
- You are making a new, different decision about the same topic
- The old decision was valid but circumstances changed
- You want to maintain a clear decision history

Example: "Use MySQL for database" is superseded by "Use PostgreSQL for database" when you migrate.

When superseding, always:
1. Create the new ADR first
2. Update the old ADR's status to "Superseded by ADR-XXX"
3. Include a link in the new ADR saying "Supersedes ADR-YYY"

---

## Common Mistakes

### Too Detailed

**The problem**: Writing a specification instead of a decision. The ADR becomes a 20-page document covering implementation details, API contracts, and database schemas.

**Why it hurts**: Long ADRs do not get read. The decision gets buried under implementation details that will become outdated. Maintenance becomes a burden.

**Better approach**: Keep ADRs focused on the *decision* and its *rationale*. Save implementation details for design documents, code comments, or wikis. An ADR should typically be 1-2 pages.

**Signs you are too detailed:**
- The ADR takes more than 15 minutes to read
- You are including code samples longer than 10 lines
- You are documenting API endpoints or database columns
- The ADR needs a table of contents

### Too Brief

**The problem**: The ADR states a decision but provides no context or reasoning.

**Example of too brief:**
```markdown
# Use Redis

## Decision
We will use Redis.
```

**Why it hurts**: Without context, future readers cannot evaluate whether the decision still makes sense. They cannot understand what alternatives were considered or what constraints drove the choice.

**Better approach**: Always include the context (what problem you were solving), alternatives considered, and why you chose this option over others.

**Signs you are too brief:**
- The Context section is one sentence
- You have not mentioned any alternatives
- Someone reading it would ask "But why?"
- The Consequences section is empty

### Not Updating Status

**The problem**: ADRs remain in "Accepted" status forever, even when the decision no longer applies or has been replaced.

**Why it hurts**: Stale ADRs mislead new team members. They might think a deprecated approach is still recommended. It erodes trust in the ADR system.

**Better approach**: When you make architectural changes, check whether any existing ADRs need status updates. Include ADR review in your regular maintenance tasks. When decommissioning a system, find its related ADRs.

With git-adr, you can easily search and update:
```bash
# Find ADRs about the old system
git adr search "legacy-service"

# Update the status
git adr edit 20230115-use-legacy-service
```

### Writing After the Fact

**The problem**: Decisions are made in meetings or Slack conversations. The ADR is written weeks later (or never) when someone finally gets around to documenting.

**Why it hurts**: Critical context is lost. The "why" fades from memory. Alternative options and their trade-offs are forgotten. The ADR becomes a retroactive justification rather than genuine documentation.

**Better approach**: Write the ADR as part of making the decision. Use "Proposed" status to draft it before the decision is final. The act of writing often clarifies thinking and surfaces concerns.

**Practical tips:**
- Start the ADR when you start researching options
- Use the ADR as the basis for decision meetings
- Block time for documentation as part of the project
- Make ADR creation part of your definition of done

---

## Quick Start with git-adr

Ready to start using ADRs? Here is a 5-minute tutorial to get you going.

### Step 1: Install git-adr

```bash
pip install git-adr
```

Or with uv:

```bash
uv tool install git-adr
```

### Step 2: Initialize in Your Repository

Navigate to your git repository and initialize ADR tracking:

```bash
cd your-project
git adr init
```

This creates the first ADR documenting your decision to use Architecture Decision Records. You can view it with:

```bash
git adr list
```

### Step 3: Create Your First ADR

Create an ADR for a decision you need to make (or have already made):

```bash
git adr new "Use PostgreSQL for primary database"
```

This opens your editor with a template. Fill in the sections:

- **Context**: Why are you making this decision? What is the situation?
- **Decision**: What did you decide?
- **Consequences**: What are the positive, negative, and neutral outcomes?

Save and close the editor. Your ADR is now stored in git notes.

### Step 4: View Your ADRs

List all ADRs:

```bash
git adr list
```

Show a specific ADR:

```bash
git adr show 20240115-use-postgresql
```

Search across all ADRs:

```bash
git adr search "database"
```

### Step 5: Link ADR to Implementation

When you commit code that implements a decision, link the ADR:

```bash
# After committing your implementation
git adr link 20240115-use-postgresql HEAD
```

Now you can see which commits implement which decisions:

```bash
git adr log
```

### Step 6: Sync with Your Team

Push ADRs to your remote so teammates can access them:

```bash
git adr sync push
```

And pull ADRs others have created:

```bash
git adr sync pull
```

### Bonus: Create a Superseding ADR

When decisions change, create a superseding ADR:

```bash
git adr supersede 20240115-use-postgresql "Migrate to CockroachDB for global distribution"
```

This automatically:
- Creates a new ADR
- Links it to the old one
- Updates the old ADR's status

---

## Further Reading

### Essential Resources

- [Michael Nygard: Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) - The original blog post that started it all (2011). Nygard introduced the concept and basic template that most ADR formats build upon.

- [MADR - Markdown Any Decision Records](https://adr.github.io/madr/) - A popular, more detailed ADR template specification. MADR extends the original format with sections for decision drivers, options considered, and decision outcomes.

- [ADR GitHub Organization](https://adr.github.io/) - Community resources, tooling, and templates for ADRs.

### Additional Reading

- [Thoughtworks Technology Radar: Lightweight ADRs](https://www.thoughtworks.com/radar/techniques/lightweight-architecture-decision-records) - Industry recognition of ADRs as a recommended practice.

- [ADR Tools by Nat Pryce](https://github.com/npryce/adr-tools) - The original command-line tools for managing ADRs as files.

- [Architecture Decision Records in Action](https://resources.sei.cmu.edu/library/asset-view.cfm?assetid=497744) - Carnegie Mellon SEI paper on ADRs in practice.

### Templates

git-adr supports multiple templates out of the box:

| Template | Description | Best For |
|----------|-------------|----------|
| `madr` | Full template with options analysis | Most decisions (default) |
| `nygard` | Original minimal format | Simple, quick decisions |
| `y-statement` | Single-sentence format | Very brief records |
| `alexandrian` | Pattern-language inspired | Pattern-heavy teams |
| `business` | Extended business case | Stakeholder-facing decisions |
| `planguage` | Quality-focused measurable | Quantifiable decisions |

To use a different template:

```bash
git adr config adr.template nygard
```

---

*Happy documenting! Remember: the best time to write an ADR is when you make the decision. The second best time is now.*
