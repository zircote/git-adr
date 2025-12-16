---
document_type: research
project_id: SPEC-2025-12-16-001
last_updated: 2025-12-16T00:00:00Z
---

# Git ADR Issue CLI - Research Notes

## Research Summary

This document captures key findings from codebase exploration and technical research conducted during the planning phase.

## Codebase Analysis

### Relevant Files Examined

| File | Purpose | Relevance |
|------|---------|-----------|
| `src/git_adr/cli.py` | Main CLI entry point | Pattern for adding new commands |
| `src/git_adr/commands/new.py` | ADR creation command | Pattern for interactive input, editor integration |
| `src/git_adr/commands/list.py` | ADR listing | Pattern for output formatting |
| `src/git_adr/core/adr.py` | ADR data model | Pattern for dataclasses with frontmatter |
| `src/git_adr/core/config.py` | Configuration management | Pattern for git config integration |
| `tests/conftest.py` | Test fixtures | Pattern for temp git repos |
| `.github/ISSUE_TEMPLATE/bug_report.md` | Bug template | Source template to parse |
| `.github/ISSUE_TEMPLATE/feature_request.md` | Feature template | Source template to parse |

### Existing Patterns Identified

1. **Typer CLI Pattern**:
   ```python
   @app.command()
   def command_name(
       arg: Annotated[str, typer.Argument(help="...")],
       option: Annotated[str, typer.Option(...)] = "default",
   ) -> None:
   ```

2. **Command Structure**: CLI wrapper in `cli.py`, implementation in `commands/<name>.py` with `run_<name>()` function

3. **Rich Console**: Use `console = Console()` for styled output, panels, tables

4. **Frontmatter Parsing**: Use `frontmatter.loads(content)` to parse YAML frontmatter

5. **Editor Integration**: GUI_EDITORS dict for wait flags, $EDITOR fallback

6. **Error Handling**: Typer exit codes, rich error messages

### Integration Points

- **Git class** (`core/git.py`): Get repo root via `get_git(cwd=Path.cwd())`
- **ConfigManager** (`core/config.py`): Read `adr.*` config from git
- **Console utilities**: Existing Rich setup for consistent output

## Technical Research

### GitHub Issue Template Formats

**Markdown Templates (.md)**:
- YAML frontmatter with: `name`, `about`, `title`, `labels`, `assignees`
- Markdown body with section headers
- Project already uses `python-frontmatter` (v1.0.0+)

**YAML Issue Forms (.yml)**:
- Full structured format with `body` array
- Element types: markdown, input, textarea, dropdown, checkboxes
- Project already uses `pyyaml` (v6.0.0+)

### Best Practices Found

| Topic | Source | Key Insight |
|-------|--------|-------------|
| Template parsing | GitHub Docs | Both .md and .yml supported, YAML forms are newer |
| gh CLI automation | gh CLI manual | Use `--body-file -` for stdin body, exit code 4 = auth required |
| Subprocess patterns | Python docs | Use list form for args, never shell=True with user input |

### Recommended Approaches

1. **Template Discovery**: Scan `.github/ISSUE_TEMPLATE/` for both `.md` and `.yml`
2. **Body Handling**: Use stdin via `--body-file -` to avoid escaping issues
3. **Auth Check**: Use `gh auth status` with exit code checking (4 = not auth'd)

### Anti-Patterns to Avoid

1. **Shell string building**: Never build command strings with user input
2. **Credential storage**: Delegate all auth to gh CLI
3. **Hardcoded templates**: Auto-discover to support custom templates

## gh CLI Integration

### Installation Detection

```python
import shutil
shutil.which("gh") is not None
```

### Authentication Check

```python
result = subprocess.run(["gh", "auth", "status"], capture_output=True)
# Exit code 0 = authenticated
# Exit code 4 = not authenticated
```

### Issue Creation

```python
subprocess.run(
    ["gh", "issue", "create",
     "--title", title,
     "--body-file", "-",
     "--label", "bug",
     "--repo", "owner/repo"],
    input=body_text,
    capture_output=True,
    text=True
)
# stdout = issue URL on success
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Cancelled |
| 4 | Auth required |

## Existing Issue Templates

### bug_report.md

```yaml
---
name: Bug Report
about: Report a bug or unexpected behavior
title: "[BUG] "
labels: bug
assignees: ""
---
```

Sections:
- Description
- Steps to Reproduce
- Expected Behavior
- Actual Behavior
- Environment
- Additional Context
- Logs/Output

### feature_request.md

```yaml
---
name: Feature Request
about: Suggest a new feature or enhancement
title: "[FEATURE] "
labels: enhancement
assignees: ""
---
```

Sections:
- Problem Statement
- Proposed Solution
- Example Usage
- Alternatives Considered
- Additional Context

## Dependencies Analysis

### Existing Dependencies (Can Reuse)

| Dependency | Version | Purpose |
|------------|---------|---------|
| python-frontmatter | >=1.0.0 | Parse .md template frontmatter |
| pyyaml | >=6.0.0 | Parse .yml form templates |
| rich | >=13.0.0 | Console prompts and output |
| typer | >=0.9.0 | CLI framework |

### External Dependencies (Optional)

| Service | Required | Fallback |
|---------|----------|----------|
| gh CLI | No | Local file storage |
| $EDITOR | No | Simple prompts |

## Sources

- [GitHub Issue Templates Documentation](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository)
- [GitHub Issue Forms Schema](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms)
- [gh CLI Manual - issue create](https://cli.github.com/manual/gh_issue_create)
- [gh CLI Manual - exit codes](https://cli.github.com/manual/gh_help_exit-codes)
- [python-frontmatter Documentation](https://python-frontmatter.readthedocs.io/)
