# Shell Completion for git-adr

git-adr provides shell completion for bash, zsh, fish, and PowerShell through
Typer's built-in completion system.

## Quick Setup

### Automatic Installation

The easiest way to enable completion:

```bash
git-adr --install-completion
```

This detects your shell and installs the completion script automatically.

### Show Completion Script

To see the completion script without installing:

```bash
git-adr --show-completion
```

## Manual Setup

### Bash

Add to your `~/.bashrc`:

```bash
# git-adr completion
eval "$(git-adr --show-completion bash)"
```

Or save to a file:

```bash
git-adr --show-completion bash > ~/.local/share/bash-completion/completions/git-adr
```

### Zsh

Add to your `~/.zshrc`:

```zsh
# git-adr completion
eval "$(git-adr --show-completion zsh)"
```

Or save to a file in your fpath:

```zsh
git-adr --show-completion zsh > ~/.zfunc/_git-adr
# Then add to .zshrc before compinit:
# fpath+=~/.zfunc
```

### Fish

Save to completions directory:

```fish
git-adr --show-completion fish > ~/.config/fish/completions/git-adr.fish
```

### PowerShell

Add to your PowerShell profile:

```powershell
git-adr --show-completion powershell | Out-String | Invoke-Expression
```

## What Gets Completed

Shell completion provides:

- **Commands**: All subcommands (`new`, `list`, `show`, etc.)
- **Options**: Command-specific flags (`--status`, `--tags`, etc.)
- **Arguments**: ADR IDs (for commands like `show`, `edit`)

## Integration with Git

Since git-adr is typically invoked as `git adr` (git alias), you may also
want to set up completion for the git alias. Add to your `.bashrc`/`.zshrc`:

```bash
# Enable completion for 'git adr' subcommand
_git_adr() {
    if command -v git-adr >/dev/null 2>&1; then
        COMPREPLY=($(compgen -W "$(git-adr --show-completion bash 2>/dev/null | grep -oP '(?<=_GIT_ADR_COMPLETE=bash_source )[a-z-]+')" -- "${COMP_WORDS[COMP_CWORD]}"))
    fi
}
```

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
2. **Check installation**: `git-adr --show-completion` should output a script
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
