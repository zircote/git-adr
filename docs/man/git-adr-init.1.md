# git-adr-init(1) -- Initialize ADR tracking in a repository

## SYNOPSIS

`git adr init` [OPTIONS]

## DESCRIPTION

Initialize Architecture Decision Record tracking in the current git repository.
This command sets up the git notes namespace for storing ADRs and configures
remote fetch/push refspecs for ADR synchronization.

## OPTIONS

`--force`, `-f`
: Reinitialize even if git-adr is already initialized. Useful for reconfiguring
  after adding new remotes.

`--namespace` TEXT
: Custom git notes namespace (default: `refs/notes/adr`).

`--template` [madr|nygard|y-statement]
: Default template format for new ADRs (default: madr).

`-h`, `--help`
: Show help message and exit.

## WHAT GETS CONFIGURED

Running `git adr init` performs the following:

1. **Notes namespace**: Creates the ADR notes namespace in git config.

2. **Remote refspecs**: For each configured remote, adds fetch and push
   refspecs for the ADR notes:
   ```
   remote.origin.fetch = +refs/notes/adr:refs/notes/adr
   remote.origin.push = refs/notes/adr
   ```

3. **Notes rewrite behavior**: Configures git to preserve ADR notes during
   rebase and amend operations:
   ```
   notes.rewriteRef = refs/notes/adr
   notes.rewrite.rebase = true
   notes.rewrite.amend = true
   ```

4. **Initialization marker**: Sets `adr.initialized = true` to indicate
   the repository is configured for git-adr.

## EXAMPLES

Basic initialization:

    $ git adr init

Initialize with a specific template:

    $ git adr init --template nygard

Reinitialize after adding a new remote:

    $ git remote add upstream https://github.com/org/repo.git
    $ git adr init --force

## NOTES

- Initialization is idempotent; running it multiple times is safe.
- Use `--force` to update remote configurations after adding new remotes.
- The ADR namespace is separate from regular git notes, avoiding conflicts.

## SEE ALSO

git-adr(1), git-adr-sync(1), git-notes(1), git-config(1)
