# SDLC Integration Guide

This guide covers integrating git-adr into your Software Development Lifecycle (SDLC) using CI/CD pipelines, governance templates, and automated workflows.

## Table of Contents

- [Overview](#overview)
- [Git Hooks](#git-hooks)
- [GitHub Actions](#github-actions)
- [GitLab CI/CD](#gitlab-cicd)
- [Governance Patterns](#governance-patterns)
- [Best Practices](#best-practices)

## Overview

git-adr provides multiple integration points for your SDLC:

| Integration | Purpose | Setup Effort |
|-------------|---------|--------------|
| Git Hooks | Automatic sync on push | `git adr hooks install` |
| CI/CD Workflows | Validate & sync ADRs | `git adr ci github/gitlab` |
| PR Templates | Document architecture impact | `git adr templates pr` |
| Issue Templates | ADR proposal workflow | `git adr templates issue` |
| CODEOWNERS | Require architecture review | `git adr templates codeowners` |

## Git Hooks

### Installation

Install git hooks for automatic ADR notes synchronization:

```bash
# Install hooks
git adr hooks install

# Check installation status
git adr hooks status

# Force reinstall (backs up existing hooks)
git adr hooks install --force
```

### How It Works

The pre-push hook automatically syncs ADR notes to the remote when you push branches:

1. **Pre-push triggered** - Git invokes the hook before pushing
2. **Branch check** - Only syncs when pushing branches (not tags)
3. **Notes sync** - Runs `git adr sync --push` to sync notes
4. **Chain execution** - Calls any backed-up existing hook

### Configuration

```bash
# Block push if notes sync fails
git adr hooks config --block-on-failure

# Allow push even if sync fails (default)
git adr hooks config --no-block-on-failure

# View current configuration
git adr hooks config --show
```

### Skip Hooks

```bash
# Skip once via environment variable
GIT_ADR_SKIP=1 git push

# Permanently disable via git config
git config adr.hooks.skip true
```

### Manual Integration

If you have existing hooks, get integration instructions:

```bash
git adr hooks install --manual
```

This outputs shell snippets to add to your existing hook scripts.

## GitHub Actions

### Generate Workflows

Generate GitHub Actions workflows for your repository:

```bash
# Generate all workflows (sync + validate)
git adr ci github

# Generate only sync workflow
git adr ci github --sync

# Generate only PR validation
git adr ci github --validate

# Customize options
git adr ci github --main-branch main --wiki-sync --export-format markdown
```

### Sync Workflow

The sync workflow (`adr-sync.yml`) runs on merges to main and:

- Synchronizes ADR notes with the remote
- Optionally syncs to wiki
- Optionally exports ADRs to files

**Generated workflow:**

```yaml
name: ADR Sync

on:
  push:
    branches:
      - main
  workflow_dispatch:

permissions:
  contents: write

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup git-adr
        run: |
          pip install git-adr
          git fetch origin 'refs/notes/*:refs/notes/*' || true

      - name: Sync ADR notes
        run: git adr sync --push
        env:
          GIT_AUTHOR_NAME: github-actions[bot]
          GIT_AUTHOR_EMAIL: github-actions[bot]@users.noreply.github.com
```

### Validation Workflow

The validation workflow (`adr-validate.yml`) runs on pull requests and:

- Lists all ADRs and validates structure
- Checks for proposed ADRs that may need review
- Reports ADR statistics

**Generated workflow:**

```yaml
name: ADR Validation

on:
  pull_request:
    branches:
      - main

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup git-adr
        run: |
          pip install git-adr
          git fetch origin 'refs/notes/*:refs/notes/*' || true

      - name: Validate ADRs
        run: |
          echo "## ADR Status" >> $GITHUB_STEP_SUMMARY
          git adr list --format markdown >> $GITHUB_STEP_SUMMARY
          git adr stats >> $GITHUB_STEP_SUMMARY
```

### Available Options

| Option | Description | Default |
|--------|-------------|---------|
| `--sync` | Generate sync workflow | Both if neither specified |
| `--validate` | Generate validation workflow | Both if neither specified |
| `--output PATH` | Output directory | `.github/workflows` |
| `--main-branch NAME` | Main branch for triggers | `main` |
| `--wiki-sync` | Enable wiki synchronization | Disabled |
| `--export-format FORMAT` | Export format (markdown/json/html) | None |

## GitLab CI/CD

### Generate Pipeline

Generate GitLab CI configuration:

```bash
# Generate full pipeline
git adr ci gitlab

# Generate as include file
git adr ci gitlab --output gitlab-ci-adr.yml
```

### Pipeline Configuration

The generated pipeline includes stages for sync and validation:

```yaml
stages:
  - validate
  - sync

variables:
  GIT_STRATEGY: clone
  GIT_DEPTH: 0

.adr-setup:
  before_script:
    - pip install git-adr
    - git fetch origin 'refs/notes/*:refs/notes/*' || true

adr-validate:
  extends: .adr-setup
  stage: validate
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  script:
    - git adr list
    - git adr stats

adr-sync:
  extends: .adr-setup
  stage: sync
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
  script:
    - git adr sync --push
```

### Include in Existing Pipeline

If you already have a `.gitlab-ci.yml`, generate a separate file and include it:

```bash
git adr ci gitlab --output gitlab-ci-adr.yml
```

Then in your main `.gitlab-ci.yml`:

```yaml
include:
  - local: 'gitlab-ci-adr.yml'
```

## Governance Patterns

### PR Template

Generate a pull request template that prompts for architecture impact:

```bash
# Generate PR template
git adr templates pr

# With architecture requirement
git adr templates pr --require-adr

# With default reviewers
git adr templates pr --reviewer @architecture-team
```

**Generated template includes:**

- Architecture impact checklist
- ADR reference section
- Review requirements for architectural changes

Example output (`.github/PULL_REQUEST_TEMPLATE.md`):

```markdown
## Description
<!-- Brief description of the changes -->

## Architecture Impact

### Does this PR include architectural changes?
- [ ] Yes - ADR required
- [ ] No - Minor change only

### Related ADRs
<!-- Link any related ADRs using: git adr show ADR-XXXX -->
- ADR-XXXX: Title (if applicable)

### Checklist
- [ ] I have considered the architectural impact of these changes
- [ ] I have created/updated an ADR if this introduces new patterns
- [ ] I have consulted with @architecture-team for significant changes
```

### Issue Template

Generate an issue template for ADR proposals:

```bash
# Generate issue template
git adr templates issue

# With custom labels
git adr templates issue --labels "architecture,needs-discussion"
```

**Generated template** (`.github/ISSUE_TEMPLATE/adr-proposal.md`):

```markdown
---
name: ADR Proposal
about: Propose a new Architecture Decision Record
title: "[ADR] "
labels: architecture, adr-proposal
---

## Context
<!-- What is the issue that we're seeing that is motivating this decision? -->

## Decision Drivers
<!-- What factors are important in making this decision? -->

## Considered Options
<!-- What options have you considered? -->

1. Option 1
2. Option 2
3. Option 3

## Proposed Decision
<!-- What is your recommendation? -->

## Expected Consequences
<!-- What are the positive and negative consequences of this decision? -->

### Positive
-

### Negative
-

## Additional Context
<!-- Any additional information that might help reviewers -->
```

### CODEOWNERS

Generate CODEOWNERS patterns to require architecture team review:

```bash
# Generate CODEOWNERS patterns
git adr templates codeowners

# With custom team
git adr templates codeowners --team @my-arch-team

# Write to file
git adr templates codeowners --team @arch --output CODEOWNERS
```

**Generated patterns:**

```
# Architecture Decision Records
# Require architecture team review for structural changes

# ADR documentation exports
docs/adr/**                    @architecture-team

# Architecture-sensitive paths
src/core/**                    @architecture-team
src/api/**                     @architecture-team
*.proto                        @architecture-team
docker-compose*.yml            @architecture-team
Dockerfile*                    @architecture-team

# Configuration that affects architecture
.github/workflows/**           @architecture-team
```

### Generate All Templates

Create all governance templates at once:

```bash
# Generate all templates
git adr templates all

# With custom team
git adr templates all --team @my-arch-team

# To custom directory
git adr templates all --output-dir .github
```

## Best Practices

### 1. Enable Hooks for Individual Developers

Encourage all team members to install git hooks:

```bash
# In your onboarding documentation
git adr hooks install
```

This ensures notes are synced even during local development.

### 2. Use CI/CD as Backup

Even with hooks installed, CI/CD workflows provide a safety net:

- Ensures notes sync even if hooks are skipped
- Validates ADR structure on every PR
- Provides visibility in PR reviews

### 3. Require ADRs for Architectural Changes

Use the `--require-adr` flag when generating PR templates:

```bash
git adr templates pr --require-adr
```

This adds explicit checkboxes requiring ADR documentation.

### 4. Set Up CODEOWNERS for Architecture-Sensitive Paths

Identify paths that should trigger architecture review:

```bash
# Generate base patterns
git adr templates codeowners --team @architecture-team

# Then customize for your project
vim CODEOWNERS
```

### 5. Use ADR Proposal Issues

Encourage discussions before implementation:

```bash
git adr templates issue
```

This creates a structured way to propose and discuss decisions before coding.

### 6. Export ADRs to Wiki

Keep ADRs accessible to non-technical stakeholders:

```bash
# Enable wiki sync in CI
git adr ci github --wiki-sync

# Or manually sync
git adr wiki sync
```

### 7. Monitor ADR Health

Use CI to track ADR metrics over time:

```yaml
# Add to your CI pipeline
- name: ADR Metrics
  run: |
    git adr stats --velocity
    git adr metrics --format json > adr-metrics.json
```

## Troubleshooting

### Notes Not Syncing

1. Check hook installation: `git adr hooks status`
2. Verify remote configuration: `git config --get-regexp adr`
3. Try manual sync: `git adr sync --push`

### CI Workflow Failing

1. Ensure git-adr is installed in CI environment
2. Fetch notes before operations: `git fetch origin 'refs/notes/*:refs/notes/*'`
3. Check permissions for pushing notes

### CODEOWNERS Not Triggering

1. Ensure CODEOWNERS is in the right location (root or `.github/`)
2. Verify team names match your GitHub/GitLab organization
3. Check that branch protection rules are enabled

## See Also

- [CONFIGURATION.md](CONFIGURATION.md) - Full configuration reference
- [COMMANDS.md](COMMANDS.md) - Command reference
- [ADR_PRIMER.md](ADR_PRIMER.md) - Introduction to ADRs
