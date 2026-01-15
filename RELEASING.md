# Releasing git-adr

This document describes the release process for git-adr (Rust implementation).

## Release Artifacts

Each release produces:

1. **Rust Crate** (crates.io)
   - `git-adr` crate published to crates.io

2. **Pre-built Binaries** (GitHub Releases)
   - `git-adr-aarch64-apple-darwin.tar.gz` - macOS Apple Silicon (M1/M2/M3/M4)
   - `git-adr-x86_64-apple-darwin.tar.gz` - macOS Intel
   - `git-adr-x86_64-unknown-linux-gnu.tar.gz` - Linux x86_64 (glibc)
   - `git-adr-x86_64-unknown-linux-musl.tar.gz` - Linux x86_64 (musl/Alpine)
   - `git-adr-aarch64-unknown-linux-gnu.tar.gz` - Linux ARM64
   - `git-adr-x86_64-pc-windows-msvc.zip` - Windows x86_64
   - `checksums.txt` - SHA256 checksums for all binaries

3. **Homebrew Formula** (via tap)
   - Updated automatically in `zircote/homebrew-tap`

## How to Release

### Prerequisites

- Push access to `zircote/git-adr`
- `CARGO_REGISTRY_TOKEN` secret configured (for crates.io publishing)
- `HOMEBREW_TAP_TOKEN` secret configured (for Homebrew formula updates)

### Release Steps

1. **Update Version**

   Update the version in `Cargo.toml`:
   ```toml
   [package]
   version = "X.Y.Z"
   ```

2. **Update CHANGELOG**

   Add a new section for the version with changes.

3. **Create Release Tag**

   ```bash
   git add Cargo.toml Cargo.lock CHANGELOG.md
   git commit -m "chore(release): bump version to vX.Y.Z"
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   git push origin main --tags
   ```

4. **Automated Workflows**

   Pushing the tag triggers:

   | Workflow | Action |
   |----------|--------|
   | `release.yml` | Builds binaries for all platforms |
   | `release.yml` | Publishes to crates.io |
   | `release.yml` | Creates GitHub Release with assets |
   | `release.yml` | Updates Homebrew formula in tap |

5. **Verify Release**

   - Check [GitHub Releases](https://github.com/zircote/git-adr/releases) for all assets
   - Verify [crates.io](https://crates.io/crates/git-adr) package
   - Test `cargo install git-adr`
   - Test Homebrew: `brew upgrade git-adr` (after tap updates)

## Build Process

Binaries are built using `cargo build --release` on GitHub Actions with cross-compilation:

| Platform | Target Triple | Runner |
|----------|---------------|--------|
| macOS ARM64 | `aarch64-apple-darwin` | `macos-14` |
| macOS Intel | `x86_64-apple-darwin` | `macos-13` |
| Linux x86_64 (glibc) | `x86_64-unknown-linux-gnu` | `ubuntu-22.04` |
| Linux x86_64 (musl) | `x86_64-unknown-linux-musl` | `ubuntu-22.04` |
| Linux ARM64 | `aarch64-unknown-linux-gnu` | `ubuntu-22.04` |
| Windows x86_64 | `x86_64-pc-windows-msvc` | `windows-2022` |

### Expected Binary Sizes

| Platform | Size |
|----------|------|
| macOS ARM64 | ~3-5 MB |
| macOS Intel | ~3-5 MB |
| Linux x86_64 | ~4-6 MB |
| Windows x86_64 | ~4-6 MB |

Note: Rust binaries are significantly smaller than the previous Python+PyInstaller binaries (~70-80 MB).

## Homebrew Formula

The Homebrew formula is maintained at:
- Repository: `zircote/homebrew-tap`
- Formula: `Formula/git-adr.rb`

The release workflow automatically updates the formula with:
- New version
- Updated tarball URL and SHA256

### Manual Formula Update

If automatic update fails:

```bash
# Clone the tap
git clone https://github.com/zircote/homebrew-tap.git
cd homebrew-tap

# Get new SHA256 from release assets
curl -sL https://github.com/zircote/git-adr/releases/download/vX.Y.Z/git-adr-x86_64-apple-darwin.tar.gz | shasum -a 256

# Update Formula/git-adr.rb
# Commit and push
```

## Feature Flags

Optional features can be enabled at build time:

```bash
# Build with AI features
cargo build --release --features ai

# Build with wiki sync
cargo build --release --features wiki

# Build with all features
cargo build --release --features all
```

Features:
- `ai` - AI integration via langchain-rust (Anthropic, OpenAI, etc.)
- `wiki` - GitHub/GitLab wiki synchronization
- `export` - Extended export formats (DOCX)
- `all` - All optional features

## Smoke Tests

Before each release, binaries are tested:

```bash
# Build and test locally
cargo build --release
./target/release/git-adr --version
./target/release/git-adr --help

# Run test suite
cargo test --all-features
```

Tests include:
- `--version` and `--help` flags
- All core commands (init, new, list, show, edit, rm, search)
- Sync operations
- Config management
- Shell completion generation

## Troubleshooting

### crates.io Publish Fails

1. Check `CARGO_REGISTRY_TOKEN` secret is valid
2. Ensure version number is unique
3. Verify `cargo publish --dry-run` works locally

### Binary Build Fails

1. Check GitHub Actions logs for specific error
2. Common issues:
   - Missing system dependencies for cross-compilation
   - Linker errors for musl builds

### Homebrew Update Fails

1. Check `HOMEBREW_TAP_TOKEN` has write access to tap repo
2. Verify release assets are available

### Slow Startup

Rust binaries should start instantly (<100ms). If slow:

1. Check for filesystem-intensive operations at startup
2. Verify no debug symbols in release build
3. Ensure using `--release` flag

## Migration from Python (v0.3.0)

The project was rewritten in Rust starting with v1.0.0. The last Python version was v0.3.0.

To access the legacy Python version:
```bash
# Install last Python release
pip install git-adr==0.3.0

# Or checkout the archived Python code
git checkout python-final
```

ADR data stored in git notes is fully compatible between Python and Rust versions.
