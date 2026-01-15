# git-adr-sync(1) -- Synchronize ADR notes with remote repository

## SYNOPSIS

`git adr sync` [OPTIONS] [REMOTE]

## DESCRIPTION

Synchronize Architecture Decision Records with a remote repository.
ADRs are stored in git notes, which require explicit push/pull operations
separate from regular git operations.

## ARGUMENTS

`REMOTE`
: Remote name (default: origin).

## OPTIONS

`--push`
: Push only (do not pull).

`--pull`
: Pull only (do not push).

`--force`, `-f`
: Force push (overwrites remote notes). Use with caution.

`-h`, `--help`
: Show help message and exit.

## OPERATIONS

By default (without `--push` or `--pull`), sync performs both pull and push:

1. First pulls remote ADR notes (fetch and merge)
2. Then pushes local ADR notes to remote

**--push**
: Push local ADR notes to the remote. This makes your ADRs available
  to team members after they fetch.

**--pull**
: Fetch and merge ADR notes from the remote. Git automatically merges
  notes using a union strategy by default.

## CONFLICT HANDLING

Git notes use a union merge strategy by default, which combines notes
from both sides. For ADRs, this generally works well since each ADR
has a unique object ID.

If conflicts occur:

1. Pull first to get latest changes
2. Resolve any content conflicts manually
3. Push your changes

## EXAMPLES

Sync with default remote (origin):

    $ git adr sync

Push only:

    $ git adr sync --push

Pull only:

    $ git adr sync --pull

Sync with a specific remote:

    $ git adr sync upstream

Force push (use with caution):

    $ git adr sync --push --force

## NOTES

- The `git adr init` command configures fetch refspecs automatically.
- Regular `git fetch` also fetches ADR notes if configured.
- Artifacts are synced separately from ADR content.

## SEE ALSO

git-adr(1), git-adr-init(1), git-notes(1), git-push(1), git-fetch(1)
