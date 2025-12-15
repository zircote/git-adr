# git-adr-sync(1) -- Synchronize ADR notes with remote repository

## SYNOPSIS

`git adr sync` [push|pull|both] [OPTIONS]

## DESCRIPTION

Synchronize Architecture Decision Records with a remote repository.
ADRs are stored in git notes, which require explicit push/pull operations
separate from regular git operations.

## ARGUMENTS

`DIRECTION`
: Sync direction: `push`, `pull`, or `both` (default: both).

## OPTIONS

`--remote`, `-r` TEXT
: Remote name (default: origin).

`--force`, `-f`
: Force push/pull (overwrites remote notes).

`--dry-run`
: Show what would be done without making changes.

`-h`, `--help`
: Show help message and exit.

## OPERATIONS

**push**
: Push local ADR notes to the remote. This makes your ADRs available
  to team members after they fetch.

**pull**
: Fetch and merge ADR notes from the remote. Git automatically merges
  notes using a union strategy by default.

**both**
: Perform both pull and push operations.

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

    $ git adr sync push

Pull from a specific remote:

    $ git adr sync pull --remote upstream

Force push (use with caution):

    $ git adr sync push --force

See what would happen:

    $ git adr sync --dry-run

## NOTES

- The `git adr init` command configures fetch refspecs automatically.
- Regular `git fetch` also fetches ADR notes if configured.
- Artifacts are synced separately from ADR content.

## SEE ALSO

git-adr(1), git-adr-init(1), git-notes(1), git-push(1), git-fetch(1)
