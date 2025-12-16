# Business Case ADR Format

A formal decision format for stakeholder communication and executive approval. Bridges technical decisions with business impact through financial analysis and risk assessment.

## When to Use

- **Budget approval**: Decisions requiring capital or operational cost changes
- **Stakeholder decisions**: Cross-functional impact requiring executive sign-off
- **Enterprise governance**: Compliance with architectural review boards
- **Vendor selection**: Third-party products with contractual implications
- **Major migrations**: Platform changes with business continuity impact

## Template

```markdown
# ADR-{ID}: {Title}

**Status**: Proposed | Under Review | Approved | Rejected | Implemented

## Executive Summary
{2-3 sentences for executives. State decision, primary benefit, key risk.}

## Business Context
- Current capabilities and limitations
- Strategic initiatives this supports
- External factors (market, regulatory, competitive)

## Problem Statement
- What business capability is missing or underperforming?
- What is the cost of inaction?
- Who is affected and how?

## Proposed Solution
- High-level description (non-technical where possible)
- Key components or phases
- Dependencies and prerequisites

## Options Analysis

### Option 1: {Name} (Recommended)
| Dimension | Assessment |
|-----------|------------|
| Cost | {$X initial / $Y ongoing} |
| Timeline | {X months} |
| Risk Level | Low / Medium / High |
| Strategic Fit | {alignment with goals} |

**Pros**: {list}  **Cons**: {list}

### Option 2: {Name}
{Same table structure}

### Option 3: Do Nothing
{Cost of inaction, risk level, consequences}

## Financial Impact
| Category | Year 1 | Year 2 | Year 3 | Total |
|----------|--------|--------|--------|-------|
| Implementation Cost | | | | |
| Operational Savings | | | | |
| Revenue Impact | | | | |
| **Net Impact** | | | | |

**ROI**: {%}  **Payback Period**: {months}

## Risk Assessment
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| {Risk 1} | L/M/H | L/M/H | {strategy} |

## Implementation Plan
| Phase | Duration | Deliverables | Success Criteria |
|-------|----------|--------------|------------------|
| Phase 1 | {weeks} | {list} | {measurable} |

## Approval
| Role | Name | Decision | Date |
|------|------|----------|------|
| Technical Lead | | Recommend / Not Recommend | |
| Architecture Board | | Approve / Reject | |
| Finance | | Approve / Reject | |
| Executive Sponsor | | Approve / Reject | |
```

## Example: Cloud Database Migration

```markdown
# ADR-20250115-001: Migrate to Cloud-Managed PostgreSQL

**Status**: Under Review

## Executive Summary
Migrate self-managed MySQL to AWS Aurora PostgreSQL to reduce database administration by 60%, improve disaster recovery, and enable scaling for projected 3x growth. Primary risk is 4-hour migration downtime.

## Business Context
- Customer base growing 25% annually, straining database capacity
- DevOps spending 30% of time on DB maintenance vs. features
- Compliance audit identified disaster recovery gaps
- Digital transformation requires cloud-first architecture

## Problem Statement
Current MySQL cannot scale without major investment. DB admin consumes engineering resources. 4-hour RTO not achievable, creating compliance risk. Cost of inaction: $150K risk exposure + blocked initiatives.

## Proposed Solution
AWS Aurora PostgreSQL with multi-AZ deployment, automated backups, read replicas, and AWS DMS for migration.

## Options Analysis

### Option 1: AWS Aurora PostgreSQL (Recommended)
| Dimension | Assessment |
|-----------|------------|
| Cost | $45K initial / $120K/year |
| Timeline | 4 months |
| Risk Level | Medium |
| Strategic Fit | Aligns with cloud-first |

**Pros**: Auto-scaling, built-in HA, reduced admin  **Cons**: Vendor lock-in, migration effort

### Option 2: Upgrade Self-Managed MySQL
| Dimension | Assessment |
|-----------|------------|
| Cost | $200K initial / $80K/year |
| Timeline | 6 months |
| Risk Level | Medium |
| Strategic Fit | Does not advance cloud strategy |

### Option 3: Do Nothing
Cost: $80K/year + $150K risk. Consequences: Performance issues in 12 months, compliance findings.

## Financial Impact
| Category | Year 1 | Year 2 | Year 3 | Total |
|----------|--------|--------|--------|-------|
| Implementation | $45K | $0 | $0 | $45K |
| Operations | $120K | $130K | $145K | $395K |
| Admin Savings | ($60K) | ($80K) | ($80K) | ($220K) |
| Avoided Infra | $0 | ($200K) | $0 | ($200K) |
| **Net** | $105K | ($150K) | $65K | $20K |

**ROI**: 180%  **Payback**: 18 months

## Risk Assessment
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Extended downtime | Medium | High | Weekend migration, rollback plan |
| Data integrity | Low | High | Parallel validation, checksums |
| Team skill gap | Medium | Medium | Training, AWS support |

## Implementation Plan
| Phase | Duration | Deliverables | Success Criteria |
|-------|----------|--------------|------------------|
| Planning | 4 weeks | Migration runbook | Successful test migration |
| Development | 6 weeks | Schema conversion | All tests passing |
| Production | 2 weeks | Cutover, validation | Zero data loss, <4hr downtime |

## Approval
| Role | Name | Decision | Date |
|------|------|----------|------|
| Technical Lead | J. Chen | Recommend | 2025-01-10 |
| Architecture Board | | | |
| Executive Sponsor | | | |
```

## Tips for Technical-Business Communication

**For Technical Teams**:
- Lead with business outcomes, not technical features
- Translate: "99.99% uptime" = "less than 1 hour downtime per year"
- Quantify engineering time in dollars
- Connect technical debt to customer impact

**For Business Stakeholders**:
- Focus on Executive Summary, Financial Impact, Risk Assessment
- Ask why alternatives were rejected
- Verify success criteria are measurable
- Ensure rollback plans exist

**Common Pitfalls**:
- Optimistic timelines (add 30% buffer)
- Hidden costs (training, support, integration)
- Assuming "do nothing" costs nothing
