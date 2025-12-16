# Alexandrian ADR Format

Pattern-based format inspired by Christopher Alexander's "A Pattern Language" (1977).
Emphasizes identifying competing forces and connecting decisions to a broader pattern catalog.

## When to Use Alexandrian Format

- **Reusable patterns**: Decision may apply across projects/teams
- **Complex trade-offs**: Multiple competing constraints need explicit analysis
- **System-wide impact**: Decision affects multiple components or quality attributes
- **Design patterns**: Implementing well-known architectural or design patterns
- **Knowledge transfer**: Building organizational pattern libraries

## Template

```markdown
# ADR-{ID}: {Title}

## Status
{Proposed | Accepted | Deprecated | Superseded}

## Context
{Describe the situation prompting this decision. Include technical landscape,
business drivers, and any relevant history.}

## Forces

The following forces are in tension:

- **{Force 1}**: {Description of constraint or requirement}
- **{Force 2}**: {Description of competing constraint}
- **{Force 3}**: {Additional force if applicable}

{Explain how these forces conflict or create tension.}

## Problem

**Therefore:** {State the core problem as a single, clear question or statement.
This should emerge naturally from the forces described above.}

## Solution

**We will** {describe the chosen approach}.

{Provide implementation details:}
- {Key implementation point 1}
- {Key implementation point 2}
- {Configuration or setup requirements}

## Resulting Context

After applying this solution:

**Benefits:**
- {Positive outcome 1}
- {Positive outcome 2}

**Liabilities:**
- {Trade-off or limitation 1}
- {New constraint introduced}

**Neutral:**
- {Unchanged aspect worth noting}

## Related Patterns

- **{Pattern Name}**: {How it relates - enables, conflicts, complements}
- **{ADR-XXX}**: {Link to related decision in this repository}
```

## Example: Circuit Breaker Pattern

```markdown
# ADR-0012: Implement Circuit Breaker for Payment Service

## Status
Accepted

## Context
Our e-commerce platform processes 50,000+ daily transactions through an external
payment gateway. During Black Friday 2024, gateway latency spikes caused request
queuing, thread pool exhaustion, and cascading failures across the checkout flow.
Users experienced 30-second timeouts and abandoned carts increased 40%.

## Forces

The following forces are in tension:

- **Availability**: Users expect checkout to work even when payment provider degrades
- **Consistency**: We must not confirm orders without successful payment authorization
- **Resource efficiency**: Thread pools and connections are finite; blocking calls exhaust them
- **User experience**: Fast feedback preferred over long waits with uncertain outcomes
- **Observability**: Operations team needs visibility into payment health

These forces conflict because maximizing availability (accepting orders optimistically)
risks consistency violations, while strict consistency (synchronous blocking) causes
resource exhaustion during outages.

## Problem

**Therefore:** How do we prevent payment gateway failures from cascading into
system-wide outages while maintaining transactional integrity?

## Solution

**We will** implement the Circuit Breaker pattern using Resilience4j for all
payment gateway calls.

Configuration:
- **Failure threshold**: 50% failures over 10-call sliding window
- **Open duration**: 30 seconds before half-open probe
- **Timeout**: 5 seconds per request (down from 30s default)
- **Fallback**: Queue order for async retry, notify user of delay

Implementation:
- Wrap PaymentGatewayClient with CircuitBreaker decorator
- Expose circuit state via /actuator/health and Prometheus metrics
- Alert on-call when circuit opens via PagerDuty integration
- Implement OrderRetryService for queued orders

## Resulting Context

After applying this solution:

**Benefits:**
- Fast failure (5s max) prevents thread exhaustion
- System remains responsive during gateway outages
- Automatic recovery when gateway stabilizes
- Clear operational visibility into payment health

**Liabilities:**
- Orders may be delayed when circuit is open
- Additional complexity in order state machine (pending-payment state)
- Requires tuning thresholds based on production traffic patterns

**Neutral:**
- No change to payment provider contract or API usage

## Related Patterns

- **Retry Pattern**: Used within closed circuit; circuit breaker prevents retry storms
- **Bulkhead Pattern**: Consider for isolating payment threads from other services
- **Timeout Pattern**: Implemented as part of this solution (5s limit)
- **ADR-0008**: Async order processing - enables the fallback queue mechanism
- **ADR-0015**: Observability standards - defines metric naming conventions used here
```

## Tips for Alexandrian Format

### Identifying Forces

Forces are constraints that pull the solution in different directions:

| Force Type | Examples |
|------------|----------|
| Quality attributes | Performance vs. security, consistency vs. availability |
| Business constraints | Time-to-market vs. technical debt, cost vs. features |
| Technical constraints | Existing stack, team expertise, dependencies |
| Organizational | Team structure, compliance requirements, vendor contracts |

**Test your forces**: If all forces point to the same solution, you either have
an obvious decision (no ADR needed) or you have not identified the real tensions.

### Pattern Thinking

1. **Name it**: Good patterns have memorable names (Circuit Breaker, not "error handling improvement")
2. **Make it reusable**: Write so another team could apply the same pattern
3. **Connect the catalog**: Link to related patterns to build institutional knowledge
4. **State the problem clearly**: The "Therefore" statement should feel inevitable after reading Forces
5. **Acknowledge liabilities**: Every pattern has trade-offs; hiding them reduces trust

### Common Mistakes

- Listing forces without explaining their tension
- Skipping "Related Patterns" (misses knowledge-building opportunity)
- Writing solution before fully articulating the problem
- Treating forces as requirements rather than competing constraints
