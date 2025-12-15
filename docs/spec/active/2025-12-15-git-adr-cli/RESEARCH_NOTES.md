---
document_type: research
project_id: SPEC-2025-12-15-001
last_updated: 2025-12-15T01:15:00Z
---

# git-adr CLI - Research Notes

## Research Summary

Two parallel research tracks were conducted:
1. **Git extension patterns**: How popular git extensions handle git operations
2. **Git notes internals**: Technical details of git notes for ADR storage

Key findings validate the product brief's approach and inform implementation decisions.

## Git Extension Patterns Research

### Tools Analyzed

| Tool | Language | Approach | Notes |
|------|----------|----------|-------|
| git-lfs | Go | Subprocess | Dedicated subprocess package |
| git-flow | Shell | Subprocess | Direct shell commands |
| git-crypt | C++ | Subprocess + filters | Git filter mechanism |
| git-secret | Shell | Subprocess | Bash script |
| GitHub CLI | Go | Subprocess | Custom Command wrapper |
| git-absorb | Rust | libgit2 | Only exception (performance-critical) |

### Key Finding

**5 of 6 major git extensions use subprocess to the git binary.** This is the industry standard approach.

Only git-absorb uses library bindings, and that's because it performs performance-critical commit analysis that benefits from direct object access.

### Recommendation Applied

Use subprocess for git-adr. Benefits:
- Zero additional dependencies
- Full feature parity
- Automatic credential inheritance
- No GPL license concerns

### Python Git Library Comparison

| Library | Approach | Verdict |
|---------|----------|---------|
| subprocess | Direct git calls | **Recommended** |
| GitPython | Shells out internally | Windows issues, CVE-2024-22190 |
| pygit2 | libgit2 bindings | GPLv2, installation complexity |

## Git Notes Research

### Storage Structure

Git notes are stored as regular git blobs in a tree structure:
```
refs/notes/adr/
├── bf/
│   └── fe30/
│       └── ...680d5a...  (note blob)
```

### Critical Findings

#### 1. Notes are NOT synced by default

**This is the most important finding.** Git notes require explicit configuration:

```bash
# Required for notes to sync
git config --add remote.origin.fetch '+refs/notes/adr:refs/notes/adr'
git config --add remote.origin.push 'refs/notes/adr'
```

**Mitigation**: `git adr init` must configure this automatically.

#### 2. Notes are lost on rebase unless configured

Notes are attached to specific commit SHAs. When rebased, notes become orphaned.

**Required configuration**:
```bash
git config notes.rewriteRef refs/notes/adr
git config notes.rewrite.rebase true
git config notes.rewrite.amend true
```

**Mitigation**: `git adr init` must configure this.

#### 3. No major platform displays notes in web UI

| Platform | Native Support |
|----------|---------------|
| GitHub | No (discontinued 2014) |
| GitLab | No |
| Bitbucket Cloud | No |
| Bitbucket Server | Plugin available |

**Mitigation**: Wiki sync feature is essential for visibility.

#### 4. Merge strategies

| Strategy | Behavior | Use Case |
|----------|----------|----------|
| manual | Checkout conflicts for resolution | Complex conflicts |
| union | Concatenate versions | **ADR content** |
| cat_sort_uniq | Union + sort + dedupe | **Index metadata** |
| ours/theirs | Keep one version | Authoritative source |

**Recommendation**: Use `union` for ADRs, `cat_sort_uniq` for index.

#### 5. Size limits

| Platform | Limit |
|----------|-------|
| GitHub | 1 MB per note |
| Git general | 50 MB warning, 100 MB hard |

**Recommendation**: Warn >1MB artifacts, refuse >10MB.

### libgit2/pygit2 Notes API

pygit2 provides notes support:
```python
repo.create_note(message, author, committer, annotated_id, ref, force)
repo.lookup_note(annotated_id, ref)
note.message
note.remove()
```

However, subprocess provides equivalent functionality without the dependency.

## Codebase Analysis

### Existing Files

| File | Purpose | Status |
|------|---------|--------|
| `src/git_adr/__init__.py` | Package init | Minimal |
| `src/git_adr/cli.py` | CLI entry point | Placeholder (prints help) |
| `tests/conftest.py` | Test fixtures | temp_git_repo fixture exists |
| `tests/test_cli.py` | CLI tests | Basic import test |

### Existing Patterns

- Uses `subprocess.run()` for git operations (in conftest.py)
- Test fixtures create temporary git repos
- Type hints used throughout

### Current Dependencies

From `pyproject.toml`:
- `click>=8.1.0` (to be replaced with typer)
- Dev: pytest, ruff, mypy, bandit

### Integration Points

1. **Git binary**: subprocess calls
2. **$EDITOR**: For ADR editing
3. **File system**: Temporary files during edit
4. **Environment**: GIT_TERMINAL_PROMPT, EDITOR, NO_COLOR

## Competitive Analysis

### Similar Solutions

| Tool | Storage | Strengths | Weaknesses |
|------|---------|-----------|------------|
| adr-tools | Files | Simple, mature | Numbering conflicts |
| log4brains | Files | Nice web UI | Node.js dependency |
| adr-cli (.NET) | Files | Windows native | Limited ecosystem |
| **git-adr** | **Notes** | **Git-native, no conflicts** | **Platform visibility** |

### Lessons from log4brains

- MADR format is widely adopted
- Web UI is valuable for browsing
- Date-based IDs avoid conflicts
- Search is essential

## Open Questions Resolved

| Question | Resolution |
|----------|------------|
| Git operations approach | Subprocess (industry standard) |
| Note attachment point | Root tree object |
| Sync configuration | Auto-configure in init |
| AI provider priority | OpenAI > Anthropic > Others > Ollama |
| CLI framework | typer (migrate from click) |
| Python version | 3.11+ |

## Sources

### Git Extension Source Code
- [git-lfs](https://github.com/git-lfs/git-lfs)
- [gitflow-avh](https://github.com/petervanderdoes/gitflow-avh)
- [git-crypt](https://github.com/AGWA/git-crypt)
- [git-secret](https://github.com/sobolevn/git-secret)
- [GitHub CLI](https://github.com/cli/cli)
- [git-absorb](https://github.com/tummychow/git-absorb)

### Git Notes Documentation
- [Git Notes Official Docs](https://git-scm.com/docs/git-notes)
- [Git Notes: Git's Coolest, Most Unloved Feature](https://tylercipriani.com/blog/2022/11/19/git-notes-gits-coolest-most-unloved-feature/)
- [Git Notes Unraveled](https://dev.to/shrsv/git-notes-unraveled-history-mechanics-and-practical-uses-25i9)

### Python Libraries
- [pygit2 documentation](https://www.pygit2.org/)
- [libgit2 notes.h header](https://github.com/libgit2/libgit2/blob/main/include/git2/notes.h)
