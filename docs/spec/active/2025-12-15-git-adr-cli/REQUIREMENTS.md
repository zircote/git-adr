---
document_type: requirements
project_id: SPEC-2025-12-15-001
version: 1.0.0
last_updated: 2025-12-15T00:30:00Z
status: draft
---

# git-adr CLI - Product Requirements Document

## Executive Summary

**git-adr** is a command-line tool implemented as a git extension that manages Architecture Decision Records (ADRs) by storing them in git notes rather than traditional file-based storage. This approach keeps ADRs synchronized with your codebase's history without polluting the working tree, enables distributed collaboration without merge conflicts, and provides a first-class git-native experience.

The **core differentiator** is git notes-based storage. Without this, the tool has no reason to exist - file-based ADR tools already serve that purpose adequately.

## Problem Statement

### The Problem

Existing ADR tools store records as files, creating three fundamental problems:

1. **Repository pollution**: `docs/adr/*.md` files clutter the working tree and require separate navigation from the code they document.

2. **Merge conflicts**: Sequential numbering schemes (0001, 0002) cause conflicts when multiple developers create ADRs concurrently.

3. **Disconnection from commits**: ADRs describe decisions that affect specific code changes, yet existing tools don't associate records with the commits implementing those decisions.

### Impact

Development teams lose architectural context over time. Running `git log` shows code changes but not the reasoning behind them. New team members struggle to understand why certain technical choices were made.

### Current State

Teams either:
- Use file-based tools (adr-tools, log4brains) and accept the limitations
- Don't document decisions at all
- Rely on tribal knowledge that doesn't scale

Git notes exist specifically for commit metadata but have no mature ADR tooling leveraging them.

## Goals and Success Criteria

### Primary Goal

Enable development teams to document architectural decisions as git notes, making decisions **invisible in the working tree but visible in history**.

### Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Command success rate | > 99% | Automated testing |
| Average command latency | < 200ms | Performance benchmarks |
| Test coverage | > 90% | pytest-cov |
| Zero data loss incidents | 0 | Production monitoring |
| Type checking | 100% pass | mypy --strict |
| Security scan | 0 critical/high | bandit, pip-audit |

### Non-Goals (Explicit Exclusions)

- Multi-repository ADR federation (deferred to future versions)
- Real-time collaboration features (beyond git's native capabilities)
- GUI/web interface (CLI only; export to HTML for viewing)
- Replacing git's native notes commands (complementing, not replacing)

## User Analysis

### Primary Users

| User Type | Needs | Context |
|-----------|-------|---------|
| Development teams | Document decisions alongside code | Daily workflow |
| Platform/DevOps engineers | Track infrastructure decisions | Configuration changes |
| Architects | Document cross-cutting concerns | System design |
| OSS maintainers | Lightweight decision logging | Contributor onboarding |

### User Stories

#### Core Workflow
1. As a developer, I want to create an ADR linked to my current commit so that future readers understand why changes were made.
2. As a tech lead, I want to list all ADRs filtered by status so that I can review pending proposals.
3. As a new team member, I want an onboarding guide through key decisions so that I can understand the architecture quickly.
4. As a maintainer, I want ADRs to sync with remotes so that all team members have access.

#### Discovery
5. As a developer, I want to search ADRs by keyword so that I can find relevant prior decisions.
6. As an architect, I want to see which commits implement a decision so that I can trace impact.
7. As a reviewer, I want to see ADRs in git log output so that context is visible during code review.

#### AI-Assisted
8. As a developer, I want AI to draft an ADR from my recent commits so that documentation is faster.
9. As a tech lead, I want AI to suggest improvements to proposed ADRs so that quality improves.
10. As a team, I want natural language queries against our ADR knowledge base so that we can ask "why did we choose X?"

#### Integration
11. As a team, I want ADRs visible in our GitHub/GitLab wiki so that non-CLI users can read them.
12. As an ops engineer, I want to export ADR metrics for dashboards so that we can track decision velocity.

## Functional Requirements

### Must Have (P0) - Core Commands

| ID | Requirement | Rationale | Acceptance Criteria |
|----|-------------|-----------|---------------------|
| FR-001 | `git adr init` initializes ADR tracking | Foundation for all other commands | Creates `refs/notes/adr` namespace, stores config, configures fetch/push |
| FR-002 | `git adr new <title>` creates ADR | Primary creation workflow | Generates ID, creates template, opens editor, stores as note; supports `--file <path>` and stdin input; editor fallback chain (vim→nano→vi) |
| FR-003 | `git adr list` displays all ADRs | Discovery and overview | Shows ID, status, date, title; supports filtering by status/tag/date |
| FR-004 | `git adr show <id>` displays ADR | Reading individual records | Renders markdown with syntax highlighting, shows linked commits |
| FR-005 | `git adr edit <id>` modifies ADR | Iteration on decisions | Opens in editor, updates note, preserves history |
| FR-006 | `git adr search <query>` finds ADRs | Discovery by content | Full-text search, highlighted snippets, regex support |
| FR-007 | `git adr link <id> <commit>` associates commits | Bidirectional traceability | Updates ADR metadata, enables discovery from either direction |
| FR-008 | `git adr supersede <id> <title>` replaces ADR | Decision evolution | Creates new ADR with supersedes reference, updates original status |
| FR-009 | `git adr log` shows annotated git log | Contextual history | Wraps `git log --show-notes=refs/notes/adr` with formatting |
| FR-010 | `git adr sync` pushes/pulls notes | Distributed collaboration | Handles push, pull, merge with configurable strategies |
| FR-011 | `git adr config` manages settings | Customization | Get/set/list config options, supports global and local |

### Must Have (P0) - Multi-Format Support

| ID | Requirement | Rationale | Acceptance Criteria |
|----|-------------|-----------|---------------------|
| FR-020 | MADR 4.0 format (default) | Industry standard | Full template with options analysis, consequences, confirmation |
| FR-021 | Nygard original format | Simplicity | Title, Status, Context, Decision, Consequences |
| FR-022 | Y-Statement format | Conciseness | Single-sentence decision format |
| FR-023 | Alexandrian pattern format | Pattern language | Forces, Problem, Solution, Resulting Context |
| FR-024 | Business Case template | Executive decisions | Financial impact, risk assessment, approval workflow |
| FR-025 | Planguage format | Quality focus | Measurable criteria (Must/Plan/Wish) |
| FR-026 | Custom template registration | Flexibility | User-provided templates via config |
| FR-027 | `git adr convert <id> --to <format>` | Migration | Converts between formats preserving content |

### Must Have (P0) - Storage Architecture

| ID | Requirement | Rationale | Acceptance Criteria |
|----|-------------|-----------|---------------------|
| FR-030 | ADRs stored in `refs/notes/adr` | Core differentiator | Notes attached to root tree object |
| FR-031 | Artifacts in `refs/notes/adr-artifacts` | Diagrams/images | Separate namespace for binary content |
| FR-032 | Index note for ADR listing | Performance | YAML index with all ADR metadata |
| FR-033 | `git adr attach <id> <file>` | Visual documentation | Stores artifact, updates ADR reference |
| FR-034 | `git adr artifacts <id>` | Discovery | Lists attached artifacts |
| FR-035 | `git adr artifact-get <id> <name>` | Extraction | Exports artifact to file |
| FR-036 | `git adr artifact-rm <id> <name>` | Cleanup | Removes artifact reference |
| FR-037 | Artifact size limits | Repository health | Warn >1MB, refuse >10MB (configurable) |

### Should Have (P1) - AI Features

| ID | Requirement | Rationale | Acceptance Criteria |
|----|-------------|-----------|---------------------|
| FR-101 | `git adr draft <title>` AI-guided creation | Accelerate authoring | Interactive elicitation by default; asks problem, options, drivers, consequences; generates complete ADR; `--batch` for one-shot mode |
| FR-102 | `git adr suggest <id>` improvements | Quality improvement | Suggests context/options/consequences |
| FR-103 | `git adr summarize` period summary | Team communication | Natural language summary of recent decisions |
| FR-104 | `git adr ask <question>` Q&A | Knowledge retrieval | Queries ADR corpus, cites sources |
| FR-105 | OpenAI provider support | Primary provider | GPT-4, GPT-4-mini, o3 models |
| FR-106 | Anthropic provider support | Secondary provider | Claude opus/sonnet/haiku models |
| FR-107 | Multi-provider support | Flexibility | Google, Bedrock, Azure, OpenRouter |
| FR-108 | Ollama local provider | Privacy/offline | Local model execution |
| FR-109 | Provider configuration | User choice | `git adr config --set ai.provider` |

### Should Have (P1) - Wiki Integration

| ID | Requirement | Rationale | Acceptance Criteria |
|----|-------------|-----------|---------------------|
| FR-120 | `git adr wiki-init` setup | Initialization | Detects forge, creates wiki structure |
| FR-121 | `git adr wiki-sync` publish | Visibility | Syncs ADRs to wiki with indexes |
| FR-122 | GitHub wiki support | Market coverage | Clone/write/push to .wiki.git |
| FR-123 | GitLab wiki support | Market coverage | Clone/write/push to .wiki.git |
| FR-124 | Auto-generated indexes | Navigation | All ADRs, by-status, by-tag pages |
| FR-125 | Sidebar navigation | UX | Platform-specific sidebar generation |
| FR-126 | Bidirectional sync | Web editing | Pull wiki edits back to notes |
| FR-127 | Optional commit pointers | Awareness | Brief comments on linked commits |
| FR-128 | CI/CD workflows | Automation | GitHub Actions, GitLab CI templates |

### Should Have (P1) - Analytics & Reporting

| ID | Requirement | Rationale | Acceptance Criteria |
|----|-------------|-----------|---------------------|
| FR-140 | `git adr report` dashboard | Insight | Terminal/HTML/JSON/Markdown output |
| FR-141 | `git adr stats` quick summary | At-a-glance | Total, by-status, velocity |
| FR-142 | `git adr metrics` export | Integration | JSON, Prometheus, CSV formats |
| FR-143 | Decision velocity tracking | Trends | Decisions per period |
| FR-144 | High-impact ADR identification | Priority | By linked commit count |
| FR-145 | Team analytics (`--team`) | Collaboration | Per-contributor metrics |
| FR-146 | Attention needed alerts | Maintenance | Stale proposals, deprecated refs |

### Nice to Have (P2) - Onboarding & Export

| ID | Requirement | Rationale | Acceptance Criteria |
|----|-------------|-----------|---------------------|
| FR-201 | `git adr onboard` wizard | New team members | Interactive guided tour |
| FR-202 | Role-based paths | Relevance | Developer/reviewer/architect tracks |
| FR-203 | Progress tracking | Completion | Track which ADRs user has read |
| FR-204 | `git adr export` formats | Documentation | HTML, JSON, Markdown, docx |
| FR-205 | `git adr import` migration | Adoption | Import from file-based ADRs |
| FR-206 | log4brains HTML compatibility | Familiarity | Similar visual output |
| FR-207 | Mermaid diagram rendering | Visualization | Render .mermaid to SVG |

## Non-Functional Requirements

### Performance

| Requirement | Target |
|-------------|--------|
| `git adr list` (1000 ADRs) | < 500ms |
| `git adr show` | < 100ms |
| `git adr new` (excluding editor) | < 200ms |
| `git adr search` | < 1s |
| Memory usage | < 100MB typical |

### Security

| Requirement | Implementation |
|-------------|----------------|
| No credential storage | Inherit git's credential system |
| API key handling | Git config (not in notes), env vars |
| Input sanitization | Validate all user input |
| Dependency audit | pip-audit in CI |
| Static analysis | bandit security scanner |
| No dynamic code execution | Safe YAML loading only |

### Scalability

| Scenario | Target |
|----------|--------|
| ADRs per repository | 10,000+ |
| Artifact size | 10MB max per artifact |
| Concurrent users | Git's native concurrency |
| Repository size impact | Minimal (notes are compressed) |

### Reliability

| Requirement | Implementation |
|-------------|----------------|
| Data integrity | Leverage git's content-addressable storage |
| Graceful degradation | Work offline, sync when connected |
| Error recovery | Clear error messages, no data corruption |
| Backup | Standard git backup (notes included in clone) |

### Maintainability

| Requirement | Target |
|-------------|--------|
| Test coverage | > 90% |
| Type coverage | 100% (mypy --strict) |
| Documentation | All public APIs documented |
| Code style | ruff enforcement |

### Usability

| Requirement | Implementation |
|-------------|----------------|
| Shell completion | Bash/Zsh/Fish via typer |
| Colorized output | rich library, respects NO_COLOR |
| Pager integration | Automatic for long output |
| Short aliases | n=new, l=list, s=search, e=edit |
| Helpful errors | Suggestions for common mistakes |

## Technical Constraints

### Technology Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Language | Python 3.11+ | Team expertise, ecosystem |
| CLI framework | typer | Type hints, auto-completion, built on click |
| Git operations | subprocess | Industry standard, zero deps, full parity |
| Markdown parsing | python-frontmatter, mistune | YAML frontmatter + rendering |
| Output formatting | rich | Modern terminal UI |
| AI abstraction | langchain-core | Multi-provider support |
| Testing | pytest, pytest-cov | Standard, comprehensive |
| Linting | ruff | Fast, comprehensive |
| Type checking | mypy (strict) | Catch errors early |

### Package Extras

| Extra | Dependencies | Use Case |
|-------|--------------|----------|
| (core) | typer, rich, python-frontmatter, mistune | Basic functionality |
| `[ai]` | langchain-core, langchain-openai, langchain-anthropic, langchain-google-genai, langchain-aws, langchain-ollama | AI features |
| `[wiki]` | PyGithub, python-gitlab | Commit pointer comments (optional) |
| `[export]` | python-docx, mermaid-py | Enhanced exports |
| `[all]` | All above | Full feature set |

### Compatibility

| Platform | Support |
|----------|---------|
| macOS | Full |
| Linux | Full |
| Windows | Full (with Git for Windows) |
| Python 3.11 | Full |
| Python 3.12 | Full |
| Python 3.13 | Full |

## Dependencies

### Internal Dependencies

- Existing CLI skeleton (to be migrated from click to typer)
- Test infrastructure (pytest fixtures for git repos)

### External Dependencies

| Dependency | Purpose | Version |
|------------|---------|---------|
| git | Core operations | >= 2.25 |
| typer | CLI framework | >= 0.9.0 |
| rich | Terminal formatting | >= 13.0 |
| python-frontmatter | YAML parsing | >= 1.0 |
| mistune | Markdown rendering | >= 3.0 |

### Optional Dependencies (AI)

| Dependency | Purpose | Provider |
|------------|---------|----------|
| langchain-openai | OpenAI provider | OpenAI |
| langchain-anthropic | Anthropic provider | Anthropic |
| langchain-google-genai | Google provider | Google |
| langchain-aws | Bedrock provider | AWS |
| langchain-ollama | Local provider | Ollama |

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Notes not synced by users | High | High | Auto-configure fetch/push in `init`, clear warnings |
| Notes lost on rebase | Medium | High | Auto-configure rewriteRef, document behavior |
| GitHub/GitLab don't display notes | Certain | Medium | Wiki sync feature, comprehensive export |
| Large artifacts bloat repo | Medium | Medium | Separate namespace, size limits, warnings |
| AI provider API changes | Medium | Low | Abstraction via langchain, version pinning |
| Merge conflicts in index | Low | Medium | cat_sort_uniq strategy for index notes |

## Open Questions

All major questions resolved during requirements elicitation.

## Appendix

### Glossary

| Term | Definition |
|------|------------|
| ADR | Architecture Decision Record |
| MADR | Markdown Architectural Decision Records (format) |
| Git notes | Git's native metadata system for annotating objects |
| refs/notes/adr | The git reference where ADRs are stored |
| Root tree | The top-level tree object of a repository |

### References

- [Product Brief](../../../git-adr-product-brief.md)
- [MADR 4.0 Template](https://adr.github.io/madr/)
- [Git Notes Documentation](https://git-scm.com/docs/git-notes)
- [Typer Documentation](https://typer.tiangolo.com/)
