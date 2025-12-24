# Remediation Tasks

Generated: 2025-12-24 (Updated with MAXALL review)
From: CODE_REVIEW.md (8 parallel specialist agents)

---

## Critical (Do Immediately)

- [x] `src/git_adr/core/notes.py:160-190` - Add optimistic locking for concurrent edit protection - Resilience
- [x] `src/git_adr/core/notes.py:325-350` - Implement streaming base64 or chunked encoding for artifacts - Performance
- [x] `src/git_adr/core/notes.py:427` - Batch artifact fetching with cat_file_batch() - Performance

## High Priority (This Sprint)

- [x] `src/git_adr/commands/export.py:72-74` - Add path traversal validation for output directory - Security
- [x] `SECURITY.md` (new file) - Create security policy with vulnerability reporting process - Compliance
- [x] `src/git_adr/ai/service.py:184-187` - Add retry logic with exponential backoff - Resilience
- [x] `src/git_adr/core/config.py:171-201` - Fix cache bypass in get() method - Performance
- [x] `src/git_adr/core/notes.py` - Add MAX_ADR_CONTENT_SIZE limit - Resilience
- [x] `src/git_adr/wiki/service.py:173` - Add URL validation before clone - Security
- [x] `src/git_adr/core/notes.py:383-425` - Add SHA256 integrity check for artifacts - Security
- [x] `src/git_adr/core/notes.py:520,585-586,600` - Fix unused variables (LSP) - Code Quality
- [x] `src/git_adr/wiki/service.py:214,254,448` - Fix unused variables (LSP) - Code Quality
- [x] `docs/CONFIGURATION.md` - Add Environment Variables section - Documentation

## Medium Priority (Next 2-3 Sprints)

### Performance

- [x] `src/git_adr/core/index.py:241-243` - Optimize tag filtering - Performance
- [x] `src/git_adr/core/index.py:373-380` - Pre-compute newline positions in snippets - Performance
- [x] `src/git_adr/core/notes.py:96-127` - Batch config reads during init - Performance
- [x] `src/git_adr/commands/report.py:49-50` - Cache ADRs after index rebuild - Performance
- [x] `src/git_adr/core/notes.py:325-350` - Stream-process large artifacts - Performance

### Architecture

- [x] `src/git_adr/cli.py` - Break into submodules (core, ai, wiki, admin) - Architecture
- [x] `src/git_adr/wiki/service.py` - Extract PlatformDetector, WikiRepoManager - Architecture
- [x] `src/git_adr/core/notes.py:583-608` - Implement index optimization - Architecture
- [x] `src/git_adr/commands/*.py` - Remove direct Git access (use managers) - Architecture
- [x] `src/git_adr/ai/service.py` - Extract provider classes - Architecture
- [x] `src/git_adr/core/issue_template.py` - Split parser classes - Architecture
- [x] `src/git_adr/hooks.py` - Add hook versioning strategy - Architecture
- [x] `src/git_adr/core/notes.py:292-481` - Add artifact garbage collection - Architecture

### Code Quality

- [x] `src/git_adr/commands/search.py` - Add type hints to \_display_match, \_highlight_snippet - Code Quality
- [x] `src/git_adr/commands/stats.py` - Add type hints to \_display_velocity - Code Quality
- [x] `src/git_adr/commands/edit.py:102,122,136` - Use dataclasses.replace() - Code Quality
- [x] `src/git_adr/core/config.py:26-27` - Extract magic numbers to constants - Code Quality
- [x] `src/git_adr/commands/import_.py` - Add module docstring - Code Quality
- [x] `src/git_adr/commands/issue.py` - Add module docstring - Code Quality

### Test Coverage

- [x] `tests/test_ai_service.py` - Add timeout/rate limit tests - Test Coverage
- [x] `tests/test_ai_exception_handling.py` - Add provider error tests - Test Coverage
- [x] `tests/test_issue_command.py` - Add interactive logic tests - Test Coverage
- [x] `tests/test_core.py` - Add git error parsing tests - Test Coverage
- [x] `tests/test_notes_artifacts.py` - Add artifact edge case tests - Test Coverage
- [x] `tests/test_wiki_service.py` - Add conflict/failure tests - Test Coverage

### Documentation

- [x] `docs/ENVIRONMENT_VARIABLES.md` - Create env var documentation - Documentation
- [x] `README.md` - Add workflow examples section - Documentation
- [x] `docs/API_REFERENCE.md` - Create programmatic usage guide - Documentation
- [x] `CHANGELOG.md` - Document recent version changes - Documentation

## Low Priority (Backlog)

### Security

- [x] `src/git_adr/core/notes.py:559-560` - Consider SHA256 for object IDs - Security
- [x] `src/git_adr/core/adr.py:157-162` - Add user list validation - Security
- [x] `src/git_adr/commands/_editor.py:59-67` - Improve editor validation - Security

### Code Quality

- [x] `src/git_adr/commands/wiki_sync.py:120,127,134` - Remove redundant str() - Code Quality
- [x] `src/git_adr/commands/init.py:33-34` - Remove empty TYPE_CHECKING block - Code Quality
- [x] `src/git_adr/core/config.py:220-226` - Add warning for invalid config values - Code Quality

### Architecture

- [x] `src/git_adr/core/adr.py`, `core/issue.py` - Deduplicate \_slugify() - Architecture
- [x] `src/git_adr/core/templates.py` - Create FormatRegistry abstraction - Architecture
- [x] `src/git_adr/core/config.py` - Create ConfigSchema validator - Architecture

### Documentation

- [x] `src/git_adr/commands/import_.py:102` - Convert TODO to issue - Documentation
- [x] `src/git_adr/commands/onboard.py:70` - Convert TODO to issue - Documentation
- [x] `docs/EXTENDING.md` - Create extension guide - Documentation
- [x] `docs/TROUBLESHOOTING.md` - Create troubleshooting guide - Documentation

---

## Quick Reference

| Category  | Count  | Est. Hours |
| --------- | ------ | ---------- |
| Critical  | 3      | 2-3        |
| High      | 9      | 4-6        |
| Medium    | 28     | 10-15      |
| Low       | 14     | 5-8        |
| **Total** | **54** | **~25**    |

### By Category

- Security: 6 tasks
- Performance: 8 tasks
- Architecture: 13 tasks
- Code Quality: 14 tasks
- Test Coverage: 6 tasks
- Documentation: 7 tasks
