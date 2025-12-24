# Code Review Report

## Metadata
- **Project**: git-adr
- **Version**: 0.2.4
- **Review Date**: 2025-12-24
- **Reviewer**: Claude Code Review Agent (Opus 4.5)
- **Scope**: Full review - 57 source files, 63 test files
- **Commit**: d25cd93 (perf: add Code Intelligence (LSP) section to CLAUDE.md)
- **LSP Available**: Yes
- **Methodology**: LSP semantic analysis + parallel specialist agents

---

## Executive Summary

### Overall Health Score: 7.5/10

| Dimension | Score | Critical | High | Medium | Low |
|-----------|-------|----------|------|--------|-----|
| Security | 8/10 | 0 | 1 | 2 | 3 |
| Performance | 6/10 | 2 | 4 | 2 | 0 |
| Architecture | 7/10 | 0 | 1 | 8 | 4 |
| Code Quality | 8/10 | 0 | 2 | 6 | 5 |
| Test Coverage | 7/10 | 0 | 2 | 6 | 2 |
| Documentation | 7/10 | 0 | 2 | 5 | 3 |

### Key Findings
1. **CRITICAL (Performance)**: N+1 artifact fetching pattern in `notes.py:427` causes O(n) subprocess calls
2. **CRITICAL (Performance)**: Multi-pass metric calculations in `stats.py` and `metrics.py` iterate 5-7x unnecessarily
3. **HIGH (Security)**: Wiki URL validation missing before subprocess clone in `wiki/service.py:173`
4. **HIGH (Architecture)**: CLI module is 1,919 lines - god class violating Single Responsibility
5. **HIGH (Code Quality)**: Missing type annotations in helper functions across command modules

### Recommended Action Plan

#### 1. Immediate (before next deploy)
- [ ] Add URL validation in wiki/service.py before clone operations
- [ ] Fix N+1 artifact fetch with batch operations
- [ ] Add artifact integrity verification (SHA256 check)

#### 2. This Sprint
- [ ] Consolidate multi-pass iterations in stats/metrics commands
- [ ] Fix unused variables flagged by LSP (notes.py, service.py, templates.py)
- [ ] Add missing type annotations to helper functions
- [ ] Document environment variables (AI API keys, EDITOR)

#### 3. Next Sprint
- [ ] Break cli.py into submodules (core, ai, wiki, admin commands)
- [ ] Extract WikiService into smaller focused classes
- [ ] Implement index optimization (currently stub methods)
- [ ] Add edge case tests for AI service error handling

#### 4. Backlog
- [ ] Create artifact garbage collection mechanism
- [ ] Add hook versioning/migration strategy
- [ ] Create API extension documentation
- [ ] Add performance tests for 1000+ ADR scenarios

---

## Critical Findings (🔴)

### PERF-001: N+1 Artifact Fetching Pattern
**Severity**: CRITICAL
**Category**: Performance
**Location**: `src/git_adr/core/notes.py:427-451`

**Description**:
The `list_artifacts()` method makes individual subprocess calls for each artifact reference found in an ADR. For an ADR with 10 artifacts, this results in 11 subprocess calls (1 for ADR + 10 for artifacts).

**Evidence**:
```python
def list_artifacts(self, adr_id: str) -> list[ArtifactInfo]:
    adr = self.get(adr_id)  # Subprocess call 1
    artifact_refs = re.findall(r"artifact:([a-f0-9]{64})", adr.content)
    artifacts: list[ArtifactInfo] = []
    for sha256 in artifact_refs:  # N subprocess calls
        result = self.get_artifact(sha256)  # Each = git notes show
        if result:
            artifacts.append(result[0])
```

**Impact**:
- Latency: +100-1000ms for ADRs with multiple artifacts
- Scales poorly: O(n) subprocess overhead

**Remediation**:
```python
def list_artifacts(self, adr_id: str) -> list[ArtifactInfo]:
    adr = self.get(adr_id)
    if adr is None:
        return []

    artifact_refs = re.findall(r"artifact:([a-f0-9]{64})", adr.content)
    if not artifact_refs:
        return []

    # Batch fetch all artifact notes in ONE subprocess call
    artifact_objs = [self._artifact_hash_to_object(sha) for sha in artifact_refs]
    artifacts_data = self._git.cat_file_batch(artifact_objs)

    return [
        self._parse_artifact_note(artifacts_data[obj], sha)
        for sha, obj in zip(artifact_refs, artifact_objs)
        if obj in artifacts_data
    ]
```

---

### PERF-002: Multiple List Iterations in Stats/Metrics
**Severity**: CRITICAL
**Category**: Performance
**Location**: `src/git_adr/commands/stats.py:59-74`, `src/git_adr/commands/metrics.py:81-161`

**Description**:
Both commands iterate over `all_adrs` multiple times (5-7 passes) for different calculations that could be done in a single pass.

**Evidence** (metrics.py):
```python
# Pass 1: Status counts
for adr in all_adrs:
    status_counts[adr.metadata.status.value] += 1

# Pass 2: Linked commits
linked_count = sum(1 for adr in all_adrs if adr.metadata.linked_commits)

# Pass 3: Superseded ADRs
superseded_adrs = [a for a in all_adrs if a.metadata.status == ADRStatus.SUPERSEDED]

# Pass 4-7: Velocity calculations
velocity_7d = sum(1 for adr in all_adrs if adr.metadata.date >= today - timedelta(days=7))
# ... etc
```

Additionally, `stats.py:69` has an **embedded N+1** calling `list_artifacts()` inside the loop.

**Impact**:
- Latency: +50-300ms on large repositories
- CPU: 5-7x iteration overhead

**Remediation**:
```python
def _calculate_metrics_single_pass(all_adrs: list[ADR]) -> dict:
    """Calculate all metrics in a single iteration."""
    today = datetime.now().date()

    status_counts: Counter[str] = Counter()
    linked_count = 0
    superseded_adrs = []
    velocity_7d = velocity_30d = velocity_90d = 0

    for adr in all_adrs:
        status_counts[adr.metadata.status.value] += 1

        if adr.metadata.linked_commits:
            linked_count += 1

        if adr.metadata.status == ADRStatus.SUPERSEDED:
            superseded_adrs.append(adr)

        # Velocity in same pass
        adr_date = adr.metadata.date
        if adr_date >= today - timedelta(days=7):
            velocity_7d += 1
        if adr_date >= today - timedelta(days=30):
            velocity_30d += 1
        if adr_date >= today - timedelta(days=90):
            velocity_90d += 1

    return {
        "status_counts": status_counts,
        "linked_count": linked_count,
        "superseded_adrs": superseded_adrs,
        "velocity": {"7d": velocity_7d, "30d": velocity_30d, "90d": velocity_90d}
    }
```

---

## High Priority Findings (🟠)

### SEC-001: Wiki URL Validation Missing
**Severity**: HIGH
**Category**: Security
**Location**: `src/git_adr/wiki/service.py:173-196`

**Description**:
The wiki service clones repositories using URLs from git config without URL validation. While git validates URL format, a compromised `.git/config` could contain malicious URLs.

**Evidence**:
```python
result = subprocess.run(
    ["git", "clone", "--depth", "1", wiki_url, str(wiki_dir)],
    check=False,
    capture_output=True,
    text=True,
    timeout=60,
)
```

**Impact**:
- Defense-in-depth gap for untrusted git configs
- Potential for unexpected behavior with crafted URLs

**Remediation**:
```python
from urllib.parse import urlparse

def _validate_wiki_url(url: str) -> str:
    """Validate wiki URL before subprocess use."""
    parsed = urlparse(url)
    if parsed.scheme not in ('https', 'ssh', 'git', ''):
        raise WikiServiceError(f"Invalid URL scheme: {parsed.scheme}")
    if parsed.scheme == 'file' and '..' in parsed.path:
        raise WikiServiceError("Path traversal in file URL")
    return url

# Usage before clone:
wiki_url = self._validate_wiki_url(self.get_wiki_url(platform))
```

---

### SEC-002: Artifact Integrity Not Verified
**Severity**: MEDIUM
**Category**: Security
**Location**: `src/git_adr/core/notes.py:383-425`

**Description**:
Artifacts are stored with SHA256 hash in filename but content is not verified against the hash on retrieval. Corrupted or tampered artifacts go undetected.

**Evidence**:
```python
def get_artifact(self, sha256: str) -> tuple[ArtifactInfo, bytes] | None:
    # ... parsing ...
    content = base64.b64decode(encoded_content)  # No hash verification!
    return artifact, content
```

**Remediation**:
```python
import hashlib

# After decoding content:
actual_sha256 = hashlib.sha256(content).hexdigest()
if actual_sha256 != sha256:
    raise ValueError(f"Artifact corruption: expected {sha256}, got {actual_sha256}")
```

---

### ARCH-001: CLI Module Too Large (God Class)
**Severity**: HIGH
**Category**: Architecture
**Location**: `src/git_adr/cli.py` (1,919 lines)

**Description**:
The CLI module contains 40+ command definitions, each with 10-50 lines of argument/option definitions. While logic is properly delegated to command modules, the file itself violates Single Responsibility.

**Impact**:
- Maintainability: Hard to navigate and modify
- Code review: Changes touch large file

**Remediation**:
Break into submodules:
```
src/git_adr/cli/
├── __init__.py      # Main app entry, combines subcommands
├── core.py          # init, new, list, show, edit, rm, search
├── ai.py            # ai-draft, ai-suggest, ai-summarize, ai-ask
├── wiki.py          # wiki-init, wiki-sync
├── admin.py         # config, stats, metrics, report, hooks-*
└── templates.py     # templates-*, ci-*
```

---

### QUAL-001: Missing Type Annotations in Helpers
**Severity**: HIGH
**Category**: Code Quality
**Location**: Multiple command files

**Description**:
Several helper functions lack type annotations, preventing static analysis and IDE support.

**Affected Functions**:
| File | Function | Issue |
|------|----------|-------|
| `commands/edit.py:150` | `_full_edit(config)` | `config` param untyped |
| `commands/report.py` | `_get_author()`, `_generate_*_report()` | No return types |
| `commands/search.py` | `_display_match()`, `_highlight_snippet()` | No type hints |
| `commands/stats.py` | `_display_velocity()` | No type hints |

**Remediation**:
```python
# Example fix for edit.py
from git_adr.core import Config

def _full_edit(notes_manager: NotesManager, adr: ADR, config: Config) -> None:
    """Open ADR in editor for full editing."""
```

---

### QUAL-002: Unused Variables (LSP Flagged)
**Severity**: MEDIUM
**Category**: Code Quality
**Location**: Multiple files

**Description**:
LSP diagnostics identified unused variables indicating dead code or incomplete implementations.

**Affected**:
| File | Line | Variable | Issue |
|------|------|----------|-------|
| `notes.py` | 520 | `merge_strategy` | Not accessed |
| `notes.py` | 585-586 | `metadata`, `action` | Stub function params |
| `notes.py` | 600 | `adr_id` | Stub function param |
| `service.py` | 214, 254 | `platform` | Not accessed |
| `service.py` | 448 | `wiki_dir` | Not accessed |
| `templates.py` | 566, 627 | `target_format`, `adr_id` | Not accessed |

**Remediation**:
Either implement the functionality or prefix with `_` to indicate intentionally unused:
```python
def _update_index(self, _metadata: ADRMetadata, _action: str = "add") -> None:
    """Update index - currently a no-op, reads all notes directly."""
    pass
```

---

## Medium Priority Findings (🟡)

### PERF-003: Inefficient Tag Filtering
**Location**: `src/git_adr/core/index.py:241-243`

Converts tags to lowercase for every entry during filter instead of once.

```python
# Current (inefficient)
entries = [e for e in entries if tag_lower in [t.lower() for t in e.tags]]

# Better
entries = [e for e in entries if any(t.lower() == tag_lower for t in e.tags)]
```

---

### PERF-004: Redundant Index Rebuilds
**Location**: `commands/report.py:49-50`, `metrics.py:46-47`, `stats.py:42-43`

Commands rebuild index then fetch all ADRs separately - double work.

---

### ARCH-002: WikiService Mixed Concerns
**Location**: `src/git_adr/wiki/service.py` (516 lines)

Class handles platform detection, repo cloning, ADR conversion, git operations, and cleanup. Should be split into focused classes.

---

### ARCH-003: Incomplete Index Optimization
**Location**: `src/git_adr/core/notes.py:583-608`

`_update_index()` and `_update_index_remove()` are stubs with `pass`. Every `list_all()` does O(N) subprocess calls.

---

### ARCH-004: Commands Import Git Directly (Layer Violation)
**Location**: 31 command files

Commands access `ctx.git.*` directly instead of through managers, violating layer architecture.

---

### TEST-001: AI Service Error Paths Not Tested
**Location**: `tests/test_ai_*.py`

Missing tests for: API timeouts, rate limiting, partial responses, invalid model names.

---

### TEST-002: Issue Command Low Coverage
**Location**: `src/git_adr/commands/issue.py` (484 lines)

Only 33 tests for 484 lines of complex interactive logic (~7% density).

---

### DOC-001: Environment Variables Undocumented
**Location**: README.md, CONFIGURATION.md

Missing documentation for: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `EDITOR`, `VISUAL`, `GIT_ADR_SKIP`.

---

### DOC-002: Report Command Missing Docstrings
**Location**: `src/git_adr/commands/report.py`

Helper functions `_get_author()`, `_generate_*_report()` lack docstrings and type hints.

---

## Low Priority Findings (🟢)

### SEC-003: Weak Hash for Object IDs
**Location**: `notes.py:559-560`

Uses SHA1 for non-security purposes. While correctly marked `usedforsecurity=False`, SHA256 would be more future-proof.

---

### QUAL-003: Magic Numbers in Config
**Location**: `config.py:26-27, 88-89, 370-371`

Artifact size limits (`1048576`, `10485760`) repeated in three places instead of constants.

---

### QUAL-004: Mutable Dataclass Modifications
**Location**: `commands/edit.py:102, 122, 136`

Direct mutation of `adr.metadata` fields instead of using `dataclasses.replace()`.

---

### ARCH-005: Duplicate Slugify Functions
**Location**: `core/adr.py`, `core/issue.py`

Identical `_slugify()` implementations exist in both files.

---

### DOC-003: TODO Comments Without Tracking
**Location**: `commands/import_.py:102`, `commands/onboard.py:70`

TODO comments for incomplete features without linked issues.

---

## Appendix

### Files Reviewed

**Core Modules (12 files)**:
- `src/git_adr/__init__.py`
- `src/git_adr/cli.py` (1,919 lines)
- `src/git_adr/hooks.py` (353 lines)
- `src/git_adr/core/adr.py`
- `src/git_adr/core/config.py` (415 lines)
- `src/git_adr/core/git.py` (921 lines)
- `src/git_adr/core/index.py` (537 lines)
- `src/git_adr/core/notes.py` (636 lines)
- `src/git_adr/core/templates.py` (678 lines)
- `src/git_adr/core/issue_template.py` (690 lines)
- `src/git_adr/core/gh_client.py` (264 lines)
- `src/git_adr/core/utils.py`

**Command Modules (32 files)**:
All files in `src/git_adr/commands/`

**Service Modules (4 files)**:
- `src/git_adr/ai/service.py` (348 lines)
- `src/git_adr/wiki/service.py` (516 lines)
- `src/git_adr/formats/__init__.py`
- `src/git_adr/templates/__init__.py`

**Test Files (63 files)**:
All files in `tests/`

### Tools & Methods
- LSP semantic analysis (Pyright) for type checking and reference finding
- 6 parallel specialist agents for comprehensive coverage
- Git blame for change attribution
- Automated code pattern detection

### Recommendations for Future Reviews
1. Add pre-commit hook for Pyright strict mode
2. Configure ruff for unused variable detection
3. Add coverage gates in CI for new code
4. Run `pip-audit` as part of CI/CD
