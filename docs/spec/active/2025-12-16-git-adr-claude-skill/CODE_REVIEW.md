# Code Review Report: git-adr

**Date:** 2025-12-16
**Target:** `./` (git-adr CLI project)
**Reviewers:** Parallel Specialist Agents (Security, Performance, Architecture, Code Quality, Test Coverage)

---

## Executive Summary

The git-adr codebase (~14,836 lines of Python) demonstrates **generally good engineering practices** with clean layer separation, proper security measures, and comprehensive type annotations. However, the review identified **26 findings** across 5 dimensions requiring attention.

### Health Scores (1-10)

| Dimension | Score | Assessment |
|-----------|-------|------------|
| **Security** | 8/10 | Good practices with 2 medium-priority fixes |
| **Performance** | 5/10 | N+1 subprocess patterns need optimization |
| **Architecture** | 7/10 | Clean layers but significant code duplication |
| **Code Quality** | 7/10 | DRY violations and missing type annotations |
| **Test Coverage** | 3/10 | Estimated 15-20% coverage, many gaps |

---

## Critical Findings (Must Fix)

### 1. N+1 Subprocess Pattern in `NotesManager.list_all()`

**File:** `src/git_adr/core/notes.py:236-258`
**Impact:** Every `list`, `search`, and `stats` command spawns N+1 git subprocess calls (N = number of ADRs)

**Current Code:**
```python
def list_all(self) -> list[ADR]:
    notes = self._git.notes_list(self.adr_ref)  # 1 subprocess
    for _note_sha, obj_sha in notes:
        content = self._git.notes_show(obj_sha, ref=self.adr_ref)  # N subprocesses!
```

**Impact:** With 100 ADRs, `git adr list` spawns ~101 subprocesses instead of ~2.

**Remediation:** Implement batch fetching using `git cat-file --batch`:
```python
def list_all(self) -> list[ADR]:
    notes = self._git.notes_list(self.adr_ref)
    obj_shas = [sha for _, sha in notes if sha != INDEX_OBJECT_ID]
    batch_content = self._git.cat_file_batch(obj_shas)  # Single subprocess
    return [ADR.from_markdown(c) for c in batch_content.values() if c]
```

---

### 2. Double Loading in `IndexManager.search()`

**File:** `src/git_adr/core/index.py:260-337`
**Impact:** Search first loads index (calls `list_all()`), then re-fetches each ADR individually.

**Remediation:** Add ADR caching in IndexManager:
```python
def _ensure_loaded(self) -> None:
    if self._loaded:
        return
    adrs = self._notes.list_all()
    for adr in adrs:
        self._entries[adr.id] = IndexEntry.from_adr(adr)
        self._adr_cache[adr.id] = adr  # Cache full ADR
    self._loaded = True
```

---

### 3. DRY Violation: Command Initialization Boilerplate

**Files:** All 27+ command files in `src/git_adr/commands/`
**Impact:** ~15 lines of identical boilerplate repeated in every command.

**Remediation:** Create a shared context factory:
```python
# commands/__init__.py
@dataclass
class CommandContext:
    git: Git
    config: Config
    notes_manager: NotesManager

def get_command_context(require_init: bool = True) -> CommandContext:
    git = get_git(cwd=Path.cwd())
    if not git.is_repository():
        raise NotARepositoryError()
    config_manager = ConfigManager(git)
    if require_init and not config_manager.get("initialized"):
        raise ADRNotInitializedError()
    config = config_manager.load()
    return CommandContext(git, config, NotesManager(git, config))
```

---

## High Priority Findings

### SEC-001: HTML Injection in Export (Low Severity)

**File:** `src/git_adr/commands/export.py:218-237`
**Issue:** ADR titles interpolated into HTML without escaping.

**Remediation:**
```python
import html
safe_title = html.escape(adr.metadata.title)
```

### SEC-006: Editor Command Construction (Medium Severity)

**File:** `src/git_adr/commands/new.py:437-460`
**Issue:** Simple `split()` on editor string; should use `shlex.split()`.

**Remediation:**
```python
import shlex
parts = shlex.split(editor)  # Proper shell-like parsing
```

### PERF-003: N+1 in Stats Artifact Counting

**File:** `src/git_adr/commands/stats.py:77-92`
**Issue:** For each ADR, makes subprocess call to list artifacts.

**Remediation:** Count artifacts from ADR content directly (already loaded).

### PERF-004: Repeated Config Loading

**Files:** All command files
**Issue:** Every command spawns 15+ `git config` calls.

**Remediation:** Use batch config loading with `git config --list`.

### ARCH-004: Cross-Module Command Imports

**File:** `src/git_adr/commands/edit.py:176-177`
**Issue:** `edit.py` imports helpers from `new.py` creating hidden coupling.

**Remediation:** Extract editor utilities to `core/editor.py`.

### QUAL-001: Duplicated Status Style Mapping

**Files:** `list.py:170-187`, `search.py:169-186`, `show.py:173-193`
**Issue:** Identical `_get_status_style()` function in 3 files.

**Remediation:** Extract to shared module:
```python
# commands/_shared.py
STATUS_STYLES: dict[ADRStatus, str] = {
    ADRStatus.DRAFT: "dim",
    ADRStatus.PROPOSED: "yellow",
    ADRStatus.ACCEPTED: "green",
    # ...
}
```

---

## Medium Priority Findings

### Architecture

| ID | Finding | File | Recommendation |
|----|---------|------|----------------|
| ARCH-001 | Layer violation in init.py | `init.py:95,99-102` | Move config writes to ConfigManager |
| ARCH-003 | Mutable ADRMetadata | `adr.py:57-86` | Make frozen, use `dataclasses.replace()` |
| ARCH-005 | God function run_new() | `new.py:58-271` | Decompose into smaller functions |
| ARCH-006 | Inconsistent error handling | Various | Standardize error display patterns |

### Performance

| ID | Finding | File | Impact |
|----|---------|------|--------|
| PERF-005 | Unnecessary index rebuild | `export.py:69-71` | Double `list_all()` call |
| PERF-006 | Template engine recreation | `new.py` | Re-scans filesystem every command |
| PERF-007 | Base64 memory inefficiency | `notes.py:277-366` | Large artifacts fully in memory |

### Code Quality

| ID | Finding | Files | Issue |
|----|---------|-------|-------|
| QUAL-002 | Empty TYPE_CHECKING block | `init.py:30-31` | Dead code |
| QUAL-003 | Unused NotesManager parameter | `export.py:111-113` | Unused function parameter |
| QUAL-004 | Missing type annotations | `show.py`, `list.py`, `stats.py` | 10+ functions with missing types |
| QUAL-005 | Bare exception clauses | `hooks_cli.py`, `new.py` | `except Exception:` too broad |

---

## Test Coverage Gaps

**Estimated Overall Coverage: 15-20%**

### Missing Test Files

| Module | Lines | Test File Status |
|--------|-------|------------------|
| `core/notes.py` | 617 | **None** |
| `core/index.py` | 520 | **None** |
| `core/config.py` | 416 | **None** |
| `core/templates.py` | 679 | **None** |
| `ai/service.py` | 349 | **None** |
| `wiki/service.py` | 517 | **None** |
| `hooks.py` | 354 | **None** |

### High-Priority Test Cases to Add

```python
# test_notes.py - New file needed
def test_notes_manager_add_stores_adr_in_notes():
def test_notes_manager_get_returns_none_for_missing_adr():
def test_attach_artifact_raises_for_oversized_file():

# test_index.py - New file needed
def test_index_manager_query_filters_by_status():
def test_index_manager_search_handles_invalid_regex():

# test_config.py - New file needed
def test_config_manager_validates_template_name():
def test_config_manager_get_bool_accepts_all_truthy_values():
```

---

## Security Positives

The codebase demonstrates good security practices:

1. ✅ **Subprocess safety**: Uses list arguments, not `shell=True`
2. ✅ **Path traversal protection**: Implemented for artifact extraction
3. ✅ **Safe YAML parsing**: Uses `yaml.safe_load()` consistently
4. ✅ **API key handling**: Environment variables, not config files
5. ✅ **Hash function flags**: Uses `usedforsecurity=False` appropriately
6. ✅ **Security tooling**: bandit and pip-audit in dev dependencies

---

## Remediation Priority Matrix

| Priority | Count | Effort | Findings |
|----------|-------|--------|----------|
| **P0** | 3 | Medium | N+1 subprocess, double loading, command boilerplate |
| **P1** | 6 | Low-Medium | SEC-001, SEC-006, PERF-003, PERF-004, ARCH-004, QUAL-001 |
| **P2** | 8 | Low-Medium | Architecture and quality improvements |
| **P3** | 9 | Ongoing | Test coverage, minor cleanups |

---

## Estimated Impact of P0/P1 Fixes

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| `git adr list` (100 ADRs) | ~100 subprocesses | ~2 | 98% reduction |
| `git adr search` (100 ADRs) | ~200 subprocesses | ~2 | 99% reduction |
| Config loading per command | ~15 subprocesses | ~1 | 93% reduction |
| Duplicated boilerplate | ~405 lines | ~27 lines | 93% reduction |

---

## Summary

The git-adr codebase is fundamentally sound with proper layering and security measures. The main areas requiring attention are:

1. **Performance**: N+1 subprocess patterns significantly impact CLI responsiveness
2. **DRY**: Command initialization boilerplate creates maintenance burden
3. **Test Coverage**: Critical modules lack dedicated test files

Addressing the P0 findings would provide the highest return on investment for both user experience (faster CLI) and maintainability (reduced duplication).
