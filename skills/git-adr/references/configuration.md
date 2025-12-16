# git-adr Configuration Reference

Quick reference for all git-adr configuration options.

## Configuration Commands

```bash
git adr config list                    # View all settings
git adr config --get adr.template      # Get specific value
git adr config adr.template madr       # Set local value
git adr config --global adr.editor vim # Set global value
git config --unset adr.template        # Remove setting
```

**Precedence**: Local (.git/config) > Global (~/.gitconfig) > Defaults

---

## Core Settings

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `adr.namespace` | string | `adr` | Git notes namespace for ADRs |
| `adr.artifacts_namespace` | string | `adr-artifacts` | Namespace for attached files |
| `adr.template` | string | `madr` | Default ADR format |
| `adr.editor` | string | $EDITOR | Editor for editing ADRs |

### adr.namespace

Notes ref: `refs/notes/<namespace>`. Changing after ADRs exist makes them invisible.

```bash
git adr config adr.namespace adr              # Default
git adr config adr.namespace team-decisions   # Custom
```

### adr.template

| Value | Description |
|-------|-------------|
| `madr` | Full MADR 4.0 with options analysis (default) |
| `nygard` | Minimal Context/Decision/Consequences |
| `y-statement` | Single-sentence format |
| `alexandrian` | Pattern-language with Forces/Solution |
| `business` | Extended with ROI/approval workflow |
| `planguage` | Quality-focused with measurable scales |

```bash
git adr config adr.template nygard
git adr new "Title" --template business  # Override per-ADR
```

### adr.editor

```bash
git adr config --global adr.editor "code --wait"  # VS Code
git adr config --global adr.editor "subl -w"      # Sublime
git adr config --global adr.editor vim
```

---

## Artifact Settings

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `adr.artifact_warn_size` | int | `1048576` (1 MB) | Warning threshold in bytes |
| `adr.artifact_max_size` | int | `10485760` (10 MB) | Hard limit in bytes |

**Size reference**: 1 MB = 1048576, 5 MB = 5242880, 10 MB = 10485760, 50 MB = 52428800

```bash
git adr config adr.artifact_warn_size 5242880   # 5 MB warning
git adr config adr.artifact_max_size 52428800   # 50 MB max
```

---

## Sync Settings

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `adr.sync.auto_push` | bool | `false` | Push notes after changes |
| `adr.sync.auto_pull` | bool | `true` | Pull notes before reads |
| `adr.sync.merge_strategy` | string | `union` | Conflict resolution |

### Merge Strategies

| Strategy | Description |
|----------|-------------|
| `union` | Combine both versions (default, recommended) |
| `ours` | Keep local, discard remote |
| `theirs` | Keep remote, discard local |
| `cat_sort_uniq` | Concatenate, sort, deduplicate |

```bash
git adr config adr.sync.auto_pull true
git adr config adr.sync.auto_push true
git adr config adr.sync.merge_strategy union
git adr sync --pull --merge-strategy theirs  # Override once
```

---

## AI Settings

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `adr.ai.provider` | string | (none) | AI service provider |
| `adr.ai.model` | string | (none) | Model name |
| `adr.ai.temperature` | float | `0.7` | Randomness (0.0-1.0) |

### Providers

| Provider | API Key Variable | Example Models |
|----------|------------------|----------------|
| `openai` | `OPENAI_API_KEY` | gpt-4, gpt-4-turbo, gpt-3.5-turbo |
| `anthropic` | `ANTHROPIC_API_KEY` | claude-3-opus, claude-3-sonnet, claude-3-haiku |
| `google` | `GOOGLE_API_KEY` | gemini-pro, gemini-1.5-pro |
| `bedrock` | AWS credentials | (AWS Bedrock models) |
| `azure` | `AZURE_OPENAI_API_KEY` | (deployment name) |
| `ollama` | (none - local) | llama2, mistral, codellama |
| `openrouter` | `OPENROUTER_API_KEY` | (multiple models) |

### Temperature Guide

| Value | Behavior |
|-------|----------|
| 0.0 | Deterministic, may be repetitive |
| 0.3 | Conservative, consistent |
| 0.7 | Balanced (default) |
| 1.0 | Creative, varied |

```bash
git adr config adr.ai.provider anthropic
git adr config adr.ai.model claude-3-sonnet-20240229
git adr config adr.ai.temperature 0.7
export ANTHROPIC_API_KEY="sk-ant-..."
```

---

## Wiki Settings

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `adr.wiki.platform` | string | `auto` | Wiki platform (github, gitlab, auto) |
| `adr.wiki.auto_sync` | bool | `false` | Auto-export to wiki |

```bash
git adr config adr.wiki.platform github
git adr config adr.wiki.auto_sync true
git adr wiki sync  # Manual sync
```

---

## Configuration Recipes

### AI Setup

```bash
# OpenAI
git adr config adr.ai.provider openai
git adr config adr.ai.model gpt-4-turbo
export OPENAI_API_KEY="sk-..."

# Anthropic
git adr config adr.ai.provider anthropic
git adr config adr.ai.model claude-3-opus-20240229
export ANTHROPIC_API_KEY="sk-ant-..."

# Local Ollama (no API key needed)
git adr config adr.ai.provider ollama
git adr config adr.ai.model mistral
```

### Team Collaboration

```bash
git adr config adr.sync.auto_pull true
git adr config adr.sync.auto_push true
git adr config adr.sync.merge_strategy union
git adr config adr.template business
git config --add remote.origin.fetch '+refs/notes/*:refs/notes/*'
```

### Offline Mode

```bash
git adr config adr.sync.auto_pull false
git adr config adr.sync.auto_push false
git adr config adr.ai.provider ollama
git adr config adr.ai.model llama2
git adr sync --push --pull  # Manual when online
```

### High-Security Environment

```bash
git adr config adr.namespace secure-decisions
git adr config adr.sync.auto_pull false
git adr config adr.sync.auto_push false
git adr config adr.sync.merge_strategy ours
git config --unset adr.ai.provider  # Disable AI
```

### Large Artifacts

```bash
git adr config adr.artifact_warn_size 5242880   # 5 MB
git adr config adr.artifact_max_size 52428800   # 50 MB
```

### Quick Decisions

```bash
git adr config adr.template nygard
git adr config adr.ai.temperature 0.3
```

### Multi-Project Setup

```bash
# Global preferences
git config --global adr.editor "code --wait"
git config --global adr.ai.provider anthropic

# Per-project overrides
git adr config adr.template business  # In formal project
git adr config adr.template nygard    # In quick project
```
