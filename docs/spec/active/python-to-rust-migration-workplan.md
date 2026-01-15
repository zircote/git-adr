# Python to Rust Migration Work Plan

## Overview

This work plan guides the complete rewrite of a Python project to Rust while preserving repository identity, git history, and documentation. Execute each phase sequentially, completing all tasks before moving to the next phase.

---

## Pre-Requisites

Before starting, confirm the following:

- [ ] You have the repository cloned locally with push access
- [ ] You know the current Python version number (for tagging)
- [ ] You have Rust toolchain installed (`rustup`, `cargo`)
- [ ] You have identified the target project directory

**Provide to Claude:**
- Repository path
- Current version number
- Project name for Cargo.toml
- Any specific features or CLI interfaces that must be preserved

---

## Phase 1: Audit and Documentation

**Goal:** Create a complete snapshot of the current Python state before any changes.

### Task 1.1: Generate Project Inventory

```bash
# Run from project root
# List all Python files
find . -name "*.py" -type f > /tmp/python-files-inventory.txt

# List all configuration files
ls -la pyproject.toml setup.py setup.cfg requirements*.txt Pipfile* poetry.lock .python-version 2>/dev/null

# Export current dependencies
pip freeze > requirements-final-snapshot.txt 2>/dev/null || true
```

**Output:** List of all Python files and dependencies to be removed later.

### Task 1.2: Document Public Interfaces

Create or update `INTERFACES.md` documenting:

- [ ] CLI commands and arguments
- [ ] Configuration file format and options
- [ ] Public API functions (if library)
- [ ] Environment variables used
- [ ] Input/output file formats

### Task 1.3: Identify Files to Preserve

Review and list files that should NOT be deleted:

- [ ] `LICENSE` / `LICENSE.md`
- [ ] `CONTRIBUTING.md`
- [ ] `CODE_OF_CONDUCT.md`
- [ ] `.github/ISSUE_TEMPLATE/`
- [ ] `.github/PULL_REQUEST_TEMPLATE.md`
- [ ] `docs/` (evaluate content - some may need updates)
- [ ] `.gitattributes`
- [ ] Any non-Python assets (images, data files, etc.)

### Task 1.4: Record Repository Metadata

Document current state for restoration:

- [ ] GitHub/GitLab topics/tags
- [ ] Repository description
- [ ] Branch protection rules
- [ ] Secrets/variables in CI (names only, not values)
- [ ] External integrations (badges, webhooks)

---

## Phase 2: Create Migration Branch and Tag

**Goal:** Establish version control structure for safe migration.

### Task 2.1: Ensure Clean Working State

```bash
# Verify no uncommitted changes
git status

# If changes exist, commit or stash them
git stash  # or commit as appropriate
```

### Task 2.2: Tag Final Python Version

```bash
# Replace X.Y.Z with actual current version
git tag -a python-final -m "Final Python version (vX.Y.Z) before Rust rewrite

This tag preserves the complete Python implementation for historical
reference. The project is being rewritten in Rust starting from this point.

To return to this version:
  git checkout python-final
"

git push origin python-final
```

### Task 2.3: Create Migration Branch

```bash
git checkout -b rust-rewrite
git push -u origin rust-rewrite
```

---

## Phase 3: Remove Python Implementation

**Goal:** Clean removal of all Python-specific files in a single atomic commit.

### Task 3.1: Remove Python Source Files

```bash
# Remove Python source directories (adjust paths to match project structure)
rm -rf src/ lib/ 2>/dev/null || true

# Remove Python files in root
rm -f *.py 2>/dev/null || true

# Remove any nested Python files
find . -name "*.py" -type f -delete 2>/dev/null || true
find . -name "*.pyi" -type f -delete 2>/dev/null || true
find . -name "*.pyx" -type f -delete 2>/dev/null || true
find . -name "*.pxd" -type f -delete 2>/dev/null || true
```

### Task 3.2: Remove Python Configuration Files

```bash
# Package configuration
rm -f pyproject.toml setup.py setup.cfg MANIFEST.in 2>/dev/null || true

# Dependency files
rm -f requirements*.txt Pipfile Pipfile.lock poetry.lock pdm.lock 2>/dev/null || true

# Tool configuration
rm -f .python-version pyrightconfig.json mypy.ini pytest.ini conftest.py 2>/dev/null || true
rm -f .coveragerc tox.ini noxfile.py .flake8 .pylintrc 2>/dev/null || true
rm -f .bandit .isort.cfg pycodestyle.cfg 2>/dev/null || true

# Pre-commit (if Python-specific, will be replaced)
rm -f .pre-commit-config.yaml 2>/dev/null || true
```

### Task 3.3: Remove Python Cache and Build Artifacts

```bash
# Cache directories
rm -rf __pycache__/ .pytest_cache/ .mypy_cache/ .ruff_cache/ 2>/dev/null || true
rm -rf .tox/ .nox/ .coverage/ htmlcov/ 2>/dev/null || true

# Build artifacts
rm -rf *.egg-info/ .eggs/ dist/ build/ 2>/dev/null || true
rm -rf wheels/ sdist/ 2>/dev/null || true

# Virtual environments
rm -rf venv/ .venv/ env/ .env/ ENV/ 2>/dev/null || true

# Find and remove any remaining pycache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true
```

### Task 3.4: Remove Python CI Workflows

```bash
# Remove Python-specific GitHub Actions (will be replaced)
rm -f .github/workflows/python*.yml 2>/dev/null || true
rm -f .github/workflows/test.yml 2>/dev/null || true
rm -f .github/workflows/lint.yml 2>/dev/null || true
rm -f .github/workflows/release.yml 2>/dev/null || true

# Or if all workflows are Python-specific:
# rm -rf .github/workflows/ 2>/dev/null || true
```

### Task 3.5: Commit Python Removal

```bash
git add -A
git commit -m "chore: remove Python implementation

BREAKING CHANGE: Complete removal of Python codebase in preparation
for Rust rewrite.

The final Python version is preserved at tag 'python-final' for
historical reference and can be accessed via:

    git checkout python-final

This commit marks the official transition point from Python to Rust.
All Python source files, configuration, dependencies, and tooling
have been removed to ensure a clean slate for the Rust implementation.
"
```

---

## Phase 4: Initialize Rust Project

**Goal:** Create the Rust project structure with proper configuration.

### Task 4.1: Initialize Cargo Project

```bash
# For a binary application
cargo init --name PROJECT_NAME

# OR for a library
cargo init --lib --name PROJECT_NAME
```

### Task 4.2: Configure Cargo.toml

Create/update `Cargo.toml` with appropriate metadata:

```toml
[package]
name = "PROJECT_NAME"
version = "VERSION"  # Start fresh or continue versioning
edition = "2021"
authors = ["Author Name <email@example.com>"]
description = "Project description"
readme = "README.md"
license = "LICENSE_TYPE"
repository = "https://github.com/OWNER/REPO"
keywords = ["keyword1", "keyword2"]
categories = ["category1"]

[dependencies]
# Add project dependencies

[dev-dependencies]
# Add test dependencies

[[bin]]  # If binary
name = "PROJECT_NAME"
path = "src/main.rs"

[lib]  # If library
name = "PROJECT_NAME"
path = "src/lib.rs"

[profile.release]
lto = true
strip = true
```

### Task 4.3: Create Initial Source Structure

For binary:
```bash
mkdir -p src
cat > src/main.rs << 'EOF'
fn main() {
    println!("Hello from Rust!");
}
EOF
```

For library:
```bash
mkdir -p src
cat > src/lib.rs << 'EOF'
//! PROJECT_NAME - Description
//!
//! This crate provides...

pub fn placeholder() {
    todo!("Implement library functionality")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn it_works() {
        // Add tests
    }
}
EOF
```

### Task 4.4: Verify Rust Project Builds

```bash
cargo build
cargo test
cargo clippy -- -D warnings
cargo fmt --check
```

### Task 4.5: Commit Rust Initialization

```bash
git add -A
git commit -m "feat: initialize Rust project structure

Introduces the Rust implementation to replace the Python version.
This is the foundation for the rewritten project.

- Cargo.toml configured with project metadata
- Initial source structure created
- Build and test infrastructure in place

The Rust implementation will achieve feature parity with the
Python version documented in MIGRATION.md.
"
```

---

## Phase 5: Update Repository Configuration

**Goal:** Replace Python tooling configuration with Rust equivalents.

### Task 5.1: Update .gitignore

Replace contents of `.gitignore`:

```gitignore
# Rust / Cargo
/target/
**/*.rs.bk
*.pdb

# Cargo.lock - KEEP for binaries, gitignore for libraries
# Uncomment next line if this is a library:
# Cargo.lock

# Build artifacts
*.so
*.dylib
*.dll
*.a
*.lib

# IDE and editors
.idea/
*.iml
.vscode/
*.swp
*.swo
*~
.DS_Store

# Environment
.env
.env.local

# Coverage
*.profraw
*.profdata
coverage/
tarpaulin-report.html

# Documentation build
/doc/

# Benchmark artifacts
/benchmark/
```

### Task 5.2: Create Rust CI Workflow

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main, rust-rewrite]
  pull_request:
    branches: [main]

env:
  CARGO_TERM_COLOR: always

jobs:
  check:
    name: Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - uses: Swatinem/rust-cache@v2
      - run: cargo check --all-features

  test:
    name: Test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - uses: Swatinem/rust-cache@v2
      - run: cargo test --all-features

  fmt:
    name: Format
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with:
          components: rustfmt
      - run: cargo fmt --all --check

  clippy:
    name: Clippy
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with:
          components: clippy
      - uses: Swatinem/rust-cache@v2
      - run: cargo clippy --all-features -- -D warnings

  docs:
    name: Documentation
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - uses: Swatinem/rust-cache@v2
      - run: cargo doc --no-deps --all-features
        env:
          RUSTDOCFLAGS: -D warnings
```

### Task 5.3: Create Release Workflow (Optional)

Create `.github/workflows/release.yml`:

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

permissions:
  contents: write

jobs:
  build:
    name: Build ${{ matrix.target }}
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        include:
          - target: x86_64-unknown-linux-gnu
            os: ubuntu-latest
          - target: x86_64-apple-darwin
            os: macos-latest
          - target: aarch64-apple-darwin
            os: macos-latest
          - target: x86_64-pc-windows-msvc
            os: windows-latest

    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with:
          targets: ${{ matrix.target }}
      - uses: Swatinem/rust-cache@v2

      - name: Build
        run: cargo build --release --target ${{ matrix.target }}

      - name: Package (Unix)
        if: runner.os != 'Windows'
        run: |
          cd target/${{ matrix.target }}/release
          tar czvf ../../../PROJECT_NAME-${{ matrix.target }}.tar.gz PROJECT_NAME
          cd -

      - name: Package (Windows)
        if: runner.os == 'Windows'
        run: |
          cd target/${{ matrix.target }}/release
          7z a ../../../PROJECT_NAME-${{ matrix.target }}.zip PROJECT_NAME.exe
          cd -

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: PROJECT_NAME-${{ matrix.target }}
          path: PROJECT_NAME-*

  release:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with:
          path: artifacts
          merge-multiple: true

      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: artifacts/*
          generate_release_notes: true
```

### Task 5.4: Create/Update rustfmt.toml

```toml
edition = "2021"
max_width = 100
use_small_heuristics = "Default"
```

### Task 5.5: Create/Update clippy.toml (Optional)

```toml
# Clippy configuration
cognitive-complexity-threshold = 30
```

### Task 5.6: Commit Configuration Updates

```bash
git add -A
git commit -m "chore: add Rust tooling and CI configuration

- Updated .gitignore for Rust project
- Added GitHub Actions CI workflow (check, test, fmt, clippy, docs)
- Added release workflow for cross-platform builds
- Added rustfmt.toml for consistent formatting
"
```

---

## Phase 6: Update Documentation

**Goal:** Update all documentation to reflect the Rust implementation.

### Task 6.1: Create MIGRATION.md

```markdown
# Migration Guide: Python to Rust

## Overview

This project was rewritten from Python to Rust starting with version X.0.0.
This guide helps users transition from the Python version.

## Why Rust?

- [Add your reasons: performance, safety, deployment simplicity, etc.]

## Breaking Changes

| Change | Python | Rust | Migration Action |
|--------|--------|------|------------------|
| Installation | `pip install X` | `cargo install X` | Reinstall |
| Config format | `.yaml` | `.toml` | Convert config file |
| [Add more] | | | |

## Feature Comparison

| Feature | Python | Rust | Notes |
|---------|--------|------|-------|
| Core functionality | ✅ | ✅ | Full parity |
| [Feature 2] | ✅ | ✅ | |
| [Feature 3] | ✅ | 🚧 | Planned for vX.Y |

## Configuration Migration

### Python Configuration (old)

```yaml
# config.yaml
setting: value
```

### Rust Configuration (new)

```toml
# config.toml
setting = "value"
```

## CLI Changes

| Python Command | Rust Command | Notes |
|----------------|--------------|-------|
| `python -m project` | `project` | Direct binary |
| `--old-flag` | `--new-flag` | Renamed |

## Accessing the Python Version

The final Python version is preserved and can be accessed:

```bash
# Via git tag
git checkout python-final

# Via PyPI (if published)
pip install PROJECT_NAME==FINAL_PYTHON_VERSION
```

## Getting Help

- [Link to discussions/issues]
- [Link to documentation]
```

### Task 6.2: Update README.md

Update the README to reflect Rust implementation:

```markdown
# PROJECT_NAME

Brief description of the project.

## Installation

### From crates.io

```bash
cargo install PROJECT_NAME
```

### From source

```bash
git clone https://github.com/OWNER/REPO
cd REPO
cargo build --release
```

### Pre-built binaries

Download from the [releases page](https://github.com/OWNER/REPO/releases).

## Usage

```bash
PROJECT_NAME [OPTIONS] [ARGS]
```

### Examples

```bash
# Example 1
PROJECT_NAME --flag value

# Example 2
PROJECT_NAME subcommand
```

## Configuration

Create a configuration file at `~/.config/PROJECT_NAME/config.toml`:

```toml
# Configuration options
```

## Documentation

- [API Documentation](https://docs.rs/PROJECT_NAME)
- [User Guide](./docs/)

## History

This project was originally written in Python and rewritten in Rust
starting with version X.0.0 for [reasons: performance/safety/etc.].

The final Python version (vY.Z.W) is preserved at the `python-final` tag.
See [MIGRATION.md](MIGRATION.md) for upgrade guidance.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[LICENSE_TYPE] - See [LICENSE](LICENSE) for details.
```

### Task 6.3: Update CHANGELOG.md

Add entry for the Rust version:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [X.0.0] - YYYY-MM-DD

### Changed

- **BREAKING**: Complete rewrite in Rust
- [List specific changes]

### Added

- [New features in Rust version]

### Removed

- Python implementation (preserved at tag `python-final`)

### Migration

See [MIGRATION.md](MIGRATION.md) for upgrade guidance from the Python version.

---

## Python Version History

The following versions were Python implementations:

## [Y.Z.W] - YYYY-MM-DD (Final Python Release)

[Previous changelog entries...]
```

### Task 6.4: Update CONTRIBUTING.md

Update for Rust development:

```markdown
# Contributing to PROJECT_NAME

## Development Setup

1. Install Rust via [rustup](https://rustup.rs/)
2. Clone the repository
3. Run `cargo build`

## Development Commands

```bash
# Build
cargo build

# Run tests
cargo test

# Run with auto-reload during development
cargo watch -x run

# Format code
cargo fmt

# Lint
cargo clippy

# Generate documentation
cargo doc --open
```

## Pull Request Process

1. Ensure `cargo fmt --check` passes
2. Ensure `cargo clippy -- -D warnings` passes
3. Ensure `cargo test` passes
4. Update documentation as needed
5. Update CHANGELOG.md

## Code Style

- Follow Rust API guidelines
- Use `rustfmt` for formatting
- Address all Clippy warnings
```

### Task 6.5: Commit Documentation Updates

```bash
git add -A
git commit -m "docs: update documentation for Rust implementation

- Created MIGRATION.md with upgrade guidance
- Updated README.md with Rust installation and usage
- Updated CHANGELOG.md with rewrite entry
- Updated CONTRIBUTING.md for Rust development
"
```

---

## Phase 7: Verification and Cleanup

**Goal:** Ensure complete removal of Python and proper Rust setup.

### Task 7.1: Verify No Python Artifacts Remain

```bash
# Check for any remaining Python files
echo "=== Checking for Python files ==="
find . -name "*.py" -o -name "*.pyi" -o -name "*.pyc" -o -name "*.pyo" 2>/dev/null | grep -v ".git"

# Check for Python configuration
echo "=== Checking for Python config ==="
ls pyproject.toml setup.py setup.cfg requirements*.txt Pipfile* poetry.lock 2>/dev/null

# Check for Python cache directories
echo "=== Checking for Python cache ==="
find . -type d -name "__pycache__" -o -name "*.egg-info" -o -name ".pytest_cache" 2>/dev/null | grep -v ".git"

# Check for Python references in CI
echo "=== Checking CI for Python references ==="
grep -r "python\|pip\|pypi" .github/workflows/ 2>/dev/null || echo "None found"

# Check .gitignore for Python entries (should be removed)
echo "=== Checking .gitignore for Python entries ==="
grep -E "\.py|__pycache__|\.egg|venv|\.pytest" .gitignore 2>/dev/null || echo "None found"
```

**Expected result:** All checks should return empty or "None found".

### Task 7.2: Verify Rust Project Health

```bash
# Full build
cargo build --release

# Run all tests
cargo test --all-features

# Lint check
cargo clippy --all-features -- -D warnings

# Format check
cargo fmt --check

# Documentation builds without warnings
RUSTDOCFLAGS="-D warnings" cargo doc --no-deps

# Check for unused dependencies (requires cargo-udeps)
# cargo +nightly udeps
```

**Expected result:** All commands succeed with no errors or warnings.

### Task 7.3: Verify Git History Integrity

```bash
# Confirm tag exists and is accessible
git show python-final --quiet && echo "✓ python-final tag accessible"

# Verify clean commit history
git log --oneline -10

# Ensure no large files accidentally committed
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | sort -k3 -n -r | head -20
```

### Task 7.4: Final Cleanup Commit (if needed)

```bash
# If any cleanup was needed
git add -A
git commit -m "chore: final cleanup for Rust migration"
```

---

## Phase 8: Merge and Release

**Goal:** Complete the migration by merging to main and creating the first Rust release.

### Task 8.1: Push Migration Branch

```bash
git push origin rust-rewrite
```

### Task 8.2: Create Pull Request

Create a PR from `rust-rewrite` to `main` with:

**Title:** `feat: Complete Python to Rust rewrite`

**Description:**
```markdown
## Summary

This PR completes the migration of PROJECT_NAME from Python to Rust.

## Changes

- Removed all Python implementation (preserved at `python-final` tag)
- Introduced complete Rust implementation with feature parity
- Updated CI/CD for Rust toolchain
- Updated all documentation

## Breaking Changes

See MIGRATION.md for complete upgrade guidance.

## Verification

- [ ] All CI checks pass
- [ ] No Python artifacts remain
- [ ] Documentation is complete
- [ ] `python-final` tag is accessible

## Post-Merge Tasks

- [ ] Create vX.0.0 release
- [ ] Publish to crates.io (if applicable)
- [ ] Update repository topics/description
- [ ] Announce migration (if applicable)
```

### Task 8.3: Merge PR

After review and CI passes:

```bash
# Merge via GitHub UI or:
git checkout main
git merge rust-rewrite
git push origin main
```

### Task 8.4: Create First Rust Release

```bash
git tag -a vX.0.0 -m "First Rust release

This is the first release of PROJECT_NAME written in Rust,
replacing the Python implementation.

See MIGRATION.md for upgrade guidance from the Python version.
The final Python version is preserved at tag 'python-final'.
"

git push origin vX.0.0
```

### Task 8.5: Post-Migration Cleanup

```bash
# Delete migration branch
git branch -d rust-rewrite
git push origin --delete rust-rewrite
```

### Task 8.6: Update Repository Metadata

Manually update on GitHub/GitLab:

- [ ] Update repository description (if needed)
- [ ] Update topics: remove `python`, add `rust`
- [ ] Verify badges in README render correctly
- [ ] Update any external documentation links

---

## Completion Checklist

### Repository State

- [ ] `main` branch contains only Rust implementation
- [ ] `python-final` tag accessible with complete Python history
- [ ] No Python files, configuration, or artifacts remain
- [ ] `.gitignore` contains only Rust patterns
- [ ] CI workflows are Rust-specific

### Documentation

- [ ] README reflects Rust installation and usage
- [ ] MIGRATION.md provides upgrade guidance
- [ ] CHANGELOG.md documents the transition
- [ ] CONTRIBUTING.md reflects Rust development

### Functionality

- [ ] `cargo build --release` succeeds
- [ ] `cargo test` passes
- [ ] `cargo clippy -- -D warnings` passes
- [ ] `cargo fmt --check` passes
- [ ] All CI checks pass

### Release

- [ ] First Rust version tagged (vX.0.0)
- [ ] Release notes reference migration guide
- [ ] Repository metadata updated

---

## Rollback Plan

If issues are discovered post-migration:

```bash
# Return to Python version
git checkout python-final

# Or create a branch from Python version for fixes
git checkout -b python-hotfix python-final

# If needed, revert main to Python
git checkout main
git revert --no-commit HEAD~N..HEAD  # N = number of migration commits
git commit -m "revert: rollback Rust migration"
```

---

## Notes for Claude

- Execute phases sequentially; do not skip phases
- Confirm completion of each task before proceeding
- Ask for clarification on project-specific details (paths, names, versions)
- Report any errors encountered during execution
- Preserve all user-specified files during Python removal
- Adapt CI workflows to match existing repository patterns
- If the Rust implementation already exists elsewhere, adapt Phase 4 to copy/move rather than initialize
- Use conventional commits format for all commit messages
- When in doubt, pause and ask before destructive operations
