# Shell Completion for git-adr

git-adr provides shell completion for bash, zsh, fish, and PowerShell.
Completion works for both `git-adr` (direct) and `git adr` (git alias).

## Quick Setup

### Using the completion command (Recommended)

The `completion` command explicitly specifies your shell type:

```bash
# Install bash completion (supports both 'git-adr' and 'git adr')
git-adr completion bash --install

# Install zsh completion
git-adr completion zsh --install

# Install fish completion (auto-creates directory)
git-adr completion fish --install
```

### Show Completion Script

To see the completion script without installing:

```bash
git-adr completion bash
git-adr completion zsh
git-adr completion fish
git-adr completion powershell
```

## Manual Setup

### Bash

Add to your `~/.bashrc`:

```bash
# git-adr completion
eval "$(git-adr completion bash)"
```

Or install directly:

```bash
git-adr completion bash --install
source ~/.bashrc
```

### Zsh

Add to your `~/.zshrc`:

```zsh
# git-adr completion
eval "$(git-adr completion zsh)"
```

Or install directly:

```bash
git-adr completion zsh --install
source ~/.zshrc
```

### Fish

Save to completions directory:

```fish
git-adr completion fish > ~/.config/fish/completions/git-adr.fish
```

Or install directly:

```bash
git-adr completion fish --install
```

### PowerShell

Add to your PowerShell profile (`$PROFILE`):

```powershell
git-adr completion powershell | Out-String | Invoke-Expression
```

## What Gets Completed

Shell completion provides:

- **Commands**: All subcommands (`new`, `list`, `show`, etc.)
- **Options**: Command-specific flags (`--status`, `--tags`, etc.)
- **Arguments**: ADR IDs (for commands like `show`, `edit`)

## Git Alias Setup

To use `git adr` instead of `git-adr`:

```bash
git config --global alias.adr '!git-adr'
```

Then you can use:

```bash
git adr new "My decision"
git adr list
git adr show 20250115-my-decision
```

## Troubleshooting

### Completion Not Working

1. **Reload shell**: `source ~/.bashrc` or `source ~/.zshrc`
2. **Check installation**: `git-adr completion bash` should output a script
3. **Verify fpath** (zsh): Ensure completion directory is in fpath

### Slow Completion

Completion requires invoking `git-adr`, which initializes Python. For
faster completion, consider:

1. Using a shell with completion caching (fish, zsh with zsh-autocomplete)
2. Pre-generating static completion files

### Git Alias Completion

If `git adr <TAB>` doesn't complete but `git-adr <TAB>` does, ensure:

1. The git alias is set up correctly
2. Your shell's git completion knows about the alias

## See Also

- [Typer Completion Documentation](https://typer.tiangolo.com/tutorial/commands/completion/)
- [git-adr Commands Reference](COMMANDS.md)
