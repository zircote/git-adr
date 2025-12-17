# Changelog

All notable changes to this project specification will be documented in this file.

## [1.0.0] - 2025-12-16

### Added
- Complete requirements specification (REQUIREMENTS.md)
  - 5 P0 requirements, 4 P1 requirements, 3 P2 requirements
  - Success metrics and non-goals defined
  - User stories for solo devs, team devs, Claude Code
- Technical architecture design (ARCHITECTURE.md)
  - Component design: SKILL.md, Context Loader, Handlers, References
  - Data models for ADR summaries and full content
  - Integration points with git-adr CLI
  - Skill file structure specification
- Implementation plan (IMPLEMENTATION_PLAN.md)
  - 4 phases: Foundation, Core Features, Enhanced Workflows, Polish
  - 16 tasks with dependencies mapped
  - Testing and documentation checklists
- Architecture decision records (DECISIONS.md)
  - ADR-001: Extend rather than replace existing skill
  - ADR-002: Shell-based git-adr integration
  - ADR-003: Structured YAML for ADR summaries
  - ADR-004: Progressive loading architecture
  - ADR-005: Read-only configuration default
  - ADR-006: Curated command subset

### Research Conducted
- Analyzed git-adr codebase: IndexManager, NotesManager, ADR dataclass, AIService
- Examined 66+ Claude skills for patterns
- Identified progressive loading as key optimization
- Documented existing git-adr skill gap analysis

## [Unreleased]

### Added
- Initial project creation
- Requirements elicitation via structured questions
- Project scaffold: README.md, CHANGELOG.md
