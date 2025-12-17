# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2025-12-17

### Changed

- Enhanced GitHub ecosystem documentation and instructions
  - Added CODEOWNERS file for repository maintenance
  - Updated Copilot instructions with accurate architecture details
  - Improved code-surgeon instructions for Python 3.11+ and Typer CLI
- Archived PyInstaller binary specification to completed directory with retrospective

## [0.2.0] - 2025-12-16

### Added

- **Standalone Binary Distribution** - Pre-built executables for all major platforms
  - macOS ARM64 (M1/M2/M3) and Intel (x86_64)
  - Linux x86_64
  - Windows x86_64
  - No Python installation required - download and run
  - Fast startup time (<1 second) using PyInstaller onedir mode
  - SHA256 checksums for all release assets
  - Curl-pipe-bash installer script with platform auto-detection

- **CI/CD for Binary Builds**
  - GitHub Actions workflow for automated binary builds on release tags
  - PR testing workflow for binary build validation
  - Binary size tracking (150MB limit enforced)
  - Smoke tests for all binary builds

### Changed

- Binary size target reduced from 200MB to 150MB (CI enforced)

## [0.1.7] - 2025-12-16

### Fixed

- Fix wheel build duplicate file entries causing PyPI upload failure
  - Removed redundant `force-include` in pyproject.toml that duplicated templates

## [0.1.6] - 2025-12-16

### Added

- **`git adr issue` command** - Create GitHub issues directly from project templates
  - Supports bug, feature, and documentation issue types
  - Interactive prompts for required fields from `.github/ISSUE_TEMPLATE/` templates
  - Supports both markdown and YAML form-based templates
  - Preview, edit, and submit workflow with `--dry-run` and `--local` options
  - Auto-detects `gh` CLI authentication status

- **Git Hooks and SDLC Integration**
  - `git adr hooks install/uninstall/status` - Manage git hooks for ADR workflows
  - `git adr ci github/gitlab` - Generate CI/CD workflow files for ADR sync and validation
  - `git adr templates pr/issue/codeowners` - Generate PR templates, issue templates, and CODEOWNERS files
  - Pre-push hook validates ADR references in commits

### Fixed

- `make ci` now mirrors GitHub Actions CI workflow exactly
  - Lint and format commands use `.` (entire repo) to match CI
- Suppressed LangChain Pydantic v1 deprecation warning on Python 3.14+
  - Warning was cosmetic but noisy; underlying issue is in LangChain internals

## [0.1.5] - 2025-12-16

### Changed

- Homebrew formula now includes all optional extras (ai, wiki, export) by default
  - Users no longer need to manually install AI dependencies after Homebrew install
  - All langchain providers, PyGithub, python-gitlab, and python-docx are bundled

## [0.1.4] - 2025-12-16

### Fixed

- Optional dependency install hints now display correctly in error messages
  - Rich console was stripping `[ai]` and `[export]` as invalid markup tags
  - Messages now properly show `pip install 'git-adr[ai]'` instead of `pip install git-adr`

## [0.1.3] - 2025-12-15

### Fixed

- Homebrew formula now correctly fetches dependency URLs from PyPI
  - Previously, all resource blocks incorrectly pointed to the main package URL
  - Formula is now fully regenerated on each release with correct dependency info

## [0.1.2] - 2025-12-15

### Added

- Manual release workflow trigger via `workflow_dispatch` for on-demand releases

### Fixed

- Release pipeline now handles `workflow_dispatch` triggers correctly across all jobs
- Homebrew tap update is more robust with `continue-on-error` to prevent blocking releases

## [0.1.1] - 2025-12-15

### Fixed

- `git adr sync --push` now handles missing artifacts ref gracefully (#23)
  - Previously failed when no artifacts had been added to any ADR
  - Now skips pushing `refs/notes/adr-artifacts` if it doesn't exist
- Security: Improved URL substring sanitization in wiki service (#22)
- CI: Fixed Homebrew tap push token URL (#21)

## [0.1.0] - 2025-12-15

Initial release of git-adr - Architecture Decision Records management for git repositories using git notes.

### Added

- **Core ADR Management**
  - `init` - Initialize ADR configuration with customizable templates
  - `new` - Create new ADRs with frontmatter support (title, status, deciders, consulted, informed)
  - `show` - Display ADR content with rich formatting and DACI metadata
  - `list` - List all ADRs with filtering and sorting options
  - `search` - Full-text search across ADR content
  - `sync` - Sync ADRs between git notes and filesystem
  - `rm` - Remove ADRs from git notes storage

- **Status Management**
  - `accept`, `supersede`, `deprecate`, `amend` - ADR lifecycle commands
  - Status tracking with timestamps and linked decisions

- **Graph & Visualization**
  - `graph` - Generate dependency graphs showing ADR relationships
  - Support for Mermaid diagram output

- **Export Capabilities**
  - `export` - Export ADRs to multiple formats (markdown, HTML, JSON)
  - Optional DOCX export with `[export]` extra

- **AI Integration** (optional `[ai]` extra)
  - AI-powered ADR generation and suggestions
  - Support for OpenAI, Anthropic, Google, and Ollama providers

- **Wiki Integration** (optional `[wiki]` extra)
  - Publish ADRs to GitHub Wiki
  - Publish ADRs to GitLab Wiki

- **Developer Experience**
  - Shell completion for Bash, Zsh, and Fish
  - Comprehensive man pages
  - Install script following git-lfs conventions
  - Git subcommand integration (`git adr` works alongside `git-adr`)

- **CI/CD**
  - GitHub Actions workflows for testing, linting, and releases
  - Automated binary releases for Linux, macOS, and Windows
  - Homebrew tap support for macOS installation

### Technical Details

- Built with Python 3.11+ using Typer for CLI
- Uses git notes for storage (non-intrusive, separate from code commits)
- Supports frontmatter-based metadata in Markdown files
- 95%+ test coverage with pytest

[0.2.1]: https://github.com/zircote/git-adr/releases/tag/v0.2.1
[0.2.0]: https://github.com/zircote/git-adr/releases/tag/v0.2.0
[0.1.7]: https://github.com/zircote/git-adr/releases/tag/v0.1.7
[0.1.6]: https://github.com/zircote/git-adr/releases/tag/v0.1.6
[0.1.5]: https://github.com/zircote/git-adr/releases/tag/v0.1.5
[0.1.4]: https://github.com/zircote/git-adr/releases/tag/v0.1.4
[0.1.3]: https://github.com/zircote/git-adr/releases/tag/v0.1.3
[0.1.2]: https://github.com/zircote/git-adr/releases/tag/v0.1.2
[0.1.1]: https://github.com/zircote/git-adr/releases/tag/v0.1.1
[0.1.0]: https://github.com/zircote/git-adr/releases/tag/v0.1.0
