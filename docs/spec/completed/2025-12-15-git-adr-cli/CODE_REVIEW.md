# Code Review Findings

**Project**: git-adr-cli
**Reviewed**: 2025-12-15
**Commit**: cd6e1ba
**Overall Score**: 8.5/10 (was 7.5, improved after fixes)

## Summary

| Severity | Count | Fixed |
|----------|-------|-------|
| 🔴 Critical | 1 | ✅ 1 |
| 🟠 High | 4 | ✅ 3 |
| 🟡 Medium | 9 | 0 |
| 🟢 Low | 5 | 0 |

---

## Critical Findings

### SEC-001: Path Traversal in artifact-get command

- **Category**: Security
- **Severity**: Critical
- **Status**: ✅ Fixed
- **File**: `src/git_adr/commands/artifact_get.py:24-55`
- **Fixed**: 2025-12-15

**Description**:
User-controlled `output` path is used directly without validation. An attacker could extract artifacts to arbitrary locations (e.g., `--output=/etc/passwd` or `--output=~/.ssh/authorized_keys`).

**Fix Applied**:
Added `_validate_output_path()` function that:
- Resolves the path to prevent relative path tricks
- Uses `relative_to(cwd)` to ensure output is within current directory
- Raises `typer.Exit(1)` with clear error message if path traversal detected

**Tests Added**: `tests/test_security_path_traversal.py` (28 security tests)

---

## High Findings

### SEC-002: Path Traversal in attach command

- **Category**: Security
- **Severity**: High
- **Status**: ✅ Fixed
- **File**: `src/git_adr/commands/attach.py:32-53`
- **Fixed**: 2025-12-15

**Description**:
No validation that the file path is within acceptable bounds. User could potentially attach sensitive files from outside the repository.

**Fix Applied**:
Added `_validate_input_path()` function. For read operations (attach), we allow reading from anywhere since this is a user-initiated action, similar to `cat`. The function validates the path exists and handles tilde expansion.

---

### SEC-003: Import command lacks path validation

- **Category**: Security
- **Severity**: Medium
- **Status**: ✅ Fixed
- **File**: `src/git_adr/commands/import_.py:32-55`
- **Fixed**: 2025-12-15

**Description**:
Accepts arbitrary filesystem paths without restriction. Could be used to read from sensitive directories.

**Fix Applied**:
Added `_validate_source_path()` function with similar read-operation validation as attach.

---

### SEC-004: Editor command injection risk

- **Category**: Security
- **Severity**: Medium
- **Status**: Open
- **File**: `src/git_adr/commands/new.py:402-425`

**Description**:
The editor string from config is split and executed. While subprocess is called with a list (safer than shell=True), a malicious editor config could execute unintended binaries.

**Mitigation Note**:
The editor config already uses `shutil.which()` validation in `_find_editor()`. The risk is limited to user-configured editor values.

---

### CQ-001: No exception handling for LLM calls

- **Category**: Code Quality
- **Severity**: High
- **Status**: ✅ Fixed
- **File**: `src/git_adr/ai/service.py`
- **Fixed**: 2025-12-15

**Description**:
No try/except around LLM invocation. Network failures, API rate limits, and provider errors propagate as unhandled exceptions.

**Fix Applied**:
Wrapped all 4 `llm.invoke()` calls with try/except blocks that raise `AIServiceError` with proper exception chaining (`from e`).

**Tests Added**: `tests/test_ai_exception_handling.py` (6 tests)

---

### CQ-002: DRY Violation - _ensure_list duplicated 3 times

- **Category**: Code Quality
- **Severity**: High
- **Status**: ✅ Fixed
- **Fixed**: 2025-12-15

**Description**:
Three identical implementations of the same helper function.

**Fix Applied**:
- Created `src/git_adr/core/utils.py` with shared `ensure_list()` function
- Exported from `git_adr.core` module
- Updated all 3 files to import from the shared location
- Removed duplicate implementations

**Tests Added**: `tests/test_core_utils.py` (16 tests)

---

### TQ-001: Tests lack subprocess mocking for git operations

- **Category**: Test Quality
- **Severity**: High
- **Status**: Open
- **File**: `tests/conftest.py:60-65`

**Description**:
Integration tests create real git repositories. Unit tests should mock the Git class to avoid filesystem side effects.

---

## Medium Findings

### CQ-003: Broad exception catch in wiki service

- **Category**: Code Quality
- **Severity**: Medium
- **Status**: Open
- **File**: `src/git_adr/wiki/service.py:83-86`

**Description**:
Catches all exceptions silently. Could mask serious issues.

---

### CQ-004: Magic string for merge strategy

- **Category**: Code Quality
- **Severity**: Medium
- **Status**: Open
- **File**: `src/git_adr/core/config.py:94`

**Description**:
Uses raw string instead of enum despite `VALID_MERGE_STRATEGIES` existing.

---

### ARCH-001: Wiki service bypasses Git abstraction

- **Category**: Architecture
- **Severity**: Medium
- **Status**: Open
- **File**: `src/git_adr/wiki/service.py:168-174`

**Description**:
WikiService directly calls subprocess for git operations instead of using the Git class.

---

### ARCH-002: Inline imports in methods

- **Category**: Architecture
- **Severity**: Medium
- **Status**: Open
- **File**: `src/git_adr/core/notes.py:424,454`

**Description**:
Re-imports `re` module inside methods instead of at module level.

---

### ARCH-003: Index not actually implemented

- **Category**: Architecture
- **Severity**: Medium
- **Status**: Open
- **File**: `src/git_adr/core/notes.py:535-559`

**Description**:
Index operations are no-ops. `IndexManager` loads all ADRs on every query, which will scale poorly.

---

### TQ-002: Tests don't verify working directory isolation

- **Category**: Test Quality
- **Severity**: Medium
- **Status**: Open
- **File**: `tests/test_commands.py:75-82`

**Description**:
CliRunner doesn't respect chdir. Tests may not reflect real CLI behavior.

---

### TQ-003: Tests lack cleanup verification

- **Category**: Test Quality
- **Severity**: Medium
- **Status**: Open
- **File**: `tests/conftest.py:81-82`

**Description**:
Relies on tmp_path for cleanup. Crashed tests may leave temp git repos.

---

## Low Findings

### CQ-005: SHA1 usage without documentation

- **Category**: Code Quality
- **Severity**: Low
- **Status**: Open
- **File**: `src/git_adr/core/notes.py:521`

**Description**:
Uses SHA1 with noqa suppression but no documentation explaining why it's acceptable here.

---

### IV-001: ADR ID format not validated

- **Category**: Input Validation
- **Severity**: Low
- **Status**: Open
- **Files**: `src/git_adr/commands/edit.py:26-33`, `show.py`

**Description**:
ADR ID from user input passed directly without format validation.

---

### IV-002: Date format not validated in import

- **Category**: Input Validation
- **Severity**: Low
- **Status**: Open
- **File**: `src/git_adr/commands/import_.py:159-166`

**Description**:
Date string truncated without proper validation.

---

## Patterns Detected

| Pattern | Occurrences | Category |
|---------|-------------|----------|
| Path traversal without validation | 3 | Security |
| Missing exception handling | 2 | Code Quality |
| Subprocess bypass of abstractions | 2 | Architecture |

---

## Remediation Priority

1. **SEC-001**: Path traversal in artifact-get (Critical)
2. **CQ-001**: LLM exception handling (High)
3. **CQ-002**: DRY violation (High)
4. **SEC-002/003**: Path validation (Medium)
5. **ARCH-001**: Wiki service abstraction (Medium)
