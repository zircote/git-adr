---
document_type: requirements
project_id: SPEC-2025-12-16-001
version: 1.0.0
last_updated: 2025-12-16T10:30:00Z
status: draft
---

# PyInstaller Binary Distribution - Product Requirements Document

## Executive Summary

Create a standalone executable for git-adr using PyInstaller, enabling instant Homebrew installation via pre-built bottles. This eliminates the current 5+ minute installation time (64 dependencies, 9+ native compilations) and matches the user experience of tools like git-lfs (~5 second install).

## Problem Statement

### The Problem

The current Homebrew installation of git-adr requires:
- 64 Python package dependencies installed sequentially
- 9+ packages requiring native compilation (tiktoken/Rust, pydantic-core/Rust, grpcio/C++, PyNaCl/C, lxml/C)
- Build-time dependencies (rust, libsodium, libyaml)
- ~5+ minutes installation time on Apple Silicon

### Impact

- **Poor first impression**: New users may abandon installation
- **CI/CD overhead**: Long install times in pipelines
- **Support burden**: Build failures from missing compilers/dependencies
- **Competitive disadvantage**: Similar tools (git-lfs, ruff, uv) install instantly

### Current State

Users install via:
```bash
brew tap zircote/git-adr
brew install git-adr  # Takes 5+ minutes, compiles from source
```

## Goals and Success Criteria

### Primary Goal

Reduce Homebrew installation time to under 10 seconds by distributing pre-built binaries.

### Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Install time (macOS ARM64) | <30 seconds | Time `brew install git-adr` |
| Install time (macOS Intel) | <30 seconds | Time `brew install git-adr` |
| Binary size | <150 MB | Check release asset size (CI enforced) |
| Feature parity | 100% | Run test suite against binary |
| Startup time | <1 second | Time `git adr --help` |

### Non-Goals (Explicit Exclusions)

- Rewriting git-adr in Rust/Go (out of scope)
- Reducing the number of features/dependencies (user chose full extras)
- Supporting architectures beyond the 4 specified platforms
- Code obfuscation or protection

## User Analysis

### Primary Users

- **Developers**: Want fast installation to try the tool
- **CI/CD pipelines**: Need reliable, fast installation without compilation
- **Enterprise teams**: May not have Rust/C compilers available

### User Stories

1. As a developer, I want to install git-adr in under 10 seconds so that I can quickly evaluate the tool
2. As a CI/CD engineer, I want deterministic installation so that builds don't fail due to compiler issues
3. As a user, I want to upgrade git-adr instantly so that I get security fixes promptly

## Functional Requirements

### Must Have (P0)

| ID | Requirement | Rationale | Acceptance Criteria |
|----|-------------|-----------|---------------------|
| FR-001 | Build standalone binary for macOS ARM64 | Primary Homebrew target | Binary runs on M1/M2/M3 Macs |
| FR-002 | Build standalone binary for macOS x86_64 | Intel Mac support | Binary runs on Intel Macs |
| FR-003 | Build standalone binary for Linux x86_64 | Linux server support | Binary runs on Ubuntu/Debian |
| FR-004 | Build standalone binary for Windows x86_64 | Windows support | Binary runs on Windows 10/11 |
| FR-005 | Include all `[all]` extras | User requirement | AI, wiki, export features work |
| FR-006 | Bundle template files | Required for issue command | `git adr issue` finds templates |
| FR-007 | Homebrew bottles for macOS | Fast install | `brew install` downloads pre-built |
| FR-008 | GitHub Releases distribution | Universal access | Binaries downloadable from releases |

### Should Have (P1)

| ID | Requirement | Rationale | Acceptance Criteria |
|----|-------------|-----------|---------------------|
| FR-101 | Standalone installer script | curl/wget install | `curl ... \| sh` works |
| FR-102 | Automatic release workflow | Maintainability | Tag triggers binary builds |
| FR-103 | SHA256 checksums | Security verification | Checksums published with releases |
| FR-104 | Continue PyPI distribution | Backward compatibility | `pip install git-adr` still works |

### Nice to Have (P2)

| ID | Requirement | Rationale | Acceptance Criteria |
|----|-------------|-----------|---------------------|
| FR-201 | Linux ARM64 binary | Raspberry Pi, AWS Graviton | Binary runs on ARM64 Linux |
| FR-202 | Reproducible builds | Supply chain security | Same input produces same binary |

## Non-Functional Requirements

### Performance

- Binary startup time: <1 second (first run on macOS may be slower due to Gatekeeper)
- Homebrew install time: <10 seconds (excluding download)
- Binary download size: <150 MB (CI enforced)

### Security

- Binaries signed (macOS: notarized if possible)
- SHA256 checksums for all release assets
- No bundled credentials or secrets

### Reliability

- Binary works offline (no runtime downloads)
- Graceful degradation if optional dependencies missing at runtime
- Clear error messages for missing external tools (git, gh)

### Maintainability

- Automated release workflow in GitHub Actions
- Version embedded in binary (`git adr --version`)
- CI builds mirror local builds

## Technical Constraints

- **PyInstaller**: Only tool with sufficient native extension support
- **Cross-compilation**: Not possible; must build on each target OS
- **External dependencies**: `git` and `gh` CLI cannot be bundled
- **Native extensions**: tiktoken (Rust), grpcio (C++), lxml (C) require compilation on build machine

## Dependencies

### Internal Dependencies

- git-adr source code (current version)
- Template files in `src/git_adr/templates/`

### External Dependencies (Build Time)

| Dependency | Purpose | Required On |
|------------|---------|-------------|
| Python 3.11+ | Runtime | All platforms |
| PyInstaller | Binary creation | All platforms |
| Rust | Build tiktoken | All platforms |
| libsodium | Build PyNaCl | All platforms |
| C compiler | Build grpcio, lxml | All platforms |

### External Dependencies (Runtime)

| Dependency | Purpose | Required |
|------------|---------|----------|
| git | Core functionality | Yes |
| gh CLI | Issue creation | Optional |

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Large binary size (>200MB) | Medium | Low | Accept; prioritize install speed over size |
| Slow startup on first run | Medium | Medium | Use `--onedir` if needed; document expected behavior |
| Missing hidden imports | High | High | Comprehensive spec file; full test suite against binary |
| Platform-specific bugs | Medium | High | Test on all platforms in CI |
| tiktoken build failures | Medium | High | Pin versions; cache build artifacts |

## Open Questions

- [x] Which platforms to support? → macOS ARM64/x86_64, Linux x86_64, Windows x86_64
- [x] Include all extras or modular? → Full `[all]` extras
- [x] Homebrew bottles or just GitHub Releases? → Both
- [ ] Code signing for macOS? → To be determined based on effort

## Appendix

### Glossary

| Term | Definition |
|------|------------|
| Bottle | Pre-built Homebrew package binary |
| PyInstaller | Tool to freeze Python applications into standalone executables |
| Hidden import | Python import not detected by static analysis |
| onefile | PyInstaller mode producing single executable (slower startup) |
| onedir | PyInstaller mode producing directory of files (faster startup) |

### References

- [PyInstaller Documentation](https://pyinstaller.org/)
- [Homebrew Bottles Documentation](https://docs.brew.sh/Bottles)
- [git-lfs Release Process](https://github.com/git-lfs/git-lfs/blob/main/docs/howto/release-git-lfs.md)
