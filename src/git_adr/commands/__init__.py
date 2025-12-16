"""CLI command implementations for git-adr.

Each command is implemented as a separate module and registered
with the main typer application.
"""

from __future__ import annotations

from git_adr.commands.ai_ask import run_ai_ask

# AI commands
from git_adr.commands.ai_draft import run_ai_draft
from git_adr.commands.ai_suggest import run_ai_suggest
from git_adr.commands.ai_summarize import run_ai_summarize
from git_adr.commands.artifact_get import run_artifact_get
from git_adr.commands.artifact_rm import run_artifact_rm
from git_adr.commands.artifacts import run_artifacts

# Artifact commands
from git_adr.commands.attach import run_attach

# CI/CD commands
from git_adr.commands.ci import run_ci_github, run_ci_gitlab, run_ci_list
from git_adr.commands.config import run_config

# Format commands
from git_adr.commands.convert import run_convert
from git_adr.commands.edit import run_edit
from git_adr.commands.export import run_export

# Hook commands (internal, called by git hook scripts)
from git_adr.commands.hook import run_hook

# Hook management commands (user-facing)
from git_adr.commands.hooks_cli import (
    run_hooks_config,
    run_hooks_install,
    run_hooks_status,
    run_hooks_uninstall,
)
from git_adr.commands.import_ import run_import

# Core commands
from git_adr.commands.init import run_init
from git_adr.commands.link import run_link
from git_adr.commands.list import run_list
from git_adr.commands.log import run_log
from git_adr.commands.metrics import run_metrics
from git_adr.commands.new import run_new

# Onboarding/Export/Import commands
from git_adr.commands.onboard import run_onboard
from git_adr.commands.report import run_report
from git_adr.commands.rm import run_rm
from git_adr.commands.search import run_search
from git_adr.commands.show import run_show

# Analytics commands
from git_adr.commands.stats import run_stats
from git_adr.commands.supersede import run_supersede
from git_adr.commands.sync import run_sync

# Templates (governance) commands
from git_adr.commands.templates_cli import (
    run_templates_all,
    run_templates_codeowners,
    run_templates_issue,
    run_templates_list,
    run_templates_pr,
)

# Wiki commands
from git_adr.commands.wiki_init import run_wiki_init
from git_adr.commands.wiki_sync import run_wiki_sync

__all__ = [
    # Core
    "run_init",
    "run_new",
    "run_list",
    "run_show",
    "run_edit",
    "run_search",
    "run_link",
    "run_supersede",
    "run_log",
    "run_sync",
    "run_config",
    "run_rm",
    # Format
    "run_convert",
    # Artifact
    "run_attach",
    "run_artifacts",
    "run_artifact_get",
    "run_artifact_rm",
    # Analytics
    "run_stats",
    "run_report",
    "run_metrics",
    # AI
    "run_ai_draft",
    "run_ai_suggest",
    "run_ai_summarize",
    "run_ai_ask",
    # Wiki
    "run_wiki_init",
    "run_wiki_sync",
    # Onboarding/Export/Import
    "run_onboard",
    "run_export",
    "run_import",
    # Hook (internal)
    "run_hook",
    # Hook management (user-facing)
    "run_hooks_install",
    "run_hooks_uninstall",
    "run_hooks_status",
    "run_hooks_config",
    # CI/CD
    "run_ci_github",
    "run_ci_gitlab",
    "run_ci_list",
    # Templates (governance)
    "run_templates_pr",
    "run_templates_issue",
    "run_templates_codeowners",
    "run_templates_all",
    "run_templates_list",
]
