---
document_type: architecture
project_id: SPEC-2025-12-15-001
version: 1.0.0
last_updated: 2025-12-15T00:00:00Z
status: draft
---

# GitHub Issues #13 & #14 - Technical Architecture

## System Overview

This document describes the technical design for two enhancements:

1. **Homebrew Distribution**: A personal tap (`homebrew-git-adr`) with automated formula updates
2. **Documentation Improvements**: New documentation files integrated with existing docs structure

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Release Trigger (git tag v*)                       │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    GitHub Actions: release.yml (existing)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │   Build     │  │  Publish    │  │   GitHub    │  │  Update Homebrew │   │
│  │   Wheel     │──▶│   PyPI      │──▶│   Release   │──▶│   Formula (NEW)  │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └────────┬─────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                                                │
                                                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    zircote/homebrew-git-adr (NEW REPO)                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Formula/git-adr.rb                                                  │   │
│  │    - Downloads from PyPI sdist                                       │   │
│  │    - Creates virtualenv in libexec                                   │   │
│  │    - Installs bin shim, man pages, completions                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         User Installation                                    │
│                                                                              │
│   $ brew tap zircote/git-adr                                                │
│   $ brew install git-adr                                                    │
│                                                                              │
│   Installed:                                                                 │
│   - /usr/local/bin/git-adr (shim → libexec)                                │
│   - /usr/local/share/man/man1/git-adr.1                                    │
│   - /usr/local/share/bash-completion/completions/git-adr                   │
│   - /usr/local/share/zsh/site-functions/_git-adr                           │
│   - /usr/local/share/fish/vendor_completions.d/git-adr.fish                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Tap vs homebrew-core | Personal tap first | Faster iteration, simpler approval |
| Package source | PyPI sdist | Standard for Python, includes dependencies |
| Python isolation | virtualenv in libexec | Homebrew-mandated pattern |
| Formula updates | GitHub Actions | Zero manual intervention |
| Docs format | Markdown | GitHub rendering, pandoc-compatible |

## Component Design

### Component 1: Homebrew Tap Repository

**Purpose**: Host the Homebrew formula for git-adr

**Repository**: `github.com/zircote/homebrew-git-adr`

**Structure**:
```
homebrew-git-adr/
├── Formula/
│   └── git-adr.rb          # Main formula
├── .github/
│   └── workflows/
│       └── test.yml        # Formula CI tests
├── README.md               # Installation instructions
└── LICENSE                 # MIT (match main repo)
```

**Responsibilities**:
- Provide installable formula for Homebrew
- Automated testing of formula on push/PR
- Documentation of tap usage

**Interfaces**:
- Input: Manual push or automated update from release workflow
- Output: Installable formula for `brew install`

**Dependencies**:
- Homebrew (user's system)
- PyPI (package source)

### Component 2: Homebrew Formula (git-adr.rb)

**Purpose**: Define how Homebrew installs git-adr

**Pattern**: Python virtualenv formula (Homebrew standard for Python CLIs)

**Template Structure**:
```ruby
class GitAdr < Formula
  include Language::Python::Virtualenv

  desc "Manage Architecture Decision Records using git notes"
  homepage "https://github.com/zircote/git-adr"
  url "https://files.pythonhosted.org/packages/source/g/git-adr/git_adr-VERSION.tar.gz"
  sha256 "SHA256_HASH"
  license "MIT"

  depends_on "python@3.12"

  # Core dependencies (from pyproject.toml)
  resource "typer" do
    url "https://files.pythonhosted.org/packages/..."
    sha256 "..."
  end
  # ... (rich, python-frontmatter, mistune, pyyaml)

  def install
    virtualenv_install_with_resources

    # Man pages
    man1.install Dir["share/man/man1/*.1"]

    # Shell completions
    generate_completions_from_executable(bin/"git-adr", "completion")
  end

  def caveats
    <<~EOS
      To use git-adr as a git subcommand, run:
        git config --global alias.adr '!git-adr'

      Then use: git adr new "My Decision"
    EOS
  end

  test do
    system bin/"git-adr", "--version"
    assert_match "git-adr", shell_output("#{bin}/git-adr --help")
  end
end
```

**Key Implementation Details**:

1. **Dependencies**: All PyPI dependencies must be declared as `resource` blocks
2. **Man pages**: Built during release, included in sdist
3. **Completions**: Generated at install time using Typer's built-in completion
4. **Testing**: Version and help output verification

### Component 3: Release Workflow Update

**Purpose**: Automate formula updates on new releases

**File**: `.github/workflows/release.yml` (existing, to be extended)

**New Job: `update-homebrew`**

```yaml
update-homebrew:
  needs: [publish]  # After PyPI upload
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4

    - name: Update Homebrew formula
      uses: mislav/bump-homebrew-formula-action@v3
      with:
        formula-name: git-adr
        formula-path: Formula/git-adr.rb
        homebrew-tap: zircote/homebrew-git-adr
        download-url: https://files.pythonhosted.org/packages/source/g/git-adr/git_adr-${{ github.ref_name }}.tar.gz
        commit-message: |
          {{formulaName}} {{version}}

          Created by https://github.com/mislav/bump-homebrew-formula-action
      env:
        COMMITTER_TOKEN: ${{ secrets.HOMEBREW_TAP_TOKEN }}
```

**Alternative**: Simon Willison's `publish-homebrew-formula.yml` pattern using custom Python script.

**Token Requirements**:
- `HOMEBREW_TAP_TOKEN`: PAT with `repo` scope for `homebrew-git-adr` repo
- Stored as repository secret in `git-adr` repo

### Component 4: Documentation Files

**Purpose**: Comprehensive documentation for configuration and ADR formats

**Files to Create**:

#### docs/CONFIGURATION.md

```
docs/CONFIGURATION.md
├── Overview
├── Setting Configuration
│   ├── Local (repository)
│   └── Global (user)
├── Core Settings
│   ├── adr.namespace
│   ├── adr.artifacts_namespace
│   ├── adr.template
│   └── adr.editor
├── Artifact Settings
│   ├── adr.artifact_warn_size
│   └── adr.artifact_max_size
├── Sync Settings
│   ├── adr.sync.auto_push
│   ├── adr.sync.auto_pull
│   └── adr.sync.merge_strategy
├── AI Settings
│   ├── adr.ai.provider
│   ├── adr.ai.model
│   └── adr.ai.temperature
├── Wiki Settings
│   ├── adr.wiki.platform
│   └── adr.wiki.auto_sync
└── Examples
    ├── Minimal setup
    └── Full configuration
```

#### docs/ADR_FORMATS.md

```
docs/ADR_FORMATS.md
├── What is an ADR Format?
├── Choosing a Format
│   └── Comparison table
├── Built-in Formats
│   ├── MADR (Markdown Any Decision Records)
│   │   ├── Description
│   │   ├── When to use
│   │   ├── Full example
│   │   └── Pros/Cons
│   ├── Nygard (Original ADR format)
│   ├── Y-Statement
│   ├── Alexandrian
│   ├── Business Case
│   └── Planguage
├── Custom Templates
│   ├── Creating a template
│   └── Registering with git-adr
└── References
```

#### docs/ADR_PRIMER.md

```
docs/ADR_PRIMER.md
├── What are Architecture Decision Records?
├── Why Document Decisions?
│   ├── Onboarding new team members
│   ├── Understanding historical context
│   └── Preventing decision repetition
├── When to Write an ADR
│   ├── Technology choices
│   ├── Pattern selections
│   └── Trade-off decisions
├── ADR Lifecycle
│   ├── Proposed → Accepted
│   ├── Accepted → Deprecated
│   └── Accepted → Superseded
├── Common Mistakes
│   ├── Too detailed
│   ├── Too brief
│   └── Not updating status
├── Getting Started with git-adr
│   └── Quick 5-minute tutorial
└── Further Reading
    └── Links to Nygard, MADR, etc.
```

### Component 5: Documentation Structure Updates

**Purpose**: Integrate new docs with existing structure

**Changes to docs/README.md** (new file, hub for all docs):

```markdown
# git-adr Documentation

## Getting Started
- [README](../README.md) - Quick start and overview
- [ADR Primer](ADR_PRIMER.md) - Introduction to ADRs for beginners

## Reference
- [Commands](COMMANDS.md) - Complete command reference
- [Configuration](CONFIGURATION.md) - All configuration options
- [ADR Formats](ADR_FORMATS.md) - Template formats and examples
- [Shell Completion](SHELL_COMPLETION.md) - Setup for bash/zsh/fish

## Man Pages
- [git-adr(1)](man/git-adr.1.md) - Main man page
```

**Changes to main README.md**:
- Add "Documentation" section linking to docs/
- Expand configuration section or link to CONFIGURATION.md

## Data Design

Not applicable - this project adds no new data structures. Documentation files are static Markdown.

## API Design

Not applicable - no new APIs. Homebrew formula uses existing CLI.

## Integration Points

### Internal Integrations

| System | Integration Type | Purpose |
|--------|-----------------|---------|
| release.yml | Workflow extension | Trigger formula update |
| pyproject.toml | Version source | Formula version matching |
| docs/man/*.md | Source files | Man page content |
| core/config.py | Documentation source | Config key reference |
| core/templates.py | Documentation source | Format definitions |

### External Integrations

| Service | Integration Type | Purpose |
|---------|-----------------|---------|
| PyPI | HTTP download | Package source for formula |
| GitHub Actions | CI/CD | Formula updates and testing |
| Homebrew | Package manager | Installation target |

## Security Design

### Homebrew Formula Security

- Downloads only from HTTPS (PyPI, GitHub)
- SHA256 verification of downloaded archive
- No credentials in formula (tokens in CI secrets only)
- Formula runs in Homebrew sandbox during test

### GitHub Actions Security

- `HOMEBREW_TAP_TOKEN` stored as repository secret
- Minimal permissions: only write to tap repository
- Token scoped to single repository (not org-wide)

## Testing Strategy

### Homebrew Formula Testing

1. **Local testing** (pre-commit):
   ```bash
   brew audit --strict Formula/git-adr.rb
   brew install --build-from-source Formula/git-adr.rb
   brew test git-adr
   ```

2. **CI testing** (on PR/push to tap):
   ```yaml
   # .github/workflows/test.yml in tap repo
   jobs:
     test:
       runs-on: macos-latest
       steps:
         - uses: actions/checkout@v4
         - run: brew install --build-from-source Formula/git-adr.rb
         - run: brew test git-adr
         - run: brew audit --strict Formula/git-adr.rb
   ```

### Documentation Testing

1. **Link validation**: Check for broken links
2. **Rendering**: Verify GitHub markdown renders correctly
3. **Man page generation**: Ensure pandoc can convert to man format
4. **Manual review**: Human review for accuracy and clarity

## Deployment Considerations

### Homebrew Tap Deployment

**Initial Setup** (one-time):
1. Create `zircote/homebrew-git-adr` repository
2. Add initial formula
3. Configure CI workflow
4. Add `HOMEBREW_TAP_TOKEN` secret to `git-adr` repo

**Ongoing**:
- Releases automatically update formula
- Manual intervention only for dependency changes

### Documentation Deployment

- Committed to main repository
- No separate hosting (GitHub renders Markdown)
- Man pages generated during release build

## Rollback Plan

### Homebrew Formula

- Revert commit in tap repository
- Users can: `brew uninstall git-adr && brew install git-adr` for previous version
- Or: `brew pin git-adr` to prevent upgrades

### Documentation

- Standard git revert
- No production dependencies on documentation

## Future Considerations

1. **homebrew-core submission**: After tap is proven stable (3+ successful releases)
2. **Bottles**: Pre-built binaries for faster installation
3. **Linux Homebrew**: Linuxbrew support (formulae work on Linux too)
4. **Documentation generation**: Auto-generate config docs from source code
5. **MkDocs/Sphinx**: If documentation grows, consider static site generator
