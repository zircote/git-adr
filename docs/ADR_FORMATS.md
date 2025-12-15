# ADR Format Guide

This guide documents all built-in ADR (Architecture Decision Record) formats supported by git-adr, helping you choose the right format for your team.

## Table of Contents

- [What is an ADR Format?](#what-is-an-adr-format)
- [Choosing a Format](#choosing-a-format)
- [Built-in Formats](#built-in-formats)
  - [MADR (Markdown Any Decision Records)](#madr-markdown-any-decision-records)
  - [Nygard (Original ADR)](#nygard-original-adr)
  - [Y-Statement](#y-statement)
  - [Alexandrian](#alexandrian)
  - [Business Case](#business-case)
  - [Planguage](#planguage)
- [Custom Templates](#custom-templates)
- [References](#references)

---

## What is an ADR Format?

An ADR format is a standardized template structure that defines how architectural decisions are documented. While all formats capture the essential elements of a decision (context, decision, consequences), they differ in:

- **Verbosity**: How much detail they encourage
- **Structure**: Which sections they include and how they are organized
- **Focus**: Whether they emphasize technical details, business value, or measurable outcomes
- **Audience**: Who the primary readers are expected to be

git-adr supports six built-in formats, each designed for different contexts and team needs. You can also create custom templates for organization-specific requirements.

---

## Choosing a Format

### Format Comparison Table

| Format | Best For | Complexity | Team Size | Decision Type | Time to Write |
|--------|----------|------------|-----------|---------------|---------------|
| **MADR** | General purpose, option analysis | Medium | Any | Technical | 15-30 min |
| **Nygard** | Simple, quick decisions | Low | Small-Medium | Technical | 5-15 min |
| **Y-Statement** | Rapid documentation, summaries | Very Low | Any | Any | 2-5 min |
| **Alexandrian** | Design patterns, complex systems | High | Medium-Large | Design/Architecture | 30-60 min |
| **Business Case** | Stakeholder approval, budget requests | Medium-High | Enterprise | Business/Technical | 30-60 min |
| **Planguage** | Performance, SLA, quality requirements | High | Enterprise | Non-functional | 20-45 min |

### Decision Tree

```
Start Here
    |
    v
Is this a quick, low-impact decision?
    |
    +-- YES --> Y-Statement (fast documentation)
    |
    +-- NO --> Does it need business/financial justification?
                    |
                    +-- YES --> Business Case
                    |
                    +-- NO --> Does it involve measurable quality targets?
                                    |
                                    +-- YES --> Planguage
                                    |
                                    +-- NO --> Are you evaluating multiple options?
                                                    |
                                                    +-- YES --> MADR
                                                    |
                                                    +-- NO --> Is it a recurring pattern?
                                                                    |
                                                                    +-- YES --> Alexandrian
                                                                    |
                                                                    +-- NO --> Nygard (simple & universal)
```

---

## Built-in Formats

### MADR (Markdown Any Decision Records)

**Origin**: Developed by Oliver Kopp and contributors at the ADR GitHub organization (2017-present). MADR (Markdown Any Decision Records) is the most widely adopted ADR format in the open-source community.

**Description**: MADR provides a comprehensive structure for documenting decisions that require evaluation of multiple options. It encourages systematic analysis by dedicating sections to decision drivers, options considered, and explicit decision outcomes with justification.

**When to Use**:
- Teams that need to evaluate and document multiple alternatives
- Organizations requiring audit trails of option analysis
- Decisions where stakeholders need to understand "why not" the alternatives
- Any team size, but particularly valuable for distributed teams

**Example**:

```markdown
# Use PostgreSQL as Primary Database

## Status

accepted

## Context

Our e-commerce platform needs a primary database for storing product catalog,
customer data, and order history. The system must handle 10,000 concurrent
users with sub-100ms query response times for product searches.

## Decision

We will use PostgreSQL 16 as our primary database.

## Consequences

### Positive

- ACID compliance ensures data integrity for financial transactions
- Rich JSON support (JSONB) allows flexible product attribute storage
- Mature ecosystem with extensive tooling and community support
- Cost-effective with no licensing fees

### Negative

- Horizontal scaling requires additional architecture (Citus, read replicas)
- Team needs training on PostgreSQL-specific features
- Migration from existing MySQL requires careful planning

### Neutral

- Standard SQL syntax familiar to most developers
- Managed options available on all major cloud providers

## Options Considered

### Option 1: PostgreSQL

Open-source relational database with advanced features.

**Pros:**
- Excellent JSON support for flexible schemas
- Strong consistency guarantees
- Free and open source
- Rich extension ecosystem (PostGIS, pg_trgm, etc.)

**Cons:**
- Horizontal scaling is more complex than NoSQL options
- Requires more upfront schema design

### Option 2: MongoDB

Document-oriented NoSQL database.

**Pros:**
- Flexible schema for evolving data models
- Built-in horizontal scaling
- Good for hierarchical data

**Cons:**
- Eventual consistency by default
- Higher operational complexity for transactions
- Licensing concerns with SSPL

### Option 3: MySQL

Traditional open-source relational database.

**Pros:**
- Team has existing expertise
- Simple replication setup
- Wide hosting availability

**Cons:**
- Weaker JSON support than PostgreSQL
- Fewer advanced features
- Oracle ownership concerns

## Decision Outcome

Chosen option: "PostgreSQL", because it provides the best balance of data
integrity (critical for e-commerce transactions), flexibility (JSONB for
product attributes), and cost-effectiveness. The team's SQL expertise
transfers well, and the rich extension ecosystem supports future features
like full-text search and geolocation.

## More Information

- [PostgreSQL 16 Release Notes](https://www.postgresql.org/docs/16/release-16.html)
- [JSONB Performance Guide](https://www.postgresql.org/docs/current/datatype-json.html)
- Related: ADR-003 (Use Redis for session caching)
```

**Pros**:
- Structured option analysis encourages thorough evaluation
- Clear decision outcome with explicit justification
- Separated positive/negative/neutral consequences aid impact assessment
- Well-suited for code review and async decision-making

**Cons**:
- Can feel heavy for simple or obvious decisions
- Requires more time investment than simpler formats
- Risk of "analysis paralysis" with too many options

---

### Nygard (Original ADR)

**Origin**: Created by Michael Nygard in his seminal 2011 blog post "Documenting Architecture Decisions." This is the original ADR format that sparked the entire movement.

**Description**: The Nygard format is intentionally minimal, containing only the essential sections needed to capture a decision: Status, Context, Decision, and Consequences. Its simplicity makes it accessible and reduces barriers to adoption.

**When to Use**:
- Teams new to ADRs who want a gentle starting point
- Quick decisions that don't require extensive option analysis
- Small teams with high-bandwidth communication
- Decisions where the "why" matters more than comparing alternatives
- Retrofitting decisions that were made verbally

**Example**:

```markdown
# Use Feature Flags for Gradual Rollouts

## Status

accepted

## Context

We are releasing new features to production weekly, but full releases
are risky. Our last release caused a 2-hour outage when a new payment
integration failed at scale. We need a way to control feature exposure
without deploying new code, enabling quick rollback and gradual rollout.

## Decision

We will implement feature flags using LaunchDarkly for controlling
feature rollouts. All new user-facing features must be wrapped in
feature flags during the initial release period. Flags will be
removed after 90 days of stable operation.

## Consequences

Gradual rollouts reduce blast radius of bugs from 100% of users to a
controllable percentage. Quick disable without deployment means
faster incident response. However, feature flags add code complexity
and require discipline to clean up old flags. We will need to train
the team on flag hygiene and establish a flag lifecycle policy. Cost
of LaunchDarkly is approximately $500/month for our team size.
```

**Pros**:
- Extremely low barrier to entry
- Fast to write (5-15 minutes)
- Easy to read and review
- Focuses on what matters: context and consequences

**Cons**:
- No structure for comparing options
- May be too brief for complex decisions
- Consequences aren't categorized (positive vs negative)

---

### Y-Statement

**Origin**: Developed by Olaf Zimmermann and colleagues at the University of Applied Sciences of Eastern Switzerland, documented in the paper "Architectural Decision Modeling with the Y-Statement" (2013).

**Description**: The Y-Statement is an ultra-concise single-sentence format that captures a decision in one structured statement. It forces clarity by constraining the author to express the decision in a specific grammatical pattern.

**When to Use**:
- Rapid documentation of decisions during fast-moving development
- Summary records when full documentation isn't practical
- Index or catalog of decisions (with links to detailed docs elsewhere)
- Teams that value brevity and resist heavyweight processes
- Capturing verbal decisions before they're forgotten

**Example**:

```markdown
# Adopt TypeScript for Frontend Development

## Status

accepted

## Decision

In the context of maintaining a large React codebase with 50+ components,
facing increasing bugs from type mismatches and difficulty onboarding new developers,
we decided to migrate to TypeScript with strict mode enabled,
to achieve compile-time type safety and improved IDE support,
accepting the initial migration effort of approximately 2 weeks and ongoing type definition maintenance.

## More Information

- Migration will follow the gradual adoption strategy: new files in TS, convert existing on touch
- ESLint rules will enforce TypeScript best practices
- See internal wiki for TypeScript style guide
- Related: ADR-007 (Use React 18)
```

**Pros**:
- Fastest format to write (2-5 minutes)
- Forces clarity through constraint
- Easy to scan when reviewing many decisions
- Low documentation overhead encourages actual use

**Cons**:
- Limited space for nuance or detailed analysis
- Can feel forced for complex, multi-faceted decisions
- "More Information" section often becomes a catch-all
- Tradeoff statement may oversimplify consequences

---

### Alexandrian

**Origin**: Inspired by Christopher Alexander's "A Pattern Language" (1977), a seminal work in architecture that influenced software design patterns. The Alexandrian format treats decisions as patterns, emphasizing the forces at play and the resulting context.

**Description**: The Alexandrian format uses a pattern-language style with rich context about competing forces. It's particularly suited for decisions that establish reusable patterns or address recurring architectural challenges. The format explicitly separates problem identification from solution and emphasizes the transformation of context.

**When to Use**:
- Establishing reusable architectural patterns
- Complex systems with many competing constraints
- Teams with strong architecture practices
- Decisions that will be referenced as precedents for future decisions
- Design decisions in domain-driven design contexts

**Example**:

```markdown
# Circuit Breaker for External Service Calls

## Status

accepted

## Context

Our platform integrates with 12 external services (payment gateways, shipping
providers, inventory systems). These services have varying reliability:
average availability ranges from 99.5% to 99.99%. When an external service
degrades, our application threads block waiting for timeouts, leading to
resource exhaustion and cascading failures affecting unrelated functionality.

## Forces

- **Resilience**: The system must remain functional even when dependencies fail
- **User Experience**: Users should not wait indefinitely for failing operations
- **Resource Efficiency**: Thread pools and connections are finite resources
- **Visibility**: Operations needs awareness of service health in real-time
- **Recovery**: The system should automatically resume normal operation when services recover
- **Simplicity**: Developers should not need to implement custom retry logic per integration

## Problem

How do we prevent failures in external services from cascading into our
application while allowing automatic recovery when services become healthy?

## Solution

Implement the Circuit Breaker pattern for all external service integrations
using resilience4j library. Each external service gets a dedicated circuit
breaker with the following configuration:

- **Failure threshold**: 50% failure rate over 10-request window
- **Open state duration**: 30 seconds before attempting half-open
- **Half-open requests**: Allow 3 requests to test recovery
- **Timeout**: 5 seconds per request before counting as failure

Fallback behaviors will be defined per service:
- Payment: Queue for retry, notify user of delay
- Shipping: Use cached rates, flag for refresh
- Inventory: Serve stale data with warning badge

## Resulting Context

External service failures are isolated to their specific functionality. The
application maintains responsiveness for unaffected features. Operations has
real-time dashboards showing circuit breaker states. The pattern is reusable:
adding new integrations follows the established template with only
configuration changes. Trade-off: some requests during the "open" state will
fail fast even if the service has recovered, until the half-open test passes.

## Related Patterns

- ADR-005: Bulkhead pattern for thread pool isolation
- ADR-008: Timeout configuration standards
- ADR-012: Retry policy with exponential backoff
- External: [Circuit Breaker (Martin Fowler)](https://martinfowler.com/bliki/CircuitBreaker.html)
```

**Pros**:
- Rich context helps readers understand the full picture
- Forces makes constraints explicit and visible
- Problem/Solution separation clarifies thinking
- Excellent for establishing reusable patterns
- "Resulting Context" emphasizes transformation

**Cons**:
- Takes longer to write thoroughly
- "Forces" section can be difficult to identify comprehensively
- May feel overly formal for simple decisions
- Requires familiarity with pattern thinking

---

### Business Case

**Origin**: Derived from traditional business case documentation practices, adapted for architectural decisions that require business stakeholder approval or have significant financial implications.

**Description**: The Business Case format extends technical ADRs with business-focused sections including executive summary, financial impact, risk assessment, and formal approval tracking. It bridges the gap between technical decisions and business governance.

**When to Use**:
- Decisions requiring budget approval
- Changes with significant cost implications (infrastructure, licensing)
- Enterprise environments with formal governance processes
- Decisions affecting multiple business units or stakeholders
- Vendor selection or technology procurement
- Compliance-related architectural changes

**Example**:

```markdown
# Migrate from On-Premise to AWS Cloud Infrastructure

## Status

proposed

## Executive Summary

We propose migrating our on-premise data center infrastructure to AWS over
18 months. This migration addresses capacity constraints limiting our
growth, reduces infrastructure management overhead, and improves disaster
recovery capabilities. The estimated 3-year total cost of ownership shows
15% savings compared to data center expansion, with break-even at month 22.

## Business Context

Our current data center reaches 85% capacity during peak seasons, requiring
$2.1M in hardware expansion to support projected 40% growth over 3 years.
The single-site architecture creates unacceptable business continuity risk:
estimated $50K/hour revenue loss during outages. Cloud migration aligns with
the board's digital transformation initiative and enables the international
expansion planned for Q3 2026.

## Problem Statement

Physical infrastructure constraints limit our ability to scale with demand,
increase operational costs through manual capacity management, and expose the
business to availability risks that impact customer trust and revenue.

## Proposed Solution

Phased migration to AWS using a lift-and-shift approach for stateless services
and re-architecture for stateful components. Multi-AZ deployment in us-east-1
with disaster recovery in us-west-2. Managed services (RDS, ElastiCache) to
reduce operational overhead.

## Options Analysis

### Option 1: AWS Migration (Recommended)

**Cost:** $180K migration + $45K/month operational
**Time:** 18 months
**Risk:** Medium

**Pros:**
- Elastic scaling eliminates capacity constraints
- Multi-region DR improves availability to 99.99%
- Reduced ops overhead (estimate 2 FTE savings)
- Pay-as-you-go aligns cost with revenue

**Cons:**
- Migration risk during transition period
- Team needs cloud skills training
- Vendor lock-in concerns
- Ongoing cost optimization required

### Option 2: Data Center Expansion

**Cost:** $2.1M capital + $35K/month operational
**Time:** 12 months
**Risk:** Low

**Pros:**
- Team has existing expertise
- Full control over hardware
- Predictable costs after initial investment
- No vendor dependency

**Cons:**
- Large upfront capital requirement
- Single point of failure remains
- Ongoing hardware refresh cycles
- Limited geographic flexibility

### Option 3: Hybrid Cloud

**Cost:** $1.4M capital + $55K/month operational
**Time:** 24 months
**Risk:** High

**Pros:**
- Gradual transition reduces risk
- Maintains some on-premise control
- Enables cloud experimentation

**Cons:**
- Complexity of managing two environments
- Higher combined operational cost
- Delayed benefits realization
- Requires dual skill sets

## Financial Impact

| Category | Year 1 | Year 2 | Year 3 | 3-Year Total |
|----------|--------|--------|--------|--------------|
| Migration Costs | $180K | $0 | $0 | $180K |
| AWS Infrastructure | $540K | $540K | $594K | $1,674K |
| Training | $50K | $20K | $10K | $80K |
| Personnel Savings | ($0) | ($150K) | ($200K) | ($350K) |
| **Net Cost** | **$770K** | **$410K** | **$404K** | **$1,584K** |

Compared to data center expansion: $2,100K + ($420K * 3) = $3,360K
**3-year savings: $1,776K (53%)**

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Migration delays | Medium | Medium | Phased approach, parallel running |
| Data loss during migration | Low | High | Full backups, validation checkpoints |
| Performance degradation | Medium | Medium | Load testing, right-sizing analysis |
| Cost overrun | Medium | Low | Reserved instances, cost alerts |
| Skill gaps | High | Medium | Training program, AWS partner support |

## Implementation Plan

**Phase 1 (Months 1-6)**: Development and staging environments
- AWS account setup and security baseline
- CI/CD pipeline migration
- Team training (AWS Solutions Architect certification)

**Phase 2 (Months 7-12)**: Stateless services migration
- API services, web frontends
- Blue-green deployment capability
- Monitoring and alerting setup

**Phase 3 (Months 13-18)**: Stateful services and cutover
- Database migration with zero-downtime approach
- Final production cutover
- Data center decommissioning

## Approval

| Role | Name | Date | Decision |
|------|------|------|----------|
| Executive Sponsor | | | |
| CTO | | | |
| CFO | | | |
| VP Engineering | | | |
| Security Officer | | | |
```

**Pros**:
- Bridges technical and business stakeholders
- Explicit financial analysis supports budget requests
- Risk assessment demonstrates due diligence
- Approval table creates accountability
- Well-suited for governance-heavy environments

**Cons**:
- Heavyweight for routine technical decisions
- Financial estimates may become outdated
- Approval section can create bureaucratic delays
- May require business analyst support to complete

---

### Planguage

**Origin**: Developed by Tom Gilb, a pioneer in software metrics and quantified requirements. Planguage (Planning Language) is a formal specification language described in his book "Competitive Engineering" (2005).

**Description**: Planguage focuses on quantified, measurable outcomes using a specific vocabulary: Scale (unit of measure), Meter (measurement method), Past (baseline), Must (minimum acceptable), Plan (target), and Wish (stretch goal). It's ideal for non-functional requirements and quality attributes.

**When to Use**:
- Performance and scalability decisions
- SLA and reliability targets
- Security and compliance requirements
- Quality attribute tradeoffs
- Decisions that need objective success criteria
- Benchmarking and capacity planning

**Example**:

```markdown
# API Response Time Performance Standards

## Status

accepted

## Tag

ADR-2025-001-PERF

## Gist

Establish quantified response time targets for customer-facing APIs to ensure
consistent user experience and contractual SLA compliance.

## Background

Customer complaints about slow page loads increased 40% in Q4. Exit surveys
cite "website speed" as the #2 reason for cart abandonment. Our enterprise
contracts include SLA penalties for API latency exceeding agreed thresholds.
Current monitoring shows inconsistent performance with P95 latency varying
from 180ms to 2.3s depending on endpoint and load.

## Scale

Response time measured in milliseconds (ms) from request receipt to response
completion at the API gateway, excluding network transit time to client.

## Meter

- **Primary**: Datadog APM P95 latency aggregated per endpoint per hour
- **Secondary**: Synthetic monitoring from 5 global regions every 60 seconds
- **Validation**: Monthly load tests simulating 2x peak traffic

## Past

Current state (Q4 2024 average):
- Product listing API: P50=145ms, P95=890ms, P99=2,100ms
- Cart operations API: P50=210ms, P95=1,200ms, P99=3,400ms
- Checkout API: P50=340ms, P95=1,800ms, P99=4,200ms

## Must

Minimum acceptable levels (hard constraints, SLA penalties apply):
- All customer-facing APIs: P95 < 1,000ms
- Checkout API: P95 < 800ms (contractual requirement)
- Error rate: < 0.1% for 5xx responses

Failure to meet "Must" levels triggers immediate incident response and
customer communication per SLA terms.

## Plan

Target levels for Q2 2025 (expected outcome with planned optimizations):
- Product listing API: P95 < 200ms
- Cart operations API: P95 < 300ms
- Checkout API: P95 < 400ms
- All APIs: P99 < 1,000ms

Achievement unlocks: Premium tier API product launch, enterprise contract
renewals at improved rates.

## Wish

Stretch goals (ideal state, enables competitive differentiation):
- All customer-facing APIs: P95 < 100ms
- Real-time inventory: P95 < 50ms
- Global edge caching: P95 < 30ms for cached content

Achievement enables: "Fastest in industry" marketing position, premium
pricing for API products.

## Assumptions

- Database query optimization project completes by end of Q1
- CDN migration to Cloudflare provides 40% latency reduction for static assets
- No significant increase in data volume (< 20% growth)
- Redis cluster upgrade provides sufficient cache capacity
- Development team capacity of 2 engineers dedicated to performance

## Risks

| Risk | Impact on Plan | Mitigation |
|------|----------------|------------|
| Database optimization delayed | P95 targets slip 4-6 weeks | Parallel track with caching improvements |
| Traffic growth exceeds 20% | Must levels threatened | Auto-scaling headroom, capacity alerts |
| Third-party API latency | Checkout targets missed | Circuit breakers, async processing |
| Cache invalidation bugs | Stale data served | Comprehensive cache testing suite |
```

**Pros**:
- Objective, measurable success criteria
- Clear distinction between minimum acceptable and target outcomes
- Excellent for tracking progress over time
- Forces concrete thinking about what "good" means
- Supports data-driven decision review

**Cons**:
- Requires ability to measure what you specify
- Not suitable for qualitative or exploratory decisions
- Learning curve for Planguage vocabulary
- Can feel overly formal for small teams
- Metrics must be maintained and validated

---

## Custom Templates

git-adr supports custom templates for organizations with specific documentation requirements.

### Creating a Custom Template

1. **Create a template file** in your repository or a shared location:

```markdown
# {title}

## Status

{status}

## Your Custom Section

<!-- Your guidance here -->

## Another Section

<!-- More guidance -->
```

2. **Place template files** in one of these locations:
   - Repository: `.git-adr/templates/your-format.md`
   - User-level: `~/.config/git-adr/templates/your-format.md`
   - System-level: `/etc/git-adr/templates/your-format.md`

3. **Use your template** when creating ADRs:

```bash
git adr new "My Decision" --format your-format
```

### Template Variables

Templates support these placeholder variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `{title}` | ADR title | "Use PostgreSQL" |
| `{status}` | Current status | "proposed" |
| `{id}` | ADR identifier | "20250115-use-postgresql" |
| `{date}` | Creation date | "2025-01-15" |
| `{tags}` | Comma-separated tags | "database, infrastructure" |
| `{deciders}` | Decision makers | "Alice, Bob" |
| `{supersedes}` | ID of superseded ADR | "20240601-use-mysql" |

### Example: RFC-Style Template

For teams accustomed to RFC (Request for Comments) style documentation:

```markdown
# RFC: {title}

**RFC ID**: {id}
**Status**: {status}
**Author(s)**: {deciders}
**Created**: {date}
**Supersedes**: {supersedes}
**Tags**: {tags}

## Abstract

<!-- 2-3 sentence summary of the proposal -->

## Motivation

<!-- Why is this change necessary? What problem does it solve? -->

## Detailed Design

<!-- Technical details of the proposed solution -->

## Alternatives Considered

<!-- Other approaches that were evaluated -->

## Unresolved Questions

<!-- Open issues to be resolved during implementation -->

## Future Possibilities

<!-- Related features or extensions enabled by this decision -->
```

### Format Conversion

Convert existing ADRs to different formats:

```bash
# Convert a single ADR
git adr convert 20250115-use-postgresql --to madr

# The original is preserved; conversion creates a new version
```

---

## References

### Primary Sources

- [Michael Nygard: Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) - The original blog post that defined ADRs (2011)
- [MADR - Markdown Any Decision Records](https://adr.github.io/madr/) - Official MADR specification and templates
- [ADR GitHub Organization](https://adr.github.io/) - Community resources and tooling
- [Tom Gilb: Competitive Engineering](https://www.gilb.com/competitive-engineering) - Planguage methodology

### Academic Papers

- Zimmermann, O. et al. "Architectural Decision Modeling with the Y-Statement" (2013)
- Zdun, U. et al. "Sustainable Architectural Design Decisions" (IEEE Software, 2013)

### Further Reading

- [Thoughtworks Technology Radar: Lightweight ADRs](https://www.thoughtworks.com/radar/techniques/lightweight-architecture-decision-records)
- [Joel Parker Henderson: Architecture Decision Record](https://github.com/joelparkerhenderson/architecture-decision-record) - Comprehensive ADR resource
- [Christopher Alexander: A Pattern Language](https://en.wikipedia.org/wiki/A_Pattern_Language) - Inspiration for Alexandrian format

### Related git-adr Documentation

- [ADR Primer](ADR_PRIMER.md) - Introduction to ADRs for beginners
- [Commands Reference](COMMANDS.md) - Complete command documentation
- [Configuration Guide](CONFIGURATION.md) - git-adr configuration options
