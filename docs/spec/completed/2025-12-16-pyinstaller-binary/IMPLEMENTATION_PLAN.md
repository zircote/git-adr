---
document_type: implementation_plan
project_id: SPEC-2025-12-16-001
version: 1.0.0
last_updated: 2025-12-16T10:30:00Z
status: draft
estimated_effort: 2-3 days
---

# PyInstaller Binary Distribution - Implementation Plan

## Overview

This plan implements standalone binary distribution for git-adr using PyInstaller, with automated CI/CD for multi-platform builds and Homebrew integration.

## Phase Summary

| Phase | Focus | Key Deliverables |
|-------|-------|------------------|
| Phase 1 | Local Build | PyInstaller spec file, build script, working local binary |
| Phase 2 | CI/CD | GitHub Actions workflow, multi-platform builds |
| Phase 3 | Distribution | Homebrew formula, installer script, release automation |
| Phase 4 | Polish | Documentation, testing, monitoring |

---

## Phase 1: Local Build Setup

**Goal**: Create a working PyInstaller build locally on macOS

### Task 1.1: Create PyInstaller Spec File

- **Description**: Create comprehensive spec file with all hidden imports and data files
- **File**: `pyinstaller/git-adr.spec`
- **Acceptance Criteria**:
  - [ ] Spec file handles all lazy imports
  - [ ] Template files bundled correctly
  - [ ] Native extensions (tiktoken, grpcio) included
  - [ ] Excludes unnecessary packages (tkinter, matplotlib)

### Task 1.2: Create Build Script

- **Description**: Shell script to build binary with proper environment
- **File**: `scripts/build-binary.sh`
- **Acceptance Criteria**:
  - [ ] Creates clean virtual environment
  - [ ] Installs all dependencies including `[all]` extras
  - [ ] Runs PyInstaller with spec file
  - [ ] Outputs binary to `dist/git-adr`

### Task 1.3: Create Smoke Test Script

- **Description**: Verify binary works correctly
- **File**: `scripts/smoke-test.sh`
- **Acceptance Criteria**:
  - [ ] Tests `--version` and `--help`
  - [ ] Tests `init` command in temp directory
  - [ ] Tests issue template loading
  - [ ] Tests shell completion generation

### Task 1.4: Local Build Verification

- **Description**: Build and test binary locally on macOS ARM64
- **Acceptance Criteria**:
  - [ ] Binary builds without errors
  - [ ] All smoke tests pass
  - [ ] Binary size under 200 MB
  - [ ] Startup time under 5 seconds

### Phase 1 Deliverables

- [ ] `pyinstaller/git-adr.spec`
- [ ] `scripts/build-binary.sh`
- [ ] `scripts/smoke-test.sh`
- [ ] Working local binary

---

## Phase 2: CI/CD Pipeline

**Goal**: Automated multi-platform binary builds on GitHub Actions

### Task 2.1: Create Build Workflow

- **Description**: GitHub Actions workflow for building binaries
- **File**: `.github/workflows/build-binaries.yml`
- **Acceptance Criteria**:
  - [ ] Triggers on version tags (v*)
  - [ ] Builds on all 4 platforms
  - [ ] Uploads binaries as artifacts
  - [ ] Generates checksums

### Task 2.2: macOS ARM64 Build Job

- **Description**: Configure ARM64 macOS build
- **Runner**: `macos-14`
- **Acceptance Criteria**:
  - [ ] Installs Python 3.12
  - [ ] Installs Rust (for tiktoken)
  - [ ] Builds binary successfully
  - [ ] Smoke tests pass

### Task 2.3: macOS x86_64 Build Job

- **Description**: Configure Intel macOS build
- **Runner**: `macos-13`
- **Acceptance Criteria**:
  - [ ] Same as ARM64 build
  - [ ] Binary works on Intel Macs

### Task 2.4: Linux x86_64 Build Job

- **Description**: Configure Linux build
- **Runner**: `ubuntu-22.04`
- **Acceptance Criteria**:
  - [ ] Installs system dependencies
  - [ ] Binary works on standard Linux distros
  - [ ] Uses glibc (not musl)

### Task 2.5: Windows x86_64 Build Job

- **Description**: Configure Windows build
- **Runner**: `windows-2022`
- **File**: Also need `scripts/build-binary.ps1`
- **Acceptance Criteria**:
  - [ ] PowerShell build script
  - [ ] Binary works on Windows 10/11
  - [ ] Outputs `.exe` file

### Task 2.6: Release Asset Upload

- **Description**: Upload binaries to GitHub Release
- **Acceptance Criteria**:
  - [ ] Creates release on tag
  - [ ] Uploads all 4 binaries
  - [ ] Uploads checksums.txt
  - [ ] Proper asset naming convention

### Phase 2 Deliverables

- [ ] `.github/workflows/build-binaries.yml`
- [ ] `scripts/build-binary.ps1` (Windows)
- [ ] All 4 platform builds passing
- [ ] Release assets uploaded correctly

---

## Phase 3: Distribution Channels

**Goal**: Users can install via Homebrew, direct download, or installer script

### Task 3.1: Update Homebrew Formula

- **Description**: Modify formula to download pre-built binary
- **Repository**: `zircote/homebrew-git-adr`
- **File**: `Formula/git-adr.rb`
- **Acceptance Criteria**:
  - [ ] Uses `on_macos`/`on_linux` blocks
  - [ ] Architecture-specific URLs
  - [ ] Verifies SHA256 checksums
  - [ ] Install time < 10 seconds

### Task 3.2: Create Installer Script

- **Description**: curl/wget installation script
- **File**: `scripts/install.sh`
- **Acceptance Criteria**:
  - [ ] Detects OS and architecture
  - [ ] Downloads correct binary
  - [ ] Verifies checksum
  - [ ] Installs to /usr/local/bin or user path
  - [ ] Handles permission errors gracefully

### Task 3.3: Upload Installer to Releases

- **Description**: Include installer script in releases
- **Acceptance Criteria**:
  - [ ] `install.sh` in release assets
  - [ ] One-liner works: `curl -fsSL .../install.sh | sh`

### Task 3.4: Maintain PyPI Distribution

- **Description**: Ensure pip install still works
- **Acceptance Criteria**:
  - [ ] `pip install git-adr` works
  - [ ] `pip install 'git-adr[all]'` works
  - [ ] Version matches binary release

### Phase 3 Deliverables

- [ ] Updated Homebrew formula
- [ ] `scripts/install.sh`
- [ ] Working `brew install git-adr` (< 10 sec)
- [ ] Working `curl ... | sh` install

---

## Phase 4: Polish & Documentation

**Goal**: Production-ready release with documentation

### Task 4.1: Update README

- **Description**: Document new installation methods
- **File**: `README.md`
- **Acceptance Criteria**:
  - [ ] Homebrew instructions
  - [ ] Direct download instructions
  - [ ] Installer script instructions
  - [ ] Platform support table

### Task 4.2: Create RELEASING.md

- **Description**: Document release process
- **File**: `docs/RELEASING.md`
- **Acceptance Criteria**:
  - [ ] Version bump process
  - [ ] Tag creation
  - [ ] CI verification
  - [ ] Homebrew formula update

### Task 4.3: Add Binary Size Tracking

- **Description**: Track binary sizes in CI to catch bloat
- **Acceptance Criteria**:
  - [ ] Log binary sizes in CI
  - [ ] Fail if > 250 MB threshold
  - [ ] Add to PR comments

### Task 4.4: Integration Tests

- **Description**: Full test suite against binary
- **Acceptance Criteria**:
  - [ ] Run pytest against installed binary
  - [ ] Cover all major commands
  - [ ] Test on clean system (no Python)

### Phase 4 Deliverables

- [ ] Updated README.md
- [ ] docs/RELEASING.md
- [ ] Binary size monitoring
- [ ] Integration test suite

---

## Dependency Graph

```
Phase 1:
  Task 1.1 (spec) ──┬──> Task 1.2 (build script) ──> Task 1.4 (verify)
                    │
  Task 1.3 (smoke) ─┘

Phase 2 (requires Phase 1):
  Task 2.1 (workflow) ──┬──> Task 2.2 (mac-arm64)
                        ├──> Task 2.3 (mac-x86)
                        ├──> Task 2.4 (linux)
                        └──> Task 2.5 (windows) ──> Task 2.6 (release)

Phase 3 (requires Phase 2):
  Task 3.1 (homebrew) ──┐
  Task 3.2 (installer) ─┼──> Task 3.4 (pypi)
  Task 3.3 (upload) ────┘

Phase 4 (requires Phase 3):
  Task 4.1 (readme)
  Task 4.2 (releasing)
  Task 4.3 (size tracking)
  Task 4.4 (integration tests)
```

## Risk Mitigation Tasks

| Risk | Mitigation Task | Phase |
|------|-----------------|-------|
| Missing hidden imports | Comprehensive testing of all commands | 1 |
| Large binary size | Exclude unnecessary deps, track size | 1, 4 |
| tiktoken build failures | Pin versions, cache Rust artifacts | 2 |
| Platform-specific bugs | Smoke tests on all platforms | 2 |
| Homebrew cache issues | Document `brew cleanup` | 3 |

## Testing Checklist

- [ ] Unit tests pass with binary
- [ ] Smoke tests on all 4 platforms
- [ ] `git adr init` works
- [ ] `git adr new` works (editor launching)
- [ ] `git adr list` works
- [ ] `git adr issue` works (template loading)
- [ ] `git adr completion` works
- [ ] AI commands work (if API keys set)
- [ ] Clean install on fresh system

## Documentation Tasks

- [ ] Update README with installation instructions
- [ ] Create RELEASING.md for maintainers
- [ ] Update CHANGELOG.md
- [ ] Add troubleshooting section

## Launch Checklist

- [ ] All 4 platform builds green
- [ ] Smoke tests passing
- [ ] Homebrew formula updated
- [ ] Installer script tested
- [ ] README updated
- [ ] Version bumped
- [ ] Tag created
- [ ] Release published
- [ ] Homebrew tested: `brew install git-adr` < 10 sec

## Post-Launch

- [ ] Monitor GitHub Issues for binary problems
- [ ] Track download counts
- [ ] Gather install time feedback
- [ ] Consider code signing for macOS (v0.3.0)
