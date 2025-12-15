# Product Brief: git-adr

## Git Extension CLI for Architecture Decision Records via Git Notes

**Version:** 1.0 Draft  
**Date:** December 14, 2025  
**Author:** Bob (Epic Pastures / HMH DevOps)

---

## Executive Summary

**git-adr** is a command-line tool implemented as a git extension that manages Architecture Decision Records (ADRs) by storing them in git notes rather than traditional file-based storage. This approach keeps ADRs synchronized with your codebase's history without polluting the working tree, enables distributed collaboration without merge conflicts, and provides a first-class git-native experience similar to `log4brains` but with the persistence and portability benefits of git's built-in notes system.

---

## Problem Statement

### Current Pain Points

1. **File-based ADRs create noise** — Traditional ADR tools (adr-tools, log4brains) store records as markdown files in `docs/adr/` directories, adding to repository clutter and requiring separate tracking from the code they document.

2. **Disconnection from commits** — ADRs describe decisions that affect specific code changes, yet existing tools don't associate records with the commits that implement those decisions.

3. **Merge conflicts** — When multiple team members create ADRs concurrently, file-based numbering (0001, 0002, etc.) leads to conflicts and renumbering overhead.

4. **Lost context when browsing history** — Running `git log` shows code changes but not the architectural reasoning behind them; you must separately navigate to ADR files.

5. **Git notes remain underutilized** — Despite git notes being purpose-built for commit metadata, no mature tooling exists to leverage them for ADR management.

### Target Users

- Development teams practicing docs-as-code
- Platform/DevOps engineers managing infrastructure decisions
- Architects documenting cross-cutting concerns
- Open source maintainers wanting lightweight decision logging

---

## Solution Overview

**git-adr** stores ADRs as git notes attached to commits, providing:

- **Native git integration** — ADRs travel with repository history via `refs/notes/adr`
- **Commit association** — Each ADR links to the commit(s) implementing the decision
- **MADR-compatible format** — Uses the widely-adopted Markdown Architectural Decision Records template
- **log4brains-like UX** — Familiar commands (`init`, `new`, `list`, `show`, `search`)
- **Distributed collaboration** — Git notes merge strategies handle concurrent changes

---

## Feature Specification

### Core Commands

| Command | Purpose |
|---------|---------|
| `git adr init` | Initialize ADR tracking in repository |
| `git adr new` | Create a new ADR |
| `git adr list` | List all ADRs with filtering |
| `git adr show` | Display a specific ADR |
| `git adr search` | Full-text search across ADRs |
| `git adr edit` | Modify an existing ADR |
| `git adr link` | Associate ADR with commits |
| `git adr supersede` | Create replacement ADR |
| `git adr log` | Git log with ADR annotations |
| `git adr export` | Export to HTML/JSON/docx |
| `git adr import` | Import file-based ADRs |
| `git adr sync` | Push/pull notes to remotes |
| `git adr report` | **Dashboard & analytics** |
| `git adr onboard` | **Interactive learning wizard** |
| `git adr stats` | Quick statistics summary |
| `git adr config` | Manage configuration |
| **Artifact Commands** | |
| `git adr attach` | Attach diagram/image to ADR |
| `git adr artifacts` | List artifacts for an ADR |
| `git adr artifact-get` | Extract artifact to file |
| `git adr artifact-rm` | Remove artifact from ADR |
| **AI Commands** | |
| `git adr draft` | AI-generate ADR from context |
| `git adr suggest` | AI suggestions for ADR improvement |
| `git adr summarize` | AI summary of recent decisions |
| `git adr ask` | Natural language ADR queries |
| **Wiki Commands** | |
| `git adr wiki-init` | Initialize wiki structure |
| `git adr wiki-sync` | Sync ADRs to GitHub/GitLab wiki |
| **Analytics Commands** | |
| `git adr metrics` | Export metrics (JSON/Prometheus/CSV) |
| `git adr convert` | Convert ADR between formats |

#### `git adr init`

Initialize ADR notes in a repository.

```bash
git adr init [--namespace <name>] [--template <madr|nygard|custom>]
```

**Behavior:**
- Creates `refs/notes/adr` namespace (or custom namespace)
- Stores configuration note on repository root tree object
- Creates initial ADR (0000-use-architecture-decision-records.md equivalent)
- Configures local git to display ADR notes in log output

**Configuration stored:**
```yaml
git-adr:
  version: "1.0"
  template: madr
  namespace: refs/notes/adr
  auto-link: true  # Automatically link ADRs to HEAD commit
  date-prefix: true  # Use YYYYMMDD prefix (log4brains style)
```

#### `git adr new <title>`

Create a new Architecture Decision Record.

```bash
git adr new "Use PostgreSQL for persistence" [--status <proposed|accepted|deprecated|superseded>]
    [--link <commit>] [--supersedes <adr-id>] [--deciders <names>] [--tags <tags>]
    [--no-edit] [--draft]
```

**Behavior:**
1. Generates ADR ID (date-based: `20251214-use-postgresql-for-persistence` or sequential)
2. Creates MADR-formatted markdown content
3. Opens `$EDITOR` for completion (unless `--no-edit`)
4. Stores as git note attached to specified commit (defaults to HEAD)
5. Updates index note listing all ADRs

**Generated MADR Template:**
```markdown
---
status: proposed
date: 2025-12-14
decision-makers: []
consulted: []
informed: []
tags: []
linked-commits: [<commit-sha>]
supersedes: null
---

# Use PostgreSQL for persistence

## Context and Problem Statement

{Describe the context and problem statement}

## Decision Drivers

* {decision driver 1}
* {decision driver 2}

## Considered Options

* {option 1}
* {option 2}
* {option 3}

## Decision Outcome

Chosen option: "{option}", because {justification}.

### Consequences

* Good, because {positive consequence}
* Bad, because {negative consequence}

### Confirmation

{How will compliance be validated?}

## Pros and Cons of the Options

### {Option 1}

* Good, because {argument}
* Bad, because {argument}

### {Option 2}

* Good, because {argument}
* Bad, because {argument}

## More Information

{Additional context, links, references}
```

#### `git adr list`

List all Architecture Decision Records.

```bash
git adr list [--status <status>] [--tag <tag>] [--since <date>] [--until <date>]
    [--format <table|json|csv|oneline>] [--linked <commit>] [--reverse]
```

**Output (default table format):**
```
ID                                    Status     Date        Title
────────────────────────────────────────────────────────────────────────────
20251214-use-postgresql-for-persistence  accepted   2025-12-14  Use PostgreSQL for persistence
20251210-adopt-event-sourcing            proposed   2025-12-10  Adopt Event Sourcing pattern
20251201-use-kubernetes                  accepted   2025-12-01  Use Kubernetes for orchestration
```

#### `git adr show <adr-id>`

Display a specific ADR.

```bash
git adr show <adr-id> [--format <markdown|yaml|json>] [--metadata-only]
```

**Behavior:**
- Retrieves ADR from git notes
- Renders with syntax highlighting (if terminal supports)
- Shows linked commits and their messages
- Displays relationship to other ADRs (supersedes/superseded-by)

#### `git adr search <query>`

Full-text search across all ADRs.

```bash
git adr search <query> [--context <lines>] [--status <status>] [--tag <tag>]
    [--case-sensitive] [--regex]
```

**Behavior:**
- Searches title, context, options, consequences
- Returns matching ADRs with highlighted snippets
- Supports fuzzy matching and regex patterns

#### `git adr edit <adr-id>`

Modify an existing ADR.

```bash
git adr edit <adr-id> [--status <status>] [--add-tag <tag>] [--remove-tag <tag>]
    [--link <commit>] [--unlink <commit>]
```

**Behavior:**
- Opens ADR in `$EDITOR`
- Updates git note with new content
- Preserves modification history (git notes are versioned)

#### `git adr link <adr-id> <commit>`

Associate an ADR with additional commits.

```bash
git adr link <adr-id> <commit>... [--unlink]
```

**Behavior:**
- Adds commit SHA to ADR's `linked-commits` metadata
- Adds ADR reference note to the commit
- Enables bidirectional discovery

#### `git adr supersede <adr-id> <new-title>`

Create a new ADR that supersedes an existing one.

```bash
git adr supersede <adr-id> "New approach to persistence"
```

**Behavior:**
- Creates new ADR with `supersedes: <adr-id>` metadata
- Updates original ADR status to `superseded by <new-adr-id>`
- Maintains full history chain

#### `git adr log`

Show git log with ADR annotations.

```bash
git adr log [<git-log-options>]
```

**Behavior:**
- Wraps `git log --show-notes=refs/notes/adr`
- Formats ADR summaries inline with commits
- Supports all standard git log options

**Example output:**
```
commit a1b2c3d4 (HEAD -> main)
Author: Bob <bob@example.com>
Date:   Sat Dec 14 10:30:00 2025 -0500

    Implement PostgreSQL connection pooling

    ADR: 20251214-use-postgresql-for-persistence (accepted)
    Title: Use PostgreSQL for persistence
    Decision: Chosen PostgreSQL for ACID compliance and JSON support

commit e5f6g7h8
Author: Alice <alice@example.com>
Date:   Fri Dec 13 15:00:00 2025 -0500

    Add user authentication service
```

#### `git adr export`

Export ADRs to various formats.

```bash
git adr export [--format <markdown|html|json|docx>] [--output <path>]
    [--status <status>] [--since <date>] [--template <path>]
```

**Behavior:**
- Generates static documentation from ADR notes
- Supports log4brains-compatible HTML output
- Creates index/table of contents
- Preserves chronological ordering and relationships

#### `git adr import`

Import existing file-based ADRs.

```bash
git adr import <path> [--format <madr|nygard|log4brains>] [--link-by-date]
```

**Behavior:**
- Reads ADRs from `docs/adr/` or specified path
- Converts to git notes format
- Optionally links to commits by matching dates

#### `git adr sync`

Synchronize ADR notes with remotes.

```bash
git adr sync [<remote>] [--push] [--pull] [--merge-strategy <ours|theirs|union|cat>]
```

**Behavior:**
- Push: `git push <remote> refs/notes/adr`
- Pull: `git fetch <remote> refs/notes/adr:refs/notes/adr`
- Handles merge conflicts with configurable strategies

#### `git adr report`

Generate an interactive decision intelligence report for onboarding and team awareness.

```bash
git adr report [--format <terminal|html|json|markdown>] [--output <path>]
    [--period <7d|30d|90d|1y|all>] [--team] [--interactive]
```

**Purpose:**
This command serves as both a dashboard and onboarding tool, giving newcomers (and veterans) a comprehensive view of the project's architectural landscape. It answers: "What decisions shaped this codebase, and what should I know before contributing?"

**Terminal Output (default):**

```
╭──────────────────────────────────────────────────────────────────────────────╮
│                    🏛️  ARCHITECTURE DECISION REPORT                          │
│                         my-project (main branch)                             │
│                         Generated: 2025-12-14 10:30 EST                      │
╰──────────────────────────────────────────────────────────────────────────────╯

📊 DECISION LANDSCAPE
─────────────────────────────────────────────────────────────────────────────────
Total ADRs: 47                    Active Decisions: 38
First ADR: 2023-06-15             Latest ADR: 2025-12-10
Decision Velocity: 2.3/month      Avg. Time to Accept: 4.2 days

Status Breakdown:
  ████████████████████████░░░░░░  accepted (32)     68%
  ████░░░░░░░░░░░░░░░░░░░░░░░░░░  proposed (6)      13%
  ███░░░░░░░░░░░░░░░░░░░░░░░░░░░  superseded (5)    11%
  ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░  deprecated (4)    8%

🏷️  TOP CATEGORIES (by tag frequency)
─────────────────────────────────────────────────────────────────────────────────
  infrastructure  ████████████████  16 ADRs   "How we deploy and operate"
  data-storage    ███████████░░░░░  11 ADRs   "Persistence and caching choices"
  api-design      ████████░░░░░░░░   8 ADRs   "Contract and interface decisions"
  security        ██████░░░░░░░░░░   6 ADRs   "Auth, encryption, compliance"
  testing         ████░░░░░░░░░░░░   4 ADRs   "Quality assurance strategy"
  frontend        ███░░░░░░░░░░░░░   3 ADRs   "UI/UX technology choices"

💡 TIP: Run `git adr list --tag infrastructure` to explore a category

🕐 RECENT DECISIONS (last 30 days)
─────────────────────────────────────────────────────────────────────────────────
  🟢 accepted   20251210  Adopt OpenTelemetry for observability
                          └─ Linked to 3 commits │ Deciders: @alice, @bob
  🟡 proposed   20251205  Migrate to arm64 containers  
                          └─ Open 9 days │ Awaiting: @infra-team review
  🟢 accepted   20251201  Use Postgres JSONB for flexible schemas
                          └─ Supersedes: 20230915-use-mongodb
  🔴 deprecated 20251128  Remove legacy REST endpoints
                          └─ Migration complete │ 12 commits linked

💡 TIP: New here? Start with `git adr show 20251210-adopt-opentelemetry`

🔥 HIGH-IMPACT DECISIONS (most linked commits)
─────────────────────────────────────────────────────────────────────────────────
  1. Use Kubernetes for orchestration (47 commits)
     └─ 20231015 │ accepted │ Foundation of deployment architecture
  2. Adopt Event Sourcing pattern (34 commits)  
     └─ 20240301 │ accepted │ Core data model transformation
  3. Implement CQRS with separate read models (28 commits)
     └─ 20240315 │ accepted │ Query optimization strategy
  4. Use PostgreSQL for persistence (23 commits)
     └─ 20251201 │ accepted │ Primary data store selection
  5. Standardize on OpenAPI 3.1 specs (19 commits)
     └─ 20240601 │ accepted │ API contract methodology

💡 TIP: High-impact ADRs affect many files—read these first!

⚡ DECISION VELOCITY TREND
─────────────────────────────────────────────────────────────────────────────────
2025 Q4 │ ████████████  12 decisions
2025 Q3 │ ████████░░░░   8 decisions  
2025 Q2 │ ██████░░░░░░   6 decisions
2025 Q1 │ ████████████  12 decisions
2024 Q4 │ █████░░░░░░░   5 decisions
2024 Q3 │ ████░░░░░░░░   4 decisions

📈 Trend: Decision activity up 50% this quarter (architectural evolution phase)

👥 DECISION MAKERS LEADERBOARD
─────────────────────────────────────────────────────────────────────────────────
  @alice      ████████████████████  18 decisions  "Infrastructure & Platform"
  @bob        ████████████░░░░░░░░  12 decisions  "Data & Backend"
  @carol      ████████░░░░░░░░░░░░   8 decisions  "API Design"
  @dave       ██████░░░░░░░░░░░░░░   6 decisions  "Security"
  @eve        ███░░░░░░░░░░░░░░░░░   3 decisions  "Frontend"

💡 TIP: Questions about infrastructure? @alice has the context.

🔗 DECISION RELATIONSHIPS
─────────────────────────────────────────────────────────────────────────────────
Supersession Chains:
  mongodb → postgresql (20230915 → 20251201)
  └─ "Migrated for ACID compliance and operational simplicity"
  
  rest-api-v1 → graphql-gateway → rest-api-v2 (3-step evolution)
  └─ "API strategy evolved with team scaling"

Decision Clusters (frequently co-referenced):
  • kubernetes + helm + argocd (GitOps deployment stack)
  • event-sourcing + cqrs + kafka (Event-driven architecture)
  • openapi + typescript-sdk + api-gateway (API ecosystem)

💡 TIP: Understanding clusters helps you see the "big picture"

🎯 ONBOARDING CHECKLIST
─────────────────────────────────────────────────────────────────────────────────
New to this project? Read these ADRs in order:

  □ 1. 20231001-use-architecture-decision-records
       └─ "Why we document decisions (meta!)"
  □ 2. 20231015-use-kubernetes-for-orchestration  
       └─ "Deployment fundamentals"
  □ 3. 20240301-adopt-event-sourcing-pattern
       └─ "Core data architecture"
  □ 4. 20240601-standardize-on-openapi-specs
       └─ "How we define APIs"
  □ 5. 20251201-use-postgresql-for-persistence
       └─ "Current data store (supersedes MongoDB)"

  Estimated reading time: ~25 minutes

💡 TIP: Run `git adr onboard` for an interactive walkthrough!

⚠️  ATTENTION NEEDED
─────────────────────────────────────────────────────────────────────────────────
  🟡 3 ADRs in "proposed" status > 7 days (may need decision)
     └─ 20251205-migrate-to-arm64, 20251130-add-redis-cache, 20251125-use-grpc
  
  🟠 2 ADRs reference deprecated dependencies
     └─ 20240115-use-moment-js (moment.js deprecated upstream)
     └─ 20230801-use-node-14 (Node 14 EOL)

  📋 Action: Run `git adr list --needs-attention` for details

╭──────────────────────────────────────────────────────────────────────────────╮
│  📖 Commands: git adr list | git adr show <id> | git adr search <query>      │
│  🔗 Export:   git adr report --format html --output report.html              │
│  💬 Help:     git adr --help | git adr report --help                         │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**Report Sections Explained:**

| Section | Purpose | Onboarding Value |
|---------|---------|------------------|
| Decision Landscape | High-level stats and health metrics | Quick sense of project maturity |
| Top Categories | Tag-based clustering with descriptions | Navigate by domain interest |
| Recent Decisions | What's changing now | Stay current with evolution |
| High-Impact Decisions | Most-linked ADRs | Identify foundational choices |
| Velocity Trend | Decision activity over time | Understand project phases |
| Decision Makers | Who knows what | Find the right person to ask |
| Relationships | Supersession chains and clusters | See decision evolution |
| Onboarding Checklist | Curated reading order | Structured learning path |
| Attention Needed | Stale proposals, deprecated refs | Maintenance awareness |

**Interactive Mode (`--interactive`):**

```bash
git adr report --interactive
```

Launches a TUI (terminal user interface) with:
- Arrow key navigation between ADRs
- `Enter` to view full ADR content
- `/` to search within report
- `o` to open ADR in editor
- `g` to see git log for linked commits
- `q` to quit

**HTML Export:**

```bash
git adr report --format html --output adr-report.html
```

Generates a single-page dashboard with:
- Interactive charts (Chart.js)
- Filterable ADR table
- Expandable decision details
- Dark/light mode toggle
- Print-friendly stylesheet
- Embeddable in documentation sites

**JSON Export (for CI/dashboards):**

```bash
git adr report --format json --output metrics.json
```

```json
{
  "generated_at": "2025-12-14T10:30:00Z",
  "repository": "my-project",
  "branch": "main",
  "summary": {
    "total_adrs": 47,
    "active": 38,
    "proposed": 6,
    "deprecated": 4,
    "superseded": 5,
    "first_adr_date": "2023-06-15",
    "latest_adr_date": "2025-12-10",
    "velocity_per_month": 2.3,
    "avg_days_to_accept": 4.2
  },
  "by_category": {
    "infrastructure": 16,
    "data-storage": 11,
    "api-design": 8
  },
  "high_impact": [
    {"id": "20231015-use-kubernetes", "linked_commits": 47}
  ],
  "needs_attention": {
    "stale_proposed": ["20251205-migrate-to-arm64"],
    "deprecated_dependencies": ["20240115-use-moment-js"]
  },
  "onboarding_sequence": [
    "20231001-use-architecture-decision-records",
    "20231015-use-kubernetes-for-orchestration"
  ]
}
```

**Team Mode (`--team`):**

Adds collaboration-focused metrics:
- Decisions per team member over time
- Review participation rates
- Cross-team decision involvement
- Consultation network graph

**Period Filtering:**

```bash
git adr report --period 90d    # Last 90 days focus
git adr report --period 2024   # Full year 2024
git adr report --period all    # Complete history
```

#### `git adr onboard`

Interactive onboarding wizard for new team members.

```bash
git adr onboard [--quick] [--category <tag>] [--role <developer|reviewer|architect>]
```

**Behavior:**

Launches a guided tour through essential ADRs:

```
╭──────────────────────────────────────────────────────────────────────────────╮
│              👋 Welcome to my-project Architecture Onboarding                │
╰──────────────────────────────────────────────────────────────────────────────╯

This project has 47 architecture decisions spanning 2.5 years of development.
Let's walk through the most important ones together.

Your role: [developer ▼]  Focus area: [all ▼]  Time available: [~30 min ▼]

Based on your selections, I'll guide you through 8 key decisions.

Ready? Press [Enter] to begin or [q] to quit...

─────────────────────────────────────────────────────────────────────────────────
📖 ADR 1 of 8: Why We Document Decisions
─────────────────────────────────────────────────────────────────────────────────

# Use Architecture Decision Records

## Context and Problem Statement
As our team grows, new members struggle to understand why certain 
technical choices were made. Tribal knowledge is being lost...

[...full ADR content with syntax highlighting...]

─────────────────────────────────────────────────────────────────────────────────
💡 Why this matters: This meta-decision explains the system you're using 
   right now. Understanding ADRs helps you contribute informed decisions.

🔗 Related: This ADR has no dependencies—it's the foundation.

📊 Impact: Referenced by 47 subsequent decisions.

[n]ext │ [p]revious │ [s]kip │ [b]ookmark │ [q]uit │ [?]help
─────────────────────────────────────────────────────────────────────────────────
```

**Quick Mode (`--quick`):**

5-minute executive summary hitting only the top 3-5 foundational ADRs.

**Role-Based Paths:**

- `--role developer`: Focus on coding patterns, testing, tooling
- `--role reviewer`: Emphasis on standards, quality gates, review criteria  
- `--role architect`: Deep dive on system design, trade-offs, evolution

**Progress Tracking:**

```bash
git adr onboard --status
```

```
Onboarding Progress for @newdev:
  ████████████████░░░░  80% complete (8/10 ADRs)
  
  ✓ 20231001-use-adrs
  ✓ 20231015-use-kubernetes  
  ✓ 20240301-event-sourcing
  ✓ 20240315-cqrs
  ✓ 20240601-openapi
  ✓ 20251201-postgresql
  ✓ 20251210-opentelemetry
  ✓ 20240801-testing-strategy
  ○ 20241001-security-baseline (next)
  ○ 20241115-ci-cd-pipeline
  
  Resume with: git adr onboard --continue
```

#### `git adr stats`

Quick statistics without full report formatting.

```bash
git adr stats [--json]
```

```
ADRs: 47 total (32 accepted, 6 proposed, 5 superseded, 4 deprecated)
Period: 2023-06-15 to 2025-12-10 (2.5 years)
Velocity: 2.3 decisions/month
Categories: infrastructure (16), data-storage (11), api-design (8), +3 more
Top contributor: @alice (18 decisions)
Needs attention: 3 stale proposals, 2 deprecated dependencies
```

#### `git adr config`

Manage git-adr configuration.

```bash
git adr config [--list] [--get <key>] [--set <key> <value>] [--global]
```

**Configuration options:**
- `adr.namespace` — Notes ref path (default: `refs/notes/adr`)
- `adr.template` — Default template (madr, nygard, custom file path)
- `adr.editor` — Override `$EDITOR` for ADRs
- `adr.datePrefix` — Use date-based IDs (default: true)
- `adr.autoLink` — Auto-link new ADRs to HEAD (default: true)
- `adr.showInLog` — Include ADR notes in `git log` (default: true)

---

### Git Notes Architecture

#### Namespace Structure

```
refs/notes/adr/
├── index                    # Index note listing all ADRs
├── config                   # Repository configuration
└── <commit-sha>            # ADR notes attached to commits
```

#### Index Note Format

```yaml
git-adr-index:
  version: "1.0"
  adrs:
    - id: "20251214-use-postgresql-for-persistence"
      title: "Use PostgreSQL for persistence"
      status: accepted
      date: "2025-12-14"
      commits: ["a1b2c3d4", "e5f6g7h8"]
    - id: "20251210-adopt-event-sourcing"
      title: "Adopt Event Sourcing pattern"
      status: proposed
      date: "2025-12-10"
      commits: ["i9j0k1l2"]
```

#### Sync Strategy

Git notes require explicit push/fetch:

```bash
# Configure remote to include ADR notes
git config --add remote.origin.fetch '+refs/notes/adr:refs/notes/adr'
git config --add remote.origin.push 'refs/notes/adr'

# Or use git adr sync
git adr sync origin --push --pull
```

#### Merge Strategies

For concurrent ADR creation:

- **union** (default): Concatenate conflicting notes
- **ours**: Keep local version
- **theirs**: Keep remote version
- **cat_sort_uniq**: Combine and deduplicate

---

## User Experience Design

### Parallels with log4brains

| log4brains | git-adr | Notes |
|------------|---------|-------|
| `log4brains init` | `git adr init` | Initialize ADR tracking |
| `log4brains adr new` | `git adr new` | Create new ADR |
| `log4brains preview` | `git adr export --html` | Generate viewable docs |
| `log4brains build` | `git adr export` | Static site generation |
| `docs/adr/*.md` files | `refs/notes/adr` | Storage location |

### Command Ergonomics

**Short aliases:**
```bash
git adr n "title"     # new
git adr l             # list  
git adr s "query"     # search
git adr e <id>        # edit
```

**Shell completion:**
- Bash/Zsh/Fish completions for ADR IDs and options
- Tab-complete `git adr show 2025<TAB>` → available ADRs

**Output formatting:**
- Colorized terminal output (respects `NO_COLOR`)
- Machine-readable JSON/CSV for scripting
- Pager integration for long output

---

## Technical Specification

### Implementation Stack

- **Language:** Python 3.11+
- **Package Manager:** `uv` (astral)
- **CLI Framework:** `typer` (built on click)
- **Git Operations:** `pygit2` or subprocess to git
- **Markdown Parsing:** `python-frontmatter`, `mistune`
- **Output Formatting:** `rich`
- **Testing:** `pytest`, `pytest-cov`
- **Linting:** `ruff`
- **Type Checking:** `mypy`

**AI Integration (optional, via extras):**
- **LLM Abstraction:** `langchain-core`
- **Providers:**
  - `langchain-anthropic` (Anthropic/Claude)
  - `langchain-openai` (OpenAI, Azure)
  - `langchain-google-genai` (Google/Gemini)
  - `langchain-aws` (AWS Bedrock)
  - `langchain-ollama` (local models)

**Wiki Integration:**
- Standard git operations (clone, commit, push)
- `PyGithub` (optional, for commit pointer comments)
- `python-gitlab` (optional, for commit pointer comments)

**Export/Visualization:**
- `python-docx` (Word export)
- `jinja2` (HTML templating)
- `mermaid-py` (diagram rendering)

### Package Structure

```
git-adr/
├── pyproject.toml
├── src/
│   └── git_adr/
│       ├── __init__.py
│       ├── cli.py              # Typer CLI application
│       ├── commands/
│       │   ├── init.py
│       │   ├── new.py
│       │   ├── list.py
│       │   ├── show.py
│       │   ├── search.py
│       │   ├── edit.py
│       │   ├── link.py
│       │   ├── supersede.py
│       │   ├── log.py
│       │   ├── export.py
│       │   ├── import_.py
│       │   ├── sync.py
│       │   ├── config.py
│       │   ├── report.py       # Dashboard and analytics
│       │   ├── onboard.py      # Interactive wizard
│       │   ├── stats.py        # Quick statistics
│       │   ├── metrics.py      # Export metrics
│       │   ├── attach.py       # Artifact management
│       │   ├── draft.py        # AI draft generation
│       │   ├── suggest.py      # AI suggestions
│       │   ├── ask.py          # AI Q&A
│       │   ├── summarize.py    # AI summaries
│       │   ├── forge_sync.py   # GitHub/GitLab sync
│       │   └── convert.py      # Format conversion
│       ├── core/
│       │   ├── notes.py        # Git notes operations
│       │   ├── adr.py          # ADR model and operations
│       │   ├── index.py        # Index management
│       │   ├── templates.py    # Template handling
│       │   ├── artifacts.py    # Binary artifact storage
│       │   └── analytics.py    # Metrics calculation
│       ├── formats/
│       │   ├── base.py         # Abstract format interface
│       │   ├── madr.py         # MADR 4.0 format
│       │   ├── nygard.py       # Nygard original format
│       │   ├── y_statement.py  # Y-Statement format
│       │   ├── alexandrian.py  # Alexandrian pattern format
│       │   ├── business_case.py # Business case template
│       │   ├── planguage.py    # Planguage quality format
│       │   └── log4brains.py   # log4brains compatibility
│       ├── ai/
│       │   ├── __init__.py
│       │   ├── providers.py    # LangChain provider setup
│       │   ├── draft.py        # ADR draft generation
│       │   ├── suggest.py      # Improvement suggestions
│       │   ├── summarize.py    # Summary generation
│       │   └── qa.py           # Q&A over ADRs
│       ├── wiki/
│       │   ├── __init__.py
│       │   ├── sync.py         # Wiki clone/push operations
│       │   ├── render.py       # ADR to wiki markdown
│       │   ├── index.py        # Index page generation
│       │   └── pointers.py     # Optional commit pointer comments
│       └── utils/
│           ├── git.py          # Git helper functions
│           ├── editor.py       # Editor integration
│           ├── output.py       # Output formatting
│           └── tui.py          # Terminal UI components
├── tests/
│   ├── conftest.py
│   ├── test_commands/
│   ├── test_core/
│   ├── test_formats/
│   ├── test_ai/
│   └── test_wiki/
└── docs/
    └── adr/                    # Dog-fooding: our own ADRs
```

### Installation

```bash
# Via pipx (recommended) - core only
pipx install git-adr

# With AI features
pipx install "git-adr[ai]"

# With wiki commit pointers (optional GitHub/GitLab API)
pipx install "git-adr[wiki]"

# Full installation (all features)
pipx install "git-adr[all]"

# Via uv
uv tool install git-adr
uv tool install "git-adr[all]"

# Via pip
pip install git-adr
pip install "git-adr[ai,wiki]"

# Development
git clone https://github.com/epicpastures/git-adr
cd git-adr
uv sync --all-extras
```

**Optional Extras:**

| Extra | Includes | Use Case |
|-------|----------|----------|
| `ai` | langchain, provider SDKs | AI-assisted ADR authoring |
| `wiki` | PyGithub, python-gitlab | Commit pointer comments (wiki sync is core) |
| `export` | python-docx, mermaid-py | Enhanced export formats |
| `all` | All of the above | Full feature set |

### Git Extension Integration

Installing creates a `git-adr` executable, which git automatically discovers as a subcommand:

```bash
git adr --help    # Works because git finds 'git-adr' in PATH
```

---

## Competitive Analysis

| Feature | git-adr | log4brains | adr-tools | adr-cli (.NET) |
|---------|---------|------------|-----------|----------------|
| Storage | git notes | Files | Files | Files |
| Commit linking | Native | Manual | No | No |
| Merge conflicts | Rare | Common | Common | Common |
| Template | **6 formats** | MADR | Nygard | Nygard |
| Web UI | Export | Built-in | No | No |
| Language | Python | Node.js | Bash | C# |
| Distributed | Yes | Partial | No | No |
| **AI Assistance** | **Yes** | No | No | No |
| **Multi-Format** | **Yes (6)** | MADR only | Nygard only | Nygard only |
| **GitHub/GitLab Wiki Sync** | **Yes** | No | No | No |
| **Team Analytics** | **Yes** | No | No | No |
| **Binary Artifacts** | **Yes** | No | No | No |
| **Analytics/Report** | **Yes** | No | No | No |
| **Onboarding Wizard** | **Yes** | No | No | No |
| **Decision Graphs** | **Yes** | Partial | No | No |

### Unique Value Propositions

1. **Zero working tree impact** — No `docs/adr/` directory cluttering repo
2. **Atomic commit association** — ADRs linked to implementing commits
3. **No numbering conflicts** — Date/hash-based IDs avoid merge pain
4. **True distribution** — Git notes sync with push/pull
5. **History preservation** — Notes versioning tracks ADR evolution
6. **Decision intelligence** — Analytics dashboard reveals architectural patterns
7. **Onboarding-first design** — Interactive wizard accelerates new team member ramp-up
8. **AI-powered authoring** — LLM integration for drafting, suggestions, and Q&A
9. **Format flexibility** — Six ADR templates (MADR, Nygard, Y-Statement, Alexandrian, Business Case, Planguage)
10. **Wiki visibility** — GitHub/GitLab wiki sync with auto-generated indexes
11. **Binary artifact support** — Diagrams and images stored alongside ADRs
12. **Team analytics** — Velocity, participation, and coverage metrics

---

## Success Metrics

### Adoption Targets (6 months)

- GitHub stars: 500+
- PyPI downloads: 5,000/month
- Active repositories using git-adr: 100+

### User Satisfaction

- Command success rate > 99%
- Average command latency < 200ms
- Zero data loss incidents

### Quality Gates

- Test coverage > 90%
- Type checking passes (mypy --strict)
- Linting clean (ruff)
- Documentation coverage 100%

---

## Roadmap

### Phase 1: Core MVP (v0.5.0) — 6 weeks

**Core Commands:**
- [ ] `init`, `new`, `list`, `show`, `edit`, `search`
- [ ] `link`, `supersede`, `log`
- [ ] `sync` (push/pull notes to remotes)

**Multi-Format Support:**
- [ ] MADR 4.0 (default)
- [ ] Nygard original template
- [ ] Y-Statement compact format
- [ ] Alexandrian pattern format
- [ ] Business Case template
- [ ] Planguage quality-focused template
- [ ] Custom template registration

**Storage Architecture:**
- [ ] Root tree attachment for ADRs
- [ ] `refs/notes/adr-artifacts` for binary assets
- [ ] Artifact attach/get/list/remove commands

**Configuration:**
- [ ] Git config-based settings
- [ ] Per-repo and global config

### Phase 2: Intelligence & Integration (v0.8.0) — 4 weeks

**AI Features (LangChain-based):**
- [ ] Provider abstraction (Anthropic, OpenAI, Google, Azure, Ollama)
- [ ] `git adr draft` — Generate ADR from commits/context
- [ ] `git adr suggest` — Improve in-progress ADRs
- [ ] `git adr summarize` — Natural language summaries
- [ ] `git adr ask` — Query ADR knowledge base

**Wiki Integration:**
- [ ] GitHub wiki sync (clone, write, push)
- [ ] GitLab wiki sync
- [ ] Auto-generated indexes (all, by-status, by-tag)
- [ ] Sidebar navigation generation
- [ ] Optional commit pointer comments
- [ ] Bidirectional sync (pull wiki edits)
- [ ] GitHub Actions / GitLab CI workflows

**Analytics:**
- [ ] `git adr report` full dashboard
- [ ] `git adr report --team` collaboration metrics
- [ ] `git adr metrics` export (JSON, Prometheus, CSV)
- [ ] `git adr stats` quick summary

### Phase 3: Onboarding & Export (v0.9.0) — 3 weeks

- [ ] `git adr onboard` interactive wizard
- [ ] Role-based onboarding paths
- [ ] Progress tracking
- [ ] `git adr export` (HTML, JSON, Markdown, docx)
- [ ] `git adr import` from file-based ADRs
- [ ] log4brains HTML theme compatibility
- [ ] Mermaid diagram rendering

### Phase 4: Polish (v1.0.0) — 3 weeks

- [ ] log4brains HTML theme compatibility
- [ ] Git hooks integration
- [ ] GitHub Actions workflow
- [ ] MCP server for Claude integration
- [ ] Documentation site
- [ ] Logo and branding
- [ ] Onboarding progress persistence

### Future Considerations

- **GitHub/GitLab integration** — Display ADRs in web UI via API
- **VS Code extension** — Inline ADR viewing/editing
- **AI assistance** — Generate ADR drafts from commit messages
- **Team analytics** — Decision velocity, participation metrics

---

## Resolved Design Decisions

### 1. Note Attachment Strategy

**Decision:** ADRs attach to the **repository root tree object**, with related commit SHAs stored in the ADR metadata.

**Rationale:**
- Root tree attachment ensures ADRs exist independently of any specific commit
- ADRs often precede or span multiple implementing commits
- Avoids orphaning ADRs if commits are rebased or amended
- Related commits are tracked bidirectionally in ADR metadata (`linked-commits: [sha1, sha2]`)
- Git notes on root tree survive branch operations

**Implementation:**
```python
# Get repository root tree SHA
root_tree = repo.head.peel(pygit2.Tree).id

# Store ADR as note on root tree
repo.notes.add(root_tree, adr_content, ref="refs/notes/adr")

# ADR metadata tracks implementing commits
linked-commits: ["a1b2c3d", "e5f6g7h"]
```

### 2. Multi-Repository ADRs

**Decision:** Out of scope for v1.0. Defer to future versions.

**Rationale:** Cross-repo decisions introduce significant complexity (sync, authorization, discovery). Focus on single-repo excellence first.

### 3. Binary Assets (Diagrams, Images)

**Decision:** Store artifacts in a separate `refs/notes/adr-artifacts` namespace, with ADRs containing references by content hash.

**Namespace Structure:**
```
refs/notes/adr/              # ADR markdown content
refs/notes/adr-artifacts/    # Binary blobs (diagrams, images)
```

**ADR Artifact Reference Format:**
```yaml
---
artifacts:
  - id: "sha256:abc123..."
    name: "architecture-diagram.png"
    type: "image/png"
    alt: "System architecture showing microservices layout"
  - id: "sha256:def456..."
    name: "sequence-flow.mermaid"
    type: "text/x-mermaid"
---
```

**Visualization Options:**
- **Terminal:** ASCII art rendering for simple diagrams; URL/path for complex images
- **HTML export:** Inline base64 or extracted to `assets/` directory
- **Mermaid support:** Render `.mermaid` files to SVG during export
- **Interactive report:** Lightbox gallery for attached diagrams

**Commands:**
```bash
# Attach artifact to ADR
git adr attach <adr-id> path/to/diagram.png --alt "Architecture overview"

# List artifacts for an ADR
git adr artifacts <adr-id>

# Extract artifact to file
git adr artifact-get <adr-id> <artifact-name> --output diagram.png

# Remove artifact
git adr artifact-rm <adr-id> <artifact-name>
```

**Size Considerations:**
- Warn if artifact > 1MB
- Refuse artifacts > 10MB by default (`--force` to override)
- Recommend external links for large assets

### 4. Forge Integration (GitHub/GitLab)

**Decision:** Include in MVP via API-based synchronization, creating commit comments/discussions that mirror ADR content.

See **Forge Integration** section below for full specification.

---

## New MVP Features

### AI-Assisted ADR Generation

Optional LLM integration for drafting ADRs from context, summarizing discussions, and suggesting improvements.

#### Configuration

AI features require explicit opt-in via git config:

```bash
# Enable AI features
git adr config --set ai.enabled true

# Configure provider
git adr config --set ai.provider anthropic  # or: openai, google, bedrock, ollama, azure

# Set API key (stored in git config, NOT in notes)
git adr config --set ai.api-key "sk-..."

# Optional: model override
git adr config --set ai.model "claude-sonnet-4.5"

# Optional: custom endpoint (for Azure, Ollama, proxies)
git adr config --set ai.endpoint "https://my-proxy.example.com/v1"

# For AWS Bedrock: uses AWS credentials from environment or ~/.aws/credentials
git adr config --set ai.provider bedrock
git adr config --set ai.aws-region "us-east-1"
```

**Supported Providers:**

| Provider | Config Value | Models | Notes |
|----------|--------------|--------|-------|
| Anthropic | `anthropic` | claude-opus-4.5, claude-sonnet-4.5, claude-haiku-4.5 | Default provider |
| OpenAI | `openai` | gpt-5, gpt-4.1, gpt-4.1-mini, o3, o4-mini | |
| Google | `google` | gemini-2.5-pro, gemini-2.5-flash, gemini-3.0-pro | Via google-generativeai |
| AWS Bedrock | `bedrock` | All Claude models, Llama, Mistral, Titan | Requires AWS credentials |
| Azure OpenAI | `azure` | Configurable (gpt-5, gpt-4.1, etc.) | Requires endpoint |
| Ollama | `ollama` | llama3.3, mistral, qwen2.5, deepseek-r1, phi4 | Local, no API key needed |
| OpenRouter | `openrouter` | Multiple | Unified API for many models |

**Implementation:** Uses LangChain for provider abstraction, allowing consistent interface across backends.

```python
# langchain provider setup
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

def get_llm(config: AdrConfig) -> BaseChatModel:
    match config.ai_provider:
        case "anthropic":
            return ChatAnthropic(model=config.ai_model, api_key=config.ai_api_key)
        case "openai":
            return ChatOpenAI(model=config.ai_model, api_key=config.ai_api_key)
        case "google":
            return ChatGoogleGenerativeAI(model=config.ai_model, api_key=config.ai_api_key)
        # ...
```

#### AI Commands

**`git adr draft <title>`**

Generate an ADR draft from commit messages, code changes, and optional context.

```bash
git adr draft "Adopt Redis for session caching" \
    --from-commits HEAD~10..HEAD \
    --context "We need sub-10ms session lookups" \
    --options "Redis, Memcached, DynamoDB"
```

**Behavior:**
1. Analyzes recent commits for relevant changes
2. Reads related code files
3. Generates MADR-formatted draft with:
   - Inferred context from code changes
   - Suggested decision drivers
   - Pros/cons for each option
   - Recommended decision (with confidence)
4. Opens in `$EDITOR` for human review and completion

**`git adr suggest <adr-id>`**

Analyze an in-progress ADR and suggest improvements.

```bash
git adr suggest 20251214-use-redis --aspect consequences
```

**Aspects:**
- `context`: Expand context with relevant technical details
- `options`: Suggest additional alternatives to consider
- `consequences`: Identify missing positive/negative outcomes
- `validation`: Propose confirmation criteria
- `all`: Full review with all suggestions

**`git adr summarize`**

Generate natural language summary of recent architectural changes.

```bash
git adr summarize --period 30d --format slack
```

**Formats:** `markdown`, `slack`, `email`, `standup`

**`git adr ask <question>`**

Query your ADR knowledge base in natural language.

```bash
git adr ask "Why did we choose PostgreSQL over MongoDB?"
git adr ask "What decisions affect our authentication system?"
git adr ask "Show me all deprecated decisions and their replacements"
```

**Behavior:**
- Embeds question and ADR corpus
- Returns relevant ADRs with contextual explanation
- Cites specific ADR sections

---

### Multiple ADR Format Support

Support multiple ADR templates beyond MADR, configurable per-repository.

#### Supported Formats

**1. MADR 4.0** (default)
```yaml
format: madr
version: "4.0"
```
Full structured template with options analysis, consequences, confirmation.

**2. Nygard (Original)**
```yaml
format: nygard
```
Minimal template: Title, Status, Context, Decision, Consequences.

```markdown
# ADR N: Title

## Status
Accepted

## Context
The forces at play...

## Decision
We will...

## Consequences
The resulting context...
```

**3. Y-Statement**
```yaml
format: y-statement
```
Single-sentence format for simple decisions:

```markdown
# Use PostgreSQL for Persistence

In the context of **data storage requirements**,
facing **need for ACID compliance and JSON support**,
we decided for **PostgreSQL**
and neglected **MongoDB, DynamoDB**,
to achieve **data integrity and flexible schemas**,
accepting **operational complexity of RDBMS**,
because **our team has PostgreSQL expertise and compliance requirements mandate ACID**.
```

**4. Alexandrian**
```yaml
format: alexandrian
```
Pattern-language inspired format with forces and resolution:

```markdown
# Use PostgreSQL for Persistence

## Context
A system that requires persistent storage with strong consistency...

## Forces
- Need for ACID transactions
- JSON document flexibility
- Team expertise in SQL
- Compliance requirements

## Problem
How do we store data reliably while maintaining schema flexibility?

## Solution
Use PostgreSQL with JSONB columns for flexible attributes...

## Resulting Context
The system now has...

## Related Patterns
- Event Sourcing (ADR-0015)
- CQRS (ADR-0016)
```

**5. Business Case**
```yaml
format: business-case
```
Extended template for decisions requiring business justification:

```markdown
# Migrate to Cloud Infrastructure

## Business Context
Current on-premise infrastructure costs...

## Problem Statement
...

## Proposed Solution
...

## Alternatives Analysis
| Option | Cost | Risk | Timeline |
|--------|------|------|----------|
| AWS    | $$   | Low  | 6 months |
| Azure  | $$$  | Med  | 4 months |
| GCP    | $$   | Low  | 5 months |

## Financial Impact
- Year 1: -$50K (migration)
- Year 2+: +$100K/year savings

## Risk Assessment
...

## Recommendation
...

## Approval
- [ ] Engineering Lead
- [ ] Finance
- [ ] Security
```

**6. Planguage**
```yaml
format: planguage
```
Quality-focused format with measurable criteria:

```markdown
# Response Time Optimization

## Tag
PERF-001

## Gist
Improve API response times to meet SLA requirements.

## Stakeholders
- Product: User experience
- Engineering: System performance
- Operations: Infrastructure costs

## Scale
Response time in milliseconds (p99)

## Meter
Application Performance Monitoring (Datadog)

## Past
p99: 850ms (baseline Q3 2024)

## Must
p99 ≤ 500ms

## Plan
p99 ≤ 200ms

## Wish
p99 ≤ 100ms

## Design Ideas
1. Add Redis caching layer
2. Optimize database queries
3. Implement CDN for static assets
```

#### Format Configuration

```bash
# Set repository default format
git adr config --set template.format madr

# Create ADR with specific format
git adr new "Use Redis" --format y-statement

# Convert existing ADR to different format
git adr convert <adr-id> --to madr

# Import with format detection
git adr import docs/adr/ --detect-format
```

#### Custom Templates

```bash
# Register custom template
git adr config --set template.custom.path ".adr-templates/my-template.md"

# Use custom template
git adr new "Decision Title" --format custom
```

---

### GitHub/GitLab Wiki Integration

Display ADRs in forge web UIs by syncing to the repository wiki.

#### Why Wiki?

Neither GitHub nor GitLab display git notes in their web interfaces—notes are completely invisible to web users. Rather than scatter ADRs across commit comments or discussions, we sync to the **wiki**, which provides:

| Benefit | Description |
|---------|-------------|
| Single browsable location | All ADRs in one place with navigation |
| Auto-generated indexes | TOC, by-status, by-tag filtered views |
| Full markdown rendering | Tables, code blocks, diagrams |
| Built-in search | Forge search indexes wiki content |
| Version history | Wiki is a git repo with full history |
| Offline access | Clone wiki repo locally |
| Web editing | Edit ADRs via browser (syncs back) |

#### How It Works

GitHub and GitLab wikis are separate git repositories:
- GitHub: `git@github.com:owner/repo.wiki.git`
- GitLab: `git@gitlab.com:group/project.wiki.git`

We clone the wiki, write ADRs as markdown pages, and push.

```
┌─────────────────────────────────────────────────────────────────┐
│                     SOURCE OF TRUTH                              │
│   refs/notes/adr (git notes in main repo)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ git adr wiki-sync
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     WIKI REPOSITORY                              │
│   architecture-decisions/                                        │
│   ├── _Sidebar.md          (navigation)                         │
│   ├── _index.md            (full ADR table)                     │
│   ├── 20251214-use-postgresql.md                                │
│   ├── 20251210-adopt-opentelemetry.md                           │
│   └── ...                                                        │
│   architecture-decisions-by-status/                              │
│   ├── accepted.md                                                │
│   ├── proposed.md                                                │
│   └── deprecated.md                                              │
│   architecture-decisions-by-tag/                                 │
│   ├── infrastructure.md                                          │
│   └── data-storage.md                                            │
└─────────────────────────────────────────────────────────────────┘
```

#### Configuration

```bash
# Auto-detect wiki URL from origin (works for GitHub/GitLab)
git adr wiki-init

# Or set explicitly
git adr config --set wiki.url "git@github.com:owner/repo.wiki.git"

# Wiki subdirectory for ADRs (default: architecture-decisions)
git adr config --set wiki.path "architecture-decisions"

# Generate filtered index pages (by status, by tag)
git adr config --set wiki.generate-indexes true

# Add brief pointer comments on linked commits (optional)
git adr config --set wiki.commit-pointers true
```

#### Commands

```bash
# Initialize wiki structure (creates directories, index templates)
git adr wiki-init

# Sync all ADRs to wiki
git adr wiki-sync

# Preview what would be written (dry-run)
git adr wiki-sync --dry-run

# Sync specific ADR only
git adr wiki-sync --adr 20251214-use-postgresql

# Pull wiki edits back to notes (if someone edited via web UI)
git adr wiki-sync --direction pull

# Full bidirectional sync
git adr wiki-sync --direction both
```

#### Generated Wiki Structure

**Index Page (`architecture-decisions/_index.md`):**

```markdown
# Architecture Decision Records

This wiki contains all Architecture Decision Records (ADRs) for this project.

## Quick Links

- [Proposed Decisions](../architecture-decisions-by-status/proposed) - 3 awaiting approval
- [Accepted Decisions](../architecture-decisions-by-status/accepted) - 32 active
- [All Tags](#by-category)

---

## All Decisions

| ID | Title | Status | Date |
|----|-------|--------|------|
| [20251214-use-postgresql](20251214-use-postgresql) | Use PostgreSQL for Persistence | ✅ accepted | 2025-12-14 |
| [20251210-adopt-opentelemetry](20251210-adopt-opentelemetry) | Adopt OpenTelemetry | ✅ accepted | 2025-12-10 |
| [20251205-migrate-to-arm64](20251205-migrate-to-arm64) | Migrate to ARM64 | 🟡 proposed | 2025-12-05 |

## By Category

- **infrastructure** (16): [View all](../architecture-decisions-by-tag/infrastructure)
- **data-storage** (11): [View all](../architecture-decisions-by-tag/data-storage)
- **api-design** (8): [View all](../architecture-decisions-by-tag/api-design)
```

**Individual ADR Page:**

```markdown
[← Back to Index](_index) | [By Status](../architecture-decisions-by-status/accepted)

---

| Status | Date | Deciders | Tags |
|--------|------|----------|------|
| `accepted` | 2025-12-14 | @alice, @bob | `data-storage`, `infrastructure` |

> **Supersedes:** [20230915-use-mongodb](20230915-use-mongodb)

# Use PostgreSQL for Persistence

## Context and Problem Statement

We need a primary data store that provides ACID compliance...

[... full ADR content ...]

## Implementing Commits

- [`a1b2c3d4`](../../commit/a1b2c3d4) - Add PostgreSQL connection pooling
- [`e5f6g7h8`](../../commit/e5f6g7h8) - Migrate user table to PostgreSQL

---

_Synced from git-adr • Last updated: 2025-12-14T10:30:00Z_
```

#### Optional: Commit Pointer Comments

When `wiki.commit-pointers` is enabled, brief pointer comments are added to linked commits:

```markdown
📋 **Related ADR:** [Use PostgreSQL for Persistence](../../wiki/architecture-decisions/20251214-use-postgresql)

Status: `accepted` | [View full decision →](../../wiki/architecture-decisions/20251214-use-postgresql)
```

This provides commit-level awareness without duplicating full ADR content.

#### GitHub Actions Workflow

```yaml
# .github/workflows/adr-wiki-sync.yml
name: Sync ADRs to Wiki

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  sync-wiki:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout main repo
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          
      - name: Fetch ADR notes
        run: git fetch origin refs/notes/adr:refs/notes/adr || true
        
      - name: Checkout wiki
        uses: actions/checkout@v4
        with:
          repository: ${{ github.repository }}.wiki
          path: wiki
          token: ${{ secrets.GITHUB_TOKEN }}
          
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          
      - name: Install git-adr
        run: pip install git-adr
        
      - name: Sync ADRs to wiki
        run: git adr wiki-sync --wiki-path ./wiki --verbose
          
      - name: Push wiki changes
        run: |
          cd wiki
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add .
          git diff --staged --quiet || git commit -m "Sync ADRs from main repo"
          git push
```

#### GitLab CI Pipeline

```yaml
# .gitlab-ci.yml
stages:
  - sync

adr-wiki-sync:
  stage: sync
  image: python:3.11-slim
  
  variables:
    GIT_STRATEGY: clone
    GIT_DEPTH: 0
    
  before_script:
    - pip install git-adr
    - git fetch origin refs/notes/adr:refs/notes/adr || true
    # Clone wiki repo
    - git clone "https://gitlab-ci-token:${CI_JOB_TOKEN}@gitlab.com/${CI_PROJECT_PATH}.wiki.git" wiki
    
  script:
    - git adr wiki-sync --wiki-path ./wiki
    - cd wiki
    - git config user.name "GitLab CI"
    - git config user.email "ci@gitlab.com"
    - git add .
    - git diff --staged --quiet || git commit -m "Sync ADRs"
    - git push
    
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

#### Bidirectional Sync

If someone edits an ADR via the wiki web UI:

```bash
# Pull wiki changes back to git notes
git adr wiki-sync --direction pull
```

**Conflict handling:**
- Git notes remain source of truth
- Wiki edits are detected by comparing timestamps
- Conflicts prompt for resolution (prefer notes, prefer wiki, or merge)

---

### Team Analytics

Decision velocity, participation metrics, and team collaboration insights.

#### Metrics Captured

**Velocity Metrics:**
- Decisions per time period (week/month/quarter)
- Average time from proposed → accepted
- Decision throughput by category/tag
- Trend analysis (accelerating/decelerating)

**Participation Metrics:**
- Decisions per team member
- Consultation frequency (who gets consulted most)
- Cross-team collaboration patterns
- Review participation rates

**Health Metrics:**
- Stale proposal rate (proposed > N days)
- Supersession frequency (how often decisions change)
- ADR coverage (commits with linked ADRs vs total)
- Documentation debt (deprecated ADRs not yet cleaned up)

#### Commands

**`git adr report --team`**

Extended report with team analytics:

```
👥 TEAM ANALYTICS (last 90 days)
─────────────────────────────────────────────────────────────────────────────────

Decision Velocity
  This quarter:  12 decisions (4/month avg)
  Last quarter:   8 decisions (2.7/month avg)
  Trend:         ▲ 50% increase

Time to Decision
  Avg proposed → accepted:  4.2 days
  Fastest:                  0.5 days (20251210-quick-fix)
  Slowest:                  21 days (20251115-major-refactor)

Participation Matrix
                    Decisions  Consultations  Reviews
  @alice            8          12             15
  @bob              5          8              11
  @carol            3          15             9
  @dave             2          4              8
  @eve              1          3              5
  
Collaboration Network
  infrastructure ←→ security    (6 shared decisions)
  api-design ←→ frontend        (4 shared decisions)
  data-storage ←→ infrastructure (3 shared decisions)

Coverage Analysis
  Commits with linked ADRs:     67% (234/350)
  Orphan commits (no ADR):      33% (116/350)
  High-impact commits w/o ADR:  12 ⚠️
  
Category Distribution
  ████████████████  infrastructure (16)
  ███████████░░░░░  data-storage (11)
  ████████░░░░░░░░  api-design (8)
  ██████░░░░░░░░░░  security (6)
  ████░░░░░░░░░░░░  testing (4)
```

**`git adr metrics`**

Export metrics for external dashboards:

```bash
# JSON for Datadog/Grafana
git adr metrics --format json --output metrics.json

# Prometheus exposition format
git adr metrics --format prometheus

# CSV for spreadsheet analysis
git adr metrics --format csv --period 1y --output adr-metrics.csv
```

**Prometheus Metrics Example:**
```prometheus
# HELP adr_total Total number of ADRs
# TYPE adr_total gauge
adr_total{status="accepted"} 32
adr_total{status="proposed"} 6
adr_total{status="deprecated"} 4
adr_total{status="superseded"} 5

# HELP adr_velocity_monthly Decisions per month (30-day rolling)
# TYPE adr_velocity_monthly gauge
adr_velocity_monthly 2.3

# HELP adr_time_to_decision_days Average days from proposed to accepted
# TYPE adr_time_to_decision_days gauge
adr_time_to_decision_days 4.2

# HELP adr_coverage_ratio Ratio of commits with linked ADRs
# TYPE adr_coverage_ratio gauge
adr_coverage_ratio 0.67
```

---

## Open Questions (Remaining)

1. **Offline-first vs sync-first** — Should forge sync be automatic on every `git adr` command, or explicit?
   - Current design: Explicit sync with optional auto-sync via CI/hooks

2. **API rate limits** — How to handle GitHub/GitLab rate limits during bulk sync?
   - Planned: Exponential backoff, batch operations, caching

3. **Conflict resolution** — If forge discussion diverges from git notes, which wins?
   - Planned: Git notes are source of truth; forge is read-mostly mirror

---

## Appendix

### MADR 4.0 Template Reference

```yaml
---
# YAML front matter (optional elements)
status: "{proposed | rejected | accepted | deprecated | superseded by ADR-NNNN}"
date: "{YYYY-MM-DD}"
decision-makers: ["{list of people}"]
consulted: ["{list of SMEs}"]
informed: ["{list of stakeholders}"]
---
# {Short title of solved problem and solution}

## Context and Problem Statement

{2-3 sentences describing the situation}

## Decision Drivers

* {Force or concern 1}
* {Force or concern 2}

## Considered Options

* {Option 1}
* {Option 2}

## Decision Outcome

Chosen option: "{Option}", because {justification}.

### Consequences

* Good, because {positive outcome}
* Bad, because {negative outcome}

### Confirmation

{How compliance will be verified}

## Pros and Cons of the Options

### {Option 1}

* Good, because {pro}
* Bad, because {con}

## More Information

{Links, references, related ADRs}
```

### Git Notes Command Reference

```bash
# Add note to commit
git notes --ref=refs/notes/adr add -m "content" <commit>

# Show note for commit
git notes --ref=refs/notes/adr show <commit>

# Edit note
git notes --ref=refs/notes/adr edit <commit>

# List all notes
git notes --ref=refs/notes/adr list

# Push notes to remote
git push origin refs/notes/adr

# Fetch notes from remote
git fetch origin refs/notes/adr:refs/notes/adr

# Show log with notes
git log --show-notes=refs/notes/adr
```

---

## References

- [MADR 4.0 Template](https://adr.github.io/madr/)
- [log4brains](https://github.com/thomvaill/log4brains)
- [Git Notes Documentation](https://git-scm.com/docs/git-notes)
- [adr-tools](https://github.com/npryce/adr-tools)
- [ADR GitHub Organization](https://adr.github.io/)
- [Michael Nygard's Original ADR Post](http://thinkrelevance.com/blog/2011/11/15/documenting-architecture-decisions)
