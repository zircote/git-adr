# Shell Completion for git-adr

> **Note:** Shell completion is planned but not yet implemented in the Rust version.
> This document describes the intended design for future implementation.

## Planned Implementation

Shell completion will be provided via the `clap_complete` crate, supporting:

- **Bash**
- **Zsh**
- **Fish**
- **PowerShell**
- **Elvish**

## Current Workaround

Until shell completion is implemented, you can use the following approaches:

### View Available Commands

```bash
git-adr --help
git-adr <command> --help
```

### Git Alias Setup

To use `git adr` instead of `git-adr`:

```bash
git config --global alias.adr '!git-adr'
```

Then you can use:

```bash
git adr new "My decision"
git adr list
git adr show ADR-0001
```

## See Also

- [Commands Reference](COMMANDS.md)
- [Quick Start](../README.md#quick-start)
