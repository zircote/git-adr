# git-adr-new(1) -- Create a new Architecture Decision Record

## SYNOPSIS

`git adr new` TITLE [OPTIONS]

## DESCRIPTION

Create a new Architecture Decision Record with the given title. By default,
opens your configured editor with a template for the ADR content. The ADR
is stored in git notes after editing.

## ARGUMENTS

`TITLE`
: The title for the new ADR. Used to generate a unique ADR ID in the format
  `YYYYMMDD-slug-from-title`.

## OPTIONS

`--status` [proposed|accepted|deprecated|superseded|draft]
: Initial status for the ADR (default: proposed).

`--tags`, `-t` TEXT
: Tags for categorization. Can be specified multiple times.

`--link` TEXT
: Commit SHA to link to this ADR.

`--template` [madr|nygard|y-statement]
: Template format to use (overrides default).

`--file`, `-f` PATH
: Read ADR content from a file instead of opening editor.

`--no-edit`
: Skip editor; requires --file or stdin input.

`--preview`
: Show the template without creating an ADR.

`--draft`
: Mark as draft status (shortcut for --status draft).

`-h`, `--help`
: Show help message and exit.

## INPUT MODES

git-adr-new supports multiple input modes:

**Editor mode** (default)
: Opens your configured editor ($EDITOR, $VISUAL, or fallback) with
  the template. Save and close to create the ADR.

**File input**
: Use `--file path/to/content.md` to read from a file.

**Stdin input**
: Pipe content: `cat adr.md | git adr new "Title"`

**Preview mode**
: Use `--preview` to see the template without creating.

## TEMPLATES

The template includes standard sections based on the format:

**MADR (default)**:
- Context and Problem Statement
- Decision Drivers
- Considered Options
- Decision Outcome
- Pros and Cons of Options
- Consequences

**Nygard**:
- Status
- Context
- Decision
- Consequences

**y-statement**:
- In the context of...
- facing...
- we decided...
- to achieve...
- accepting...

## EXAMPLES

Create an ADR with editor:

    $ git adr new "Use PostgreSQL for primary database"

Create with specific status and tags:

    $ git adr new "Adopt React" --status accepted --tags frontend --tags ui

Create from file:

    $ git adr new "API Design" --file api-decision.md

Create from stdin:

    $ cat << 'EOF' | git adr new "Use REST API"
    ## Context
    We need an API design approach.

    ## Decision
    Use RESTful API design.
    EOF

Preview template:

    $ git adr new "Example" --preview --template nygard

Link to commit during creation:

    $ git adr new "Database Migration" --link abc1234

## FRONTMATTER

Content can include YAML frontmatter for metadata:

    ---
    status: accepted
    date: 2025-01-15
    deciders:
      - Alice
      - Bob
    tags:
      - database
      - infrastructure
    ---

    ## Context
    ...

CLI arguments take precedence over frontmatter values.

## SEE ALSO

git-adr(1), git-adr-edit(1), git-adr-list(1)
