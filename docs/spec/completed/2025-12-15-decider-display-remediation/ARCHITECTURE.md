---
document_type: architecture
project_id: SPEC-2025-12-15-001
version: 1.0.0
last_updated: 2025-12-15T19:45:00Z
status: draft
---

# Decider Display Remediation - Technical Architecture

## System Overview

This enhancement modifies four components of the git-adr system to properly display, validate, and prompt for stakeholder metadata (deciders, consulted, informed).

### Architecture Diagram

```
+------------------+     +------------------+     +------------------+
|    CLI Layer     |     |   Core Layer     |     |  Storage Layer   |
|  (commands/*.py) |---->|  (core/*.py)     |---->| (git notes)      |
+------------------+     +------------------+     +------------------+
        |                        |
        v                        v
+------------------+     +------------------+
|  show.py         |     |  adr.py          |
|  - Add display   |     |  - MADR 4.0 alias|
|  - Interactive   |     |  - Validation    |
|    prompt        |     +------------------+
+------------------+
        |
+------------------+
|  new.py          |
|  - --deciders    |
|  - Pre-editor    |
|    prompt        |
+------------------+
```

### Key Design Decisions

1. **Display Enhancement**: Add stakeholder fields to `_output_markdown()` following existing patterns for tags/commits
2. **MADR 4.0 Compatibility**: Handle `decision-makers` as alias in `ADRMetadata.from_dict()`
3. **Required Field**: Use typer.prompt() for interactive deciders input in `new` command
4. **Interactive Backfill**: Prompt on `show` when deciders is empty, using `typer.confirm()`

## Component Design

### Component 1: show.py Modifications

**Purpose**: Display stakeholder metadata in markdown panel output

**Changes**:
- Add deciders display after status (line ~99)
- Add consulted display after deciders
- Add informed display after consulted
- Add interactive prompt when deciders is empty

**Format**:
```python
# After status line
if adr.metadata.deciders:
    header_content.append(f"Deciders: {', '.join(adr.metadata.deciders)}")
if adr.metadata.consulted:
    header_content.append(f"Consulted: {', '.join(adr.metadata.consulted)}")
if adr.metadata.informed:
    header_content.append(f"Informed: {', '.join(adr.metadata.informed)}")
```

**Interactive Prompt Logic**:
```python
if not adr.metadata.deciders:
    if typer.confirm("This ADR has no deciders. Would you like to add them now?"):
        deciders_input = typer.prompt("Enter deciders (comma-separated)")
        # Parse, update ADR, save
```

**Dependencies**:
- `NotesManager.update()` for saving changes
- `typer` for interactive prompts

### Component 2: adr.py Modifications

**Purpose**: MADR 4.0 compatibility and validation

**Changes to ADRMetadata.from_dict()**:
```python
# Support both 'deciders' and 'decision-makers' (MADR 4.0)
deciders = ensure_list(
    data.get("deciders") or data.get("decision-makers") or []
)
```

**Changes to validate_adr()**:
```python
# Add deciders validation (for new ADRs only)
if not adr.metadata.deciders:
    issues.append("Missing deciders - decision makers must be specified")
```

**Note**: Validation for empty deciders should be a warning, not error, to support existing ADRs.

### Component 3: new.py Modifications

**Purpose**: CLI support and pre-editor prompt for deciders

**New Parameter**:
```python
def run_new(
    title: str,
    status: str = "proposed",
    tags: list[str] | None = None,
    deciders: list[str] | None = None,  # NEW
    link: str | None = None,
    ...
)
```

**Pre-Editor Prompt Logic**:
```python
# Before opening editor, prompt for deciders if not provided
if deciders is None:
    if sys.stdin.isatty():  # Only if interactive terminal
        deciders_input = typer.prompt(
            "Enter deciders (comma-separated, or press Enter to skip)",
            default=""
        )
        if deciders_input:
            deciders = [d.strip() for d in deciders_input.split(",")]
```

**Validation Before Save**:
```python
# Reject ADR if deciders still empty after all inputs
if not fm_deciders and not deciders:
    err_console.print("[red]Error:[/red] Deciders are required")
    raise typer.Exit(1)
```

### Component 4: cli.py Modifications

**Purpose**: Expose --deciders flag in CLI

**Changes**:
```python
@app.command()
def new(
    title: str,
    deciders: Annotated[
        Optional[list[str]],
        typer.Option(
            "--deciders", "-d",
            help="Decision makers (can be specified multiple times)"
        )
    ] = None,
    ...
)
```

## Data Design

### Data Models

No schema changes required. `ADRMetadata` already has:
```python
deciders: list[str] = field(default_factory=list)
consulted: list[str] = field(default_factory=list)
informed: list[str] = field(default_factory=list)
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                       ADR Creation Flow                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  CLI Input ──┬── --deciders flag ──────────┬─> ADRMetadata     │
│              │                              │                   │
│              └── Interactive prompt ────────┘                   │
│                                                                 │
│              └── Frontmatter (deciders: [])─┘                   │
│                                                                 │
│              └── Frontmatter (decision-makers: [])──┘           │
│                      (MADR 4.0 alias)                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       ADR Display Flow                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  git adr show ──> NotesManager.get() ──> ADR                   │
│                                            │                    │
│                                            v                    │
│                              ┌─ deciders empty? ─┐              │
│                              │                   │              │
│                          Yes v               No  v              │
│                    Interactive prompt      Display panel        │
│                              │                   │              │
│                              v                   │              │
│                    User provides deciders        │              │
│                              │                   │              │
│                              v                   │              │
│                    NotesManager.update()         │              │
│                              │                   │              │
│                              └───────────────────┘              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## API Design

### CLI Interface Changes

**git adr new**:
```bash
# New --deciders/-d option
git adr new "Use PostgreSQL" --deciders "Alice <alice@example.com>" --deciders "Bob"
git adr new "Use PostgreSQL" -d "Alice, Bob"  # Comma-separated single value also works

# Interactive prompt if --deciders not provided (and TTY available)
git adr new "Use PostgreSQL"
# > Enter deciders (comma-separated, or press Enter to skip): Alice, Bob
```

**git adr show** (behavior change):
```bash
# When deciders is empty
git adr show 20251215-use-postgresql
# > This ADR has no deciders. Would you like to add them now? [y/N]:
```

### Internal API Changes

**show.py**:
- `run_show()`: Add `interactive: bool = True` parameter to control prompting
- `_output_markdown()`: Add stakeholder display logic
- `_prompt_for_deciders()`: New helper function for interactive input

**new.py**:
- `run_new()`: Add `deciders: list[str] | None` parameter
- `_prompt_for_deciders()`: New helper (shared with show.py?)

**adr.py**:
- `ADRMetadata.from_dict()`: Add MADR 4.0 alias handling
- `validate_adr()`: Add deciders validation warning

## Integration Points

### Internal Integrations

| System | Integration Type | Purpose |
|--------|-----------------|---------|
| NotesManager | Method call | Save updated ADR after prompt |
| ConfigManager | Read | Check if interactive mode disabled |
| TemplateEngine | Read | Ensure template includes deciders field |

### External Integrations

None required.

## Security Design

### Data Protection

- Decider information stored in git notes (same as all ADR data)
- No encryption required (names/emails are not sensitive secrets)
- No PII concerns beyond what git already stores

### Input Validation

- Sanitize deciders input (trim whitespace, remove empty entries)
- No command injection risk (values stored as data, not executed)

## Testing Strategy

### Unit Testing

| Component | Test Cases |
|-----------|------------|
| show.py | Display with deciders, display without, interactive prompt |
| new.py | --deciders flag, interactive prompt, validation error |
| adr.py | MADR 4.0 alias parsing, validation warnings |

### Integration Testing

| Scenario | Expected Result |
|----------|-----------------|
| Create ADR with --deciders | ADR stored with deciders |
| Show ADR with deciders | Deciders displayed in panel |
| Show ADR without deciders | Interactive prompt appears |
| YAML frontmatter with decision-makers | Parsed as deciders |

### Test File Locations

- `tests/test_show_stakeholders.py` - New file for display tests
- `tests/test_new_deciders.py` - New file for creation tests
- `tests/test_adr_madr4.py` - New file for MADR 4.0 parsing

## Deployment Considerations

### Backward Compatibility

- Existing ADRs without deciders will work (prompt on show, not error)
- MADR 4.0 templates with `decision-makers` will be parsed correctly
- `--no-interactive` flag available to suppress prompts in CI/CD

### Configuration

Add optional config:
```ini
[adr]
require_deciders = true  # Default: true for new ADRs
interactive = true       # Default: true, set false for CI
```

## Future Considerations

1. **Migration Command**: `git adr migrate-deciders` to bulk-set deciders on existing ADRs
2. **--consulted and --informed flags**: Parity with deciders CLI support
3. **Decider Format Validation**: Optional strict validation of email format
4. **Integration with Git Blame**: Suggest deciders based on file history
