# Changelog

## [1.0.0] - 2025-12-16

### Added
- Complete requirements specification with 9 functional requirements
- Technical architecture with workflow design and validation rules
- Implementation plan with 7 tasks across 3 phases

### Research Conducted
- Analyzed existing release.yml workflow patterns (artifact upload/download, version extraction)
- Reviewed skill-creator's quick_validate.py for validation rules
- Confirmed .skill files are ZIP archives per skill-spec v1.0
- Identified documentation structure in existing README

### Decisions Made
- Release trigger: v* tags (same as main release)
- Artifact naming: git-adr-{version}.skill (versioned)
- Documentation: README section + docs/git-adr-skill.md
- Validation: Include in CI, embedded script (no external dependency)
