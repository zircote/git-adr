# git-adr-rm(1) -- Remove an ADR from git notes

## SYNOPSIS

`git adr rm` ADR_ID [OPTIONS]

## DESCRIPTION

**git adr rm** removes an Architecture Decision Record from git notes storage.
This permanently removes the ADR from the notes namespace. The operation cannot
be undone through git-adr, though the ADR may be recoverable from git reflog
until garbage collection runs.

Before removing an ADR, the command displays the ADR's title, status, and any
warnings about linked commits or supersession relationships.

## ARGUMENTS

`ADR_ID`
: The ID of the ADR to remove (e.g., `20250115-use-postgresql`).

## OPTIONS

`-f`, `--force`
: Skip the confirmation prompt. Useful for scripting.

`-h`, `--help`
: Show help message and exit.

## WARNINGS

The command warns if the ADR being removed:

- Has linked commits (traceability will be lost)
- Supersedes another ADR (the chain will be broken)
- Is superseded by another ADR (the reference will become stale)

## EXAMPLES

Remove an ADR interactively:

    $ git adr rm 20250115-use-postgresql
    ADR: Use PostgreSQL for primary database
    ID: 20250115-use-postgresql
    Status: accepted

    Remove this ADR? [y/N]: y
    ✓ Removed ADR: 20250115-use-postgresql

Force remove without confirmation:

    $ git adr rm 20250115-use-postgresql --force
    ✓ Removed ADR: 20250115-use-postgresql

Remove an ADR with linked commits (shows warning):

    $ git adr rm 20250115-use-postgresql
    ADR: Use PostgreSQL for primary database
    ID: 20250115-use-postgresql
    Status: accepted

    Warning: ADR is linked to commits: abc1234, def5678
    Remove this ADR? [y/N]:

## RECOVERY

If an ADR is accidentally removed, it may be recoverable from git reflog:

    # Find the notes commit before removal
    git reflog refs/notes/adr

    # Restore the notes ref
    git update-ref refs/notes/adr <commit-sha>

Note: This only works before `git gc` runs and removes unreferenced objects.

## SEE ALSO

git-adr(1), git-adr-edit(1), git-notes(1), git-reflog(1)

## AUTHOR

Written by zircote.

## COPYRIGHT

Copyright (C) 2025 zircote. License MIT.
