"""Tests for shell completion command."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from git_adr.cli import app

runner = CliRunner()


class TestCompletionCommand:
    """Tests for completion command."""

    def test_completion_help(self) -> None:
        """Test completion --help."""
        result = runner.invoke(app, ["completion", "--help"])
        assert result.exit_code == 0
        assert "bash" in result.output.lower()
        assert "zsh" in result.output.lower()

    def test_completion_bash(self) -> None:
        """Test bash completion script generation."""
        result = runner.invoke(app, ["completion", "bash"])
        assert result.exit_code == 0
        # Check for bash completion markers
        assert "_git_adr_completion" in result.output or "compgen" in result.output

    def test_completion_zsh(self) -> None:
        """Test zsh completion script generation."""
        result = runner.invoke(app, ["completion", "zsh"])
        assert result.exit_code == 0
        # Zsh completion should have some content
        assert len(result.output) > 0

    def test_completion_fish(self) -> None:
        """Test fish completion script generation."""
        result = runner.invoke(app, ["completion", "fish"])
        assert result.exit_code == 0
        # Fish completion should have some content
        assert len(result.output) > 0

    def test_completion_powershell(self) -> None:
        """Test PowerShell completion script generation."""
        result = runner.invoke(app, ["completion", "powershell"])
        assert result.exit_code == 0
        # PowerShell completion should have some content
        assert len(result.output) > 0

    def test_completion_invalid_shell(self) -> None:
        """Test completion with invalid shell."""
        result = runner.invoke(app, ["completion", "invalid"])
        assert result.exit_code != 0
        assert "invalid" in result.output.lower()

    def test_completion_case_insensitive(self) -> None:
        """Test completion with uppercase shell name."""
        result = runner.invoke(app, ["completion", "BASH"])
        assert result.exit_code == 0


class TestCompletionInstall:
    """Tests for completion installation."""

    def test_completion_fish_install(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test fish completion installation."""
        # Create fake fish completions dir
        fish_dir = tmp_path / ".config" / "fish" / "completions"

        # Monkeypatch Path.home() to return tmp_path
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = runner.invoke(app, ["completion", "fish", "--install"])
        assert result.exit_code == 0
        assert "installed" in result.output.lower()

        # Check file was created
        completion_file = fish_dir / "git-adr.fish"
        assert completion_file.exists()

    def test_completion_bash_install(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test bash completion installation."""
        # Create fake bashrc
        bashrc = tmp_path / ".bashrc"
        bashrc.touch()

        # Monkeypatch expanduser to return our tmp path
        def fake_expanduser(path):
            if str(path) == "~/.bashrc":
                return bashrc
            return Path(str(path).replace("~", str(tmp_path)))

        monkeypatch.setattr(Path, "expanduser", fake_expanduser)

        result = runner.invoke(app, ["completion", "bash", "--install"])
        assert result.exit_code == 0
        assert "installed" in result.output.lower()

    def test_completion_bash_already_installed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test bash completion when already installed."""
        # Create fake bashrc with existing completion
        bashrc = tmp_path / ".bashrc"
        bashrc.write_text("# git-adr completion\nexisting completion")

        def fake_expanduser(path):
            if str(path) == "~/.bashrc":
                return bashrc
            return Path(str(path).replace("~", str(tmp_path)))

        monkeypatch.setattr(Path, "expanduser", fake_expanduser)

        result = runner.invoke(app, ["completion", "bash", "--install"])
        assert result.exit_code == 0
        assert "already installed" in result.output.lower()

    def test_completion_zsh_install(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test zsh completion installation."""
        # Create fake zshrc
        zshrc = tmp_path / ".zshrc"
        zshrc.touch()

        def fake_expanduser(path):
            if str(path) == "~/.zshrc":
                return zshrc
            return Path(str(path).replace("~", str(tmp_path)))

        monkeypatch.setattr(Path, "expanduser", fake_expanduser)

        result = runner.invoke(app, ["completion", "zsh", "--install"])
        assert result.exit_code == 0
        assert "installed" in result.output.lower()

    def test_completion_powershell_install(self) -> None:
        """Test PowerShell completion installation shows manual setup message."""
        result = runner.invoke(app, ["completion", "powershell", "--install"])
        assert result.exit_code == 0
        assert "manual" in result.output.lower() or "setup" in result.output.lower()
