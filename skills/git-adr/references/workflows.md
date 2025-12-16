# git-adr Workflow Patterns

Step-by-step guides for common git-adr workflows.

## 1. New Project Setup

Initialize ADR tracking for a new or existing project.

### Steps

```bash
# 1. Ensure you're in a git repository
git rev-parse --is-inside-work-tree || git init

# 2. Initialize ADR tracking
git adr init

# 3. Configure default template (optional)
git adr config adr.template madr

# 4. Create your first ADR documenting the ADR practice itself
git adr new "Record architecture decisions"

# 5. Push to remote to share with team
git adr sync push
```

### First ADR Content Suggestion

The first ADR should document the decision to use ADRs:
- **Context**: Team needs to document architectural decisions
- **Decision**: Use git-adr to store ADRs in git notes
- **Consequences**: Decisions travel with code, no file clutter

## 2. Team Collaboration

Synchronize ADRs across team members using remote repositories.

### Daily Workflow

```bash
# Start of day: Pull latest ADRs
git adr sync pull

# Check for new decisions
git adr list --since "1 week ago"

# Read any new decisions
git adr show <adr-id>
```

### Creating and Sharing Decisions

```bash
# 1. Create the ADR
git adr new "Adopt React Query for data fetching"

# 2. Push to share with team
git adr sync push

# 3. Notify team (ADR ID is printed after creation)
```

### Resolving Sync Conflicts

If sync fails due to conflicts:

```bash
# 1. Pull and attempt merge
git adr sync pull

# 2. If conflicts exist, list and review
git adr list

# 3. Edit conflicted ADR to resolve
git adr edit <adr-id>

# 4. Push resolved version
git adr sync push
```

## 3. Migration from File-Based ADRs

Import existing ADRs from a `docs/adr/` or `decisions/` directory.

### Steps

```bash
# 1. Initialize git-adr if not done
git adr init

# 2. Import from directory (preserves dates and numbering)
git adr import docs/adr/

# 3. Verify imported ADRs
git adr list
git adr stats

# 4. Spot-check a few ADRs
git adr show <imported-id>

# 5. After verification, archive old files
mkdir -p docs/adr-archive
mv docs/adr/*.md docs/adr-archive/

# 6. Push imported ADRs to remote
git adr sync push
```

### Import Options

```bash
# Import with specific format detection
git adr import docs/adr/ --format madr

# Import single file
git adr import docs/adr/0001-use-postgres.md

# Dry run to preview
git adr import docs/adr/ --dry-run
```

## 4. Onboarding New Team Members

Help new developers understand architectural decisions.

### Onboarding Command

```bash
# Generate onboarding summary
git adr onboard

# Focus on specific topics
git adr onboard --topic database
git adr onboard --topic authentication
```

### Self-Guided Exploration

New team members can explore on their own:

```bash
# 1. List all active decisions
git adr list --status accepted

# 2. View statistics and trends
git adr stats

# 3. Search for domain-specific decisions
git adr search "database"
git adr search "authentication"
git adr search "API"

# 4. Read key ADRs
git adr show <adr-id>

# 5. See which decisions affect specific code
git adr log src/database/
```

### Recommended Reading Order

1. First ADR (usually documents ADR practice)
2. ADRs tagged as "foundational" or "core"
3. Recent accepted decisions
4. Decisions related to assigned work area

## 5. Superseding Decisions

Replace outdated decisions while preserving history.

### When to Supersede

Supersede when:
- Technology choice has changed
- Requirements have significantly evolved
- Original decision proved incorrect
- Better alternatives have emerged

Do NOT supersede when:
- Making minor clarifications (use edit instead)
- Adding implementation details

### Steps

```bash
# 1. Review the original decision
git adr show 20240101-use-mysql

# 2. Create superseding ADR
git adr supersede 20240101-use-mysql "Migrate from MySQL to PostgreSQL"

# 3. In the new ADR, document:
#    - Why the original decision is being superseded
#    - What changed since then
#    - Migration plan (if applicable)

# 4. Original ADR status automatically updates to "superseded"
git adr show 20240101-use-mysql  # Status: Superseded by 20250115-...
```

### Supersession Chain

View the history of related decisions:

```bash
# See what superseded what
git adr show 20250115-use-postgresql --references

# List all superseded decisions
git adr list --status superseded
```

## 6. Linking to Implementation

Connect ADRs to the commits that implement them.

### After Implementing a Decision

```bash
# 1. Get the commit SHA that implements the decision
git log --oneline -5

# 2. Link ADR to implementation commit(s)
git adr link 20250115-use-postgresql abc1234
git adr link 20250115-use-postgresql def5678

# 3. View linked commits
git adr show 20250115-use-postgresql
```

### Using git adr log

Track which decisions affect which files:

```bash
# See ADRs related to files in a directory
git adr log src/database/

# See ADRs for a specific file
git adr log src/config/database.ts

# See ADRs for recent commits
git adr log HEAD~10..HEAD
```

### Best Practice: Link During Development

```bash
# When completing work on an ADR:
git commit -m "Implement PostgreSQL migration per ADR-42"
git adr link 20250115-use-postgresql $(git rev-parse HEAD)
```

## 7. Decision Review Process

Conduct periodic reviews of architectural decisions.

### Quarterly Review

```bash
# 1. List decisions by age
git adr list --sort date

# 2. Find decisions that may need review
git adr list --status accepted --before "6 months ago"

# 3. Check for decisions without linked commits (unimplemented?)
git adr list --unlinked

# 4. Review statistics
git adr stats
```

### Questions for Each ADR

- Is this decision still valid?
- Has context changed significantly?
- Are there new alternatives to consider?
- Should this be superseded?

## 8. Exporting and Reporting

Generate documentation from ADRs.

### Export to Files

```bash
# Export all ADRs to markdown files
git adr export --format markdown --output docs/decisions/

# Export as HTML for documentation site
git adr export --format html --output docs/site/decisions/

# Export specific ADRs
git adr export --id 20250115-use-postgresql
```

### Generate Reports

```bash
# Summary report
git adr stats --format markdown > DECISIONS.md

# Timeline view
git adr list --format timeline

# By status
git adr list --status accepted --format table
```

## Quick Reference

| Workflow | Key Commands |
|----------|--------------|
| New project | `git adr init && git adr new "..." && git adr sync push` |
| Daily sync | `git adr sync pull` |
| Share decision | `git adr new "..." && git adr sync push` |
| Import files | `git adr import docs/adr/` |
| Onboard | `git adr onboard` or `git adr list && git adr show <id>` |
| Supersede | `git adr supersede <old-id> "<new title>"` |
| Link commit | `git adr link <adr-id> <commit-sha>` |
| Review | `git adr list --status accepted && git adr stats` |
