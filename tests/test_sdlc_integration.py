"""Comprehensive tests for SDLC integration features.

Tests cover:
- templates/__init__.py: Jinja2 template rendering utilities
- commands/ci.py: CI/CD workflow generation
- commands/templates_cli.py: Governance template generation
- commands/hooks_cli.py: Hook management commands
- hooks.py: Core hook installation logic
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator


# =============================================================================
# Templates Module Tests
# =============================================================================


class TestTemplatesInit:
    """Tests for src/git_adr/templates/__init__.py."""

    def test_get_template_environment(self) -> None:
        """Test that template environment is properly configured."""
        from git_adr.templates import get_template_environment

        env = get_template_environment()

        # Check Jinja2 environment settings
        assert env.trim_blocks is True
        assert env.lstrip_blocks is True
        assert env.keep_trailing_newline is True

    def test_render_template_github_actions_sync(self) -> None:
        """Test rendering GitHub Actions sync template."""
        from git_adr.templates import render_template

        content = render_template(
            "ci/github-actions-sync.yml.j2",
            main_branch="main",
            wiki_sync=False,
            python_version="3.11",
        )

        assert "name: Sync ADRs" in content
        assert "main" in content
        assert "python-version: '3.11'" in content

    def test_render_template_github_actions_sync_with_wiki(self) -> None:
        """Test rendering GitHub Actions sync template with wiki sync enabled."""
        from git_adr.templates import render_template

        content = render_template(
            "ci/github-actions-sync.yml.j2",
            main_branch="develop",
            wiki_sync=True,
            wiki_provider="github",
            python_version="3.12",
        )

        assert "develop" in content
        assert "pages: write" in content
        assert "wiki sync" in content.lower() or "Sync to wiki" in content

    def test_render_template_github_actions_validate(self) -> None:
        """Test rendering GitHub Actions validate template."""
        from git_adr.templates import render_template

        content = render_template(
            "ci/github-actions-validate.yml.j2",
            main_branch="main",
            python_version="3.11",
        )

        assert "name: Validate ADRs" in content
        assert "pull_request" in content
        assert "Validate ADR format" in content

    def test_render_template_gitlab_ci(self) -> None:
        """Test rendering GitLab CI template."""
        from git_adr.templates import render_template

        content = render_template(
            "ci/gitlab-ci-sync.yml.j2",
            main_branch="main",
            validate_adrs=True,
            wiki_sync=False,
            python_version="3.11",
        )

        assert "stages:" in content or "stage:" in content
        assert "git-adr" in content

    def test_render_template_pr_template(self) -> None:
        """Test rendering PR template."""
        from git_adr.templates import render_template

        content = render_template(
            "governance/pr-template.md.j2",
            require_adr=True,
            reviewers=["@team-lead", "@architect"],
        )

        assert "Architecture Impact" in content
        assert "@team-lead" in content
        assert "@architect" in content
        assert "ADR required" in content or "Required" in content

    def test_render_template_pr_template_no_require(self) -> None:
        """Test rendering PR template without ADR requirement."""
        from git_adr.templates import render_template

        content = render_template(
            "governance/pr-template.md.j2",
            require_adr=False,
            reviewers=[],
        )

        assert "Architecture Impact" in content
        # Should not have required text or reviewer section
        assert "Reviewers" not in content or "/cc" not in content

    def test_render_template_issue_template(self) -> None:
        """Test rendering issue template."""
        from git_adr.templates import render_template

        content = render_template(
            "governance/issue-template-adr.md.j2",
            labels="architecture, proposal",
            stakeholders=["@cto", "@staff-eng"],
        )

        assert "Architecture Decision Proposal" in content
        assert "architecture, proposal" in content
        assert "@cto" in content
        assert "@staff-eng" in content

    def test_render_template_codeowners(self) -> None:
        """Test rendering CODEOWNERS template."""
        from git_adr.templates import render_template

        content = render_template(
            "governance/codeowners.j2",
            team="@arch-team",
            adr_directory="docs/adr",
            protected_paths=["src/core/", "lib/"],
            api_paths=["api/"],
            schema_paths=["db/migrations/"],
            infra_paths=["terraform/"],
        )

        assert "@arch-team" in content
        assert "docs/adr" in content
        assert "src/core/" in content
        assert "lib/" in content
        assert "api/" in content
        assert "db/migrations/" in content
        assert "terraform/" in content

    def test_render_template_codeowners_minimal(self) -> None:
        """Test rendering CODEOWNERS with minimal config."""
        from git_adr.templates import render_template

        content = render_template(
            "governance/codeowners.j2",
            team="@reviewers",
        )

        assert "@reviewers" in content
        assert ".git-adr.yaml" in content

    def test_list_templates_all(self) -> None:
        """Test listing all templates."""
        from git_adr.templates import list_templates

        templates = list_templates()

        assert len(templates) >= 5
        assert any("ci/" in t for t in templates)
        assert any("governance/" in t for t in templates)

    def test_list_templates_ci_category(self) -> None:
        """Test listing CI templates only."""
        from git_adr.templates import list_templates

        templates = list_templates("ci")

        assert len(templates) >= 2
        assert all("ci/" in t for t in templates)
        assert any("github" in t for t in templates)
        assert any("gitlab" in t for t in templates)

    def test_list_templates_governance_category(self) -> None:
        """Test listing governance templates only."""
        from git_adr.templates import list_templates

        templates = list_templates("governance")

        assert len(templates) >= 3
        assert all("governance/" in t for t in templates)

    def test_list_templates_invalid_category(self) -> None:
        """Test listing templates with non-existent category."""
        from git_adr.templates import list_templates

        templates = list_templates("nonexistent")

        assert templates == []

    def test_render_template_not_found(self) -> None:
        """Test that rendering non-existent template raises error."""
        from jinja2 import TemplateNotFound

        from git_adr.templates import render_template

        with pytest.raises(TemplateNotFound):
            render_template("nonexistent/template.j2")

    def test_templates_dir_path(self) -> None:
        """Test that TEMPLATES_DIR is correctly set."""
        from git_adr.templates import TEMPLATES_DIR

        assert TEMPLATES_DIR.exists()
        assert (TEMPLATES_DIR / "ci").exists()
        assert (TEMPLATES_DIR / "governance").exists()


# =============================================================================
# CI Commands Tests
# =============================================================================


class TestCICommands:
    """Tests for src/git_adr/commands/ci.py."""

    def test_run_ci_github_default(self, tmp_path: Path) -> None:
        """Test generating both GitHub workflows by default."""
        from git_adr.commands.ci import run_ci_github

        os.chdir(tmp_path)

        run_ci_github(output=str(tmp_path / ".github/workflows"))

        sync_file = tmp_path / ".github/workflows/adr-sync.yml"
        validate_file = tmp_path / ".github/workflows/adr-validate.yml"

        assert sync_file.exists()
        assert validate_file.exists()

    def test_run_ci_github_sync_only(self, tmp_path: Path) -> None:
        """Test generating only sync workflow."""
        from git_adr.commands.ci import run_ci_github

        os.chdir(tmp_path)

        run_ci_github(sync=True, validate=False, output=str(tmp_path / "workflows"))

        sync_file = tmp_path / "workflows/adr-sync.yml"
        validate_file = tmp_path / "workflows/adr-validate.yml"

        assert sync_file.exists()
        assert not validate_file.exists()

    def test_run_ci_github_validate_only(self, tmp_path: Path) -> None:
        """Test generating only validate workflow."""
        from git_adr.commands.ci import run_ci_github

        os.chdir(tmp_path)

        run_ci_github(sync=False, validate=True, output=str(tmp_path / "workflows"))

        sync_file = tmp_path / "workflows/adr-sync.yml"
        validate_file = tmp_path / "workflows/adr-validate.yml"

        assert not sync_file.exists()
        assert validate_file.exists()

    def test_run_ci_github_with_wiki_sync(self, tmp_path: Path) -> None:
        """Test generating workflow with wiki sync enabled."""
        from git_adr.commands.ci import run_ci_github

        os.chdir(tmp_path)

        run_ci_github(
            sync=True,
            validate=False,
            output=str(tmp_path / "workflows"),
            wiki_sync=True,
            wiki_provider="github",
        )

        sync_file = tmp_path / "workflows/adr-sync.yml"
        content = sync_file.read_text()

        assert "pages: write" in content

    def test_run_ci_github_custom_branch(self, tmp_path: Path) -> None:
        """Test generating workflow with custom main branch."""
        from git_adr.commands.ci import run_ci_github

        os.chdir(tmp_path)

        run_ci_github(
            sync=True,
            validate=False,
            output=str(tmp_path / "workflows"),
            main_branch="develop",
        )

        sync_file = tmp_path / "workflows/adr-sync.yml"
        content = sync_file.read_text()

        assert "develop" in content

    def test_run_ci_github_overwrite_warning(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test warning when overwriting existing workflow."""
        from git_adr.commands.ci import run_ci_github

        os.chdir(tmp_path)

        # Create existing file
        workflow_dir = tmp_path / ".github/workflows"
        workflow_dir.mkdir(parents=True)
        (workflow_dir / "adr-sync.yml").write_text("existing content")

        run_ci_github(sync=True, validate=False, output=str(workflow_dir))

        captured = capsys.readouterr()
        assert "already exists" in captured.out or "overwriting" in captured.out.lower()

    def test_run_ci_gitlab_default(self, tmp_path: Path) -> None:
        """Test generating GitLab CI pipeline."""
        from git_adr.commands.ci import run_ci_gitlab

        os.chdir(tmp_path)

        run_ci_gitlab(output=str(tmp_path / ".gitlab-ci.yml"))

        gitlab_file = tmp_path / ".gitlab-ci.yml"
        assert gitlab_file.exists()
        content = gitlab_file.read_text()
        assert "stage" in content.lower() or "adr" in content.lower()

    def test_run_ci_gitlab_separate_file(self, tmp_path: Path) -> None:
        """Test generating GitLab CI as include file when .gitlab-ci.yml exists."""
        from git_adr.commands.ci import run_ci_gitlab

        os.chdir(tmp_path)

        # Create existing .gitlab-ci.yml
        (tmp_path / ".gitlab-ci.yml").write_text("stages:\n  - build\n")

        run_ci_gitlab()

        # Should create separate file
        separate_file = tmp_path / "gitlab-ci-adr.yml"
        assert separate_file.exists()

    def test_run_ci_gitlab_with_wiki(self, tmp_path: Path) -> None:
        """Test generating GitLab CI with wiki sync."""
        from git_adr.commands.ci import run_ci_gitlab

        os.chdir(tmp_path)

        run_ci_gitlab(
            output=str(tmp_path / "gitlab-ci.yml"),
            wiki_sync=True,
            wiki_provider="gitlab",
        )

        content = (tmp_path / "gitlab-ci.yml").read_text()
        # Should have wiki-related configuration
        assert "git-adr" in content

    def test_run_ci_list(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test listing available CI templates."""
        from git_adr.commands.ci import run_ci_list

        run_ci_list()

        captured = capsys.readouterr()
        assert "github" in captured.out.lower()
        assert "gitlab" in captured.out.lower()


# =============================================================================
# Templates CLI Commands Tests
# =============================================================================


class TestTemplatesCLICommands:
    """Tests for src/git_adr/commands/templates_cli.py."""

    def test_run_templates_pr(self, tmp_path: Path) -> None:
        """Test generating PR template."""
        from git_adr.commands.templates_cli import run_templates_pr

        os.chdir(tmp_path)

        run_templates_pr(output=str(tmp_path / "PR_TEMPLATE.md"))

        pr_file = tmp_path / "PR_TEMPLATE.md"
        assert pr_file.exists()
        content = pr_file.read_text()
        assert "Architecture Impact" in content

    def test_run_templates_pr_with_require_adr(self, tmp_path: Path) -> None:
        """Test generating PR template with ADR requirement."""
        from git_adr.commands.templates_cli import run_templates_pr

        os.chdir(tmp_path)

        run_templates_pr(
            output=str(tmp_path / "PR_TEMPLATE.md"),
            require_adr=True,
            reviewers=["@arch-team"],
        )

        content = (tmp_path / "PR_TEMPLATE.md").read_text()
        assert "Required" in content or "ADR required" in content
        assert "@arch-team" in content

    def test_run_templates_pr_default_location(self, tmp_path: Path) -> None:
        """Test PR template goes to default GitHub location."""
        from git_adr.commands.templates_cli import run_templates_pr

        os.chdir(tmp_path)

        run_templates_pr()

        default_file = tmp_path / ".github/PULL_REQUEST_TEMPLATE.md"
        assert default_file.exists()

    def test_run_templates_issue(self, tmp_path: Path) -> None:
        """Test generating issue template."""
        from git_adr.commands.templates_cli import run_templates_issue

        os.chdir(tmp_path)

        run_templates_issue(output=str(tmp_path / "issue.md"))

        issue_file = tmp_path / "issue.md"
        assert issue_file.exists()
        content = issue_file.read_text()
        assert "Architecture Decision Proposal" in content

    def test_run_templates_issue_with_labels(self, tmp_path: Path) -> None:
        """Test generating issue template with custom labels."""
        from git_adr.commands.templates_cli import run_templates_issue

        os.chdir(tmp_path)

        run_templates_issue(
            output=str(tmp_path / "issue.md"),
            labels="adr, needs-review, architecture",
            stakeholders=["@cto"],
        )

        content = (tmp_path / "issue.md").read_text()
        assert "adr, needs-review, architecture" in content
        assert "@cto" in content

    def test_run_templates_issue_default_location(self, tmp_path: Path) -> None:
        """Test issue template goes to default GitHub location."""
        from git_adr.commands.templates_cli import run_templates_issue

        os.chdir(tmp_path)

        run_templates_issue()

        default_file = tmp_path / ".github/ISSUE_TEMPLATE/adr-proposal.md"
        assert default_file.exists()

    def test_run_templates_codeowners_to_stdout(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test generating CODEOWNERS to stdout."""
        from git_adr.commands.templates_cli import run_templates_codeowners

        run_templates_codeowners(team="@my-team")

        captured = capsys.readouterr()
        assert "@my-team" in captured.out
        assert "CODEOWNERS" in captured.out

    def test_run_templates_codeowners_to_file(self, tmp_path: Path) -> None:
        """Test generating CODEOWNERS to file."""
        from git_adr.commands.templates_cli import run_templates_codeowners

        os.chdir(tmp_path)

        run_templates_codeowners(
            output=str(tmp_path / "CODEOWNERS"),
            team="@arch-team",
            adr_directory="docs/decisions",
            protected_paths=["src/"],
        )

        codeowners_file = tmp_path / "CODEOWNERS"
        assert codeowners_file.exists()
        content = codeowners_file.read_text()
        assert "@arch-team" in content
        assert "docs/decisions" in content
        assert "src/" in content

    def test_run_templates_codeowners_with_paths(self, tmp_path: Path) -> None:
        """Test generating CODEOWNERS with various path types."""
        from git_adr.commands.templates_cli import run_templates_codeowners

        os.chdir(tmp_path)

        run_templates_codeowners(
            output=str(tmp_path / "CODEOWNERS"),
            team="@arch",
            api_paths=["api/v1/", "openapi/"],
            schema_paths=["db/"],
            infra_paths=["terraform/", "k8s/"],
        )

        content = (tmp_path / "CODEOWNERS").read_text()
        assert "api/v1/" in content
        assert "openapi/" in content
        assert "db/" in content
        assert "terraform/" in content
        assert "k8s/" in content

    def test_run_templates_all(self, tmp_path: Path) -> None:
        """Test generating all templates at once."""
        from git_adr.commands.templates_cli import run_templates_all

        os.chdir(tmp_path)

        run_templates_all(output_dir=str(tmp_path), team="@arch-team")

        # Check all files created
        pr_template = tmp_path / ".github/PULL_REQUEST_TEMPLATE.md"
        issue_template = tmp_path / ".github/ISSUE_TEMPLATE/adr-proposal.md"
        codeowners = tmp_path / "CODEOWNERS.adr"

        assert pr_template.exists()
        assert issue_template.exists()
        assert codeowners.exists()

    def test_run_templates_list(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test listing available governance templates."""
        from git_adr.commands.templates_cli import run_templates_list

        run_templates_list()

        captured = capsys.readouterr()
        assert "pr" in captured.out.lower() or "pull request" in captured.out.lower()
        assert "issue" in captured.out.lower()
        assert "codeowners" in captured.out.lower()


# =============================================================================
# Hooks CLI Commands Tests
# =============================================================================


class TestHooksCLICommands:
    """Tests for src/git_adr/commands/hooks_cli.py."""

    @pytest.fixture
    def git_repo_with_adr(self, tmp_path: Path) -> Iterator[Path]:
        """Create a git repo with git-adr initialized."""
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()

        # Initialize git
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # Create initial commit
        (repo_path / "README.md").write_text("# Test\n")
        subprocess.run(
            ["git", "add", "."], cwd=repo_path, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # Initialize git-adr
        subprocess.run(
            ["git", "config", "adr.namespace", "adr"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        yield repo_path

    def test_run_hooks_install(self, git_repo_with_adr: Path) -> None:
        """Test installing git hooks."""
        from git_adr.commands.hooks_cli import run_hooks_install

        os.chdir(git_repo_with_adr)

        run_hooks_install()

        hook_path = git_repo_with_adr / ".git/hooks/pre-push"
        assert hook_path.exists()
        assert os.access(hook_path, os.X_OK)

    def test_run_hooks_install_force(self, git_repo_with_adr: Path) -> None:
        """Test force reinstalling git hooks."""
        from git_adr.commands.hooks_cli import run_hooks_install

        os.chdir(git_repo_with_adr)

        # Create existing hook
        hooks_dir = git_repo_with_adr / ".git/hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        existing_hook = hooks_dir / "pre-push"
        existing_hook.write_text("#!/bin/sh\necho existing\n")
        existing_hook.chmod(0o755)

        run_hooks_install(force=True)

        # Backup should exist
        backup_hook = hooks_dir / "pre-push.git-adr-backup"
        assert backup_hook.exists()

        # New hook should be installed
        content = existing_hook.read_text()
        assert "git-adr" in content or "GIT_ADR" in content

    def test_run_hooks_install_manual(
        self, git_repo_with_adr: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test getting manual hook installation instructions."""
        from git_adr.commands.hooks_cli import run_hooks_install

        os.chdir(git_repo_with_adr)

        run_hooks_install(manual=True)

        captured = capsys.readouterr()
        # Should print instructions instead of installing
        assert "pre-push" in captured.out.lower() or "hook" in captured.out.lower()

    def test_run_hooks_uninstall(self, git_repo_with_adr: Path) -> None:
        """Test uninstalling git hooks."""
        from git_adr.commands.hooks_cli import run_hooks_install, run_hooks_uninstall

        os.chdir(git_repo_with_adr)

        # First install
        run_hooks_install()

        hook_path = git_repo_with_adr / ".git/hooks/pre-push"
        assert hook_path.exists()

        # Then uninstall
        run_hooks_uninstall()

        # Hook should be removed or restored to backup
        assert not hook_path.exists() or "git-adr" not in hook_path.read_text()

    def test_run_hooks_status_not_installed(
        self, git_repo_with_adr: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test hooks status when not installed."""
        from git_adr.commands.hooks_cli import run_hooks_status

        os.chdir(git_repo_with_adr)

        run_hooks_status()

        captured = capsys.readouterr()
        assert (
            "not installed" in captured.out.lower()
            or "no" in captured.out.lower()
            or "✗" in captured.out
        )

    def test_run_hooks_status_installed(
        self, git_repo_with_adr: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test hooks status when installed."""
        from git_adr.commands.hooks_cli import run_hooks_install, run_hooks_status

        os.chdir(git_repo_with_adr)

        run_hooks_install()
        run_hooks_status()

        captured = capsys.readouterr()
        assert (
            "installed" in captured.out.lower()
            or "✓" in captured.out
            or "pre-push" in captured.out.lower()
        )

    def test_run_hooks_config_show(
        self, git_repo_with_adr: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test showing hooks configuration."""
        from git_adr.commands.hooks_cli import run_hooks_config

        os.chdir(git_repo_with_adr)

        run_hooks_config(show=True)

        captured = capsys.readouterr()
        assert "block" in captured.out.lower() or "config" in captured.out.lower()

    def test_run_hooks_config_block_on_failure(self, git_repo_with_adr: Path) -> None:
        """Test enabling block on failure."""
        from git_adr.commands.hooks_cli import run_hooks_config

        os.chdir(git_repo_with_adr)

        run_hooks_config(block_on_failure=True)

        # Check config was set
        result = subprocess.run(
            ["git", "config", "--get", "adr.hooks.blockOnFailure"],
            cwd=git_repo_with_adr,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.stdout.strip() == "true"

    def test_run_hooks_config_no_block_on_failure(
        self, git_repo_with_adr: Path
    ) -> None:
        """Test disabling block on failure."""
        from git_adr.commands.hooks_cli import run_hooks_config

        os.chdir(git_repo_with_adr)

        # First enable
        run_hooks_config(block_on_failure=True)

        # Then disable
        run_hooks_config(no_block_on_failure=True)

        # Check config was set
        result = subprocess.run(
            ["git", "config", "--get", "adr.hooks.blockOnFailure"],
            cwd=git_repo_with_adr,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.stdout.strip() == "false"

    def test_run_hooks_install_not_git_repo(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test hooks install when not in a git repo."""
        from git_adr.commands.hooks_cli import run_hooks_install

        os.chdir(tmp_path)

        run_hooks_install()

        captured = capsys.readouterr()
        assert (
            "not in a git repository" in captured.err.lower()
            or "error" in captured.err.lower()
        )

    def test_run_hooks_uninstall_not_git_repo(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test hooks uninstall when not in a git repo."""
        from git_adr.commands.hooks_cli import run_hooks_uninstall

        os.chdir(tmp_path)

        run_hooks_uninstall()

        captured = capsys.readouterr()
        assert (
            "not in a git repository" in captured.err.lower()
            or "error" in captured.err.lower()
        )

    def test_run_hooks_status_not_git_repo(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test hooks status when not in a git repo."""
        from git_adr.commands.hooks_cli import run_hooks_status

        os.chdir(tmp_path)

        run_hooks_status()

        captured = capsys.readouterr()
        assert (
            "not in a git repository" in captured.err.lower()
            or "error" in captured.err.lower()
        )

    def test_run_hooks_config_not_git_repo(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test hooks config when not in a git repo."""
        from git_adr.commands.hooks_cli import run_hooks_config
        from git_adr.core.git import GitError

        os.chdir(tmp_path)

        # get_git() may succeed (if parent is git repo) but config_set will fail
        # or get_git() may fail with GitError
        try:
            run_hooks_config(block_on_failure=True)
            captured = capsys.readouterr()
            assert (
                "not in a git repository" in captured.err.lower()
                or "error" in captured.err.lower()
            )
        except GitError:
            # This is expected when not in a git repo
            pass

    def test_run_hooks_status_outdated(
        self, git_repo_with_adr: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test hooks status with outdated hook."""
        from git_adr.commands.hooks_cli import run_hooks_status
        from git_adr.hooks import HOOK_MARKER

        os.chdir(git_repo_with_adr)

        # Install a hook with an old version
        hooks_dir = git_repo_with_adr / ".git/hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        hook_path = hooks_dir / "pre-push"
        # Write an old version hook
        hook_path.write_text(f"#!/bin/sh\n{HOOK_MARKER}\n# Version: 0.1\n")
        hook_path.chmod(0o755)

        run_hooks_status()

        captured = capsys.readouterr()
        # Should show outdated status
        assert "outdated" in captured.out.lower() or "↑" in captured.out

    def test_run_hooks_status_foreign(
        self, git_repo_with_adr: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test hooks status with foreign hook."""
        from git_adr.commands.hooks_cli import run_hooks_status

        os.chdir(git_repo_with_adr)

        # Create a foreign hook (not ours)
        hooks_dir = git_repo_with_adr / ".git/hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        hook_path = hooks_dir / "pre-push"
        hook_path.write_text("#!/bin/sh\necho foreign\n")
        hook_path.chmod(0o755)

        run_hooks_status()

        captured = capsys.readouterr()
        # Should show foreign status
        assert "foreign" in captured.out.lower() or "?" in captured.out

    def test_run_hooks_install_skipped_message(
        self, git_repo_with_adr: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test hooks install shows proper message for already installed hooks."""
        from git_adr.commands.hooks_cli import run_hooks_install

        os.chdir(git_repo_with_adr)

        # Install once
        run_hooks_install()

        # Clear capture
        capsys.readouterr()

        # Install again without force
        run_hooks_install()

        captured = capsys.readouterr()
        # Should show already installed message
        assert "already" in captured.out.lower() or "installed" in captured.out.lower()

    def test_run_hooks_uninstall_not_ours(
        self, git_repo_with_adr: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test hooks uninstall shows message for hooks not ours."""
        from git_adr.commands.hooks_cli import run_hooks_uninstall

        os.chdir(git_repo_with_adr)

        # Create a foreign hook
        hooks_dir = git_repo_with_adr / ".git/hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        hook_path = hooks_dir / "pre-push"
        hook_path.write_text("#!/bin/sh\necho foreign\n")
        hook_path.chmod(0o755)

        run_hooks_uninstall()

        captured = capsys.readouterr()
        # Should show not our hook message
        assert "not" in captured.out.lower() or "skipped" in captured.out.lower()

    def test_run_hooks_config_default_shows_config(
        self, git_repo_with_adr: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test hooks config with no args shows config."""
        from git_adr.commands.hooks_cli import run_hooks_config

        os.chdir(git_repo_with_adr)

        # Call with no args (should show config)
        run_hooks_config()

        captured = capsys.readouterr()
        assert "block" in captured.out.lower() or "config" in captured.out.lower()

    def test_run_hooks_status_config_block_enabled(
        self, git_repo_with_adr: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test hooks status shows block on failure enabled."""
        from git_adr.commands.hooks_cli import run_hooks_config, run_hooks_status

        os.chdir(git_repo_with_adr)

        # Enable block on failure
        run_hooks_config(block_on_failure=True)

        # Clear capture
        capsys.readouterr()

        run_hooks_status()

        captured = capsys.readouterr()
        # Should show enabled block on failure
        assert "enabled" in captured.out.lower() or "block" in captured.out.lower()

    def test_run_hooks_status_config_skip_enabled(
        self, git_repo_with_adr: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test hooks status shows skip enabled."""
        os.chdir(git_repo_with_adr)

        # Set skip config
        subprocess.run(
            ["git", "config", "adr.hooks.skip", "true"],
            cwd=git_repo_with_adr,
            check=True,
            capture_output=True,
        )

        from git_adr.commands.hooks_cli import run_hooks_status

        run_hooks_status()

        captured = capsys.readouterr()
        # Should show skip enabled
        assert "skip" in captured.out.lower() or "yes" in captured.out.lower()


# =============================================================================
# Hooks Module Tests
# =============================================================================


class TestHooksModule:
    """Tests for src/git_adr/hooks.py."""

    @pytest.fixture
    def git_repo(self, tmp_path: Path) -> Iterator[Path]:
        """Create a basic git repo."""
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()

        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        yield repo_path

    def test_hook_dataclass(self, git_repo: Path) -> None:
        """Test Hook dataclass creation."""
        from git_adr.hooks import Hook

        hook = Hook(
            hook_type="pre-push",
            hooks_dir=git_repo / ".git/hooks",
        )

        assert hook.hook_type == "pre-push"
        assert hook.hooks_dir == git_repo / ".git/hooks"

    def test_hook_path(self, git_repo: Path) -> None:
        """Test Hook hook_path property."""
        from git_adr.hooks import Hook

        hook = Hook(
            hook_type="pre-push",
            hooks_dir=git_repo / ".git/hooks",
        )

        assert hook.hook_path == git_repo / ".git/hooks/pre-push"

    def test_hook_backup_path(self, git_repo: Path) -> None:
        """Test Hook backup path property."""
        from git_adr.hooks import Hook

        hook = Hook(
            hook_type="pre-push",
            hooks_dir=git_repo / ".git/hooks",
        )

        assert hook.backup_path == git_repo / ".git/hooks/pre-push.git-adr-backup"

    def test_hook_install_creates_executable(self, git_repo: Path) -> None:
        """Test that Hook.install() creates executable script."""
        from git_adr.hooks import Hook

        hooks_dir = git_repo / ".git/hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        hook = Hook(hook_type="pre-push", hooks_dir=hooks_dir)
        hook.install()

        assert hook.hook_path.exists()
        assert os.access(hook.hook_path, os.X_OK)

    def test_hook_install_backs_up_existing(self, git_repo: Path) -> None:
        """Test that Hook.install() backs up existing hooks."""
        from git_adr.hooks import Hook

        hooks_dir = git_repo / ".git/hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        # Create existing hook
        existing = hooks_dir / "pre-push"
        existing.write_text("#!/bin/sh\necho old\n")
        existing.chmod(0o755)

        hook = Hook(hook_type="pre-push", hooks_dir=hooks_dir)
        hook.install(force=True)

        assert hook.backup_path.exists()
        assert hook.backup_path.read_text() == "#!/bin/sh\necho old\n"

    def test_hook_install_chains_backup(self, git_repo: Path) -> None:
        """Test that installed hook chains to backup."""
        from git_adr.hooks import Hook

        hooks_dir = git_repo / ".git/hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        # Create existing hook
        existing = hooks_dir / "pre-push"
        existing.write_text("#!/bin/sh\necho old\n")
        existing.chmod(0o755)

        hook = Hook(hook_type="pre-push", hooks_dir=hooks_dir)
        hook.install(force=True)

        content = hook.hook_path.read_text()
        assert "backup" in content.lower() or "git-adr-backup" in content

    def test_hook_uninstall_removes_hook(self, git_repo: Path) -> None:
        """Test that Hook.uninstall() removes hook."""
        from git_adr.hooks import Hook

        hooks_dir = git_repo / ".git/hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        hook = Hook(hook_type="pre-push", hooks_dir=hooks_dir)
        hook.install()
        assert hook.hook_path.exists()

        hook.uninstall()
        assert not hook.hook_path.exists()

    def test_hook_uninstall_restores_backup(self, git_repo: Path) -> None:
        """Test that Hook.uninstall() restores backup."""
        from git_adr.hooks import Hook

        hooks_dir = git_repo / ".git/hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        # Create existing hook
        existing = hooks_dir / "pre-push"
        existing.write_text("#!/bin/sh\necho original\n")
        existing.chmod(0o755)

        hook = Hook(hook_type="pre-push", hooks_dir=hooks_dir)
        hook.install(force=True)
        hook.uninstall()

        # Original should be restored
        assert hook.hook_path.read_text() == "#!/bin/sh\necho original\n"

    def test_hook_is_ours_true(self, git_repo: Path) -> None:
        """Test Hook.is_ours() returns True for our hooks."""
        from git_adr.hooks import Hook

        hooks_dir = git_repo / ".git/hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        hook = Hook(hook_type="pre-push", hooks_dir=hooks_dir)
        hook.install()

        assert hook.is_ours() is True

    def test_hook_is_ours_false(self, git_repo: Path) -> None:
        """Test Hook.is_ours() returns False for other hooks."""
        from git_adr.hooks import Hook

        hooks_dir = git_repo / ".git/hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        # Create a non-git-adr hook
        existing = hooks_dir / "pre-push"
        existing.write_text("#!/bin/sh\necho other\n")
        existing.chmod(0o755)

        hook = Hook(hook_type="pre-push", hooks_dir=hooks_dir)

        assert hook.is_ours() is False

    def test_hook_is_ours_not_exists(self, git_repo: Path) -> None:
        """Test Hook.is_ours() returns False when no hook exists."""
        from git_adr.hooks import Hook

        hooks_dir = git_repo / ".git/hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        hook = Hook(hook_type="pre-push", hooks_dir=hooks_dir)

        assert hook.is_ours() is False

    def test_hook_get_version(self, git_repo: Path) -> None:
        """Test Hook.get_installed_version() extracts version."""
        from git_adr.hooks import Hook

        hooks_dir = git_repo / ".git/hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        hook = Hook(hook_type="pre-push", hooks_dir=hooks_dir)
        hook.install()

        version = hook.get_installed_version()
        assert version is not None

    def test_hooks_manager_install_all(self, git_repo: Path) -> None:
        """Test HooksManager.install_all()."""
        from git_adr.hooks import HooksManager

        git_dir = git_repo / ".git"
        git_dir.mkdir(parents=True, exist_ok=True)
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        manager = HooksManager(git_dir=git_dir)
        manager.install_all()

        pre_push = hooks_dir / "pre-push"
        assert pre_push.exists()

    def test_hooks_manager_uninstall_all(self, git_repo: Path) -> None:
        """Test HooksManager.uninstall_all()."""
        from git_adr.hooks import HooksManager

        git_dir = git_repo / ".git"
        git_dir.mkdir(parents=True, exist_ok=True)
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        manager = HooksManager(git_dir=git_dir)
        manager.install_all()

        pre_push = hooks_dir / "pre-push"
        assert pre_push.exists()

        manager.uninstall_all()
        assert not pre_push.exists()

    def test_hooks_manager_status(self, git_repo: Path) -> None:
        """Test HooksManager.get_status()."""
        from git_adr.hooks import HooksManager, HookStatus

        git_dir = git_repo / ".git"
        git_dir.mkdir(parents=True, exist_ok=True)
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        manager = HooksManager(git_dir=git_dir)

        status_before = manager.get_status()
        assert "pre-push" in status_before
        assert status_before["pre-push"] == HookStatus.NOT_INSTALLED

        manager.install_all()

        status_after = manager.get_status()
        assert status_after["pre-push"] == HookStatus.INSTALLED

    def test_get_pre_push_script_template(self) -> None:
        """Test that PRE_PUSH_TEMPLATE is valid shell."""
        from git_adr.hooks import PRE_PUSH_TEMPLATE

        script = PRE_PUSH_TEMPLATE

        assert script.startswith("#!/bin/sh")
        assert "GIT_ADR" in script
        assert "pre-push" in script.lower() or "hook" in script.lower()

    def test_hook_get_script_content_unknown_type(self, git_repo: Path) -> None:
        """Test get_script_content raises for unknown hook type."""
        from git_adr.hooks import Hook

        hooks_dir = git_repo / ".git/hooks"
        hook = Hook(hook_type="unknown-hook", hooks_dir=hooks_dir)

        with pytest.raises(ValueError) as excinfo:
            hook.get_script_content()
        assert "Unknown hook type" in str(excinfo.value)

    def test_hook_is_installed(self, git_repo: Path) -> None:
        """Test Hook.is_installed() method."""
        from git_adr.hooks import Hook

        hooks_dir = git_repo / ".git/hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        hook = Hook(hook_type="pre-push", hooks_dir=hooks_dir)

        # Not installed initially
        assert hook.is_installed() is False

        # After install
        hook.install()
        assert hook.is_installed() is True

    def test_hook_get_status_foreign(self, git_repo: Path) -> None:
        """Test Hook.get_status() returns FOREIGN for non-git-adr hooks."""
        from git_adr.hooks import Hook, HookStatus

        hooks_dir = git_repo / ".git/hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        # Create a foreign hook (not ours)
        (hooks_dir / "pre-push").write_text("#!/bin/sh\necho foreign\n")
        (hooks_dir / "pre-push").chmod(0o755)

        hook = Hook(hook_type="pre-push", hooks_dir=hooks_dir)
        assert hook.get_status() == HookStatus.FOREIGN

    def test_hook_get_status_outdated(self, git_repo: Path) -> None:
        """Test Hook.get_status() returns OUTDATED for old version."""
        from git_adr.hooks import HOOK_MARKER, Hook, HookStatus

        hooks_dir = git_repo / ".git/hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        # Create an old version of our hook
        old_script = f"""#!/bin/sh
{HOOK_MARKER}
# Version: 0.1
echo old
"""
        (hooks_dir / "pre-push").write_text(old_script)
        (hooks_dir / "pre-push").chmod(0o755)

        hook = Hook(hook_type="pre-push", hooks_dir=hooks_dir)
        assert hook.get_status() == HookStatus.OUTDATED

    def test_hook_install_already_installed(self, git_repo: Path) -> None:
        """Test Hook.install() when already installed same version."""
        from git_adr.hooks import Hook

        hooks_dir = git_repo / ".git/hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        hook = Hook(hook_type="pre-push", hooks_dir=hooks_dir)
        hook.install()

        # Install again without force
        result = hook.install(force=False)
        assert "already installed" in result

    def test_hook_uninstall_not_ours(self, git_repo: Path) -> None:
        """Test Hook.uninstall() skips foreign hooks."""
        from git_adr.hooks import Hook

        hooks_dir = git_repo / ".git/hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        # Create foreign hook
        (hooks_dir / "pre-push").write_text("#!/bin/sh\necho foreign\n")
        (hooks_dir / "pre-push").chmod(0o755)

        hook = Hook(hook_type="pre-push", hooks_dir=hooks_dir)
        result = hook.uninstall()

        assert "not our hook" in result
        # Hook should still exist
        assert hook.hook_path.exists()

    def test_hook_uninstall_not_installed(self, git_repo: Path) -> None:
        """Test Hook.uninstall() handles non-existent hook."""
        from git_adr.hooks import Hook

        hooks_dir = git_repo / ".git/hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        hook = Hook(hook_type="pre-push", hooks_dir=hooks_dir)
        result = hook.uninstall()

        assert "not installed" in result

    def test_hook_get_manual_instructions(self, git_repo: Path) -> None:
        """Test Hook.get_manual_instructions()."""
        from git_adr.hooks import Hook

        hooks_dir = git_repo / ".git/hooks"
        hook = Hook(hook_type="pre-push", hooks_dir=hooks_dir)

        instructions = hook.get_manual_instructions()
        assert "pre-push" in instructions
        assert "git adr hook" in instructions

    def test_hooks_manager_get_manual_instructions(self, git_repo: Path) -> None:
        """Test HooksManager.get_manual_instructions()."""
        from git_adr.hooks import HooksManager

        git_dir = git_repo / ".git"
        git_dir.mkdir(parents=True, exist_ok=True)
        (git_dir / "hooks").mkdir(parents=True, exist_ok=True)

        manager = HooksManager(git_dir=git_dir)
        instructions = manager.get_manual_instructions()

        assert "Manual" in instructions
        assert "pre-push" in instructions

    def test_hooks_manager_find_git_dir_worktree(self, tmp_path: Path) -> None:
        """Test HooksManager._find_git_dir() with worktree."""
        from git_adr.hooks import HooksManager

        # Create a worktree-style .git file
        repo_path = tmp_path / "worktree"
        repo_path.mkdir()

        actual_git_dir = tmp_path / "main/.git/worktrees/branch"
        actual_git_dir.mkdir(parents=True)

        git_file = repo_path / ".git"
        git_file.write_text(f"gitdir: {actual_git_dir}")

        os.chdir(repo_path)

        git_dir = HooksManager._find_git_dir()
        assert git_dir == actual_git_dir

    def test_hooks_manager_find_git_dir_not_found(self, tmp_path: Path) -> None:
        """Test HooksManager._find_git_dir() raises when not in repo."""
        from git_adr.hooks import HooksManager

        # Create a directory without .git
        non_repo = tmp_path / "not_a_repo"
        non_repo.mkdir()

        os.chdir(non_repo)

        with pytest.raises(FileNotFoundError) as excinfo:
            HooksManager._find_git_dir()
        assert "Not in a git repository" in str(excinfo.value)


# =============================================================================
# Hook Command Tests
# =============================================================================


class TestHookCommand:
    """Tests for src/git_adr/commands/hook.py."""

    @pytest.fixture
    def initialized_adr_repo(self, tmp_path: Path) -> Iterator[Path]:
        """Create a fully initialized ADR repo."""
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()

        # Initialize git
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # Create initial commit
        (repo_path / "README.md").write_text("# Test\n")
        subprocess.run(
            ["git", "add", "."], cwd=repo_path, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # Initialize git-adr config
        subprocess.run(
            ["git", "config", "adr.namespace", "adr"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        yield repo_path

    def test_run_hook_pre_push_no_args(self, initialized_adr_repo: Path) -> None:
        """Test run_hook for pre-push with no remote arg exits with error."""
        from git_adr.commands.hook import run_hook

        os.chdir(initialized_adr_repo)

        # Should exit with error - no remote provided
        with pytest.raises(SystemExit) as excinfo:
            run_hook("pre-push")
        assert excinfo.value.code == 1

    def test_run_hook_unknown_type(self, initialized_adr_repo: Path) -> None:
        """Test run_hook with unknown hook type exits."""
        from git_adr.commands.hook import run_hook

        os.chdir(initialized_adr_repo)

        # Unknown hook types should exit with error
        with pytest.raises(SystemExit) as excinfo:
            run_hook("unknown-hook")
        assert excinfo.value.code == 1

    def test_handle_pre_push(self, initialized_adr_repo: Path) -> None:
        """Test _handle_pre_push directly."""
        from git_adr.commands.hook import _handle_pre_push

        os.chdir(initialized_adr_repo)

        # Will raise because there's no remote - but that's expected
        # We're just testing that the function executes the right path
        with pytest.raises(RuntimeError) as excinfo:
            _handle_pre_push("origin")

        # Error should mention the remote
        assert "origin" in str(excinfo.value)

    def test_handle_pre_push_with_timeout_config(
        self, initialized_adr_repo: Path
    ) -> None:
        """Test that timeout config is read."""
        from git_adr.commands.hook import _handle_pre_push

        os.chdir(initialized_adr_repo)

        # Set timeout config
        subprocess.run(
            ["git", "config", "adr.sync.timeout", "10"],
            cwd=initialized_adr_repo,
            check=True,
            capture_output=True,
        )

        # Should still work (will fail for other reason - no remote)
        with pytest.raises(RuntimeError):
            _handle_pre_push("origin")

    def test_handle_pre_push_invalid_timeout(self, initialized_adr_repo: Path) -> None:
        """Test that invalid timeout config defaults to 5."""
        from git_adr.commands.hook import _handle_pre_push

        os.chdir(initialized_adr_repo)

        # Set invalid timeout config
        subprocess.run(
            ["git", "config", "adr.sync.timeout", "notanumber"],
            cwd=initialized_adr_repo,
            check=True,
            capture_output=True,
        )

        # Should still work (will fail for other reason - no remote)
        with pytest.raises(RuntimeError):
            _handle_pre_push("origin")


# =============================================================================
# Additional Coverage Tests
# =============================================================================


class TestAdditionalCoverage:
    """Additional tests to reach 95% coverage threshold."""

    @pytest.fixture
    def git_repo_with_adr(self, tmp_path: Path) -> Iterator[Path]:
        """Create a git repo with git-adr initialized."""
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()

        # Initialize git
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # Create initial commit
        (repo_path / "README.md").write_text("# Test\n")
        subprocess.run(
            ["git", "add", "."], cwd=repo_path, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # Initialize git-adr config
        subprocess.run(
            ["git", "config", "adr.namespace", "adr"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        yield repo_path

    def test_hook_is_ours_oserror(self, tmp_path: Path) -> None:
        """Test Hook.is_ours() handles OSError when reading hook."""
        from git_adr.hooks import Hook

        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()

        hook = Hook(hook_type="pre-push", hooks_dir=hooks_dir)

        # Create a directory instead of a file (will cause read error)
        hook_path = hooks_dir / "pre-push"
        hook_path.mkdir()

        # Should return False on OSError
        assert hook.is_ours() is False

    def test_hook_get_installed_version_oserror(self, tmp_path: Path) -> None:
        """Test Hook.get_installed_version() handles OSError."""
        from git_adr.hooks import Hook

        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()

        hook = Hook(hook_type="pre-push", hooks_dir=hooks_dir)

        # Create a directory instead of a file (will cause read error)
        hook_path = hooks_dir / "pre-push"
        hook_path.mkdir()

        # Should return None on OSError
        assert hook.get_installed_version() is None

    def test_hook_get_installed_version_no_version(self, tmp_path: Path) -> None:
        """Test Hook.get_installed_version() when no version comment exists."""
        from git_adr.hooks import Hook

        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()

        hook = Hook(hook_type="pre-push", hooks_dir=hooks_dir)

        # Create hook without version comment
        hook_path = hooks_dir / "pre-push"
        hook_path.write_text("#!/bin/sh\necho 'no version'\n")

        # Should return None when no version match
        assert hook.get_installed_version() is None

    def test_hooks_manager_find_git_dir_in_parent(self, tmp_path: Path) -> None:
        """Test HooksManager._find_git_dir() finds .git in parent directory."""
        from git_adr.hooks import HooksManager

        # Create a git repo with nested directory
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        git_dir = repo_path / ".git"
        git_dir.mkdir()

        # Create nested subdirectory
        nested = repo_path / "src" / "deep" / "nested"
        nested.mkdir(parents=True)

        os.chdir(nested)

        # Should find .git in parent
        found_git_dir = HooksManager._find_git_dir()
        assert found_git_dir == git_dir

    def test_hooks_manager_find_git_dir_worktree_in_parent(
        self, tmp_path: Path
    ) -> None:
        """Test HooksManager._find_git_dir() finds worktree .git file in parent."""
        from git_adr.hooks import HooksManager

        # Create main repo with actual git dir
        actual_git_dir = tmp_path / "main/.git/worktrees/feature"
        actual_git_dir.mkdir(parents=True)

        # Create worktree directory with .git file in parent
        worktree_root = tmp_path / "worktree"
        worktree_root.mkdir()
        git_file = worktree_root / ".git"
        git_file.write_text(f"gitdir: {actual_git_dir}")

        # Create nested subdirectory in worktree
        nested = worktree_root / "src" / "nested"
        nested.mkdir(parents=True)

        os.chdir(nested)

        # Should find .git file in parent and resolve it
        found_git_dir = HooksManager._find_git_dir()
        assert found_git_dir == actual_git_dir

    def test_run_hooks_install_already_message(
        self, git_repo_with_adr: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test run_hooks_install shows 'already installed' message."""
        from git_adr.commands.hooks_cli import run_hooks_install

        os.chdir(git_repo_with_adr)

        # Install hooks first
        run_hooks_install()
        capsys.readouterr()  # Clear output

        # Install again without force - should show "already" message
        run_hooks_install()
        captured = capsys.readouterr()

        # Should see the yellow "already" indicator
        assert "already" in captured.out.lower() or "○" in captured.out

    def test_run_hooks_install_other_message(
        self, git_repo_with_adr: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test run_hooks_install shows generic message for other results."""
        from unittest.mock import patch

        from git_adr.commands.hooks_cli import run_hooks_install

        os.chdir(git_repo_with_adr)

        # Mock manager to return a result that's neither "installed" nor "skipped"
        with patch("git_adr.commands.hooks_cli.get_hooks_manager") as mock_manager:
            mock_instance = mock_manager.return_value
            mock_instance.install_all.return_value = ["pre-push: some other message"]

            run_hooks_install()
            captured = capsys.readouterr()

            # Should see the dim dot indicator for "other" messages
            assert "•" in captured.out

    def test_run_hooks_status_unknown_status(
        self, git_repo_with_adr: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test run_hooks_status handles unknown hook status."""
        from unittest.mock import MagicMock, patch

        from git_adr.commands.hooks_cli import run_hooks_status

        os.chdir(git_repo_with_adr)

        # Create a mock status that's not in the enum
        mock_status = MagicMock()
        mock_status.name = "UNKNOWN"

        with patch("git_adr.commands.hooks_cli.get_hooks_manager") as mock_manager:
            mock_instance = mock_manager.return_value
            mock_instance.get_status.return_value = {"pre-push": mock_status}

            run_hooks_status()
            captured = capsys.readouterr()

            # Should see the unknown indicator
            assert "Unknown" in captured.out or "?" in captured.out

    def test_run_hooks_config_show_flag(
        self, git_repo_with_adr: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test run_hooks_config with show=True."""
        from git_adr.commands.hooks_cli import run_hooks_config

        os.chdir(git_repo_with_adr)

        # Run with show flag
        run_hooks_config(show=True)
        captured = capsys.readouterr()

        # Should show config status
        assert (
            "Hook Configuration" in captured.out or "Block on failure" in captured.out
        )

    def test_run_hooks_config_no_block_on_failure(
        self, git_repo_with_adr: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test run_hooks_config with no_block_on_failure."""
        from git_adr.commands.hooks_cli import run_hooks_config

        os.chdir(git_repo_with_adr)

        # First enable it
        run_hooks_config(block_on_failure=True)
        capsys.readouterr()

        # Then disable it
        run_hooks_config(no_block_on_failure=True)
        captured = capsys.readouterr()

        # Should confirm disabled
        assert "disabled" in captured.out.lower()

    def test_ci_github_output_exists_warning(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test ci github shows warning when output already exists."""
        from git_adr.commands.ci import run_ci_github

        # Create output directory with existing file
        output_dir = tmp_path / ".github" / "workflows"
        output_dir.mkdir(parents=True)
        (output_dir / "adr-sync.yml").write_text("existing content")

        os.chdir(tmp_path)

        run_ci_github(sync=True, validate=False, output=str(output_dir))
        captured = capsys.readouterr()

        # Should show warning about overwriting
        assert "already exists" in captured.out or "overwriting" in captured.out.lower()

    def test_ci_gitlab_with_explicit_output(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test ci gitlab with explicit output path."""
        from git_adr.commands.ci import run_ci_gitlab

        output_file = tmp_path / "custom-ci.yml"

        os.chdir(tmp_path)

        run_ci_gitlab(sync=True, validate=True, output=str(output_file))
        captured = capsys.readouterr()

        # Should generate to custom path
        assert output_file.exists()
        assert "Generated" in captured.out

    def test_templates_pr_output_exists_warning(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test templates pr shows warning when output exists (overwrites)."""
        from git_adr.commands.templates_cli import run_templates_pr

        # Create output file
        output_file = tmp_path / "PULL_REQUEST_TEMPLATE.md"
        output_file.write_text("existing content")

        os.chdir(tmp_path)

        run_templates_pr(output=str(output_file))
        captured = capsys.readouterr()

        # Should show warning about overwriting
        assert "already exists" in captured.out or "overwriting" in captured.out.lower()

    def test_templates_issue_output_exists_warning(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test templates issue shows warning when output exists (overwrites)."""
        from git_adr.commands.templates_cli import run_templates_issue

        # Create output file
        output_file = tmp_path / "adr-proposal.md"
        output_file.write_text("existing content")

        os.chdir(tmp_path)

        run_templates_issue(output=str(output_file))
        captured = capsys.readouterr()

        # Should show warning about overwriting
        assert "already exists" in captured.out or "overwriting" in captured.out.lower()

    def test_templates_codeowners_output_exists_warning(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test templates codeowners shows warning when output exists."""
        from git_adr.commands.templates_cli import run_templates_codeowners

        # Create output file
        output_file = tmp_path / "CODEOWNERS"
        output_file.write_text("# Existing content\n* @default-team\n")

        os.chdir(tmp_path)

        run_templates_codeowners(output=str(output_file), team="@arch-team")
        captured = capsys.readouterr()

        # Should show warning about overwriting
        assert "already exists" in captured.out or "overwriting" in captured.out.lower()

    def test_hook_install_existing_hook_backup(self, tmp_path: Path) -> None:
        """Test Hook.install() backs up existing non-git-adr hook."""
        from git_adr.hooks import Hook

        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()

        hook = Hook(hook_type="pre-push", hooks_dir=hooks_dir)

        # Create existing hook (not ours)
        hook_path = hooks_dir / "pre-push"
        hook_path.write_text("#!/bin/sh\necho 'user hook'\n")
        hook_path.chmod(0o755)

        # Install our hook
        result = hook.install(force=True)

        # Should mention backup
        assert "backed up" in result.lower()

        # Backup should exist
        backup_path = hooks_dir / "pre-push.git-adr-backup"
        assert backup_path.exists()
        assert "user hook" in backup_path.read_text()

    def test_hook_uninstall_restores_backup(self, tmp_path: Path) -> None:
        """Test Hook.uninstall() restores backup when present."""
        from git_adr.hooks import Hook

        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()

        hook = Hook(hook_type="pre-push", hooks_dir=hooks_dir)

        # Create existing hook (not ours) and install ours
        hook_path = hooks_dir / "pre-push"
        hook_path.write_text("#!/bin/sh\necho 'user hook'\n")
        hook_path.chmod(0o755)

        hook.install(force=True)

        # Now uninstall
        result = hook.uninstall()

        # Should mention restore
        assert "restored" in result.lower()

        # Original hook should be restored
        assert "user hook" in hook_path.read_text()

    def test_hook_uninstall_not_ours(self, tmp_path: Path) -> None:
        """Test Hook.uninstall() skips foreign hooks."""
        from git_adr.hooks import Hook

        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()

        hook = Hook(hook_type="pre-push", hooks_dir=hooks_dir)

        # Create a foreign hook (not ours)
        hook_path = hooks_dir / "pre-push"
        hook_path.write_text("#!/bin/sh\necho 'foreign hook'\n")

        result = hook.uninstall()

        # Should skip
        assert "not our hook" in result.lower() or "skipped" in result.lower()

        # Foreign hook should still exist
        assert hook_path.exists()

    def test_ci_github_validate_output_exists_warning(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test ci github shows warning when validate output exists."""
        from git_adr.commands.ci import run_ci_github

        # Create output directory with existing validate file
        output_dir = tmp_path / ".github" / "workflows"
        output_dir.mkdir(parents=True)
        (output_dir / "adr-validate.yml").write_text("existing content")

        os.chdir(tmp_path)

        run_ci_github(sync=False, validate=True, output=str(output_dir))
        captured = capsys.readouterr()

        # Should show warning about overwriting
        assert "already exists" in captured.out or "overwriting" in captured.out.lower()

    def test_ci_gitlab_default_output_new_file(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test ci gitlab creates .gitlab-ci.yml when no existing file."""
        from git_adr.commands.ci import run_ci_gitlab

        os.chdir(tmp_path)

        # No existing .gitlab-ci.yml, should create it
        run_ci_gitlab(sync=True, validate=True)
        captured = capsys.readouterr()

        # Should create .gitlab-ci.yml
        assert (tmp_path / ".gitlab-ci.yml").exists()
        assert "Generated" in captured.out

    def test_ci_gitlab_existing_ci_file_warning(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test ci gitlab shows warning when overwriting existing .gitlab-ci.yml."""
        from git_adr.commands.ci import run_ci_gitlab

        # Create existing .gitlab-ci.yml
        (tmp_path / ".gitlab-ci.yml").write_text("# existing pipeline")

        os.chdir(tmp_path)

        # Should create gitlab-ci-adr.yml instead and show note
        run_ci_gitlab(sync=True, validate=True)
        captured = capsys.readouterr()

        # Should note the existing file and create separate file
        assert (
            "existing .gitlab-ci.yml found" in captured.out.lower()
            or "gitlab-ci-adr.yml" in captured.out
        )

    def test_ci_list(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Test ci list shows available templates."""
        from git_adr.commands.ci import run_ci_list

        os.chdir(tmp_path)

        run_ci_list()
        captured = capsys.readouterr()

        # Should list templates
        assert "Available CI/CD Templates" in captured.out
        assert "github" in captured.out.lower() or "gitlab" in captured.out.lower()

    def test_run_hook_pre_push_success(
        self, git_repo_with_adr: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test run_hook successfully calls pre-push handler."""
        from unittest.mock import patch

        from git_adr.commands.hook import run_hook

        os.chdir(git_repo_with_adr)

        # Mock _handle_pre_push to avoid needing a real remote
        with patch("git_adr.commands.hook._handle_pre_push") as mock_handler:
            mock_handler.return_value = None
            run_hook("pre-push", "origin")
            # Should have called the handler
            mock_handler.assert_called_once_with("origin")

    def test_run_hook_exception_handling(
        self, git_repo_with_adr: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test run_hook handles exceptions from handler."""
        from unittest.mock import patch

        from git_adr.commands.hook import run_hook

        os.chdir(git_repo_with_adr)

        # Mock _handle_pre_push to raise an exception
        with patch("git_adr.commands.hook._handle_pre_push") as mock_handler:
            mock_handler.side_effect = RuntimeError("Test error")
            with pytest.raises(SystemExit) as excinfo:
                run_hook("pre-push", "origin")
            assert excinfo.value.code == 1

        captured = capsys.readouterr()
        assert "Hook error" in captured.err or "error" in captured.err.lower()
