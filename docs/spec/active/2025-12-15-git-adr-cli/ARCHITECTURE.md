---
document_type: architecture
project_id: SPEC-2025-12-15-001
version: 1.0.0
last_updated: 2025-12-15T00:45:00Z
status: draft
---

# git-adr CLI - Technical Architecture

## System Overview

git-adr is a Python CLI application that extends git with Architecture Decision Record management capabilities. It stores ADRs as git notes attached to the repository's root tree object, providing invisible-in-worktree but visible-in-history documentation.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  CLI Layer (typer)                                                          │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐        │
│  │   init   │   new    │   list   │   show   │  search  │   edit   │        │
│  ├──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤        │
│  │   link   │supersede │   log    │   sync   │  config  │  attach  │        │
│  ├──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤        │
│  │  draft   │ suggest  │summarize │   ask    │  report  │  onboard │        │
│  ├──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤        │
│  │wiki-init │wiki-sync │  export  │  import  │  stats   │ metrics  │        │
│  └──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CORE LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │   ADR Model     │  │  Index Manager  │  │ Template Engine │              │
│  │  (core/adr.py)  │  │ (core/index.py) │  │(core/templates) │              │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘              │
│           │                    │                    │                       │
│  ┌────────▼────────────────────▼────────────────────▼────────┐              │
│  │                    Notes Manager                          │              │
│  │                    (core/notes.py)                        │              │
│  └────────────────────────────┬──────────────────────────────┘              │
│                               │                                             │
│  ┌────────────────────────────▼──────────────────────────────┐              │
│  │                    Git Executor                           │              │
│  │                    (core/git.py)                          │              │
│  └────────────────────────────┬──────────────────────────────┘              │
└───────────────────────────────┼─────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           INTEGRATION LAYER                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │   AI Module     │  │   Wiki Module   │  │ Analytics Module│              │
│  │    (ai/*.py)    │  │  (wiki/*.py)    │  │(core/analytics) │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL SYSTEMS                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ git binary  │  │  LLM APIs   │  │ GitHub/Lab  │  │   $EDITOR   │         │
│  │ (subprocess)│  │ (langchain) │  │  Wiki APIs  │  │  (environ)  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Git operations | subprocess to git binary | Industry standard (5/6 tools), zero deps, full parity |
| Note attachment | Root tree object | Survives rebase, independent of commits |
| CLI framework | typer | Type safety, auto-completion, rich integration |
| AI abstraction | langchain-core | Multi-provider support, active maintenance |
| Storage format | YAML frontmatter + Markdown | Human-readable, parseable, merge-friendly |

## Component Design

### Component 1: CLI Layer (`cli.py`, `commands/*.py`)

**Purpose**: Entry point for all user interactions

**Responsibilities**:
- Parse command-line arguments via typer
- Validate user input
- Route to appropriate command handlers
- Format and display output via rich
- Handle errors gracefully with helpful messages

**Interfaces**:
- Input: Command-line arguments, stdin (for piped content), environment variables
- Output: stdout (formatted), stderr (errors), exit codes

**Technology**: typer, rich

**Editor Integration** (for `new`, `edit` commands):
- Fallback chain: `$EDITOR` → `$VISUAL` → `vim` → `nano` → `vi`
- GUI editor detection: auto-adds `--wait` flag for VS Code, Sublime, Atom, etc.
- Alternative inputs: `--file <path>` or stdin (`cat file.md | git adr new "Title"`)
- `--no-edit` flag bypasses editor entirely (requires `--file` or stdin)
- `--preview` flag displays rendered template to stdout without creating ADR

**Key Classes**:
```python
# cli.py
app = typer.Typer(
    name="git-adr",
    help="Architecture Decision Records for git repositories",
    add_completion=True,
)

# Subcommand groups
app.add_typer(core_app, name="")        # Core commands (init, new, list, etc.)
app.add_typer(ai_app, name="")          # AI commands (draft, suggest, ask)
app.add_typer(wiki_app, name="wiki")    # Wiki commands (init, sync)
app.add_typer(artifact_app, name="")    # Artifact commands (attach, artifacts)
```

### Component 2: ADR Model (`core/adr.py`)

**Purpose**: Domain model for Architecture Decision Records

**Responsibilities**:
- Parse ADR content from markdown with YAML frontmatter
- Validate ADR structure and metadata
- Serialize ADR to storage format
- Track ADR relationships (supersedes, linked-commits)

**Interfaces**:
- Input: Raw markdown string, metadata dict
- Output: ADR dataclass, serialized markdown

**Key Classes**:
```python
@dataclass
class ADRMetadata:
    """YAML frontmatter fields."""
    status: ADRStatus
    date: date
    decision_makers: list[str]
    consulted: list[str]
    informed: list[str]
    tags: list[str]
    linked_commits: list[str]
    supersedes: str | None
    superseded_by: str | None
    artifacts: list[ArtifactRef]

@dataclass
class ADR:
    """Complete ADR with metadata and content."""
    id: str                    # e.g., "20251214-use-postgresql"
    title: str
    metadata: ADRMetadata
    content: str               # Markdown body
    format: ADRFormat          # MADR, Nygard, etc.

    @classmethod
    def from_markdown(cls, raw: str) -> "ADR": ...
    def to_markdown(self) -> str: ...

class ADRStatus(Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"
```

### Component 3: Notes Manager (`core/notes.py`)

**Purpose**: Interface to git notes operations

**Responsibilities**:
- Add, read, update, remove notes
- Manage namespaces (adr, adr-artifacts)
- Handle notes sync (push/pull)
- Configure notes behavior (merge strategy, rewrite)

**Interfaces**:
- Input: ADR ID, content, commit SHA
- Output: Note content, operation status

**Key Classes**:
```python
class NotesManager:
    """Manages git notes operations for ADRs."""

    ADR_REF = "refs/notes/adr"
    ARTIFACTS_REF = "refs/notes/adr-artifacts"

    def __init__(self, git: Git):
        self.git = git

    def add(self, adr_id: str, content: str) -> None:
        """Store ADR as note on root tree."""
        root_tree = self._get_root_tree()
        self.git.notes_add(content, root_tree, ref=self.ADR_REF)

    def get(self, adr_id: str) -> str | None:
        """Retrieve ADR content by ID."""
        ...

    def list_all(self) -> list[tuple[str, str]]:
        """List all ADR note references."""
        ...

    def sync_push(self, remote: str = "origin") -> None:
        """Push notes to remote."""
        self.git.run("push", remote, self.ADR_REF)

    def sync_pull(self, remote: str = "origin") -> None:
        """Fetch and merge notes from remote."""
        self.git.run("fetch", remote, f"{self.ADR_REF}:{self.ADR_REF}")
```

### Component 4: Index Manager (`core/index.py`)

**Purpose**: Maintain searchable index of all ADRs

**Responsibilities**:
- Create and update ADR index
- Enable fast listing and filtering
- Support search operations
- Handle index consistency

**Interfaces**:
- Input: ADR operations (add, update, delete)
- Output: Filtered/sorted ADR lists

**Key Classes**:
```python
@dataclass
class IndexEntry:
    """Single entry in the ADR index."""
    id: str
    title: str
    status: ADRStatus
    date: date
    tags: list[str]
    linked_commits: list[str]

class IndexManager:
    """Manages the ADR index note."""

    INDEX_ID = "__index__"

    def __init__(self, notes: NotesManager):
        self.notes = notes

    def rebuild(self) -> None:
        """Rebuild index from all ADRs."""
        ...

    def add_entry(self, adr: ADR) -> None:
        """Add ADR to index."""
        ...

    def query(
        self,
        status: ADRStatus | None = None,
        tags: list[str] | None = None,
        since: date | None = None,
        until: date | None = None,
    ) -> list[IndexEntry]:
        """Query index with filters."""
        ...

    def search(self, query: str, regex: bool = False) -> list[SearchResult]:
        """Full-text search across ADRs."""
        ...
```

### Component 5: Template Engine (`core/templates.py`, `formats/*.py`)

**Purpose**: Generate and parse ADR templates in multiple formats

**Responsibilities**:
- Provide templates for all supported formats
- Parse format-specific structure
- Convert between formats
- Support custom templates

**Key Classes**:
```python
class ADRFormat(Enum):
    MADR = "madr"
    NYGARD = "nygard"
    Y_STATEMENT = "y-statement"
    ALEXANDRIAN = "alexandrian"
    BUSINESS_CASE = "business-case"
    PLANGUAGE = "planguage"
    CUSTOM = "custom"

class TemplateEngine:
    """Template rendering and parsing."""

    def __init__(self, config: Config):
        self.config = config
        self._templates: dict[ADRFormat, Template] = {}

    def render(
        self,
        format: ADRFormat,
        title: str,
        **kwargs,
    ) -> str:
        """Render new ADR from template."""
        ...

    def parse(self, content: str) -> tuple[ADRFormat, ADR]:
        """Detect format and parse ADR."""
        ...

    def convert(self, adr: ADR, target_format: ADRFormat) -> ADR:
        """Convert ADR to different format."""
        ...
```

### Component 6: Git Executor (`core/git.py`)

**Purpose**: Safe interface to git binary via subprocess

**Responsibilities**:
- Locate git executable
- Execute git commands with proper error handling
- Parse git output
- Handle credentials transparently

**Key Classes**:
```python
class GitError(Exception):
    """Git command execution error."""
    def __init__(self, message: str, exit_code: int, stderr: str):
        super().__init__(message)
        self.exit_code = exit_code
        self.stderr = stderr

@dataclass
class GitResult:
    """Result of a git command execution."""
    stdout: str
    stderr: str
    exit_code: int

class Git:
    """Git command executor with proper error handling."""

    def __init__(self, repo_path: Path | None = None):
        self.git_path = self._find_git()
        self.repo_path = repo_path or Path.cwd()

    @staticmethod
    def _find_git() -> str:
        """Locate git executable with fallbacks."""
        git_path = shutil.which("git")
        if git_path:
            return git_path
        # Platform-specific fallbacks
        ...
        raise FileNotFoundError("git not found")

    def run(self, *args: str, check: bool = True) -> GitResult:
        """Execute a git command."""
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"

        result = subprocess.run(
            [self.git_path, *args],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            env=env,
        )
        ...

    # Convenience methods
    def notes_add(self, message: str, obj: str, ref: str) -> None: ...
    def notes_show(self, obj: str, ref: str) -> str | None: ...
    def notes_list(self, ref: str) -> list[tuple[str, str]]: ...
    def get_root_tree(self) -> str: ...
    def get_config(self, key: str) -> str | None: ...
    def set_config(self, key: str, value: str) -> None: ...
```

### Component 7: AI Module (`ai/*.py`)

**Purpose**: LLM integration for ADR assistance

**Responsibilities**:
- Abstract multiple AI providers
- Generate ADR drafts from context
- Suggest improvements
- Answer questions about ADR corpus

**Technology**: langchain-core, provider-specific packages

**Key Classes**:
```python
class AIProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    BEDROCK = "bedrock"
    AZURE = "azure"
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"

class AIConfig:
    """AI feature configuration."""
    enabled: bool
    provider: AIProvider
    model: str | None
    api_key: str | None
    endpoint: str | None

class AIAssistant:
    """AI-powered ADR assistance."""

    def __init__(self, config: AIConfig):
        self.llm = self._create_llm(config)

    def _create_llm(self, config: AIConfig) -> BaseChatModel:
        """Factory for LLM instances."""
        match config.provider:
            case AIProvider.OPENAI:
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(model=config.model, api_key=config.api_key)
            case AIProvider.ANTHROPIC:
                from langchain_anthropic import ChatAnthropic
                return ChatAnthropic(model=config.model, api_key=config.api_key)
            ...

    def draft_interactive(
        self,
        title: str,
        console: Console,
    ) -> str:
        """Guide user through ADR creation via Socratic elicitation.

        Asks sequential questions:
        1. Problem statement
        2. Options considered
        3. Decision drivers
        4. Trade-offs/consequences

        Synthesizes responses into complete ADR.
        """
        ...

    def draft_batch(
        self,
        title: str,
        commits: list[str] | None = None,
        context: str | None = None,
        options: list[str] | None = None,
    ) -> str:
        """Generate ADR draft from context (non-interactive)."""
        ...

    def suggest(self, adr: ADR, aspect: str = "all") -> list[Suggestion]:
        """Suggest improvements to ADR."""
        ...

    def ask(self, question: str, adrs: list[ADR]) -> Answer:
        """Answer question about ADR corpus."""
        ...
```

### Component 8: Wiki Module (`wiki/*.py`)

**Purpose**: Sync ADRs to GitHub/GitLab wikis

**Responsibilities**:
- Clone wiki repositories
- Render ADRs to wiki pages
- Generate index and navigation
- Handle bidirectional sync

**Key Classes**:
```python
class WikiPlatform(Enum):
    GITHUB = "github"
    GITLAB = "gitlab"

class WikiSync:
    """Synchronize ADRs to wiki."""

    def __init__(self, git: Git, config: WikiConfig):
        self.git = git
        self.config = config

    def detect_platform(self) -> WikiPlatform:
        """Detect GitHub vs GitLab from remote URL."""
        ...

    def init(self) -> None:
        """Initialize wiki structure."""
        ...

    def sync(self, direction: str = "push") -> None:
        """Sync ADRs to/from wiki."""
        ...

    def render_page(self, adr: ADR) -> str:
        """Render ADR as wiki page."""
        ...

    def generate_index(self, adrs: list[ADR]) -> str:
        """Generate index page."""
        ...

    def generate_sidebar(self, adrs: list[ADR]) -> str:
        """Generate navigation sidebar."""
        ...
```

### Component 9: Analytics Module (`core/analytics.py`)

**Purpose**: Calculate metrics and generate reports

**Responsibilities**:
- Calculate decision velocity
- Track participation metrics
- Identify high-impact ADRs
- Generate reports in multiple formats

**Key Classes**:
```python
@dataclass
class AnalyticsReport:
    """Comprehensive analytics report."""
    total_adrs: int
    by_status: dict[ADRStatus, int]
    velocity: float  # decisions per month
    avg_time_to_accept: timedelta
    high_impact: list[ADR]  # by linked commits
    by_tag: dict[str, int]
    by_contributor: dict[str, int]
    needs_attention: list[ADR]
    onboarding_sequence: list[str]

class Analytics:
    """ADR analytics and reporting."""

    def __init__(self, index: IndexManager, notes: NotesManager):
        self.index = index
        self.notes = notes

    def calculate(self, period: str = "all") -> AnalyticsReport:
        """Calculate all metrics."""
        ...

    def render_terminal(self, report: AnalyticsReport) -> str:
        """Render report for terminal."""
        ...

    def render_html(self, report: AnalyticsReport) -> str:
        """Render report as HTML."""
        ...

    def export_prometheus(self, report: AnalyticsReport) -> str:
        """Export metrics in Prometheus format."""
        ...
```

## Data Design

### Git Notes Structure

```
refs/notes/adr/                    # ADR content namespace
├── __index__                      # Index note (attached to root tree)
│   └── YAML listing all ADRs
├── __config__                     # Configuration note
│   └── YAML with repository settings
└── <adr-id>                       # Individual ADR notes
    └── YAML frontmatter + Markdown body

refs/notes/adr-artifacts/          # Binary artifacts namespace
└── <sha256-hash>                  # Content-addressed artifacts
    └── Binary blob
```

### ADR Storage Format

```yaml
---
status: accepted
date: 2025-12-14
decision-makers: [alice, bob]
consulted: [carol]
informed: [team-leads]
tags: [database, infrastructure]
linked-commits: [a1b2c3d4, e5f6g7h8]
supersedes: null
superseded-by: null
artifacts:
  - id: "sha256:abc123..."
    name: "architecture-diagram.png"
    type: "image/png"
    alt: "System architecture"
---

# Use PostgreSQL for Persistence

## Context and Problem Statement

We need a primary data store that provides ACID compliance...

[... rest of MADR content ...]
```

### Index Format

```yaml
git-adr-index:
  version: "1.0"
  updated: "2025-12-14T10:30:00Z"
  adrs:
    - id: "20251214-use-postgresql"
      title: "Use PostgreSQL for Persistence"
      status: accepted
      date: "2025-12-14"
      tags: [database, infrastructure]
      linked_commits: [a1b2c3d4]
    - id: "20251210-adopt-opentelemetry"
      title: "Adopt OpenTelemetry"
      status: accepted
      date: "2025-12-10"
      tags: [observability]
      linked_commits: []
```

### Configuration Format

```yaml
git-adr:
  version: "1.0"
  template: madr
  namespace: refs/notes/adr
  auto_link: true
  date_prefix: true
  artifact:
    max_size_mb: 10
    warn_size_mb: 1
  ai:
    enabled: false
    provider: openai
    model: null
  wiki:
    url: null
    path: architecture-decisions
    generate_indexes: true
    commit_pointers: false
```

## Data Flow

### Creating an ADR

```
┌──────┐    ┌─────────┐    ┌────────────┐    ┌─────────────┐    ┌─────────┐
│ User │───▶│   CLI   │───▶│  Template  │───▶│   $EDITOR   │───▶│  Notes  │
│      │    │ (new)   │    │  Engine    │    │  (user edit)│    │ Manager │
└──────┘    └─────────┘    └────────────┘    └─────────────┘    └────┬────┘
                                                                      │
                                                                      ▼
                                                               ┌─────────────┐
                                                               │    Index    │
                                                               │   Manager   │
                                                               └─────────────┘
```

### Syncing ADRs

```
┌──────────┐    ┌─────────┐    ┌───────────┐    ┌────────────┐
│  Local   │───▶│  Notes  │───▶│    Git    │───▶│   Remote   │
│  ADRs    │    │ Manager │    │  (push)   │    │ refs/notes │
└──────────┘    └─────────┘    └───────────┘    └────────────┘

┌────────────┐    ┌───────────┐    ┌─────────┐    ┌──────────┐
│   Remote   │───▶│    Git    │───▶│  Notes  │───▶│  Local   │
│ refs/notes │    │ (fetch)   │    │ Manager │    │  ADRs    │
└────────────┘    └───────────┘    └─────────┘    └──────────┘
```

## API Design (CLI Commands)

### Command Structure

```
git adr <command> [subcommand] [options] [arguments]
```

### Core Commands

| Command | Arguments | Options | Description |
|---------|-----------|---------|-------------|
| `init` | - | `--namespace`, `--template` | Initialize ADR tracking |
| `new` | `<title>` | `--status`, `--link`, `--tags`, `--no-edit`, `--draft` | Create ADR |
| `list` | - | `--status`, `--tag`, `--since`, `--until`, `--format`, `--reverse` | List ADRs |
| `show` | `<id>` | `--format`, `--metadata-only` | Display ADR |
| `edit` | `<id>` | `--status`, `--add-tag`, `--remove-tag`, `--link`, `--unlink` | Modify ADR |
| `search` | `<query>` | `--context`, `--status`, `--tag`, `--case-sensitive`, `--regex` | Search ADRs |
| `link` | `<id> <commit>...` | `--unlink` | Link ADR to commits |
| `supersede` | `<id> <title>` | - | Create superseding ADR |
| `log` | - | (git log options) | Show annotated log |
| `sync` | `[remote]` | `--push`, `--pull`, `--merge-strategy` | Sync notes |
| `config` | `[key] [value]` | `--list`, `--get`, `--set`, `--global` | Manage config |

### Short Aliases

| Alias | Command |
|-------|---------|
| `n` | `new` |
| `l` | `list` |
| `s` | `search` |
| `e` | `edit` |

## Integration Points

### Internal Integrations

| System | Integration Type | Purpose |
|--------|-----------------|---------|
| Git | subprocess | All repository operations |
| $EDITOR | subprocess | ADR editing |
| File system | stdlib | Temporary files, config |

### External Integrations

| Service | Integration Type | Purpose |
|---------|-----------------|---------|
| OpenAI API | HTTP/langchain | AI features |
| Anthropic API | HTTP/langchain | AI features |
| GitHub Wiki | git clone/push | Wiki sync |
| GitLab Wiki | git clone/push | Wiki sync |
| GitHub API | PyGithub (optional) | Commit comments |
| GitLab API | python-gitlab (optional) | Commit comments |

## Security Design

### Authentication

- **Git operations**: Inherit git's credential system entirely
- **AI APIs**: API keys stored in git config (local, not committed) or environment variables
- **Wiki access**: Uses git credentials for clone/push

### Input Validation

```python
def validate_adr_id(id: str) -> bool:
    """Validate ADR ID format."""
    # Date-based: YYYYMMDD-slug
    # Sequential: NNNN-slug
    pattern = r"^(\d{8}|\d{4})-[a-z0-9-]+$"
    return bool(re.match(pattern, id))

def validate_tags(tags: list[str]) -> list[str]:
    """Sanitize and validate tags."""
    return [
        re.sub(r"[^a-z0-9-]", "", tag.lower())
        for tag in tags
        if tag
    ]
```

### Security Considerations

| Threat | Mitigation |
|--------|------------|
| Command injection | Use subprocess list args, never shell=True |
| Path traversal | Validate all file paths, use pathlib |
| YAML bombs | Use safe_load only, limit document size |
| API key exposure | Never store in notes, use config/env |
| Malicious ADR content | Sanitize for wiki output, escape HTML |

## Performance Considerations

### Expected Load

| Metric | Target |
|--------|--------|
| ADRs per repo | Up to 10,000 |
| Notes per command | Typically 1-100 |
| Artifacts per ADR | Typically 0-5 |

### Optimization Strategies

1. **Index caching**: Keep parsed index in memory during session
2. **Lazy loading**: Only load full ADR content when needed
3. **Batch operations**: Group git operations where possible
4. **Streaming output**: Use rich's Live for progress on long operations

### Performance Targets

| Operation | Target | Strategy |
|-----------|--------|----------|
| `list` (1000 ADRs) | < 500ms | Index-only, no content load |
| `show` | < 100ms | Single note fetch |
| `search` | < 1s | Stream results |
| `sync` | Git-bound | Parallel where possible |

## Reliability & Operations

### Error Handling

```python
class GitADRError(Exception):
    """Base exception for git-adr."""
    pass

class ADRNotFoundError(GitADRError):
    """ADR with given ID not found."""
    pass

class NotesNotInitializedError(GitADRError):
    """ADR notes not initialized in this repository."""
    pass

class SyncConflictError(GitADRError):
    """Conflict during notes sync."""
    pass
```

### Graceful Degradation

| Scenario | Behavior |
|----------|----------|
| No network | Work offline, warn on sync |
| AI unavailable | Skip AI features, inform user |
| Wiki unavailable | Skip wiki sync, inform user |
| Invalid ADR found | Skip in listing, warn user |

### Monitoring

- Exit codes: 0 (success), 1 (error), 2 (user error)
- Verbose mode: `--verbose` for detailed output
- Debug mode: `GIT_ADR_DEBUG=1` for full traces

## Testing Strategy

### Unit Testing

- All core modules independently testable
- Mock Git class for isolated testing
- Test all ADR formats parsing/rendering

### Integration Testing

- Use temporary git repositories
- Test actual git operations
- Test command-line interface end-to-end

### Fixtures

```python
@pytest.fixture
def temp_git_repo(tmp_path: Path) -> Iterator[Path]:
    """Create initialized git repository."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo)
    # Create initial commit
    (repo / "README.md").write_text("# Test")
    subprocess.run(["git", "add", "."], cwd=repo)
    subprocess.run(["git", "commit", "-m", "Initial"], cwd=repo)
    yield repo

@pytest.fixture
def initialized_adr_repo(temp_git_repo: Path) -> Iterator[Path]:
    """Repository with ADR notes initialized."""
    # Run git adr init
    ...
    yield temp_git_repo
```

### Test Coverage Targets

| Module | Target |
|--------|--------|
| core/git.py | 95% |
| core/adr.py | 95% |
| core/notes.py | 90% |
| core/index.py | 90% |
| formats/*.py | 95% |
| commands/*.py | 85% |
| ai/*.py | 80% |

## Deployment Considerations

### Package Structure

```
git-adr/
├── pyproject.toml
├── src/
│   └── git_adr/
│       ├── __init__.py
│       ├── __main__.py        # Entry point
│       ├── cli.py             # Main typer app
│       ├── commands/          # Command implementations
│       │   ├── __init__.py
│       │   ├── init.py
│       │   ├── new.py
│       │   ├── list.py
│       │   └── ...
│       ├── core/              # Core functionality
│       │   ├── __init__.py
│       │   ├── adr.py
│       │   ├── git.py
│       │   ├── notes.py
│       │   ├── index.py
│       │   ├── templates.py
│       │   └── analytics.py
│       ├── formats/           # ADR format handlers
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── madr.py
│       │   ├── nygard.py
│       │   └── ...
│       ├── ai/                # AI integration
│       │   ├── __init__.py
│       │   ├── providers.py
│       │   ├── draft.py
│       │   └── ...
│       ├── wiki/              # Wiki integration
│       │   ├── __init__.py
│       │   ├── sync.py
│       │   └── ...
│       └── utils/             # Utilities
│           ├── __init__.py
│           ├── editor.py
│           ├── output.py
│           └── tui.py
└── tests/
    ├── conftest.py
    ├── test_commands/
    ├── test_core/
    ├── test_formats/
    └── test_ai/
```

### Installation Entry Point

```toml
[project.scripts]
git-adr = "git_adr.cli:main"
```

Git automatically discovers `git-adr` in PATH as a subcommand, enabling `git adr`.

### Configuration Locations

| Scope | Location |
|-------|----------|
| Repository | `.git/config` or note |
| User | `~/.gitconfig` |
| System | `/etc/gitconfig` |

## Future Considerations

1. **MCP Server**: Expose git-adr as MCP tools for Claude integration
2. **VS Code Extension**: Inline ADR viewing/editing
3. **GitHub App**: Display ADRs in pull request UI
4. **Multi-repo federation**: Cross-repository ADR discovery
5. **Webhooks**: Notify on ADR changes
