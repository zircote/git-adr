"""Unit tests for init command interactive features.

Tests for TTY detection, template selection, and interactive prompts.
"""

from __future__ import annotations

from unittest.mock import patch


class TestIsInteractive:
    """Tests for _is_interactive() TTY detection."""

    def test_is_interactive_with_tty(self) -> None:
        """Test returns True when both stdin and stdout are TTY."""
        from git_adr.commands.init import _is_interactive

        with (
            patch("sys.stdin.isatty", return_value=True),
            patch("sys.stdout.isatty", return_value=True),
        ):
            assert _is_interactive() is True

    def test_is_interactive_stdin_not_tty(self) -> None:
        """Test returns False when stdin is not TTY (piped input)."""
        from git_adr.commands.init import _is_interactive

        with (
            patch("sys.stdin.isatty", return_value=False),
            patch("sys.stdout.isatty", return_value=True),
        ):
            assert _is_interactive() is False

    def test_is_interactive_stdout_not_tty(self) -> None:
        """Test returns False when stdout is not TTY (redirected output)."""
        from git_adr.commands.init import _is_interactive

        with (
            patch("sys.stdin.isatty", return_value=True),
            patch("sys.stdout.isatty", return_value=False),
        ):
            assert _is_interactive() is False

    def test_is_interactive_neither_tty(self) -> None:
        """Test returns False when neither stdin nor stdout is TTY."""
        from git_adr.commands.init import _is_interactive

        with (
            patch("sys.stdin.isatty", return_value=False),
            patch("sys.stdout.isatty", return_value=False),
        ):
            assert _is_interactive() is False


class TestPromptForTemplate:
    """Tests for _prompt_for_template() interactive selection."""

    def test_prompt_accepts_template_name(self) -> None:
        """Test that template name is accepted directly."""
        from git_adr.commands.init import _prompt_for_template

        with patch("typer.prompt", return_value="nygard"):
            result = _prompt_for_template()
            assert result == "nygard"

    def test_prompt_accepts_number_selection(self) -> None:
        """Test that numeric selection works."""
        from git_adr.commands.init import _prompt_for_template

        # "2" should select nygard (second in the list)
        with patch("typer.prompt", return_value="2"):
            result = _prompt_for_template()
            assert result == "nygard"

    def test_prompt_defaults_to_madr(self) -> None:
        """Test that empty input defaults to madr."""
        from git_adr.commands.init import _prompt_for_template

        with patch("typer.prompt", return_value="madr"):
            result = _prompt_for_template()
            assert result == "madr"

    def test_prompt_handles_invalid_number(self) -> None:
        """Test that invalid number falls back to madr."""
        from git_adr.commands.init import _prompt_for_template

        with patch("typer.prompt", return_value="99"):
            result = _prompt_for_template()
            assert result == "madr"

    def test_prompt_handles_unknown_template(self) -> None:
        """Test that unknown template name falls back to madr."""
        from git_adr.commands.init import _prompt_for_template

        with patch("typer.prompt", return_value="unknown"):
            result = _prompt_for_template()
            assert result == "madr"


class TestHandleHooksInstallation:
    """Tests for _handle_hooks_installation() logic."""

    def test_explicit_install_hooks_true(self) -> None:
        """Test explicit --install-hooks flag installs hooks."""
        from git_adr.commands.init import _handle_hooks_installation

        with patch("git_adr.hooks.get_hooks_manager") as mock_manager:
            mock_manager.return_value.install_all.return_value = ["pre-push: installed"]
            result = _handle_hooks_installation(
                install_hooks=True, interactive=False, force=False
            )
            assert result is True
            mock_manager.return_value.install_all.assert_called_once()

    def test_explicit_install_hooks_false(self) -> None:
        """Test explicit --no-install-hooks flag skips installation."""
        from git_adr.commands.init import _handle_hooks_installation

        with patch("git_adr.hooks.get_hooks_manager") as mock_manager:
            result = _handle_hooks_installation(
                install_hooks=False, interactive=True, force=False
            )
            assert result is False
            mock_manager.assert_not_called()

    def test_prompt_when_interactive_and_none(self) -> None:
        """Test prompts user when interactive and no explicit flag."""
        from git_adr.commands.init import _handle_hooks_installation

        with (
            patch(
                "git_adr.commands.init.typer.confirm", return_value=True
            ) as mock_confirm,
            patch("git_adr.hooks.get_hooks_manager") as mock_manager,
        ):
            mock_manager.return_value.install_all.return_value = ["pre-push: installed"]
            result = _handle_hooks_installation(
                install_hooks=None, interactive=True, force=False
            )
            assert result is True
            mock_confirm.assert_called_once()

    def test_no_prompt_when_non_interactive(self) -> None:
        """Test no prompt when non-interactive mode."""
        from git_adr.commands.init import _handle_hooks_installation

        with patch("git_adr.commands.init.typer.confirm") as mock_confirm:
            result = _handle_hooks_installation(
                install_hooks=None, interactive=False, force=False
            )
            assert result is False
            mock_confirm.assert_not_called()


class TestHandleGithubCiSetup:
    """Tests for _handle_github_ci_setup() logic."""

    def test_explicit_setup_ci_true(self) -> None:
        """Test explicit --setup-github-ci flag generates workflows."""
        from git_adr.commands.init import _handle_github_ci_setup

        with patch("git_adr.commands.ci.run_ci_github") as mock_ci:
            result = _handle_github_ci_setup(setup_github_ci=True, interactive=False)
            assert result is True
            mock_ci.assert_called_once_with(sync=True, validate=True)

    def test_explicit_setup_ci_false(self) -> None:
        """Test explicit --no-setup-github-ci flag skips generation."""
        from git_adr.commands.init import _handle_github_ci_setup

        with patch("git_adr.commands.ci.run_ci_github") as mock_ci:
            result = _handle_github_ci_setup(setup_github_ci=False, interactive=True)
            assert result is False
            mock_ci.assert_not_called()

    def test_prompt_when_interactive_and_none(self) -> None:
        """Test prompts user when interactive and no explicit flag."""
        from git_adr.commands.init import _handle_github_ci_setup

        with (
            patch(
                "git_adr.commands.init.typer.confirm", return_value=True
            ) as mock_confirm,
            patch("git_adr.commands.ci.run_ci_github") as mock_ci,
        ):
            result = _handle_github_ci_setup(setup_github_ci=None, interactive=True)
            assert result is True
            mock_confirm.assert_called_once()
            mock_ci.assert_called_once()

    def test_no_prompt_when_non_interactive(self) -> None:
        """Test no prompt when non-interactive mode."""
        from git_adr.commands.init import _handle_github_ci_setup

        with patch("git_adr.commands.init.typer.confirm") as mock_confirm:
            result = _handle_github_ci_setup(setup_github_ci=None, interactive=False)
            assert result is False
            mock_confirm.assert_not_called()
