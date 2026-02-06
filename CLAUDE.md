# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Development Commands

```bash
# Build the project
cargo build

# Build release binary
cargo build --release

# Run all tests
cargo test

# Run specific test
cargo test test_name

# Run tests with output
cargo test -- --nocapture

# Run with all features
cargo test --all-features

# Format code
cargo fmt

# Check formatting without modifying
cargo fmt -- --check

# Run clippy lints
cargo clippy --all-targets --all-features -- -D warnings

# Check for security advisories
cargo deny check

# Generate documentation
cargo doc --open

# Run the CLI
cargo run -- --help
cargo run -- init
cargo run -- new "My Decision"
```

## Architecture Overview

git-adr stores Architecture Decision Records in **git notes** (not files), making ADRs non-intrusive and portable with git history.

### Storage Model

- `refs/notes/adr` - ADR content (markdown with YAML frontmatter)
- `refs/notes/adr-index` - Search index for fast full-text lookup
- `refs/notes/adr-artifacts` - Binary attachments (base64 encoded)

### Layer Architecture

```
src/main.rs (Binary entry point)
    ↓
src/cli/*.rs (Clap-based command handlers)
    ↓
src/core/*.rs (Core business logic)
├── notes.rs - NotesManager: CRUD for ADRs in git notes
├── index.rs - IndexManager: Search index operations
├── git.rs - Git: Low-level git subprocess wrapper
├── config.rs - ConfigManager: adr.* git config settings
├── adr.rs - Adr struct: Metadata + content model
└── templates.rs - TemplateEngine: ADR format templates
    ↓
Optional Feature Modules
├── src/ai/*.rs - AI integration (langchain-rust)
├── src/wiki/*.rs - GitHub/GitLab wiki sync
└── src/export/*.rs - Export to DOCX/HTML/JSON
```

### Key Patterns

**Command structure** (Clap derive-based):
```rust
use clap::Args as ClapArgs;
use anyhow::Result;

#[derive(ClapArgs, Debug)]
pub struct Args {
    /// The ADR title
    pub title: String,

    /// ADR format
    #[arg(long, short, default_value = "madr")]
    pub format: String,
}

pub fn run(args: Args) -> Result<()> {
    let git = Git::new();
    let config = ConfigManager::new(git.clone()).load()?;
    let notes = NotesManager::new(git, config);
    // ... implementation
    Ok(())
}
```

**Error handling**: Use `thiserror` for library errors, `anyhow` for binary.

## Code Style

- Rust 2021 edition, MSRV 1.92
- Full type annotations on public APIs
- Use `#[must_use]` for methods returning values
- Use `const fn` where possible
- Prefer `&str` parameters over `String` when not taking ownership
- Use `impl Into<String>` for flexible string parameters

## Testing

Test files are in `tests/` directory and inline with `#[cfg(test)]` modules.

**Test organization**:
```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_function_scenario_expected() {
        // Arrange
        // Act
        // Assert
    }
}
```

**Integration test fixtures** (in `tests/`):
- Use `tempfile` crate for temporary git repos
- Use `assert_cmd` for CLI testing

## Version Management

Version is defined in `Cargo.toml` (single source of truth).

To release: push a tag like `v1.0.0` - CI handles:
- GitHub Release with binaries
- crates.io publish
- Homebrew formula update

## Optional Features

Core package is minimal. Enable features for specific capabilities:
- `ai` - AI integration via langchain-rust
- `wiki` - GitHub/GitLab wiki synchronization
- `export` - DOCX export via docx-rs
- `all` - All features

```bash
cargo build --features ai
cargo build --features all
```

## Code Intelligence (LSP)

### Navigation & Understanding
- Use LSP `goToDefinition` before modifying unfamiliar functions, structs, or modules
- Use LSP `findReferences` before refactoring any symbol to understand full impact
- Use LSP `documentSymbol` to get file structure overview before major edits
- Prefer LSP navigation over grep—it resolves through imports and re-exports

### Verification Workflow
- Check LSP diagnostics after each edit to catch type errors immediately
- Run `cargo clippy` for comprehensive linting
- Verify imports resolve correctly via LSP after adding new dependencies

### Pre-Edit Checklist
- [ ] Navigate to definition to understand implementation
- [ ] Find all references to assess change impact
- [ ] Review type annotations via hover before modifying function signatures
- [ ] Check trait definitions before implementing

### Error Handling
- If LSP reports errors, fix them before proceeding to next task
- Treat clippy warnings as blocking (configured to error in CI)
- Use LSP diagnostics output to guide fixes, not guesswork

### Language Server Details
- **Server**: rust-analyzer
- **Install**: `rustup component add rust-analyzer`
- **Features**: Full Rust support including type inference, traits, generics, macros

## Project Structure

```
git-adr/
├── Cargo.toml          # Package manifest and dependencies
├── Cargo.lock          # Locked dependencies
├── src/
│   ├── lib.rs          # Library entry point, Error types
│   ├── main.rs         # Binary entry point
│   ├── cli/            # CLI command implementations
│   │   ├── mod.rs      # CLI definition and Commands enum
│   │   ├── init.rs     # Initialize ADR in repo
│   │   ├── new.rs      # Create new ADR
│   │   └── ...         # Other commands
│   ├── core/           # Core business logic
│   │   ├── mod.rs      # Module exports
│   │   ├── adr.rs      # ADR data model
│   │   ├── git.rs      # Git subprocess wrapper
│   │   ├── notes.rs    # Notes CRUD operations
│   │   ├── config.rs   # Configuration management
│   │   ├── index.rs    # Search index
│   │   └── templates.rs# Template engine
│   ├── ai/             # AI feature (optional)
│   ├── wiki/           # Wiki sync feature (optional)
│   └── export/         # Export feature (optional)
├── tests/              # Integration tests
├── .github/workflows/  # CI/CD workflows
└── docs/               # Documentation
```
