# Planguage Format

Planguage (Planning Language) was developed by Tom Gilb for specifying quantified requirements. It forces precise, measurable definitions of quality attributes rather than vague statements like "the system should be fast."

## When to Use

- **Performance targets**: Response times, throughput, latency
- **Service Level Agreements**: Availability, uptime, error rates
- **Quality requirements**: Reliability, scalability, security metrics
- **Measurable outcomes**: Any decision with quantifiable success criteria

## Template

```markdown
# ADR: [Decision Title]

**Status**: [proposed | accepted | deprecated | superseded]
**Tag**: [Unique identifier, e.g., PERF-001, SLA-API-RESPONSE]

## Gist
[One sentence summary of what this requirement achieves]

## Background
[Context: business drivers, current pain points, stakeholder needs, constraints]

## Scale
[Unit of measurement: milliseconds, percentage, transactions/second, hours/month]

## Meter
[How to measure: tool, sampling frequency, test conditions, data source]

## Past
[Current baseline: measured value, date, conditions]

## Must
[Minimum acceptable level - failure to meet this is a defect]

## Plan
[Target level - realistic goal for this iteration]

## Wish
[Stretch goal - ideal performance if resources allow]

## Assumptions
[Conditions that must hold: load patterns, infrastructure, dependencies]

## Risks
[What could prevent targets: technical risks, constraints, external factors]
```

## Example: API Response Time

```markdown
# ADR: API Response Time Requirements

**Status**: accepted
**Tag**: PERF-API-001

## Gist
Define acceptable response times for the public REST API to ensure user satisfaction.

## Background
User research shows abandonment rates increase sharply when API responses exceed 500ms. Our current p95 latency of 800ms is causing customer complaints. Competitors advertise sub-200ms response times.

## Scale
Milliseconds of server response time (request received to response sent, excluding network).

## Meter
- **Tool**: Datadog APM with custom instrumentation
- **Sampling**: 100% of production requests
- **Metric**: p95 latency over 5-minute rolling windows

## Past
800ms (p95), measured 2025-01-10, production traffic at 50 RPS

## Must
- p95 <= 500ms
- p99 <= 1000ms
- Zero requests exceeding 5000ms

## Plan
- p95 <= 200ms
- p99 <= 500ms

## Wish
- p95 <= 100ms
- Consistent performance up to 500 RPS

## Assumptions
- Database optimization complete by Q1
- CDN caching enabled
- Peak traffic under 200 RPS

## Risks
- Legacy queries may resist optimization
- Third-party API calls add 100-200ms latency
- Budget constraints for infrastructure
```

## Tips for Quantifying Quality Attributes

1. **Start with outcomes**: Define what "good" looks like before deciding how to achieve it
2. **Use ranges**: Must/Plan/Wish levels acknowledge uncertainty and provide flexibility
3. **Make meters reproducible**: Anyone should get consistent results
4. **Document baselines**: You cannot improve what you have not measured
5. **Separate concerns**: Create distinct specs for different quality attributes
6. **Link to monitoring**: Connect specs to dashboards for continuous validation

## Common Quality Attributes

| Attribute | Example Scale | Example Meter |
|-----------|---------------|---------------|
| Availability | Percentage uptime | Pingdom, 1-minute intervals |
| Throughput | Requests/second | k6 load test, 10 minutes |
| Latency | Milliseconds p95 | APM, production traffic |
| Error rate | Percentage 5xx | Log aggregation, hourly |
| Recovery time | Minutes to restore | Incident tracking |
| Data freshness | Seconds since sync | Custom timestamp metric |
