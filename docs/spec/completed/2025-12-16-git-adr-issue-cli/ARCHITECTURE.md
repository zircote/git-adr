---
document_type: architecture
project_id: SPEC-2025-12-16-001
version: 1.0.0
last_updated: 2025-12-16T00:00:00Z
status: draft
---

# Git ADR Issue CLI - Technical Architecture

## System Overview

The `git adr issue` command extends the existing git-adr CLI with GitHub issue creation capabilities. It follows established patterns from the codebase: Typer-based CLI with Rich console output, modular command implementation, and clean separation between CLI interface and core logic.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          git adr issue                              │
├─────────────────────────────────────────────────────────────────────┤
│  CLI Layer (cli.py)                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ @app.command("issue")                                           ││
│  │ def issue(type, title, body, labels, assignee, ...)             ││
│  └─────────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────┤
│  Command Layer (commands/issue.py)                                  │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ def run_issue(type, title, body, ...) -> None                   ││
│  │   1. Load templates via TemplateManager                         ││
│  │   2. Resolve type to template                                   ││
│  │   3. Collect input (flags + interactive prompts)                ││
│  │   4. Build issue content                                        ││
│  │   5. Preview and confirm                                        ││
│  │   6. Submit via GitHubIssueClient or save locally               ││
│  └─────────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────┤
│  Core Layer (core/)                                                 │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────────┐│
│  │ template.py     │ │ issue.py        │ │ gh_client.py            ││
│  │ TemplateManager │ │ Issue           │ │ GitHubIssueClient       ││
│  │ IssueTemplate   │ │ IssueBuilder    │ │ - check_installation()  ││
│  │ FormElement     │ │                 │ │ - check_auth()          ││
│  │                 │ │                 │ │ - create_issue()        ││
│  └─────────────────┘ └─────────────────┘ └─────────────────────────┘│
├─────────────────────────────────────────────────────────────────────┤
│  External Dependencies                                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────────────┐ │
│  │ frontmatter  │ │ pyyaml       │ │ rich         │ │ gh CLI      │ │
│  │ (parse .md)  │ │ (parse .yml) │ │ (prompts/UI) │ │ (submit)    │ │
│  └──────────────┘ └──────────────┘ └──────────────┘ └─────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **Follow existing git-adr patterns** - Typer commands, Rich console, command-in-commands-dir structure
2. **Optional gh CLI dependency** - Graceful fallback to local file when gh unavailable
3. **Template-first approach** - Parse project templates rather than hardcoding structures
4. **Hybrid input model** - Flags for scripting, prompts for interactive use

## Component Design

### Component 1: TemplateManager (`core/issue_template.py`)

**Purpose**: Parse and manage GitHub issue templates from bundled defaults and optional project overrides

**Template Resolution Order** (highest priority first):
1. Project's `.github/ISSUE_TEMPLATE/` (user customizations)
2. git-adr bundled templates in `src/git_adr/templates/issues/` (always available, even offline/air-gapped)

**Responsibilities**:
- Load bundled default templates from package resources (works offline)
- Discover project-specific templates that can override bundled defaults
- Parse both markdown (`.md`) and YAML form (`.yml`) templates
- Maintain type alias mappings (bug → bug_report, feat → feature_request, docs → documentation)
- Provide template lookup by type or filename

**Interfaces**:
```python
class TemplateManager:
    def __init__(self, repo_root: Path | None = None) -> None: ...
    def get_bundled_templates(self) -> list[IssueTemplate]: ...
    def get_project_templates(self) -> list[IssueTemplate]: ...
    def discover_templates(self) -> list[IssueTemplate]: ...  # Merged, project overrides bundled
    def get_template(self, type_or_name: str) -> IssueTemplate | None: ...
    def get_available_types(self) -> list[str]: ...
```

**Dependencies**: python-frontmatter, pyyaml, pathlib, importlib.resources

**Technology**: Pure Python with dataclasses, package resources for bundled templates

### Component 2: IssueTemplate & FormElement (`core/issue_template.py`)

**Purpose**: Data models for parsed templates

**Responsibilities**:
- Store template metadata (name, description, title prefix, labels, assignees)
- Store template body structure (sections for .md, form elements for .yml)
- Provide iteration over promptable fields

**Data Models**:
```python
@dataclass
class FormElement:
    """A form element from YAML issue forms."""
    type: Literal["markdown", "input", "textarea", "dropdown", "checkboxes"]
    id: str | None
    attributes: dict[str, Any]  # label, description, placeholder, options, etc.
    validations: dict[str, Any]  # required, etc.

    @property
    def label(self) -> str | None: ...
    @property
    def required(self) -> bool: ...
    @property
    def placeholder(self) -> str | None: ...

@dataclass
class TemplateSection:
    """A section from markdown templates (## Header + content)."""
    header: str
    hint: str  # Parsed from content placeholder text
    required: bool = False

@dataclass
class IssueTemplate:
    """Parsed GitHub issue template."""
    name: str
    description: str  # 'about' in .md, 'description' in .yml
    title_prefix: str | None
    labels: list[str]
    assignees: list[str]

    # Content structure
    sections: list[TemplateSection]  # For .md templates
    form_elements: list[FormElement]  # For .yml templates

    # Source info
    source_file: Path
    template_format: Literal["markdown", "yaml"]

    @property
    def promptable_fields(self) -> Iterator[TemplateSection | FormElement]: ...
```

### Component 3: IssueBuilder (`core/issue.py`)

**Purpose**: Construct issue content from user input

**Responsibilities**:
- Collect values for each template field
- Validate required fields
- Render final markdown body from template + values
- Support partial builds (for preview)

**Interfaces**:
```python
@dataclass
class Issue:
    """A complete issue ready for submission."""
    title: str
    body: str
    labels: list[str]
    assignees: list[str]

class IssueBuilder:
    def __init__(self, template: IssueTemplate) -> None: ...
    def set_title(self, title: str) -> IssueBuilder: ...
    def set_field(self, field_id: str, value: str | list[str]) -> IssueBuilder: ...
    def is_complete(self) -> bool: ...
    def missing_required_fields(self) -> list[str]: ...
    def build(self) -> Issue: ...
    def preview(self) -> str: ...
```

### Component 4: InteractivePrompter (`commands/issue.py`)

**Purpose**: Guide user through template fields interactively

**Responsibilities**:
- Display field headers and hints
- Prompt for input using Rich Prompt/Confirm
- Handle multi-line input for textarea fields
- Handle dropdown/checkbox selections
- Skip fields already provided via flags

**Key Patterns**:
```python
def prompt_for_field(
    field: TemplateSection | FormElement,
    console: Console
) -> str | list[str]:
    """Prompt user for a single field value."""

    if isinstance(field, FormElement):
        if field.type == "input":
            return Prompt.ask(field.label, default=field.placeholder or "")
        elif field.type == "textarea":
            # Multi-line input or editor
            ...
        elif field.type == "dropdown":
            # Selection from options
            ...
        elif field.type == "checkboxes":
            # Multiple selection
            ...
    else:
        # TemplateSection from .md
        console.print(f"[bold]## {field.header}[/bold]")
        console.print(f"[dim]{field.hint}[/dim]")
        return Prompt.ask(">")
```

### Component 5: GitHubIssueClient (`core/gh_client.py`)

**Purpose**: Interface with gh CLI for issue submission

**Responsibilities**:
- Check if gh is installed
- Check if gh is authenticated
- Submit issues via `gh issue create`
- Parse response (issue URL, number)
- Handle errors with meaningful messages

**Interfaces**:
```python
@dataclass
class IssueCreateResult:
    success: bool
    issue_url: str | None = None
    issue_number: int | None = None
    error: str | None = None

class GitHubIssueClient:
    def __init__(self, repo: str | None = None) -> None: ...

    @classmethod
    def is_available(cls) -> bool:
        """Check if gh CLI is installed."""

    @classmethod
    def is_authenticated(cls) -> tuple[bool, str | None]:
        """Check if gh is authenticated, return (success, username)."""

    def create_issue(self, issue: Issue) -> IssueCreateResult: ...
```

**Implementation Notes**:
- Uses subprocess to invoke gh CLI
- Passes body via stdin (`--body-file -`) to avoid shell escaping issues
- Timeout of 60 seconds for network operations

### Component 6: LocalIssueStorage (`commands/issue.py`)

**Purpose**: Save issues locally when gh is unavailable

**Responsibilities**:
- Generate timestamped filename
- Write issue markdown to configurable directory
- Support draft recovery

**Output Format**:
```markdown
---
title: "[BUG] Application crashes on startup"
labels: [bug]
assignees: []
template: bug_report
created: 2025-12-16T10:30:00Z
status: draft
---

## Description

Application crashes immediately after launch...

## Steps to Reproduce

1. Open the app
2. See crash
...
```

**Default Location**: `.github/issues/drafts/YYYY-MM-DD-HH-MM-title-slug.md`

## Data Flow

```
User Input                    Template                      Output
───────────                   ────────                      ──────

--type bug ──────────────┐    bug_report.md
--title "Title"          │    ┌─────────────┐
                         │    │ name: ...   │
                         ├───►│ about: ...  │
Interactive prompts      │    │ labels: ... │
                         │    │ ---         │               Issue Object
[Description]: ...       │    │ ## Desc     │    ┌───────────────────────┐
[Steps]: ...            ─┴───►│ ## Steps    │───►│ title: "[BUG] Title"  │
                              │ ## Expected │    │ body: "## Desc\n..."  │
                              └─────────────┘    │ labels: ["bug"]       │
                                                 └───────────────────────┘
                                                           │
                                                           ▼
                                                 ┌─────────────────────┐
                                     Preview ◄───┤  Confirmation Flow  │
                                                 └─────────────────────┘
                                                           │
                                      ┌────────────────────┼────────────────────┐
                                      ▼                    ▼                    ▼
                               ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
                               │ Edit in     │     │ Submit via  │     │ Save Local  │
                               │ $EDITOR     │     │ gh CLI      │     │ File        │
                               └─────────────┘     └─────────────┘     └─────────────┘
```

## API Design

### CLI Interface

```bash
git adr issue [OPTIONS]

Options:
  -t, --type TEXT        Issue type (bug, feat, docs) or template filename
  --title TEXT           Issue title (skips prompt)
  --description TEXT     Main description (skips prompt)
  -l, --label TEXT       Additional labels (repeatable)
  -a, --assignee TEXT    Assignees (repeatable, use @me for self)
  --local-only           Save locally, don't submit to GitHub
  --dry-run              Preview only, don't create or save
  --no-edit              Skip editor preview step
  --repo TEXT            Target repo (OWNER/REPO format)
  -h, --help             Show help
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | User cancelled |
| 3 | Template not found |
| 4 | gh CLI not available (when --local-only not set) |
| 5 | gh CLI not authenticated |

## Integration Points

### Internal Integrations

| System | Integration Type | Purpose |
|--------|-----------------|---------|
| git-adr core (Git class) | Import | Get repo root, detect git context |
| git-adr config (ConfigManager) | Import | Read adr.issue.* config options |
| Rich console | Import | Consistent output formatting |

### External Integrations

| Service | Integration Type | Purpose |
|---------|-----------------|---------|
| gh CLI | subprocess | Issue submission |
| $EDITOR | subprocess | Edit preview |
| .github/ISSUE_TEMPLATE/ | Filesystem | Template source |

## Security Design

### Input Handling

- User input is **never** passed directly to shell commands
- Body content sent via stdin to avoid injection
- Template content treated as data, never executed

### Credential Management

- **No credentials stored** by this feature
- Delegates all authentication to gh CLI
- No token handling in Python code

### Security Considerations

| Threat | Mitigation |
|--------|------------|
| Command injection via title/body | Use subprocess list form, body via stdin |
| Malicious template content | Parse as data only, no eval/exec |
| Credential exposure | Delegate to gh CLI, no token handling |

## Testing Strategy

### Unit Testing

```python
# test_issue_template.py
class TestTemplateParser:
    def test_parse_markdown_template(self): ...
    def test_parse_yaml_form(self): ...
    def test_handle_missing_frontmatter(self): ...
    def test_extract_sections_from_body(self): ...

class TestIssueBuilder:
    def test_build_complete_issue(self): ...
    def test_missing_required_field(self): ...
    def test_render_markdown_body(self): ...

# test_gh_client.py
class TestGitHubIssueClient:
    def test_is_available_when_installed(self): ...
    def test_is_available_when_not_installed(self): ...
    def test_create_issue_success(self, mock_subprocess): ...
    def test_create_issue_auth_failure(self, mock_subprocess): ...
```

### Integration Testing

```python
# test_issue_integration.py
@pytest.mark.integration
class TestIssueCommand:
    def test_interactive_bug_report(self, temp_git_repo): ...
    def test_flags_skip_prompts(self, temp_git_repo): ...
    def test_local_only_mode(self, temp_git_repo): ...
    def test_dry_run_mode(self, temp_git_repo): ...
```

### Test Fixtures

```python
@pytest.fixture
def sample_bug_template(tmp_path) -> Path:
    """Create a sample bug report template."""
    template_dir = tmp_path / ".github" / "ISSUE_TEMPLATE"
    template_dir.mkdir(parents=True)
    (template_dir / "bug_report.md").write_text("""---
name: Bug Report
about: Report a bug
title: "[BUG] "
labels: bug
---

## Description
Describe the bug

## Steps to Reproduce
1. Step one
2. Step two
""")
    return tmp_path
```

## Deployment Considerations

### No Additional Infrastructure

This is a CLI feature - no servers, databases, or external services required beyond what git-adr already uses.

### Configuration Options

```ini
# In git config (local or global)
adr.issue.template_dir = .github/ISSUE_TEMPLATE  # Default
adr.issue.draft_dir = .github/issues/drafts      # Default
adr.issue.default_type = bug                      # Default type if not specified
```

### Feature Flag (Future)

If gradual rollout desired, could use:
```ini
adr.experimental.issue = true
```

## File Structure

```
src/git_adr/
├── cli.py                    # Add @app.command("issue")
├── commands/
│   └── issue.py              # NEW: run_issue() implementation
├── core/
│   ├── issue_template.py     # NEW: TemplateManager, IssueTemplate
│   ├── issue.py              # NEW: Issue, IssueBuilder
│   └── gh_client.py          # NEW: GitHubIssueClient
└── templates/
    └── issues/               # NEW: Bundled templates (static assets, work offline)
        ├── bug_report.md     # Default bug report template
        ├── feature_request.md # Default feature request template
        └── documentation.md  # Default documentation request template

tests/
├── test_issue_template.py    # NEW: Template parsing tests
├── test_issue.py             # NEW: Issue building tests
├── test_gh_client.py         # NEW: gh CLI integration tests
└── test_issue_integration.py # NEW: End-to-end tests
```

**Note**: Bundled templates in `src/git_adr/templates/issues/` are included as package data via `importlib.resources`. They provide offline/air-gapped capability. Project-specific templates in `.github/ISSUE_TEMPLATE/` override bundled defaults when present.

## Future Considerations

1. **YAML form field type support** - Full support for dropdown, checkboxes, etc.
2. **Issue linking** - Link issues to ADRs (`git adr link --issue #123`)
3. **Issue templates in ADR context** - Generate "ADR discussion" issues
4. **GitHub Enterprise support** - Custom API endpoints
5. **GitLab/Bitbucket support** - Alternative providers
