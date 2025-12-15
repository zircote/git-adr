# Changelog

All notable changes to this planning project will be documented here.

## [1.1.0] - 2025-12-15

### Scope Creep & Late Additions

The following items were added during implementation beyond the original specification:

#### New Features (Not Originally Planned)
- **`git adr rm` command** - Remove ADRs from git notes (user request)
- **git-lfs style distribution** - Makefile, install.sh, release.yml (user request)
- **Extended bash completion** - Support both `git-adr` and `git adr` invocations

#### Infrastructure Changes (Not Originally Planned)
- **Coverage target raised** - From 90% to 95% (PR requirement)
- **Shell completion tests** - Added to meet coverage target
- **GitHub Actions v6/v7** - Upgraded for consistency with ci.yml
- **`.gitignore` fixes** - Prevent ignoring docs/man/ source files

#### Documentation Extensions
- Man page for `rm` command (docs/man/git-adr-rm.1.md)
- Updated COMMANDS.md with rm command
- Updated main man page with rm command reference

### Impact Assessment
- **Scope increase**: ~15% additional work
- **Risk**: Low (features align with tool philosophy)
- **Technical debt**: None introduced

---

## [1.0.0] - 2025-12-15

### Added
- Complete REQUIREMENTS.md with 60+ functional requirements
- Technical ARCHITECTURE.md with component design
- IMPLEMENTATION_PLAN.md with 80+ tasks across 4 phases
- DECISIONS.md with 8 architecture decision records
- RESEARCH_NOTES.md with git extension and git notes findings

### Research Conducted
- Analyzed 6 major git extensions (git-lfs, git-flow, git-crypt, git-secret, gh CLI, git-absorb)
- Investigated git notes internals, sync patterns, and limitations
- Validated subprocess approach as industry standard
- Identified critical notes configuration requirements

### Key Decisions
- Git operations: subprocess to git binary
- Note attachment: root tree object
- CLI framework: typer (migrate from click)
- Python version: 3.11+
- AI provider priority: OpenAI → Anthropic → Others → Ollama
- Storage format: YAML frontmatter + Markdown

## [0.1.0] - 2025-12-15

### Added
- Initial project workspace created
- Requirements elicitation begun
- Product brief analyzed
