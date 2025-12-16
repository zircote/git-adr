# Git Hooks Guide

This guide covers git-adr's pre-push hooks for automatic ADR notes synchronization.

## Quick Start

The fastest way to set up hooks is during initialization:

```bash
# Interactive setup prompts for hooks installation
git adr init

# Or explicitly install hooks during init
git adr init --install-hooks
```

If you've already initialized git-adr, install hooks separately:

```bash
git adr hooks install
```

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                     git push                                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Pre-push Hook Triggered                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  1. Check if GIT_ADR_SKIP=1 → Skip if set                   │
│  2. Check if pushing branch (not tag) → Skip for tags       │
│  3. Run: git adr sync --push                                │
│  4. Execute backed-up hook (if any)                         │
└─────────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  Push completes                              │
└─────────────────────────────────────────────────────────────┘
```

When you push a branch, the pre-push hook:

1. **Checks for skip conditions** - Respects `GIT_ADR_SKIP=1` environment variable
2. **Validates push type** - Only syncs for branch pushes (not tags)
3. **Syncs ADR notes** - Pushes notes refs to the remote
4. **Chains to existing hooks** - Calls any backed-up hook that was present before installation

## Installation Methods

### Method 1: During Init (Recommended)

```bash
# Interactive - prompts for hooks
git adr init

# Non-interactive - install hooks automatically
git adr init --install-hooks

# Full automation with all features
git adr init --no-input --install-hooks --setup-github-ci
```

### Method 2: Standalone Command

```bash
# Install hooks
git adr hooks install

# Force reinstall (backs up existing hooks)
git adr hooks install --force

# Check status
git adr hooks status
```

### Method 3: Manual Integration

If you have complex existing hooks, get integration snippets:

```bash
git adr hooks install --manual
```

This outputs shell code to add to your existing hook scripts:

```bash
# Add to your existing .git/hooks/pre-push:
if command -v git-adr >/dev/null 2>&1; then
    git adr hook pre-push "$@" || exit $?
fi
```

## Configuration

### Block on Failure

By default, if notes sync fails, the push continues. To require successful sync:

```bash
# Block push if sync fails
git adr hooks config --block-on-failure

# Allow push even if sync fails (default)
git adr hooks config --no-block-on-failure

# View current settings
git adr hooks config --show
```

### Skip Hooks

```bash
# Skip once via environment variable
GIT_ADR_SKIP=1 git push

# Skip permanently via git config
git config adr.hooks.skip true

# Re-enable
git config --unset adr.hooks.skip
```

## Troubleshooting

### Hook Not Executing

1. **Check installation status**:
   ```bash
   git adr hooks status
   ```

2. **Verify hook is executable**:
   ```bash
   ls -la .git/hooks/pre-push
   ```

3. **Test manually**:
   ```bash
   .git/hooks/pre-push
   ```

### Notes Not Syncing

1. **Check remote configuration**:
   ```bash
   git config --get-all remote.origin.push
   ```
   Should include `refs/notes/adr:refs/notes/adr`

2. **Manual sync test**:
   ```bash
   git adr sync --push --verbose
   ```

3. **Check for fetch configuration**:
   ```bash
   git config --get-all remote.origin.fetch
   ```
   Should include `+refs/notes/adr:refs/notes/adr`

### Existing Hook Conflict

If you had a pre-existing pre-push hook:

1. Check for backup: `.git/hooks/pre-push.git-adr-backup`
2. Verify chaining works: The git-adr hook should call the backup
3. If needed, manually integrate using `git adr hooks install --manual`

### Uninstalling Hooks

```bash
# Remove git-adr hooks and restore backups
git adr hooks uninstall
```

## Integration Patterns

### CI/CD Complementary Setup

For robust ADR tracking, combine hooks with CI/CD:

```bash
# Local: Hooks sync on developer push
git adr hooks install

# Remote: CI validates and syncs on merge
git adr ci github
```

This provides:
- **Local hooks**: Immediate sync from developers
- **CI validation**: Catch issues in pull requests
- **CI sync**: Authoritative sync on merge to main

### Team Onboarding

Add to your repository's setup documentation:

```markdown
## Development Setup

1. Clone the repository
2. Initialize git-adr: `git adr init --install-hooks`
3. Start developing!

ADR notes will automatically sync when you push.
```

### Pre-commit Integration

If using [pre-commit](https://pre-commit.com/), you can manage the hook there:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: git-adr-sync
        name: Sync ADR Notes
        entry: git adr sync --push
        language: system
        stages: [pre-push]
        pass_filenames: false
```

## Related Commands

| Command | Description |
|---------|-------------|
| `git adr hooks install` | Install pre-push hooks |
| `git adr hooks uninstall` | Remove hooks and restore backups |
| `git adr hooks status` | Check hook installation status |
| `git adr hooks config` | Configure hook behavior |
| `git adr sync` | Manually sync notes with remote |
| `git adr ci github` | Generate CI/CD workflows |

## Further Reading

- [SDLC Integration Guide](./SDLC_INTEGRATION.md) - Complete CI/CD and governance setup
- [Commands Reference](./COMMANDS.md) - Full command documentation
