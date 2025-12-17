# Releasing git-adr

This document describes the release process for git-adr.

## Release Artifacts

Each release produces:

1. **Python Package** (PyPI)
   - Source distribution (`.tar.gz`)
   - Wheel distribution (`.whl`)

2. **Standalone Binaries** (GitHub Releases)
   - `git-adr-macos-arm64.tar.gz` - macOS Apple Silicon
   - `git-adr-macos-x86_64.tar.gz` - macOS Intel
   - `git-adr-linux-x86_64.tar.gz` - Linux x86_64
   - `git-adr-windows-x86_64.zip` - Windows x86_64
   - `checksums.txt` - SHA256 checksums for all binaries

3. **Release Tarball** (GitHub Releases)
   - Man pages
   - Shell completions
   - Install script

## How to Release

### Prerequisites

- Push access to `zircote/git-adr`
- `HOMEBREW_TAP_TOKEN` secret configured (for Homebrew formula updates)
- `PYPI_API_TOKEN` secret configured (for PyPI publishing)

### Release Steps

1. **Update Version**

   Update the version in:
   - `pyproject.toml` → `version = "X.Y.Z"`
   - `src/git_adr/__init__.py` → `__version__ = "X.Y.Z"`

2. **Update CHANGELOG**

   Add a new section for the version with changes.

3. **Create Release Tag**

   ```bash
   git add pyproject.toml src/git_adr/__init__.py CHANGELOG.md
   git commit -m "Release vX.Y.Z"
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   git push origin main --tags
   ```

4. **Automated Workflows**

   Pushing the tag triggers:

   | Workflow | Action |
   |----------|--------|
   | `release.yml` | Builds Python package, publishes to PyPI |
   | `build-binaries.yml` | Builds standalone binaries for all platforms |
   | `release.yml` (Homebrew) | Updates Homebrew formula in tap |

5. **Verify Release**

   - Check [GitHub Releases](https://github.com/zircote/git-adr/releases) for all assets
   - Verify [PyPI](https://pypi.org/project/git-adr/) package
   - Test binary installation: `curl -sSL .../install-binary.sh | bash`
   - Test Homebrew: `brew upgrade git-adr` (after tap updates)

### Manual Release (workflow_dispatch)

If you need to release without creating a tag:

1. Go to Actions → Release → Run workflow
2. Enter the version (e.g., `0.1.1`)
3. Click "Run workflow"

This will:
- Build and publish to PyPI
- Create a git tag
- Create a GitHub release

## Binary Build Process

Binaries are built using PyInstaller on GitHub Actions:

| Platform | Runner | Notes |
|----------|--------|-------|
| macOS ARM64 | `macos-14` | Apple Silicon (M1/M2/M3) |
| macOS x86_64 | `macos-13` | Intel Macs |
| Linux x86_64 | `ubuntu-22.04` | glibc-based |
| Windows x86_64 | `windows-2022` | Windows 10/11 |

### Binary Structure (onedir mode)

Each binary package contains:
```
git-adr-{platform}/
├── git-adr           # Executable
└── _internal/        # Bundled Python + dependencies
```

The `onedir` mode is used for fast startup (<1 second) vs `onefile` which extracts on each run.

### Expected Binary Sizes

| Platform | Size |
|----------|------|
| macOS ARM64 | ~70-80 MB |
| macOS x86_64 | ~70-80 MB |
| Linux x86_64 | ~80-90 MB |
| Windows x86_64 | ~70-80 MB |

## Homebrew Formula

The Homebrew formula is maintained at:
- Repository: `zircote/homebrew-tap`
- Formula: `Formula/git-adr.rb`

The `release.yml` workflow automatically updates the formula with:
- New version
- Updated PyPI URL and SHA256
- Dependency resources

### Manual Formula Update

If automatic update fails:

```bash
# Clone the tap
git clone https://github.com/zircote/homebrew-tap.git
cd homebrew-tap

# Get new SHA256
curl -L https://pypi.org/pypi/git-adr/X.Y.Z/json | jq '.urls[] | select(.packagetype=="sdist") | .digests.sha256'

# Update Formula/git-adr.rb
# Commit and push
```

## Smoke Tests

Before each release, binaries are smoke tested:

```bash
# Run locally
./scripts/smoke-test.sh dist/git-adr/git-adr
```

Tests include:
- `--version` flag
- `--help` flag
- `init` command
- `list` command
- `show` command
- `search` command
- `stats` command
- `config` command
- `issue` command (template bundling)
- Shell completion generation

## Troubleshooting

### PyPI Publish Fails

1. Check `PYPI_API_TOKEN` secret is valid
2. Ensure version number is unique (can't republish same version)

### Binary Build Fails

1. Check GitHub Actions logs for specific error
2. Common issues:
   - Missing hidden imports → Update `pyinstaller/git-adr.spec`
   - Native library issues → Check system dependencies in workflow

### Homebrew Update Fails

1. Check `HOMEBREW_TAP_TOKEN` has write access to tap repo
2. Verify PyPI package is available before formula update

### Binary Too Large

Target: <100 MB per platform. If exceeded:

1. Check `excludes` in `pyinstaller/git-adr.spec`
2. Add unnecessary packages to exclude list
3. Verify no large data files are bundled

### Slow Startup

Target: <1 second (subsequent runs). If slow:

1. Ensure using `onedir` mode (not `onefile`)
2. First run may be slower due to OS verification (macOS Gatekeeper)
3. Check for filesystem-intensive operations at startup
