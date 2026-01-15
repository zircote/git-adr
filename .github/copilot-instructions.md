# GitHub Copilot Instructions for git-adr

## Project Overview

git-adr is a Rust CLI tool for managing Architecture Decision Records (ADRs) stored in **git notes** (not files), making ADRs non-intrusive and portable with git history.

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

## Code Style

- Rust 2021 edition, MSRV 1.80
- Full type annotations on public APIs
- Use `#[must_use]` for methods returning values
- Use `const fn` where possible
- Prefer `&str` parameters over `String` when not taking ownership
- Use `impl Into<String>` for flexible string parameters

## Testing

- Test files are in `tests/` directory and inline with `#[cfg(test)]` modules
- Use `tempfile` crate for temporary git repos
- Use `assert_cmd` for CLI testing
- Test naming: `test_<function>_<scenario>_<expected>`

**Test organization:**
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

## Common Patterns

### CLI Commands (Clap derive-based)

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

### Error Handling

- Use `thiserror` for library errors in `src/lib.rs`
- Use `anyhow` for binary errors
- Return `Result<()>` from command handlers

### Console Output

Use the `colored` crate for terminal output:
```rust
use colored::Colorize;

println!("{} ADR created: {}", "✓".green(), id.cyan());
eprintln!("{} Warning: {}", "!".yellow(), message);
```

## ADR Format

ADRs use YAML frontmatter with markdown body:
- **Status**: Proposed, Accepted, Deprecated, Superseded, Rejected
- **Sections**: Context, Decision, Consequences (varies by template)

## Optional Features

Build with features as needed:
- `ai` - LangChain providers for AI commands
- `wiki` - GitHub/GitLab wiki sync
- `export` - DOCX export via docx-rs
- `all` - All features

```bash
cargo build --features ai
cargo build --features all
```

## Development Commands

```bash
cargo build                                    # Build debug
cargo build --release                          # Build release
cargo test                                     # Run all tests
cargo test --all-features                      # Test with features
cargo fmt                                      # Format code
cargo clippy --all-targets --all-features -- -D warnings  # Lint
cargo doc --open                               # Generate docs
```

## Project Structure

```
git-adr/
├── Cargo.toml          # Package manifest
├── src/
│   ├── lib.rs          # Library entry, Error types
│   ├── main.rs         # Binary entry point
│   ├── cli/            # CLI command implementations
│   │   ├── mod.rs      # CLI definition and Commands enum
│   │   ├── init.rs     # Initialize ADR in repo
│   │   ├── new.rs      # Create new ADR
│   │   └── ...         # Other commands
│   └── core/           # Core business logic
│       ├── mod.rs      # Module exports
│       ├── adr.rs      # ADR data model
│       ├── git.rs      # Git subprocess wrapper
│       ├── notes.rs    # Notes CRUD operations
│       └── ...
├── tests/              # Integration tests
└── docs/               # Documentation
```
