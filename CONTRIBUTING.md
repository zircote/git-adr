# Contributing to git-adr

Thank you for your interest in contributing to git-adr! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Rust 1.85 or higher
- Git
- Cargo (comes with Rust)

### Setting Up Your Development Environment

```bash
# Clone the repository
git clone https://github.com/zircote/git-adr.git
cd git-adr

# Build the project
cargo build

# Verify installation
cargo run -- --version
```

### Running Tests

```bash
# Run all tests
cargo test

# Run with verbose output
cargo test -- --nocapture

# Run specific test
cargo test test_name

# Run tests with all features
cargo test --all-features

# Run specific test module
cargo test core::adr
```

### Code Quality Checks

Before submitting a PR, ensure all checks pass:

```bash
# Format code
cargo fmt

# Check formatting without changes
cargo fmt -- --check

# Run clippy lints
cargo clippy --all-targets --all-features -- -D warnings

# Run security audit
cargo deny check

# Generate docs and check for warnings
RUSTDOCFLAGS="-D warnings" cargo doc --all-features --no-deps

# Run all checks (as CI does)
cargo fmt -- --check && \
cargo clippy --all-targets --all-features -- -D warnings && \
cargo test --all-features
```

## Project Architecture

### Directory Structure

```
src/
├── lib.rs           # Library entry point, Error types
├── main.rs          # Binary entry point
├── cli/             # CLI command implementations
│   ├── mod.rs       # CLI definition and Commands enum
│   ├── init.rs      # Initialize command
│   ├── new.rs       # New ADR command
│   ├── list.rs      # List command
│   ├── show.rs      # Show command
│   ├── edit.rs      # Edit command
│   └── ...          # Other commands
├── core/            # Core business logic
│   ├── mod.rs       # Module exports
│   ├── adr.rs       # ADR struct and AdrStatus enum
│   ├── config.rs    # Configuration management
│   ├── git.rs       # Git operations wrapper
│   ├── notes.rs     # Git notes CRUD operations
│   ├── index.rs     # Search index management
│   └── templates.rs # ADR templates
├── ai/              # AI service layer (optional)
│   ├── mod.rs       # Module exports
│   ├── provider.rs  # Provider abstraction
│   └── service.rs   # AI service implementation
├── wiki/            # Wiki providers (optional)
│   ├── mod.rs       # Module exports
│   ├── github.rs    # GitHub wiki
│   ├── gitlab.rs    # GitLab wiki
│   └── service.rs   # Wiki service abstraction
└── export/          # Format exporters (optional)
    ├── mod.rs       # Module exports
    ├── docx.rs      # DOCX export
    ├── html.rs      # HTML export
    └── json.rs      # JSON export
```

### Key Components

#### Core Layer (`core/`)

- **Git**: Low-level git subprocess wrapper
- **NotesManager**: CRUD operations for ADRs stored in git notes
- **IndexManager**: Search index for fast full-text search
- **ConfigManager**: Git config-based configuration
- **Adr**: Struct representing an ADR with frontmatter metadata

#### Command Layer (`cli/`)

Commands are implemented using Clap derive:

```rust
use clap::Args as ClapArgs;
use anyhow::Result;

#[derive(ClapArgs, Debug)]
pub struct Args {
    /// ADR title
    pub title: String,

    /// ADR status
    #[arg(long, short, default_value = "proposed")]
    pub status: String,
}

pub fn run(args: Args) -> Result<()> {
    let git = Git::new();
    let config = ConfigManager::new(git.clone()).load()?;
    let notes = NotesManager::new(git, config);
    // ... implementation
    Ok(())
}
```

#### AI Layer (`ai/`)

Abstracts LLM providers using langchain-rust:

- Anthropic (Claude)
- OpenAI (GPT-4)
- Google (Gemini)
- Ollama (local models)

## Making Changes

### Workflow

1. **Fork and clone** the repository
2. **Create a feature branch**: `git checkout -b feature/my-feature`
3. **Make changes** following the coding standards
4. **Write tests** for new functionality
5. **Run checks** to ensure quality
6. **Commit** with conventional commit messages
7. **Push** and open a Pull Request

### Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add wiki sync for GitLab
fix: handle empty ADR content gracefully
docs: update README with AI examples
test: add coverage for artifact operations
refactor: extract common validation logic
chore: update dependencies
```

### Code Style

- Follow Rust idioms and conventions
- Use `#[must_use]` for functions that return values that shouldn't be ignored
- Use `const fn` where possible
- Write doc comments for all public items
- Keep functions focused and small
- Prefer borrowing over ownership when possible
- Use `impl Into<String>` for flexible string parameters

### Testing Guidelines

- Write tests for all new functionality
- Use inline `#[cfg(test)]` modules for unit tests
- Use `tests/` directory for integration tests
- Test both success and error cases
- Use meaningful test names: `test_<function>_<scenario>_<expected>`

Example test structure:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_adr_from_markdown_parses_frontmatter() {
        let content = r#"---
title: Test ADR
status: proposed
---

## Context

Test content.
"#;

        let adr = Adr::from_markdown(
            "ADR-0001".to_string(),
            "abc123".to_string(),
            content,
        ).unwrap();

        assert_eq!(adr.title(), "Test ADR");
        assert_eq!(*adr.status(), AdrStatus::Proposed);
    }
}
```

## Adding New Features

### Adding a New Command

1. Create a new file under `cli/`:

```rust
// cli/mycommand.rs
use anyhow::Result;
use clap::Args as ClapArgs;

#[derive(ClapArgs, Debug)]
pub struct Args {
    /// Description of argument
    pub arg: String,

    /// Description of option
    #[arg(long, short, default_value = "default")]
    pub option: String,
}

pub fn run(args: Args) -> Result<()> {
    // Implementation
    Ok(())
}
```

2. Register in `cli/mod.rs`:

```rust
pub mod mycommand;

#[derive(Subcommand, Debug)]
pub enum Commands {
    // ... existing commands
    MyCommand(mycommand::Args),
}
```

3. Handle in `main.rs`:

```rust
Commands::MyCommand(args) => git_adr::cli::mycommand::run(args),
```

4. Add tests
5. Update README with documentation

### Adding a New AI Provider

1. Update `ai/provider.rs` to add the new provider variant
2. Update `ai/service.rs` to handle the new provider
3. Add any required dependencies to `Cargo.toml` under the `ai` feature
4. Add tests with mocked provider

### Adding Export Format

1. Create format module under `export/`:

```rust
// export/newformat.rs
use crate::core::Adr;
use crate::Error;
use std::path::Path;

pub struct NewFormatExporter {
    // configuration
}

impl NewFormatExporter {
    pub fn export(&self, adr: &Adr, path: &Path) -> Result<(), Error> {
        // Implementation
    }
}
```

2. Register in `export/mod.rs`
3. Add to `ExportFormat` enum
4. Add dependencies to `Cargo.toml` if needed

## Pull Request Process

1. **Ensure all checks pass** locally
2. **Update documentation** if needed
3. **Fill out the PR template** completely
4. **Request review** from maintainers
5. **Address feedback** promptly
6. **Squash commits** if requested

### PR Template

PRs should include:

- Description of changes
- Link to related issue (if any)
- Test coverage for new code
- Documentation updates

## Getting Help

- **Issues**: For bugs and feature requests
- **Discussions**: For questions and ideas
- **Code of Conduct**: Be respectful and inclusive

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
