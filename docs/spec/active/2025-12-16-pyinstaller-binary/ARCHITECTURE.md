---
document_type: architecture
project_id: SPEC-2025-12-16-001
version: 1.0.0
last_updated: 2025-12-16T10:30:00Z
status: draft
---

# PyInstaller Binary Distribution - Technical Architecture

## System Overview

This document describes the architecture for building and distributing git-adr as standalone executables using PyInstaller, with automated CI/CD for multi-platform builds and Homebrew bottle integration.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Release Workflow                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  git tag v0.2.0                                                     │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              GitHub Actions: build-binaries.yml              │   │
│  │                                                              │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │   │
│  │  │ macOS    │  │ macOS    │  │ Linux    │  │ Windows  │    │   │
│  │  │ ARM64    │  │ x86_64   │  │ x86_64   │  │ x86_64   │    │   │
│  │  │ runner   │  │ runner   │  │ runner   │  │ runner   │    │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │   │
│  │       │             │             │             │           │   │
│  │       ▼             ▼             ▼             ▼           │   │
│  │  PyInstaller   PyInstaller   PyInstaller   PyInstaller     │   │
│  │       │             │             │             │           │   │
│  │       ▼             ▼             ▼             ▼           │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │   │
│  │  │ git-adr  │  │ git-adr  │  │ git-adr  │  │ git-adr  │    │   │
│  │  │ (arm64)  │  │ (x86_64) │  │ (linux)  │  │ (win)    │    │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │   │
│  │       │             │             │             │           │   │
│  └───────┼─────────────┼─────────────┼─────────────┼───────────┘   │
│          │             │             │             │               │
│          ▼             ▼             ▼             ▼               │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    GitHub Releases                          │   │
│  │                                                              │   │
│  │  git-adr-v0.2.0-aarch64-apple-darwin.tar.gz                │   │
│  │  git-adr-v0.2.0-x86_64-apple-darwin.tar.gz                 │   │
│  │  git-adr-v0.2.0-x86_64-unknown-linux-gnu.tar.gz            │   │
│  │  git-adr-v0.2.0-x86_64-pc-windows-msvc.zip                 │   │
│  │  checksums.txt                                              │   │
│  │  install.sh                                                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│          ┌───────────────────┼───────────────────┐                 │
│          ▼                   ▼                   ▼                 │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐           │
│  │  Homebrew    │   │   Direct     │   │  Installer   │           │
│  │  Bottles     │   │   Download   │   │   Script     │           │
│  │  (macOS)     │   │  (all OS)    │   │  (Linux/Mac) │           │
│  └──────────────┘   └──────────────┘   └──────────────┘           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **PyInstaller over alternatives**: Best compatibility with native extensions (tiktoken, grpcio, lxml)
2. **onefile mode**: Single executable for simple distribution, despite slower startup
3. **Platform-native builds**: Build on each OS (no cross-compilation) for maximum compatibility
4. **GitHub Releases hosting**: Free, automatic via CI, works with Homebrew bottles

## Component Design

### Component 1: PyInstaller Spec File

- **Purpose**: Define how to bundle git-adr into standalone executable
- **Location**: `pyinstaller/git-adr.spec`
- **Responsibilities**:
  - Specify entry point (`src/git_adr/cli.py`)
  - Define hidden imports for lazy-loaded modules
  - Include template data files
  - Configure native extension handling

### Component 2: Build Scripts

- **Purpose**: Orchestrate PyInstaller builds with proper environment
- **Location**: `scripts/build-binary.sh` (Unix), `scripts/build-binary.ps1` (Windows)
- **Responsibilities**:
  - Set up virtual environment with all dependencies
  - Run PyInstaller with spec file
  - Verify binary works
  - Package into distributable archive

### Component 3: GitHub Actions Workflow

- **Purpose**: Automated multi-platform builds on release
- **Location**: `.github/workflows/build-binaries.yml`
- **Responsibilities**:
  - Trigger on tag push (v*)
  - Build on 4 platform runners
  - Upload binaries to GitHub Releases
  - Generate checksums

### Component 4: Homebrew Formula Update

- **Purpose**: Download pre-built binary instead of building from source
- **Location**: `zircote/homebrew-git-adr/Formula/git-adr.rb`
- **Responsibilities**:
  - Point to GitHub Releases for binary download
  - Verify checksum
  - Extract and install binary
  - Generate shell completions

### Component 5: Installer Script

- **Purpose**: One-line installation for Linux/macOS
- **Location**: `scripts/install.sh` (also uploaded to releases)
- **Responsibilities**:
  - Detect OS and architecture
  - Download correct binary from GitHub Releases
  - Verify checksum
  - Install to `/usr/local/bin` or user-specified location

## Data Design

### Release Asset Naming Convention

Following the pattern established by ruff/uv:

```
git-adr-v{VERSION}-{ARCH}-{PLATFORM}.{EXT}
```

| Platform | Architecture | Filename |
|----------|--------------|----------|
| macOS | ARM64 | `git-adr-v0.2.0-aarch64-apple-darwin.tar.gz` |
| macOS | Intel | `git-adr-v0.2.0-x86_64-apple-darwin.tar.gz` |
| Linux | x86_64 | `git-adr-v0.2.0-x86_64-unknown-linux-gnu.tar.gz` |
| Windows | x86_64 | `git-adr-v0.2.0-x86_64-pc-windows-msvc.zip` |

### Checksums File Format

```
# SHA256 checksums for git-adr v0.2.0
abc123...  git-adr-v0.2.0-aarch64-apple-darwin.tar.gz
def456...  git-adr-v0.2.0-x86_64-apple-darwin.tar.gz
ghi789...  git-adr-v0.2.0-x86_64-unknown-linux-gnu.tar.gz
jkl012...  git-adr-v0.2.0-x86_64-pc-windows-msvc.zip
```

## PyInstaller Spec File Design

```python
# git-adr.spec
# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files

block_cipher = None

# Collect native extensions
tiktoken_datas, tiktoken_binaries, tiktoken_hiddenimports = collect_all('tiktoken')
pydantic_datas, pydantic_binaries, pydantic_hiddenimports = collect_all('pydantic')
pydantic_core_datas, pydantic_core_binaries, pydantic_core_hiddenimports = collect_all('pydantic_core')

# All lazy-loaded command modules
command_modules = [
    'git_adr.commands.init',
    'git_adr.commands.new',
    'git_adr.commands.list',
    'git_adr.commands.show',
    'git_adr.commands.edit',
    'git_adr.commands.rm',
    'git_adr.commands.search',
    'git_adr.commands.link',
    'git_adr.commands.supersede',
    'git_adr.commands.log',
    'git_adr.commands.sync',
    'git_adr.commands.config',
    'git_adr.commands.convert',
    'git_adr.commands.attach',
    'git_adr.commands.artifacts',
    'git_adr.commands.artifact_get',
    'git_adr.commands.artifact_rm',
    'git_adr.commands.ai_draft',
    'git_adr.commands.ai_suggest',
    'git_adr.commands.ai_summarize',
    'git_adr.commands.ai_ask',
    'git_adr.commands.wiki_init',
    'git_adr.commands.wiki_sync',
    'git_adr.commands.stats',
    'git_adr.commands.report',
    'git_adr.commands.metrics',
    'git_adr.commands.onboard',
    'git_adr.commands.export',
    'git_adr.commands.import_',
    'git_adr.commands.issue',
]

# Core modules
core_modules = [
    'git_adr.core',
    'git_adr.core.adr',
    'git_adr.core.config',
    'git_adr.core.git',
    'git_adr.core.index',
    'git_adr.core.notes',
    'git_adr.core.templates',
    'git_adr.core.utils',
    'git_adr.core.issue',
    'git_adr.core.issue_template',
    'git_adr.core.gh_client',
    'git_adr.formats',
    'git_adr.wiki',
    'git_adr.wiki.service',
    'git_adr.ai',
    'git_adr.ai.service',
]

# AI provider modules (optional extras)
ai_modules = [
    'langchain_openai',
    'langchain_anthropic',
    'langchain_google_genai',
    'langchain_ollama',
    'langchain_core',
]

# Native extension hidden imports
native_hiddenimports = [
    'tiktoken_ext.openai_public',
    'tiktoken_ext',
    'grpc',
    'grpc._cython',
    'grpc._cython.cygrpc',
    'lxml.etree',
    'xml.etree',
    'xml.etree.ElementTree',
]

a = Analysis(
    ['src/git_adr/cli.py'],
    pathex=[],
    binaries=tiktoken_binaries + pydantic_binaries + pydantic_core_binaries,
    datas=[
        ('src/git_adr/templates', 'git_adr/templates'),
    ] + tiktoken_datas + pydantic_datas + pydantic_core_datas,
    hiddenimports=(
        command_modules +
        core_modules +
        ai_modules +
        native_hiddenimports +
        tiktoken_hiddenimports +
        pydantic_hiddenimports +
        pydantic_core_hiddenimports +
        collect_submodules('grpc') +
        ['typer.completion']
    ),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'PIL',
        'IPython',
        'jupyter',
        'pytest',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='git-adr',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,  # UPX causes issues on macOS
    console=True,
)
```

## CI/CD Workflow Design

### Build Matrix

```yaml
strategy:
  matrix:
    include:
      - os: macos-14          # ARM64 runner
        target: aarch64-apple-darwin
        ext: tar.gz
      - os: macos-13          # Intel runner
        target: x86_64-apple-darwin
        ext: tar.gz
      - os: ubuntu-22.04
        target: x86_64-unknown-linux-gnu
        ext: tar.gz
      - os: windows-2022
        target: x86_64-pc-windows-msvc
        ext: zip
```

### Workflow Steps (per platform)

1. Checkout code
2. Set up Python 3.12
3. Install Rust (for tiktoken)
4. Install system dependencies (libsodium, etc.)
5. Install Python dependencies (`pip install '.[all]'`)
6. Install PyInstaller
7. Run PyInstaller with spec file
8. Test binary (`./dist/git-adr --version`)
9. Run smoke tests
10. Package binary into archive
11. Upload as release asset

## Homebrew Formula Design

### New Formula Structure

```ruby
class GitAdr < Formula
  desc "Architecture Decision Records management using git notes"
  homepage "https://github.com/zircote/git-adr"
  license "MIT"
  version "0.2.0"

  on_macos do
    on_arm do
      url "https://github.com/zircote/git-adr/releases/download/v0.2.0/git-adr-v0.2.0-aarch64-apple-darwin.tar.gz"
      sha256 "abc123..."
    end
    on_intel do
      url "https://github.com/zircote/git-adr/releases/download/v0.2.0/git-adr-v0.2.0-x86_64-apple-darwin.tar.gz"
      sha256 "def456..."
    end
  end

  on_linux do
    url "https://github.com/zircote/git-adr/releases/download/v0.2.0/git-adr-v0.2.0-x86_64-unknown-linux-gnu.tar.gz"
    sha256 "ghi789..."
  end

  def install
    bin.install "git-adr"

    # Generate shell completions
    generate_completions_from_executable(bin/"git-adr", "completion")
  end

  def caveats
    <<~EOS
      To use git-adr as a git subcommand:
        git config --global alias.adr '!git-adr'

      Then you can use: git adr <command>
    EOS
  end

  test do
    system bin/"git-adr", "--version"
  end
end
```

## Installer Script Design

```bash
#!/bin/bash
# install.sh - Install git-adr binary

set -euo pipefail

VERSION="${GIT_ADR_VERSION:-latest}"
INSTALL_DIR="${GIT_ADR_INSTALL_DIR:-/usr/local/bin}"

# Detect OS and architecture
detect_platform() {
    local os arch
    os="$(uname -s)"
    arch="$(uname -m)"

    case "$os" in
        Darwin)
            case "$arch" in
                arm64) echo "aarch64-apple-darwin" ;;
                x86_64) echo "x86_64-apple-darwin" ;;
                *) echo "Unsupported architecture: $arch" >&2; exit 1 ;;
            esac
            ;;
        Linux)
            case "$arch" in
                x86_64) echo "x86_64-unknown-linux-gnu" ;;
                aarch64) echo "aarch64-unknown-linux-gnu" ;;
                *) echo "Unsupported architecture: $arch" >&2; exit 1 ;;
            esac
            ;;
        *) echo "Unsupported OS: $os" >&2; exit 1 ;;
    esac
}

# Get latest version from GitHub API
get_latest_version() {
    curl -fsSL https://api.github.com/repos/zircote/git-adr/releases/latest \
        | grep '"tag_name":' \
        | sed -E 's/.*"([^"]+)".*/\1/'
}

main() {
    local platform version url tmpdir

    platform="$(detect_platform)"

    if [ "$VERSION" = "latest" ]; then
        version="$(get_latest_version)"
    else
        version="$VERSION"
    fi

    url="https://github.com/zircote/git-adr/releases/download/${version}/git-adr-${version}-${platform}.tar.gz"

    echo "Installing git-adr ${version} for ${platform}..."

    tmpdir="$(mktemp -d)"
    trap 'rm -rf "$tmpdir"' EXIT

    curl -fsSL "$url" | tar -xz -C "$tmpdir"

    if [ -w "$INSTALL_DIR" ]; then
        mv "$tmpdir/git-adr" "$INSTALL_DIR/"
    else
        sudo mv "$tmpdir/git-adr" "$INSTALL_DIR/"
    fi

    chmod +x "$INSTALL_DIR/git-adr"

    echo "Installed git-adr to $INSTALL_DIR/git-adr"
    echo "Run 'git-adr --version' to verify installation"
}

main "$@"
```

## Testing Strategy

### Binary Verification Tests

1. **Startup test**: `git-adr --version` succeeds
2. **Help test**: `git-adr --help` shows all commands
3. **Core command test**: `git adr init` in temp directory
4. **Template test**: `git adr issue --help` shows issue types
5. **Completion test**: `git-adr completion bash` outputs script

### CI Smoke Tests

```bash
#!/bin/bash
# smoke-test.sh

set -ex

# Version check
./dist/git-adr --version

# Help works
./dist/git-adr --help

# Init in temp directory
TMPDIR=$(mktemp -d)
cd "$TMPDIR"
git init
./dist/git-adr init
./dist/git-adr list

# Cleanup
rm -rf "$TMPDIR"

echo "Smoke tests passed!"
```

## Security Considerations

### Binary Integrity

- SHA256 checksums published with every release
- Checksums signed with GPG (optional enhancement)
- Homebrew formula verifies checksums before installation

### Supply Chain

- GitHub Actions builds are reproducible (pinned action versions)
- Dependencies pinned in `uv.lock`
- No secrets embedded in binary

## Performance Considerations

### Expected Metrics

| Metric | Target | Notes |
|--------|--------|-------|
| Binary size | <150 MB | Using onedir mode |
| First startup | <1 second | macOS Gatekeeper may add delay on first run |
| Subsequent startup | <0.2 seconds | OS caches binary (measured: 0.15s) |
| Homebrew install | <10 seconds | Download + extract only |

### Optimization Options

If size becomes an issue:
1. Exclude AI extras from default binary
2. Create separate `git-adr-full` with all extras
3. Use `--onefile` mode (single file, but slower startup due to extraction)

## Future Considerations

1. **Code signing**: macOS notarization for Gatekeeper approval
2. **Auto-update**: Built-in update checker and self-update
3. **Linux ARM64**: Support for Raspberry Pi, AWS Graviton
4. **Modular binaries**: Separate core/AI/full builds
5. **Nuitka migration**: If startup time becomes critical
