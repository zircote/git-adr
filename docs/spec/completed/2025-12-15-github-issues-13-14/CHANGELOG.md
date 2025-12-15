# Changelog

## [1.0.0] - 2025-12-15

### Added
- Complete REQUIREMENTS.md with functional requirements for both issues
- Complete ARCHITECTURE.md with Homebrew formula design and documentation structure
- Complete IMPLEMENTATION_PLAN.md with 4 phases and 17 tasks

### Research Conducted
- Analyzed git-adr codebase: 31 commands, 15+ config options, existing release workflow
- Researched Homebrew Python CLI patterns (Simon Willison's llm formula)
- Researched homebrew-releaser and bump-homebrew-formula-action
- Documented virtualenv pattern for Homebrew Python tools

### Decisions Made
- Personal tap (zircote/homebrew-git-adr) over homebrew-core submission initially
- Comprehensive ADR format documentation (all 6 formats with examples)
- Target audience: ADR beginners (concept explanations included)
- PyPI sdist as package source for formula

## [COMPLETED] - 2025-12-15

### Project Closed
- Final status: Success
- Actual effort: ~6 hours
- Moved to: docs/spec/completed/2025-12-15-github-issues-13-14/
- PR created: https://github.com/zircote/git-adr/pull/16

### Retrospective Summary
- What went well: Parallel subagent execution, comprehensive documentation, automated release pipeline
- What to improve: PyPI dependency blocking full testing, could have simulated more thoroughly
- Scope additions: Homebrew automation workflow, tap CI, extended man pages

### Deliverables Completed
- ✅ CONFIGURATION.md - 14 config keys with examples
- ✅ ADR_FORMATS.md - All 6 formats with full examples
- ✅ ADR_PRIMER.md - Beginner guide with quick start
- ✅ Homebrew tap created at github.com/zircote/homebrew-git-adr
- ✅ Formula with virtualenv pattern and all dependencies
- ✅ CI workflow for tap testing
- ✅ update-homebrew job in release.yml
- ✅ Man page with config reference
- ✅ README with Homebrew installation

### Remaining User Actions
1. Create fine-grained PAT for homebrew-git-adr repo
2. Add HOMEBREW_TAP_TOKEN secret to git-adr repo
3. Create v0.1.0 release to trigger automation

## [Unreleased]

### Implementation Progress
- Implementation started: 2025-12-15
- PROGRESS.md initialized with 17 tasks across 4 phases
- Status changed from `in-review` to `in-progress`

### Added
- Initial project creation
- Requirements elicitation begun
- Downloaded and analyzed GitHub issues #13 and #14
