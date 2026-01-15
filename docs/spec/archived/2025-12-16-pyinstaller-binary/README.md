---
project_id: SPEC-2025-12-16-001
project_name: "PyInstaller Binary Distribution"
slug: pyinstaller-binary
status: completed
created: 2025-12-16T10:00:00Z
approved: 2025-12-16T11:00:00Z
started: 2025-12-16T11:00:00Z
completed: 2025-12-16T17:30:00Z
expires: 2026-03-16T10:00:00Z
superseded_by: null
final_effort: "8 hours"
outcome: success
tags: [distribution, packaging, pyinstaller, homebrew]
stakeholders: []
worktree:
  branch: plan/git-adr-issue-cli
  base_branch: main
---

# PyInstaller Binary Distribution

Create a standalone executable for git-adr, similar to git-lfs, eliminating the need for Python runtime and dramatically reducing Homebrew installation time.

## Quick Links

- [Requirements](./REQUIREMENTS.md)
- [Architecture](./ARCHITECTURE.md)
- [Implementation Plan](./IMPLEMENTATION_PLAN.md)

## Status

**Current Phase**: Requirements Elicitation

## Problem Statement

The current Homebrew installation of git-adr requires:
- 64 Python package dependencies
- 9+ packages with native compilation (Rust, C)
- ~5+ minutes installation time vs ~5 seconds for git-lfs

## Proposed Solution

Create a PyInstaller-based standalone binary that:
- Ships as a single executable (like git-lfs)
- Requires no Python runtime on user's machine
- Enables instant Homebrew installation via bottles
