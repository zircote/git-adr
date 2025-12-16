---
document_type: architecture
project_id: SPEC-2025-12-15-002
version: 1.0.0
last_updated: 2025-12-15T23:45:00Z
status: draft
---

# Git Hooks & SDLC Integration - Technical Architecture

## System Overview

This architecture defines three complementary mechanisms for automatic ADR notes synchronization and SDLC integration:

1. **Pre-push hooks** - Active enforcement via git hook scripts
2. **Push refspec configuration** - Passive sync via git config
3. **CI/CD integration** - Centralized validation and workflow templates

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Developer Workflow                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   git commit ──► git push ──► Pre-push Hook ──► Remote Repository   │
│                                    │                                 │
│                          ┌─────────┴─────────┐                       │
│                          │                   │                       │
│                    Push ADR Notes      Chain Existing                │
│                    (refs/notes/adr)    Hooks (backup)                │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                        CI/CD Pipeline                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   Pull Request ──► GitHub Actions ──► Validate ADRs ──► Report      │
│                    GitLab CI                                         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Resolution | Rationale |
|----------|------------|-----------|
| Hook script language | POSIX sh | Maximum portability across platforms |
| Hook installation | Interactive prompt | Balance convenience with user control |
| Existing hook handling | Backup-and-chain | Non-destructive, preserves user hooks |
| Sync failure behavior | Configurable | Default non-blocking, optional strict mode |
| Hook management | Dedicated commands | Clear separation from init logic |

## Component Design

### Component 1: Hook Manager (`src/git_adr/hooks.py`)

**Purpose**: Manage git hook installation, versioning, and lifecycle

**Responsibilities**:
- Install/uninstall pre-push hooks
- Detect and backup existing hooks
- Chain with user hooks
- Track hook versions for upgrades
- Generate manual integration instructions

**Interfaces**:
```python
class Hook:
    """Single hook manager."""
    type: str           # "pre-push", "post-commit", etc.
    hooks_dir: Path     # .git/hooks/
    version: str        # "1.0"

    def install(self, force: bool = False) -> str
    def uninstall(self) -> str
    def is_ours(self) -> bool
    def get_manual_instructions(self) -> str

class HooksManager:
    """Manages all git-adr hooks."""
    def install_all(self, force: bool = False) -> list[str]
    def uninstall_all(self) -> list[str]
    def get_status() -> dict[str, HookStatus]
```

**Dependencies**:
- `core/git.py` - Git directory detection
- `core/config.py` - Hook configuration settings

**Technology**: Python 3.11+, pathlib for file operations

### Component 2: Hook Scripts (Shell)

**Purpose**: Actual git hook scripts installed in `.git/hooks/`

**Script Template** (`pre-push`):
```bash
#!/bin/sh
# git-adr hook - pre-push
# Version: 1.0
# Installed by: git adr hooks install

# Recursion guard
[ -n "$GIT_ADR_HOOK_RUNNING" ] && exit 0
export GIT_ADR_HOOK_RUNNING=1

# Skip if disabled
[ "$GIT_ADR_SKIP" = "1" ] && exit 0

# Check if git-adr exists
command -v git-adr >/dev/null 2>&1 || {
    printf >&2 '\ngit-adr not found. Hook skipped.\n'
    exit 0
}

# Get remote name from arguments
remote="$1"

# Only sync if pushing branches (not tags)
has_branch=false
while read local_ref local_sha remote_ref remote_sha; do
    case "$remote_ref" in
        refs/heads/*) has_branch=true; break ;;
    esac
done
[ "$has_branch" = "true" ] || exit 0

# Sync notes (delegate to git-adr)
git adr hook pre-push "$remote" || {
    # Check if blocking is enabled
    block=$(git config --get adr.hooks.blockOnFailure 2>/dev/null)
    if [ "$block" = "true" ]; then
        printf >&2 'git-adr: notes sync failed, push blocked\n'
        exit 1
    fi
    printf >&2 'git-adr: notes sync failed (non-blocking)\n'
}

# Chain to backup hook if exists
backup_hook="$(dirname "$0")/pre-push.git-adr-backup"
if [ -f "$backup_hook" ]; then
    "$backup_hook" "$@"
fi

exit 0
```

### Component 3: Hook Command Handler (`src/git_adr/commands/hook.py`)

**Purpose**: Handle hook callbacks from shell scripts

**Responsibilities**:
- Execute notes sync on pre-push
- Handle errors gracefully
- Respect configuration settings

**Interface**:
```python
def run_hook(hook_type: str, *args: str) -> None:
    """Execute hook logic for given hook type."""
    match hook_type:
        case "pre-push":
            _handle_pre_push(args[0])  # remote name
        case _:
            raise ValueError(f"Unknown hook type: {hook_type}")

def _handle_pre_push(remote: str) -> None:
    """Sync notes to remote on push."""
    git = get_git(cwd=Path.cwd())
    config = ConfigManager(git).load()
    notes_manager = NotesManager(git, config)

    notes_manager.sync_push(remote)
```

### Component 4: Hook CLI Commands (`src/git_adr/commands/hooks_cli.py`)

**Purpose**: User-facing commands for hook management

**Commands**:
```bash
git adr hooks install [--force] [--manual]
git adr hooks uninstall
git adr hooks status
```

**Integration with CLI** (`cli.py`):
```python
@app.command()
def hooks_install(
    force: Annotated[bool, typer.Option("--force", "-f")] = False,
    manual: Annotated[bool, typer.Option("--manual")] = False,
) -> None:
    """Install git-adr hooks."""
    from git_adr.commands.hooks_cli import run_hooks_install
    run_hooks_install(force=force, manual=manual)
```

### Component 5: Init Integration

**Purpose**: Integrate hook installation into `git adr init` flow

**Changes to `commands/init.py`**:
```python
def run_init(..., install_hooks: bool | None = None) -> None:
    # ... existing init logic ...

    # Hook installation prompt (after config, before initial ADR)
    if install_hooks is None:
        install_hooks = _prompt_for_hooks()

    if install_hooks:
        from git_adr.hooks import HooksManager
        manager = HooksManager(git.git_dir)
        results = manager.install_all()
        for result in results:
            console.print(f"  {result}")
```

**Interactive Prompt**:
```python
def _prompt_for_hooks() -> bool:
    """Ask user about hook installation."""
    console.print("\n[bold]Git Hooks[/bold]")
    console.print("Install pre-push hook to auto-sync ADR notes?")
    console.print("  [dim]This ensures notes are pushed with your code.[/dim]\n")

    return typer.confirm("Install hooks?", default=True)
```

### Component 6: Push Refspec Configuration

**Purpose**: Optional passive sync via git config

**Changes to `core/notes.py`**:
```python
def _configure_remote_notes(self, remote: str, auto_push: bool = False) -> None:
    """Configure a remote for notes fetch and optionally push."""
    # Existing fetch refspec logic...

    if auto_push:
        push_key = f"remote.{remote}.push"
        existing_push = self._git.config_get_all(push_key)

        # Must explicitly add heads if first push entry
        if not existing_push:
            self._git.config_add(push_key, "refs/heads/*:refs/heads/*")

        # Add notes refspecs
        for ref in [self.adr_ref, self.artifacts_ref]:
            push_spec = f"{ref}:{ref}"
            if push_spec not in existing_push:
                self._git.config_add(push_key, push_spec)
```

### Component 7: CI/CD Templates

**Purpose**: Generate workflow files for GitHub Actions and GitLab CI

**Template Structure**:
```
src/git_adr/
├── templates/
│   ├── ci/
│   │   ├── github-actions-sync.yml.j2
│   │   ├── github-actions-validate.yml.j2
│   │   ├── gitlab-ci-sync.yml.j2
│   │   └── gitlab-ci-validate.yml.j2
│   └── governance/
│       ├── pr-template.md.j2
│       ├── issue-template.md.j2
│       └── codeowners.j2
```

**Commands**:
```bash
git adr ci github [--sync] [--validate]  # Generate GitHub Actions
git adr ci gitlab [--sync] [--validate]  # Generate GitLab CI
git adr templates pr                      # Generate PR template
git adr templates issue                   # Generate issue template
git adr templates codeowners              # Generate CODEOWNERS snippet
```

## Data Design

### Configuration Schema

New configuration keys in git config:

```ini
[adr "hooks"]
    # Block push if notes sync fails (default: false)
    blockOnFailure = false

    # Installed hook version (for upgrade detection)
    installedVersion = 1.0

    # Skip hooks via config (alternative to env var)
    skip = false

[adr "sync"]
    # Auto-push enabled via refspec (default: false)
    autoPush = false

    # Sync timeout in seconds (default: 5)
    timeout = 5
```

### Hook State Tracking

Hook state tracked via:
1. **Version comment in hook script** - Enables upgrade detection
2. **Backup file existence** - `.git/hooks/pre-push.git-adr-backup`
3. **Git config** - `adr.hooks.installedVersion`

## Integration Points

### Internal Integrations

| System | Integration Type | Purpose |
|--------|-----------------|---------|
| `core/git.py` | Direct import | Git directory, config operations |
| `core/notes.py` | Direct import | Notes sync operations |
| `core/config.py` | Direct import | Configuration management |
| `commands/init.py` | Code modification | Hook installation prompt |
| `commands/sync.py` | Reference | Existing sync logic |

### External Integrations

| Service | Integration Type | Purpose |
|---------|-----------------|---------|
| GitHub Actions | Template generation | CI/CD workflows |
| GitLab CI | Template generation | CI/CD pipelines |
| Git hooks system | Script installation | Pre-push automation |

## Security Design

### Hook Script Security

- No credentials in hook scripts (uses git credential chain)
- Scripts are not world-writable (mode 0755)
- Backup files are not executable (mode 0644)
- No remote code execution (all logic in git-adr binary)

### Environment Variables

| Variable | Purpose | Risk Mitigation |
|----------|---------|-----------------|
| `GIT_ADR_HOOK_RUNNING` | Recursion guard | Internal use only |
| `GIT_ADR_SKIP` | Emergency bypass | Logged when used |
| `GIT_ADR_DEBUG` | Verbose output | No sensitive data logged |

## Reliability & Operations

### Failure Modes

| Failure | Impact | Recovery |
|---------|--------|----------|
| Network timeout | Notes not synced | Retry on next push; warn user |
| git-adr not in PATH | Hook skipped | Warn in stderr; push continues |
| Backup hook fails | User workflow broken | Propagate exit code; user fixes |
| Permission denied | Hook not installed | Clear error message; suggest fix |

### Idempotency

All operations are idempotent:
- `hooks install` - Safe to run multiple times
- `hooks uninstall` - No error if not installed
- Config additions - Checks for duplicates

## Testing Strategy

### Unit Testing

- `Hook` class methods
- Version detection regex
- Config key generation
- Template rendering

### Integration Testing

```python
def test_hook_install_creates_file(temp_git_repo):
    manager = HooksManager(temp_git_repo / ".git")
    manager.install_all()

    hook = temp_git_repo / ".git" / "hooks" / "pre-push"
    assert hook.exists()
    assert hook.stat().st_mode & 0o111  # Executable

def test_hook_chains_existing(temp_git_repo):
    # Create existing hook
    existing = temp_git_repo / ".git" / "hooks" / "pre-push"
    existing.write_text("#!/bin/sh\necho 'existing'")
    existing.chmod(0o755)

    manager = HooksManager(temp_git_repo / ".git")
    manager.install_all()

    # Backup should exist
    backup = temp_git_repo / ".git" / "hooks" / "pre-push.git-adr-backup"
    assert backup.exists()
```

### End-to-End Testing

```python
def test_pre_push_syncs_notes(temp_git_repo_with_remote):
    # Initialize with hooks
    subprocess.run(["git", "adr", "init", "--install-hooks"])

    # Create ADR
    subprocess.run(["git", "adr", "new", "Test Decision", "--no-edit"])

    # Push (triggers hook)
    subprocess.run(["git", "push", "origin", "main"])

    # Verify notes on remote
    result = subprocess.run(
        ["git", "ls-remote", "origin", "refs/notes/adr"],
        capture_output=True
    )
    assert result.stdout  # Notes ref exists on remote
```

## Deployment Considerations

### Installation

Hooks are local to each repository clone:
- Each developer runs `git adr init` or `git adr hooks install`
- No central deployment needed
- CI/CD templates are committed to repo

### Migration

For existing git-adr users:
1. Update git-adr package
2. Run `git adr hooks install` in each repo
3. Or re-run `git adr init` (will prompt)

### Rollback

```bash
# Remove hooks
git adr hooks uninstall

# Disable via config (keeps hooks but skips)
git config adr.hooks.skip true

# Emergency bypass
GIT_ADR_SKIP=1 git push
```

## Future Considerations

- **post-commit hook** - Alternative sync point for more immediate sync
- **commit-msg hook** - Auto-link ADRs mentioned in commit messages
- **prepare-commit-msg hook** - Suggest ADR references
- **pre-receive hook** - Server-side validation (requires server access)
- **Husky/lefthook integration** - Native support for hook managers
