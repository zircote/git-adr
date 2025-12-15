# git-adr Configuration Reference

This document provides a comprehensive reference for all configuration options available in git-adr.

## Table of Contents

- [Overview](#overview)
- [Setting Configuration](#setting-configuration)
- [Core Settings](#core-settings)
- [Artifact Settings](#artifact-settings)
- [Sync Settings](#sync-settings)
- [AI Settings](#ai-settings)
- [Wiki Settings](#wiki-settings)
- [Common Recipes](#common-recipes)

---

## Overview

git-adr stores configuration in git config (local or global). All keys are prefixed with `adr.`.

```bash
# View all git-adr configuration
git adr config list

# Get a specific value
git adr config --get adr.template

# Set a value (local to repo)
git adr config adr.template madr

# Set a value (global)
git adr config --global adr.template madr
```

---

## Setting Configuration

Configuration can be set at two levels:

### Local Configuration (Repository-Specific)

Local configuration is stored in `.git/config` and applies only to the current repository. This is the default when setting values.

```bash
# Set local configuration
git adr config adr.template nygard

# Or explicitly specify local
git config --local adr.template nygard
```

### Global Configuration (User-Wide)

Global configuration is stored in `~/.gitconfig` and applies to all repositories for the current user. Use this for personal preferences that should apply everywhere.

```bash
# Set global configuration
git adr config --global adr.editor "code --wait"
git adr config --global adr.ai.provider anthropic
```

### Configuration Precedence

1. **Local** (repository `.git/config`) - highest priority
2. **Global** (user `~/.gitconfig`)
3. **Default values** (built into git-adr) - lowest priority

### Viewing Configuration

```bash
# List all adr.* settings
git adr config list

# Get a specific value
git adr config --get adr.template

# Check where a value comes from
git config --show-origin adr.template
```

### Unsetting Configuration

```bash
# Remove a local setting (falls back to global or default)
git config --unset adr.template

# Remove a global setting
git config --global --unset adr.ai.provider
```

---

## Core Settings

### adr.namespace

The git notes namespace used to store ADR content.

| Property | Value |
|----------|-------|
| **Type** | string |
| **Default** | `adr` |

**Description:**

ADRs are stored in git notes under `refs/notes/<namespace>`. Changing this value allows you to run multiple independent ADR systems in the same repository or avoid conflicts with other tools using git notes.

**Example Usage:**

```bash
# Use default namespace (refs/notes/adr)
git adr config adr.namespace adr

# Use a custom namespace for a specific project
git adr config adr.namespace project-decisions

# Use a team-specific namespace
git adr config adr.namespace team-alpha-adr
```

**Notes:**
- Changing the namespace after ADRs exist will make existing ADRs invisible to git-adr
- The namespace becomes part of the git notes ref: `refs/notes/<namespace>`
- Keep namespace names simple (alphanumeric with hyphens)

---

### adr.artifacts_namespace

The git notes namespace used to store ADR artifacts (attached files).

| Property | Value |
|----------|-------|
| **Type** | string |
| **Default** | `adr-artifacts` |

**Description:**

Artifacts (diagrams, documents, images) attached to ADRs are stored separately from the ADR content. This namespace controls where those artifacts are stored in git notes.

**Example Usage:**

```bash
# Use default artifacts namespace
git adr config adr.artifacts_namespace adr-artifacts

# Use a custom artifacts namespace
git adr config adr.artifacts_namespace project-artifacts
```

**Notes:**
- Should be different from `adr.namespace` to keep ADRs and artifacts separate
- Artifacts are compressed and stored as base64-encoded data in git notes
- Changing this after artifacts exist will make them inaccessible

---

### adr.template

The default ADR template format used when creating new ADRs.

| Property | Value |
|----------|-------|
| **Type** | string |
| **Default** | `madr` |
| **Valid Values** | `madr`, `nygard`, `y-statement`, `alexandrian`, `business`, `planguage` |

**Description:**

Controls which template structure is used when creating new ADRs. Each template provides a different level of detail and structure suited to different use cases.

**Available Templates:**

| Template | Description | Best For |
|----------|-------------|----------|
| `madr` | MADR 4.0 - Full template with options analysis | Complex decisions requiring detailed analysis |
| `nygard` | Original minimal format (Context/Decision/Consequences) | Quick, lightweight decisions |
| `y-statement` | Single-sentence decision format | Concise documentation |
| `alexandrian` | Pattern-language inspired with Forces/Solution | Pattern-based decision making |
| `business` | Extended business justification with ROI/approval | Decisions requiring stakeholder sign-off |
| `planguage` | Quality-focused measurable format with scales | Decisions with quantifiable success criteria |

**Example Usage:**

```bash
# Use the detailed MADR format (default)
git adr config adr.template madr

# Use the minimal Nygard format for quick decisions
git adr config adr.template nygard

# Use business case format for executive decisions
git adr config adr.template business

# Override template for a single ADR
git adr new "Use Redis for caching" --template nygard
```

---

### adr.editor

The editor command used when editing ADRs.

| Property | Value |
|----------|-------|
| **Type** | string |
| **Default** | System editor (`$EDITOR`, `$VISUAL`, or fallback chain) |

**Description:**

Specifies which editor to launch when creating or editing ADRs. If not set, git-adr follows the standard Unix editor resolution:

1. `$EDITOR` environment variable
2. `$VISUAL` environment variable
3. `git config core.editor`
4. Fallback chain: `vim`, `vi`, `nano`, `notepad` (Windows)

**Example Usage:**

```bash
# Use VS Code (wait for editor to close)
git adr config --global adr.editor "code --wait"

# Use Sublime Text
git adr config --global adr.editor "subl -w"

# Use vim
git adr config --global adr.editor vim

# Use nano
git adr config --global adr.editor nano

# Use IntelliJ IDEA
git adr config --global adr.editor "idea --wait"

# Use Emacs
git adr config --global adr.editor "emacsclient -t"
```

**Notes:**
- For GUI editors, use the `--wait` or `-w` flag so git-adr waits for the editor to close
- This setting is typically set globally for user preference
- The command should block until editing is complete

---

## Artifact Settings

### adr.artifact_warn_size

Size threshold (in bytes) at which git-adr warns before attaching a file.

| Property | Value |
|----------|-------|
| **Type** | integer |
| **Default** | `1048576` (1 MB) |

**Description:**

When attaching files to an ADR, git-adr will display a warning if the file exceeds this size. This helps prevent accidentally bloating the git notes with large files.

**Example Usage:**

```bash
# Set warning threshold to 500 KB
git adr config adr.artifact_warn_size 512000

# Set warning threshold to 2 MB
git adr config adr.artifact_warn_size 2097152

# Disable warning (set very high)
git adr config adr.artifact_warn_size 999999999
```

**Notes:**
- Value is in bytes
- The warning can be bypassed with `--force` flag on attachment commands
- Consider that git notes are pushed/pulled with regular git operations

---

### adr.artifact_max_size

Maximum allowed file size (in bytes) for artifacts.

| Property | Value |
|----------|-------|
| **Type** | integer |
| **Default** | `10485760` (10 MB) |

**Description:**

Files larger than this limit cannot be attached to ADRs. This is a hard limit to prevent repository bloat. The attachment will be rejected with an error.

**Example Usage:**

```bash
# Set maximum to 5 MB
git adr config adr.artifact_max_size 5242880

# Set maximum to 20 MB (for repositories with large diagrams)
git adr config adr.artifact_max_size 20971520

# Set maximum to 50 MB
git adr config adr.artifact_max_size 52428800
```

**Notes:**
- Value is in bytes
- This is a hard limit that cannot be bypassed
- Consider repository cloning time when setting high limits
- Common size references:
  - 1 MB = 1048576 bytes
  - 5 MB = 5242880 bytes
  - 10 MB = 10485760 bytes
  - 50 MB = 52428800 bytes

---

## Sync Settings

### adr.sync.auto_push

Automatically push notes to remote after creating or editing ADRs.

| Property | Value |
|----------|-------|
| **Type** | boolean |
| **Default** | `false` |

**Description:**

When enabled, git-adr automatically pushes ADR notes to the remote repository after any operation that modifies ADRs (new, edit, status change, supersede, etc.). This keeps the remote synchronized with local changes.

**Example Usage:**

```bash
# Enable automatic pushing
git adr config adr.sync.auto_push true

# Disable automatic pushing (default)
git adr config adr.sync.auto_push false
```

**Notes:**
- Requires remote repository to be configured
- May slow down ADR operations due to network calls
- Useful for teams that want immediate visibility of decisions
- Consider using `git adr sync --push` manually for more control

---

### adr.sync.auto_pull

Automatically pull notes from remote before listing or showing ADRs.

| Property | Value |
|----------|-------|
| **Type** | boolean |
| **Default** | `true` |

**Description:**

When enabled, git-adr automatically fetches and merges ADR notes from the remote repository before operations that read ADRs (list, show, search). This ensures you always see the latest decisions from the team.

**Example Usage:**

```bash
# Enable automatic pulling (default)
git adr config adr.sync.auto_pull true

# Disable automatic pulling (work offline)
git adr config adr.sync.auto_pull false
```

**Notes:**
- Enabled by default to ensure teams see latest decisions
- May slow down ADR operations due to network calls
- Disable when working offline or on slow networks
- Conflicts are resolved using `adr.sync.merge_strategy`

---

### adr.sync.merge_strategy

Strategy for resolving conflicts when merging notes from remote.

| Property | Value |
|----------|-------|
| **Type** | string |
| **Default** | `union` |
| **Valid Values** | `union`, `ours`, `theirs`, `cat_sort_uniq` |

**Description:**

Determines how conflicts are resolved when pulling notes that have been modified both locally and remotely. This maps to git's notes merge strategies.

**Available Strategies:**

| Strategy | Description | Best For |
|----------|-------------|----------|
| `union` | Combines both versions, keeping all lines from both | Default, collaborative environments |
| `ours` | Keeps local version, discards remote changes | Local changes take precedence |
| `theirs` | Keeps remote version, discards local changes | Remote changes take precedence |
| `cat_sort_uniq` | Concatenates, sorts, and removes duplicates | Deterministic merging |

**Example Usage:**

```bash
# Use union strategy (default)
git adr config adr.sync.merge_strategy union

# Prefer local changes
git adr config adr.sync.merge_strategy ours

# Prefer remote changes
git adr config adr.sync.merge_strategy theirs

# Override strategy for a single sync
git adr sync --pull --merge-strategy theirs
```

**Notes:**
- `union` is recommended for most teams as it preserves all changes
- `ours` is useful when local edits should not be overwritten
- `theirs` is useful when remote is the source of truth
- `cat_sort_uniq` produces deterministic results but may reorder content

---

## AI Settings

### adr.ai.provider

The AI service provider for AI-assisted features.

| Property | Value |
|----------|-------|
| **Type** | string |
| **Default** | (none) |
| **Valid Values** | `openai`, `anthropic`, `google`, `bedrock`, `azure`, `ollama`, `openrouter` |

**Description:**

Configures which AI provider to use for AI-assisted features such as ADR generation, summarization, and content suggestions. Each provider requires appropriate API credentials.

**Available Providers:**

| Provider | Description | API Key Variable |
|----------|-------------|------------------|
| `openai` | OpenAI (GPT-4, GPT-3.5) | `OPENAI_API_KEY` |
| `anthropic` | Anthropic (Claude) | `ANTHROPIC_API_KEY` |
| `google` | Google AI (Gemini) | `GOOGLE_API_KEY` |
| `bedrock` | AWS Bedrock | AWS credentials |
| `azure` | Azure OpenAI | `AZURE_OPENAI_API_KEY` |
| `ollama` | Local Ollama server | (none, local) |
| `openrouter` | OpenRouter (multiple models) | `OPENROUTER_API_KEY` |

**Example Usage:**

```bash
# Use OpenAI
git adr config adr.ai.provider openai
export OPENAI_API_KEY="sk-..."

# Use Anthropic Claude
git adr config adr.ai.provider anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Use local Ollama
git adr config adr.ai.provider ollama

# Use Google Gemini
git adr config adr.ai.provider google
export GOOGLE_API_KEY="..."
```

**Notes:**
- Provider must be set before using AI features
- API keys should be set as environment variables (not in git config)
- Ollama runs locally and does not require API keys
- OpenRouter provides access to multiple model providers through one API

---

### adr.ai.model

The specific AI model to use with the configured provider.

| Property | Value |
|----------|-------|
| **Type** | string |
| **Default** | (provider-specific default) |

**Description:**

Specifies which model to use with the configured AI provider. Available models depend on the provider and your API access level.

**Common Models by Provider:**

| Provider | Example Models |
|----------|---------------|
| `openai` | `gpt-4`, `gpt-4-turbo`, `gpt-3.5-turbo` |
| `anthropic` | `claude-3-opus-20240229`, `claude-3-sonnet-20240229`, `claude-3-haiku-20240307` |
| `google` | `gemini-pro`, `gemini-1.5-pro` |
| `ollama` | `llama2`, `mistral`, `codellama` |
| `azure` | Deployment name configured in Azure |

**Example Usage:**

```bash
# Use GPT-4 with OpenAI
git adr config adr.ai.provider openai
git adr config adr.ai.model gpt-4-turbo

# Use Claude 3 Opus
git adr config adr.ai.provider anthropic
git adr config adr.ai.model claude-3-opus-20240229

# Use local Mistral with Ollama
git adr config adr.ai.provider ollama
git adr config adr.ai.model mistral
```

**Notes:**
- Model availability depends on your API access and subscription
- Newer models may provide better results but cost more
- Local models (Ollama) have no API costs but require local resources

---

### adr.ai.temperature

Controls the randomness/creativity of AI-generated content.

| Property | Value |
|----------|-------|
| **Type** | float |
| **Default** | `0.7` |
| **Range** | `0.0` to `1.0` |

**Description:**

Temperature controls the randomness of AI responses. Lower values produce more focused, deterministic outputs, while higher values produce more creative, varied outputs.

| Temperature | Behavior |
|-------------|----------|
| `0.0` | Very focused, deterministic, may be repetitive |
| `0.3` | Conservative, consistent outputs |
| `0.7` | Balanced (default), good for general use |
| `1.0` | Creative, varied, may be less accurate |

**Example Usage:**

```bash
# More focused, consistent output
git adr config adr.ai.temperature 0.3

# Balanced output (default)
git adr config adr.ai.temperature 0.7

# More creative output
git adr config adr.ai.temperature 0.9
```

**Notes:**
- Lower temperatures are better for factual, technical content
- Higher temperatures are better for brainstorming alternatives
- Default of 0.7 works well for most ADR generation tasks
- Some providers may interpret temperature slightly differently

---

## Wiki Settings

### adr.wiki.platform

The wiki platform for exporting ADRs.

| Property | Value |
|----------|-------|
| **Type** | string |
| **Default** | (auto-detect) |
| **Valid Values** | `github`, `gitlab`, `auto` |

**Description:**

Specifies the wiki platform when exporting ADRs to a project wiki. git-adr can format content appropriately for each platform's wiki syntax and conventions.

**Platforms:**

| Platform | Description |
|----------|-------------|
| `github` | GitHub Wiki (Markdown) |
| `gitlab` | GitLab Wiki (Markdown with extensions) |
| `auto` | Auto-detect from remote URL |

**Example Usage:**

```bash
# Auto-detect from remote (default)
git adr config adr.wiki.platform auto

# Explicitly set GitHub
git adr config adr.wiki.platform github

# Explicitly set GitLab
git adr config adr.wiki.platform gitlab
```

**Notes:**
- Auto-detection examines the remote URL to determine the platform
- Explicit setting overrides auto-detection
- Wiki export formats Markdown appropriately for each platform

---

### adr.wiki.auto_sync

Automatically sync ADRs to wiki after modifications.

| Property | Value |
|----------|-------|
| **Type** | boolean |
| **Default** | `false` |

**Description:**

When enabled, git-adr automatically exports ADRs to the project wiki after any operation that modifies ADRs. This keeps the wiki in sync with the ADR notes.

**Example Usage:**

```bash
# Enable automatic wiki sync
git adr config adr.wiki.auto_sync true

# Disable automatic wiki sync (default)
git adr config adr.wiki.auto_sync false
```

**Notes:**
- Requires wiki to be configured for the repository
- May require additional authentication for wiki access
- Consider using manual wiki export for more control
- Wiki sync is additive and does not delete wiki pages

---

## Common Recipes

### Minimal Setup

Basic configuration to get started with git-adr:

```bash
# Initialize git-adr in your repository
git adr init

# That's it! Defaults work well for most cases:
# - Template: madr
# - Namespace: adr
# - Auto-pull: enabled
# - Auto-push: disabled
```

### AI-Powered Workflow

Configure git-adr to use AI for generating and improving ADRs:

```bash
# Configure OpenAI
git adr config adr.ai.provider openai
git adr config adr.ai.model gpt-4-turbo
git adr config adr.ai.temperature 0.7
export OPENAI_API_KEY="sk-..."

# Or configure Anthropic Claude
git adr config adr.ai.provider anthropic
git adr config adr.ai.model claude-3-opus-20240229
export ANTHROPIC_API_KEY="sk-ant-..."

# Or use local Ollama (no API key needed)
git adr config adr.ai.provider ollama
git adr config adr.ai.model mistral
# Ensure Ollama is running: ollama serve
```

### Wiki Sync Setup

Configure automatic wiki synchronization:

```bash
# Set wiki platform (or leave as auto)
git adr config adr.wiki.platform github

# Enable automatic sync after ADR changes
git adr config adr.wiki.auto_sync true

# Manual sync command
git adr wiki sync
```

### Team Configuration

Recommended settings for team collaboration:

```bash
# Enable automatic sync with remote
git adr config adr.sync.auto_pull true
git adr config adr.sync.auto_push true
git adr config adr.sync.merge_strategy union

# Use business case template for formal decisions
git adr config adr.template business

# Set up remote tracking for notes
git config --add remote.origin.fetch '+refs/notes/*:refs/notes/*'
```

### Offline Development

Configure git-adr for offline or low-connectivity environments:

```bash
# Disable automatic network operations
git adr config adr.sync.auto_pull false
git adr config adr.sync.auto_push false

# Use local Ollama for AI features
git adr config adr.ai.provider ollama
git adr config adr.ai.model llama2

# Manual sync when connectivity is available
git adr sync --push --pull
```

### High-Security Environment

Settings for repositories with strict controls:

```bash
# Use local namespace to avoid conflicts
git adr config adr.namespace secure-decisions

# Disable automatic sync (manual control)
git adr config adr.sync.auto_pull false
git adr config adr.sync.auto_push false

# Prefer local changes in conflicts
git adr config adr.sync.merge_strategy ours

# Disable AI features (no external API calls)
git config --unset adr.ai.provider
git config --unset adr.ai.model
```

### Large File Support

Configure for projects with large diagrams or documents:

```bash
# Increase artifact size limits
git adr config adr.artifact_warn_size 5242880   # 5 MB warning
git adr config adr.artifact_max_size 52428800   # 50 MB maximum

# Attach large architecture diagram
git adr attach ADR-123 architecture-diagram.png
```

### Quick Decisions

Configuration for rapid, lightweight decision tracking:

```bash
# Use minimal Nygard template
git adr config adr.template nygard

# Lower AI temperature for focused output
git adr config adr.ai.temperature 0.3

# Create quick ADR
git adr new "Use PostgreSQL for main database"
```

### Custom Editor Setup

Configure your preferred editor:

```bash
# VS Code (recommended for markdown)
git adr config --global adr.editor "code --wait"

# Sublime Text
git adr config --global adr.editor "subl -w"

# Vim with custom settings
git adr config --global adr.editor "vim -c 'set spell spelllang=en_us'"

# Emacs
git adr config --global adr.editor "emacsclient -t -a ''"
```

### Multi-Project Setup

Configure different settings per project while sharing global preferences:

```bash
# Global settings (in ~/.gitconfig)
git config --global adr.editor "code --wait"
git config --global adr.ai.provider anthropic
git config --global adr.ai.model claude-3-sonnet-20240229

# Project A: Formal decisions
cd /path/to/project-a
git adr config adr.template business
git adr config adr.sync.auto_push true

# Project B: Quick technical decisions
cd /path/to/project-b
git adr config adr.template nygard
git adr config adr.sync.auto_push false
```

---

## Quick Reference

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `adr.namespace` | string | `adr` | Notes namespace for ADRs |
| `adr.artifacts_namespace` | string | `adr-artifacts` | Notes namespace for artifacts |
| `adr.template` | string | `madr` | Default ADR template format |
| `adr.editor` | string | (system) | Editor for ADR editing |
| `adr.artifact_warn_size` | int | `1048576` | Warning threshold (bytes) |
| `adr.artifact_max_size` | int | `10485760` | Maximum artifact size (bytes) |
| `adr.sync.auto_push` | bool | `false` | Auto-push after changes |
| `adr.sync.auto_pull` | bool | `true` | Auto-pull before reads |
| `adr.sync.merge_strategy` | string | `union` | Conflict resolution strategy |
| `adr.ai.provider` | string | (none) | AI service provider |
| `adr.ai.model` | string | (none) | AI model name |
| `adr.ai.temperature` | float | `0.7` | AI randomness (0.0-1.0) |
| `adr.wiki.platform` | string | `auto` | Wiki platform |
| `adr.wiki.auto_sync` | bool | `false` | Auto-sync to wiki |
