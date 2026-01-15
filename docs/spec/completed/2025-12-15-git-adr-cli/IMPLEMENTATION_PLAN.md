---
document_type: implementation_plan
project_id: SPEC-2025-12-15-001
version: 1.0.0
last_updated: 2025-12-15T01:00:00Z
status: draft
---

# git-adr CLI - Implementation Plan

## Overview

This plan covers the complete implementation of git-adr from the existing CLI skeleton to a production-ready v1.0.0 release. The work is organized into 4 phases with clear deliverables and dependencies.

## Phase Summary

| Phase | Focus | Key Deliverables |
|-------|-------|------------------|
| Phase 1 | Core MVP | Git notes storage, core commands, multi-format |
| Phase 2 | Intelligence & Integration | AI features, wiki sync, analytics |
| Phase 3 | Onboarding & Export | Interactive wizard, export formats, import |
| Phase 4 | Polish | Documentation, CI/CD, final QA |

---

## Phase 1: Core MVP (v0.5.0)

**Goal**: Establish the foundational git notes architecture and core command set

**Prerequisites**: Existing CLI skeleton, test infrastructure

### 1.1 Project Setup & Migration

#### Task 1.1.1: Migrate CLI from click to typer
- **Description**: Replace click dependency with typer, update CLI structure
- **Acceptance Criteria**:
  - [ ] pyproject.toml updated with typer>=0.9.0, rich>=13.0
  - [ ] cli.py refactored to use typer.Typer()
  - [ ] `git adr --help` shows formatted help
  - [ ] Shell completion generation works
  - [ ] All existing tests pass
- **Dependencies**: None

#### Task 1.1.2: Update Python version requirement
- **Description**: Lower minimum Python to 3.11, verify compatibility
- **Acceptance Criteria**:
  - [ ] pyproject.toml requires-python updated to ">=3.11"
  - [ ] CI tests against 3.11, 3.12, 3.13
  - [ ] No 3.12+ only features used
- **Dependencies**: None

#### Task 1.1.3: Add core dependencies
- **Description**: Add python-frontmatter, mistune for markdown handling
- **Acceptance Criteria**:
  - [ ] Dependencies added to pyproject.toml
  - [ ] Import validation tests pass
- **Dependencies**: 1.1.1

### 1.2 Core Infrastructure

#### Task 1.2.1: Implement Git executor (core/git.py)
- **Description**: Create subprocess wrapper for git operations
- **Acceptance Criteria**:
  - [ ] Git class with run() method
  - [ ] GitError exception with exit code, stderr
  - [ ] GitResult dataclass for output
  - [ ] Git executable discovery with fallbacks
  - [ ] GIT_TERMINAL_PROMPT=0 for non-interactive
  - [ ] Unit tests with mocked subprocess
- **Dependencies**: 1.1.1

#### Task 1.2.2: Implement git notes operations
- **Description**: Add notes-specific methods to Git class
- **Acceptance Criteria**:
  - [ ] notes_add(message, obj, ref) method
  - [ ] notes_show(obj, ref) method
  - [ ] notes_list(ref) method
  - [ ] notes_remove(obj, ref) method
  - [ ] get_root_tree() method
  - [ ] Integration tests with real git repos
- **Dependencies**: 1.2.1

#### Task 1.2.3: Implement ADR model (core/adr.py)
- **Description**: Create ADR dataclass with parsing/serialization
- **Acceptance Criteria**:
  - [ ] ADRMetadata dataclass with all fields
  - [ ] ADR dataclass with from_markdown/to_markdown
  - [ ] ADRStatus enum
  - [ ] YAML frontmatter parsing via python-frontmatter
  - [ ] Unit tests for parse/serialize roundtrip
- **Dependencies**: 1.1.3

#### Task 1.2.4: Implement Notes Manager (core/notes.py)
- **Description**: High-level interface for ADR notes operations
- **Acceptance Criteria**:
  - [ ] NotesManager class with Git dependency
  - [ ] ADR_REF and ARTIFACTS_REF constants
  - [ ] add(), get(), list_all(), remove() methods
  - [ ] sync_push(), sync_pull() methods
  - [ ] Integration tests with temp repos
- **Dependencies**: 1.2.2

#### Task 1.2.5: Implement Index Manager (core/index.py)
- **Description**: ADR index for fast listing/querying
- **Acceptance Criteria**:
  - [ ] IndexEntry dataclass
  - [ ] IndexManager with CRUD operations
  - [ ] query() with status/tag/date filters
  - [ ] search() with full-text support
  - [ ] rebuild() for index reconstruction
  - [ ] Unit and integration tests
- **Dependencies**: 1.2.4

#### Task 1.2.6: Implement Configuration (core/config.py)
- **Description**: Configuration management via git config
- **Acceptance Criteria**:
  - [ ] Config dataclass with all settings
  - [ ] Load from git config (local + global)
  - [ ] Save to git config
  - [ ] Default values for all settings
  - [ ] Unit tests
- **Dependencies**: 1.2.1

### 1.3 Core Commands

#### Task 1.3.1: Implement `git adr init`
- **Description**: Initialize ADR tracking in repository
- **Acceptance Criteria**:
  - [ ] Creates refs/notes/adr namespace
  - [ ] Stores configuration note
  - [ ] Configures fetch/push for notes
  - [ ] Configures notes.rewriteRef for rebase safety
  - [ ] Creates initial ADR (0000-use-adrs)
  - [ ] --namespace and --template options
  - [ ] Idempotent (safe to run twice)
  - [ ] Integration tests
- **Dependencies**: 1.2.4, 1.2.6

#### Task 1.3.2: Implement `git adr new`
- **Description**: Create new ADR with editor flow and multiple input modes
- **Acceptance Criteria**:
  - [ ] Generates date-based ID (YYYYMMDD-slug)
  - [ ] Creates template from configured format
  - [ ] Editor flow with GUI detection (adds --wait for code/subl/atom)
  - [ ] Editor fallback chain: $EDITOR → $VISUAL → vim → nano → vi
  - [ ] `--file <path>` option to use file content instead of editor
  - [ ] Stdin support: `cat file.md | git adr new "Title"`
  - [ ] Stores as note on root tree
  - [ ] Updates index
  - [ ] --status, --link, --tags, --no-edit, --draft options
  - [ ] `--preview` to display template without creating ADR
  - [ ] Integration tests for all input modes
- **Dependencies**: 1.3.1, 1.3.6

#### Task 1.3.3: Implement `git adr list`
- **Description**: List all ADRs with filtering
- **Acceptance Criteria**:
  - [ ] Table output with rich formatting
  - [ ] --status, --tag, --since, --until filters
  - [ ] --format (table, json, csv, oneline)
  - [ ] --reverse for chronological order
  - [ ] Pager integration for long output
  - [ ] Unit and integration tests
- **Dependencies**: 1.2.5

#### Task 1.3.4: Implement `git adr show`
- **Description**: Display single ADR with formatting
- **Acceptance Criteria**:
  - [ ] Markdown rendering with syntax highlighting
  - [ ] Shows linked commits
  - [ ] Shows supersedes/superseded-by relationships
  - [ ] --format (markdown, yaml, json)
  - [ ] --metadata-only option
  - [ ] Integration tests
- **Dependencies**: 1.2.4

#### Task 1.3.5: Implement `git adr edit`
- **Description**: Modify existing ADR
- **Acceptance Criteria**:
  - [ ] Opens ADR in $EDITOR
  - [ ] Updates note with new content
  - [ ] --status quick status change
  - [ ] --add-tag, --remove-tag
  - [ ] --link, --unlink commits
  - [ ] Preserves history (notes are versioned)
  - [ ] Integration tests
- **Dependencies**: 1.2.4

#### Task 1.3.6: Implement Template Engine (core/templates.py)
- **Description**: Multi-format template rendering
- **Acceptance Criteria**:
  - [ ] TemplateEngine class
  - [ ] render() for new ADRs
  - [ ] parse() with format detection
  - [ ] convert() between formats
  - [ ] Support for custom templates
  - [ ] Unit tests for all formats
- **Dependencies**: 1.2.3

#### Task 1.3.7: Implement `git adr search`
- **Description**: Full-text search across ADRs
- **Acceptance Criteria**:
  - [ ] Searches title, content
  - [ ] Highlighted snippets in results
  - [ ] --context lines option
  - [ ] --status, --tag filters
  - [ ] --case-sensitive, --regex options
  - [ ] Integration tests
- **Dependencies**: 1.2.5

#### Task 1.3.8: Implement `git adr link`
- **Description**: Associate ADR with commits
- **Acceptance Criteria**:
  - [ ] Updates linked-commits in ADR metadata
  - [ ] Supports multiple commits
  - [ ] --unlink to remove associations
  - [ ] Validates commit SHAs exist
  - [ ] Integration tests
- **Dependencies**: 1.2.4

#### Task 1.3.9: Implement `git adr supersede`
- **Description**: Create replacement ADR
- **Acceptance Criteria**:
  - [ ] Creates new ADR with supersedes reference
  - [ ] Updates original ADR status to superseded
  - [ ] Sets superseded_by on original
  - [ ] Integration tests
- **Dependencies**: 1.3.2

#### Task 1.3.10: Implement `git adr log`
- **Description**: Git log with ADR annotations
- **Acceptance Criteria**:
  - [ ] Wraps git log --show-notes=refs/notes/adr
  - [ ] Formatted ADR summaries inline
  - [ ] Passes through git log options
  - [ ] Integration tests
- **Dependencies**: 1.2.1

#### Task 1.3.11: Implement `git adr sync`
- **Description**: Push/pull notes to remotes
- **Acceptance Criteria**:
  - [ ] --push to push notes
  - [ ] --pull to fetch and merge
  - [ ] --merge-strategy option (union, ours, theirs)
  - [ ] Default remote detection
  - [ ] Conflict handling with clear messages
  - [ ] Integration tests (requires remote setup)
- **Dependencies**: 1.2.4

#### Task 1.3.12: Implement `git adr config`
- **Description**: Configuration management CLI
- **Acceptance Criteria**:
  - [ ] --list to show all config
  - [ ] --get <key> to read value
  - [ ] --set <key> <value> to write
  - [ ] --global for user-level config
  - [ ] Tab completion for known keys
  - [ ] Integration tests
- **Dependencies**: 1.2.6

### 1.4 Multi-Format Support

#### Task 1.4.1: Implement MADR 4.0 format
- **Description**: Full MADR template (default)
- **Acceptance Criteria**:
  - [ ] Complete template with all sections
  - [ ] Parser for MADR structure
  - [ ] Serializer preserving format
  - [ ] Unit tests
- **Dependencies**: 1.3.6

#### Task 1.4.2: Implement Nygard format
- **Description**: Original minimal ADR format
- **Acceptance Criteria**:
  - [ ] Template: Status, Context, Decision, Consequences
  - [ ] Parser and serializer
  - [ ] Unit tests
- **Dependencies**: 1.3.6

#### Task 1.4.3: Implement Y-Statement format
- **Description**: Single-sentence decision format
- **Acceptance Criteria**:
  - [ ] Template with structured sentence
  - [ ] Parser and serializer
  - [ ] Unit tests
- **Dependencies**: 1.3.6

#### Task 1.4.4: Implement Alexandrian format
- **Description**: Pattern-language inspired format
- **Acceptance Criteria**:
  - [ ] Template: Context, Forces, Problem, Solution, Resulting Context
  - [ ] Parser and serializer
  - [ ] Unit tests
- **Dependencies**: 1.3.6

#### Task 1.4.5: Implement Business Case format
- **Description**: Extended business justification template
- **Acceptance Criteria**:
  - [ ] Template with financial/risk sections
  - [ ] Approval workflow fields
  - [ ] Parser and serializer
  - [ ] Unit tests
- **Dependencies**: 1.3.6

#### Task 1.4.6: Implement Planguage format
- **Description**: Quality-focused measurable format
- **Acceptance Criteria**:
  - [ ] Template: Tag, Gist, Scale, Meter, Past, Must, Plan, Wish
  - [ ] Parser and serializer
  - [ ] Unit tests
- **Dependencies**: 1.3.6

#### Task 1.4.7: Implement `git adr convert`
- **Description**: Convert ADR between formats
- **Acceptance Criteria**:
  - [ ] --to <format> option
  - [ ] Preserves content during conversion
  - [ ] Warns about format-specific loss
  - [ ] Integration tests
- **Dependencies**: 1.4.1 - 1.4.6

### 1.5 Artifact Support

#### Task 1.5.1: Implement artifact storage
- **Description**: Store binary artifacts in separate namespace
- **Acceptance Criteria**:
  - [ ] refs/notes/adr-artifacts namespace
  - [ ] Content-addressed storage (SHA256)
  - [ ] Size limit enforcement (warn >1MB, refuse >10MB)
  - [ ] Unit tests
- **Dependencies**: 1.2.4

#### Task 1.5.2: Implement `git adr attach`
- **Description**: Attach file to ADR
- **Acceptance Criteria**:
  - [ ] Stores file in artifacts namespace
  - [ ] Updates ADR metadata with reference
  - [ ] --alt option for alt text
  - [ ] Size validation
  - [ ] Integration tests
- **Dependencies**: 1.5.1

#### Task 1.5.3: Implement `git adr artifacts`
- **Description**: List artifacts for ADR
- **Acceptance Criteria**:
  - [ ] Table output with name, type, size
  - [ ] Integration tests
- **Dependencies**: 1.5.1

#### Task 1.5.4: Implement `git adr artifact-get`
- **Description**: Extract artifact to file
- **Acceptance Criteria**:
  - [ ] --output option for destination
  - [ ] Default to original filename
  - [ ] Integration tests
- **Dependencies**: 1.5.1

#### Task 1.5.5: Implement `git adr artifact-rm`
- **Description**: Remove artifact from ADR
- **Acceptance Criteria**:
  - [ ] Removes reference from ADR metadata
  - [ ] Note: blob remains in git (garbage collected later)
  - [ ] Integration tests
- **Dependencies**: 1.5.1

### Phase 1 Deliverables

- [ ] All core commands functional
- [ ] All 6 ADR formats supported
- [ ] Artifact attachment support
- [ ] 90%+ test coverage
- [ ] Type checking passes (mypy --strict)
- [ ] Security scan clean (bandit)

---

## Phase 2: Intelligence & Integration (v0.8.0)

**Goal**: Add AI assistance, wiki integration, and analytics

**Prerequisites**: Phase 1 complete

### 2.1 AI Infrastructure

#### Task 2.1.1: Implement AI provider abstraction
- **Description**: LangChain-based multi-provider support
- **Acceptance Criteria**:
  - [ ] AIProvider enum
  - [ ] AIConfig dataclass
  - [ ] Factory for LLM instances
  - [ ] Provider configuration via git config
  - [ ] Unit tests with mocked providers
- **Dependencies**: Phase 1

#### Task 2.1.2: Implement OpenAI provider
- **Description**: Primary AI provider support
- **Acceptance Criteria**:
  - [ ] langchain-openai integration
  - [ ] GPT-4, GPT-4-mini, o3 model support
  - [ ] API key from config/environment
  - [ ] Integration tests (optional, require API key)
- **Dependencies**: 2.1.1

#### Task 2.1.3: Implement Anthropic provider
- **Description**: Secondary AI provider support
- **Acceptance Criteria**:
  - [ ] langchain-anthropic integration
  - [ ] Claude opus/sonnet/haiku support
  - [ ] API key handling
  - [ ] Integration tests (optional)
- **Dependencies**: 2.1.1

#### Task 2.1.4: Implement additional providers
- **Description**: Google, Bedrock, Azure, Ollama, OpenRouter
- **Acceptance Criteria**:
  - [ ] Each provider package added to extras
  - [ ] Factory handles all providers
  - [ ] Ollama works without API key (local)
  - [ ] Unit tests for factory
- **Dependencies**: 2.1.1

### 2.2 AI Commands

#### Task 2.2.1: Implement `git adr draft`
- **Description**: AI-guided ADR creation with interactive elicitation
- **Acceptance Criteria**:
  - [ ] **Interactive mode (default)**: Socratic elicitation process
    - [ ] Asks: "What problem are you solving?"
    - [ ] Asks: "What options have you considered?"
    - [ ] Asks: "What's driving this decision?"
    - [ ] Asks: "What are the trade-offs/consequences?"
    - [ ] Synthesizes answers into complete ADR
  - [ ] `--batch` flag for one-shot generation (no prompts)
  - [ ] Analyzes recent commits if --from-commits specified
  - [ ] Accepts --context for additional background
  - [ ] Generates complete ADR in configured format
  - [ ] Opens in $EDITOR for final review
  - [ ] Integration tests with mocked LLM
- **Dependencies**: 2.1.1

#### Task 2.2.2: Implement `git adr suggest`
- **Description**: AI suggestions for improvements
- **Acceptance Criteria**:
  - [ ] --aspect option (context, options, consequences, all)
  - [ ] Returns actionable suggestions
  - [ ] Respects existing ADR content
  - [ ] Integration tests
- **Dependencies**: 2.1.1

#### Task 2.2.3: Implement `git adr summarize`
- **Description**: Natural language summary of decisions
- **Acceptance Criteria**:
  - [ ] --period option (7d, 30d, 90d, etc.)
  - [ ] --format (markdown, slack, email, standup)
  - [ ] Concise, useful summaries
  - [ ] Integration tests
- **Dependencies**: 2.1.1

#### Task 2.2.4: Implement `git adr ask`
- **Description**: Natural language Q&A
- **Acceptance Criteria**:
  - [ ] Queries ADR corpus
  - [ ] Returns answer with citations
  - [ ] Handles "why did we choose X?" queries
  - [ ] Integration tests
- **Dependencies**: 2.1.1

### 2.3 Wiki Integration

#### Task 2.3.1: Implement wiki platform detection
- **Description**: Auto-detect GitHub vs GitLab
- **Acceptance Criteria**:
  - [ ] Parse remote URL
  - [ ] Detect github.com, gitlab.com, custom instances
  - [ ] Unit tests
- **Dependencies**: Phase 1

#### Task 2.3.2: Implement wiki clone/push
- **Description**: Git operations for wiki repo
- **Acceptance Criteria**:
  - [ ] Clone wiki repo to temp directory
  - [ ] Commit and push changes
  - [ ] Handle authentication via git credentials
  - [ ] Integration tests (require wiki access)
- **Dependencies**: 2.3.1

#### Task 2.3.3: Implement ADR to wiki rendering
- **Description**: Convert ADR to wiki page
- **Acceptance Criteria**:
  - [ ] Render metadata as header table
  - [ ] Format supersedes/superseded-by links
  - [ ] Link to implementing commits
  - [ ] Footer with sync timestamp
  - [ ] Unit tests
- **Dependencies**: Phase 1

#### Task 2.3.4: Implement index generation
- **Description**: Generate wiki index pages
- **Acceptance Criteria**:
  - [ ] Main index with all ADRs table
  - [ ] By-status pages (accepted, proposed, etc.)
  - [ ] By-tag pages
  - [ ] Unit tests
- **Dependencies**: 2.3.3

#### Task 2.3.5: Implement sidebar generation
- **Description**: Platform-specific navigation
- **Acceptance Criteria**:
  - [ ] GitHub _Sidebar.md format
  - [ ] GitLab sidebar format
  - [ ] Unit tests
- **Dependencies**: 2.3.3

#### Task 2.3.6: Implement `git adr wiki-init`
- **Description**: Initialize wiki structure
- **Acceptance Criteria**:
  - [ ] Detects platform
  - [ ] Creates directory structure
  - [ ] Stores wiki URL in config
  - [ ] Integration tests
- **Dependencies**: 2.3.1 - 2.3.5

#### Task 2.3.7: Implement `git adr wiki-sync`
- **Description**: Full wiki synchronization
- **Acceptance Criteria**:
  - [ ] Default: push to wiki
  - [ ] --direction pull for reverse
  - [ ] --dry-run option
  - [ ] --adr option for single ADR
  - [ ] Integration tests
- **Dependencies**: 2.3.6

#### Task 2.3.8: Implement bidirectional sync
- **Description**: Pull wiki edits back to notes
- **Acceptance Criteria**:
  - [ ] Detect wiki changes by timestamp
  - [ ] Conflict resolution (notes win by default)
  - [ ] --direction both option
  - [ ] Integration tests
- **Dependencies**: 2.3.7

#### Task 2.3.9: Create CI/CD templates
- **Description**: GitHub Actions and GitLab CI for wiki sync
- **Acceptance Criteria**:
  - [ ] .github/workflows/adr-wiki-sync.yml template
  - [ ] .gitlab-ci.yml template
  - [ ] Documentation for setup
- **Dependencies**: 2.3.7

### 2.4 Analytics & Reporting

#### Task 2.4.1: Implement analytics calculations
- **Description**: Core metrics engine
- **Acceptance Criteria**:
  - [ ] Total ADRs, by status
  - [ ] Decision velocity (per month)
  - [ ] Average time to accept
  - [ ] High-impact ADRs (by commits)
  - [ ] By-tag breakdown
  - [ ] Needs attention detection
  - [ ] Unit tests
- **Dependencies**: Phase 1

#### Task 2.4.2: Implement `git adr stats`
- **Description**: Quick statistics summary
- **Acceptance Criteria**:
  - [ ] One-line summary format
  - [ ] --json option
  - [ ] Integration tests
- **Dependencies**: 2.4.1

#### Task 2.4.3: Implement `git adr report` terminal output
- **Description**: Full dashboard in terminal
- **Acceptance Criteria**:
  - [ ] Rich formatting with panels/tables
  - [ ] All sections from product brief
  - [ ] Respects terminal width
  - [ ] Integration tests
- **Dependencies**: 2.4.1

#### Task 2.4.4: Implement `git adr report` HTML output
- **Description**: Static HTML dashboard
- **Acceptance Criteria**:
  - [ ] Single-page with Chart.js
  - [ ] Dark/light mode
  - [ ] Print-friendly
  - [ ] --output option
  - [ ] Integration tests
- **Dependencies**: 2.4.1

#### Task 2.4.5: Implement `git adr report --team`
- **Description**: Team collaboration metrics
- **Acceptance Criteria**:
  - [ ] Per-contributor stats
  - [ ] Consultation patterns
  - [ ] Cross-team analysis
  - [ ] Integration tests
- **Dependencies**: 2.4.1

#### Task 2.4.6: Implement `git adr metrics`
- **Description**: Export metrics for dashboards
- **Acceptance Criteria**:
  - [ ] --format json
  - [ ] --format prometheus
  - [ ] --format csv
  - [ ] --output option
  - [ ] Integration tests
- **Dependencies**: 2.4.1

### Phase 2 Deliverables

- [ ] AI features functional with all providers
- [ ] Wiki sync for GitHub and GitLab
- [ ] Full analytics dashboard
- [ ] CI/CD templates included
- [ ] Documentation updated

---

## Phase 3: Onboarding & Export (v0.9.0)

**Goal**: Complete user journey with onboarding and import/export

**Prerequisites**: Phase 2 complete

### 3.1 Onboarding

#### Task 3.1.1: Implement onboarding sequence detection
- **Description**: Determine recommended ADR reading order
- **Acceptance Criteria**:
  - [ ] Identify foundational ADRs
  - [ ] Sort by importance (linked commits, supersession)
  - [ ] Role-based filtering
  - [ ] Unit tests
- **Dependencies**: Phase 2

#### Task 3.1.2: Implement `git adr onboard` TUI
- **Description**: Interactive guided tour
- **Acceptance Criteria**:
  - [ ] Rich-based TUI
  - [ ] ADR display with navigation
  - [ ] Progress indicator
  - [ ] Keyboard shortcuts (n/p/s/b/q)
  - [ ] Integration tests
- **Dependencies**: 3.1.1

#### Task 3.1.3: Implement role-based paths
- **Description**: Different tracks for different roles
- **Acceptance Criteria**:
  - [ ] --role developer|reviewer|architect
  - [ ] Filters ADRs by relevance
  - [ ] Adjusts reading time estimates
  - [ ] Integration tests
- **Dependencies**: 3.1.2

#### Task 3.1.4: Implement progress tracking
- **Description**: Track onboarding completion
- **Acceptance Criteria**:
  - [ ] Store progress in git config
  - [ ] --status to show progress
  - [ ] --continue to resume
  - [ ] Integration tests
- **Dependencies**: 3.1.2

#### Task 3.1.5: Implement `git adr onboard --quick`
- **Description**: 5-minute executive summary
- **Acceptance Criteria**:
  - [ ] Top 3-5 foundational ADRs only
  - [ ] Streamlined presentation
  - [ ] Integration tests
- **Dependencies**: 3.1.2

### 3.2 Export

#### Task 3.2.1: Implement Markdown export
- **Description**: Export ADRs to markdown files
- **Acceptance Criteria**:
  - [ ] Individual files per ADR
  - [ ] Index file
  - [ ] --output directory
  - [ ] Integration tests
- **Dependencies**: Phase 1

#### Task 3.2.2: Implement JSON export
- **Description**: Machine-readable export
- **Acceptance Criteria**:
  - [ ] All ADRs with metadata
  - [ ] Index structure
  - [ ] --output file or stdout
  - [ ] Integration tests
- **Dependencies**: Phase 1

#### Task 3.2.3: Implement HTML export
- **Description**: Static site generation
- **Acceptance Criteria**:
  - [ ] log4brains-compatible styling
  - [ ] Index with navigation
  - [ ] Syntax highlighting
  - [ ] --template option for custom
  - [ ] Integration tests
- **Dependencies**: Phase 1

#### Task 3.2.4: Implement docx export
- **Description**: Word document export
- **Acceptance Criteria**:
  - [ ] python-docx integration
  - [ ] Proper formatting
  - [ ] Single document or per-ADR
  - [ ] Integration tests
- **Dependencies**: Phase 1 + python-docx

#### Task 3.2.5: Implement Mermaid rendering
- **Description**: Render .mermaid artifacts to SVG
- **Acceptance Criteria**:
  - [ ] mermaid-py integration
  - [ ] Include in HTML export
  - [ ] Integration tests
- **Dependencies**: 3.2.3 + mermaid-py

### 3.3 Import

#### Task 3.3.1: Implement file-based ADR detection
- **Description**: Find existing ADRs in docs/adr/
- **Acceptance Criteria**:
  - [ ] Scan common locations
  - [ ] Detect format (MADR, Nygard, etc.)
  - [ ] Unit tests
- **Dependencies**: Phase 1

#### Task 3.3.2: Implement `git adr import`
- **Description**: Import file-based ADRs to notes
- **Acceptance Criteria**:
  - [ ] --format to specify source format
  - [ ] --detect-format for auto-detection
  - [ ] --link-by-date to associate with commits
  - [ ] Preview mode (--dry-run)
  - [ ] Integration tests
- **Dependencies**: 3.3.1

#### Task 3.3.3: Implement log4brains import
- **Description**: Specific support for log4brains projects
- **Acceptance Criteria**:
  - [ ] Parse log4brains directory structure
  - [ ] Preserve metadata
  - [ ] Integration tests
- **Dependencies**: 3.3.2

### Phase 3 Deliverables

- [ ] Interactive onboarding wizard
- [ ] All export formats functional
- [ ] Import from file-based ADRs
- [ ] Documentation updated

---

## Phase 4: Polish (v1.0.0)

**Goal**: Production readiness, documentation, final QA

**Prerequisites**: Phase 3 complete

### 4.1 Documentation

#### Task 4.1.1: Write comprehensive README
- **Description**: User-facing documentation
- **Acceptance Criteria**:
  - [ ] Installation instructions
  - [ ] Quick start guide
  - [ ] Command reference
  - [ ] Configuration reference
  - [ ] FAQ section
- **Dependencies**: Phase 3

#### Task 4.1.2: Write API documentation
- **Description**: Developer documentation
- **Acceptance Criteria**:
  - [ ] All public modules documented
  - [ ] Docstrings complete
  - [ ] Type hints complete
  - [ ] Examples included
- **Dependencies**: Phase 3

#### Task 4.1.3: Create examples repository
- **Description**: Example ADRs and workflows
- **Acceptance Criteria**:
  - [ ] Sample ADRs in each format
  - [ ] Common workflow examples
  - [ ] CI/CD integration examples
- **Dependencies**: Phase 3

### 4.2 CI/CD & Quality

#### Task 4.2.1: Comprehensive CI pipeline
- **Description**: GitHub Actions for all checks
- **Acceptance Criteria**:
  - [ ] Tests on Python 3.11, 3.12, 3.13
  - [ ] Tests on Linux, macOS, Windows
  - [ ] Coverage reporting
  - [ ] Type checking
  - [ ] Security scanning
  - [ ] Lint checking
- **Dependencies**: Phase 3

#### Task 4.2.2: Release automation
- **Description**: Automated PyPI publishing
- **Acceptance Criteria**:
  - [ ] Tag-triggered releases
  - [ ] Changelog generation
  - [ ] PyPI publishing
  - [ ] GitHub release creation
- **Dependencies**: 4.2.1

#### Task 4.2.3: Security audit
- **Description**: Final security review
- **Acceptance Criteria**:
  - [ ] bandit scan clean
  - [ ] pip-audit clean
  - [ ] Manual review of sensitive areas
  - [ ] SECURITY.md file
- **Dependencies**: Phase 3

### 4.3 Final QA

#### Task 4.3.1: End-to-end testing
- **Description**: Full workflow tests
- **Acceptance Criteria**:
  - [ ] Create → Edit → Supersede workflow
  - [ ] Sync to remote workflow
  - [ ] Wiki sync workflow
  - [ ] Import → Export roundtrip
  - [ ] AI features (with mocks)
- **Dependencies**: Phase 3

#### Task 4.3.2: Performance testing
- **Description**: Verify performance targets
- **Acceptance Criteria**:
  - [ ] list with 1000 ADRs < 500ms
  - [ ] show < 100ms
  - [ ] search < 1s
  - [ ] Document results
- **Dependencies**: Phase 3

#### Task 4.3.3: Usability review
- **Description**: UX improvements
- **Acceptance Criteria**:
  - [ ] Error messages are helpful
  - [ ] Help text is clear
  - [ ] Shell completion works
  - [ ] Colors respect NO_COLOR
- **Dependencies**: Phase 3

### 4.4 Launch Preparation

#### Task 4.4.1: Branding
- **Description**: Logo and visual identity
- **Acceptance Criteria**:
  - [ ] Logo design
  - [ ] README badges
  - [ ] Social preview image
- **Dependencies**: None

#### Task 4.4.2: Create CHANGELOG
- **Description**: User-facing changelog
- **Acceptance Criteria**:
  - [ ] All features documented
  - [ ] Breaking changes noted
  - [ ] Migration guide if needed
- **Dependencies**: Phase 3

#### Task 4.4.3: Publish v1.0.0
- **Description**: Initial public release
- **Acceptance Criteria**:
  - [ ] PyPI package published
  - [ ] GitHub release created
  - [ ] Announcement prepared
- **Dependencies**: All above

### Phase 4 Deliverables

- [ ] Complete documentation
- [ ] CI/CD fully automated
- [ ] Security audit passed
- [ ] Performance targets met
- [ ] v1.0.0 published to PyPI

---

## Dependency Graph

```
Phase 1: Core MVP
━━━━━━━━━━━━━━━━━
1.1.1 (typer) ─────────────────┐
1.1.2 (python 3.11) ───────────┤
1.1.3 (deps) ──────────────────┼──▶ 1.2.1 (git.py)
                               │         │
                               │         ▼
                               │    1.2.2 (notes ops)
                               │         │
                               │         ▼
                               └───▶ 1.2.3 (adr.py)
                                         │
                                    1.2.4 (notes mgr)
                                         │
                               ┌─────────┼─────────┐
                               ▼         ▼         ▼
                          1.2.5     1.2.6     1.3.6
                         (index)   (config) (templates)
                               │         │         │
                               └─────────┼─────────┘
                                         │
                          ┌──────────────┼──────────────┐
                          ▼              ▼              ▼
                     1.3.1-12       1.4.1-7        1.5.1-5
                   (commands)      (formats)     (artifacts)

Phase 2: Integration
━━━━━━━━━━━━━━━━━━━━
Phase 1 ──▶ 2.1.1 (AI infra) ──▶ 2.1.2-4 (providers) ──▶ 2.2.1-4 (AI cmds)
       └──▶ 2.3.1-9 (wiki)
       └──▶ 2.4.1-6 (analytics)

Phase 3: Onboarding
━━━━━━━━━━━━━━━━━━━
Phase 2 ──▶ 3.1.1-5 (onboarding)
       └──▶ 3.2.1-5 (export)
       └──▶ 3.3.1-3 (import)

Phase 4: Polish
━━━━━━━━━━━━━━━
Phase 3 ──▶ 4.1-4 (docs, CI, QA, launch)
```

---

## Risk Mitigation Tasks

| Risk | Mitigation Task | Phase |
|------|-----------------|-------|
| Notes not synced | Auto-configure in init (1.3.1) | 1 |
| Notes lost on rebase | Configure rewriteRef (1.3.1) | 1 |
| AI API changes | Abstraction layer (2.1.1) | 2 |
| Wiki access issues | Clear error messages (2.3.7) | 2 |
| Large artifacts | Size limits (1.5.1) | 1 |

---

## Testing Checklist

### Unit Tests
- [ ] core/git.py
- [ ] core/adr.py
- [ ] core/notes.py
- [ ] core/index.py
- [ ] core/templates.py
- [ ] core/config.py
- [ ] core/analytics.py
- [ ] formats/*.py
- [ ] ai/providers.py
- [ ] wiki/sync.py

### Integration Tests
- [ ] All commands with temp repos
- [ ] Format roundtrips
- [ ] Sync operations
- [ ] Wiki operations (mocked)
- [ ] AI operations (mocked)

### End-to-End Tests
- [ ] Full ADR lifecycle
- [ ] Multi-user sync scenario
- [ ] Import/export roundtrip

---

## Launch Checklist

- [ ] All tests passing (>90% coverage)
- [ ] Type checking clean (mypy --strict)
- [ ] Security scan clean
- [ ] Documentation complete
- [ ] README polished
- [ ] CHANGELOG written
- [ ] CI/CD fully automated
- [ ] Performance targets verified
- [ ] PyPI package metadata complete
- [ ] GitHub release prepared
