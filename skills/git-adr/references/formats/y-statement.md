# Y-Statement Format

The Y-Statement format, created by Olaf Zimmermann, captures architecture decisions in a single structured sentence. It forces clarity by constraining the decision to one statement that includes context, problem, decision, goal, and tradeoff.

## When to Use

- **Rapid documentation**: Capture decisions quickly during meetings
- **ADR indexes**: Summarize longer ADRs in a scannable format
- **Decision logs**: Maintain lightweight decision trails
- **Retrospectives**: Document past decisions without extensive write-up
- **Early-stage projects**: When full ADRs feel premature

## The Pattern

```
In the context of [situation],
facing [problem],
we decided [decision],
to achieve [goal],
accepting [tradeoff].
```

Each clause serves a purpose:
- **Context**: The situation, project state, or architectural scope
- **Problem**: The specific challenge or question being addressed
- **Decision**: The choice made (use active voice: "we decided to use X")
- **Goal**: The benefit or quality attribute being optimized
- **Tradeoff**: The accepted downside or compromise

## Examples

### Database Selection
In the context of a new e-commerce platform with unpredictable traffic patterns, facing the need for horizontal scalability and flexible schema evolution, we decided to use MongoDB as the primary database, to achieve elastic scaling and rapid feature iteration, accepting eventual consistency and the learning curve for the team.

### API Design
In the context of a public developer API with diverse client capabilities, facing the tension between bandwidth efficiency and client simplicity, we decided to implement GraphQL alongside REST endpoints, to achieve flexible data fetching for sophisticated clients while maintaining simplicity for basic integrations, accepting increased backend complexity and dual maintenance burden.

### Authentication
In the context of a B2B SaaS product serving enterprise customers, facing requirements for SSO integration and compliance audit trails, we decided to adopt Auth0 as our identity provider, to achieve rapid SSO implementation and SOC2-ready audit logging, accepting vendor dependency and per-user pricing at scale.

### Deployment Strategy
In the context of a monolithic application being migrated to microservices, facing the need for zero-downtime deployments with limited DevOps capacity, we decided to use blue-green deployments on Kubernetes, to achieve instant rollback capability and deployment confidence, accepting doubled infrastructure costs during deployment windows.

## More Information

Expand a Y-Statement into a full ADR when:
- Multiple stakeholders need detailed rationale
- The decision requires formal approval
- Alternatives analysis should be preserved
- The tradeoffs need quantification

Reference the Y-Statement in the full ADR's summary section.

## Tips for Clarity

**Force specificity**: If any clause feels vague, the decision needs more thought.

**Test completeness**: Can someone unfamiliar with the project understand the tradeoff?

**One decision per statement**: Split compound decisions into separate y-statement.

**Active voice**: "we decided to use X" not "X was chosen"

**Quantify when possible**: "accepting 200ms added latency" over "accepting some latency"
