---
project_id: SPEC-2025-12-15-001
project_name: "Decider Display Remediation"
slug: decider-display-remediation
status: completed
created: 2025-12-15T19:00:00Z
approved: 2025-12-15T20:20:00Z
started: 2025-12-15T20:20:00Z
completed: 2025-12-15T21:45:00Z
final_effort: "~5 hours"
outcome: success
expires: 2026-03-15T19:00:00Z
superseded_by: null
tags: [bug-fix, display, stakeholder-metadata, issue-15]
stakeholders: [Robert Allen <zircote@gmail.com>]
github_issue: 15
worktree:
  branch: plan/download-and-review-issue-15-a
  base_branch: main
last_updated: 2025-12-15T21:45:00Z
---

# Decider Display Remediation

## Overview

Remediation for GitHub Issue #15: The `show` command's markdown output does not display `deciders`, `consulted`, and `informed` fields in the ADR header panel. Scope expanded to include making deciders required, CLI support, interactive backfill, and MADR 4.0 compatibility.

## Problem Statement

When using `git adr show <id>`, the rich markdown panel displays tags, linked commits, and supersession info, but omits stakeholder metadata (deciders/consulted/informed) even though these fields are fully modeled and stored.

## Scope Summary

| Feature | Description |
|---------|-------------|
| Display Fix | Add deciders/consulted/informed to markdown panel |
| Required Field | Make deciders required for new ADRs |
| CLI Support | Add `--deciders` flag to `git adr new` |
| Interactive Prompt | Prompt for deciders on creation and empty viewing |
| MADR 4.0 | Support `decision-makers` field alias |

## Implementation Phases

1. **Phase 1**: Core Display Fix (3 tasks)
2. **Phase 2**: MADR 4.0 Compatibility (2 tasks)
3. **Phase 3**: CLI Enhancement (3 tasks)
4. **Phase 4**: Interactive Backfill (2 tasks)
5. **Phase 5**: Testing & Polish (3 tasks)

**Estimated Effort**: 4-6 hours

## Quick Links

- [Requirements](./REQUIREMENTS.md)
- [Architecture](./ARCHITECTURE.md)
- [Implementation Plan](./IMPLEMENTATION_PLAN.md)
- [GitHub Issue #15](https://github.com/zircote/git-adr/issues/15)
