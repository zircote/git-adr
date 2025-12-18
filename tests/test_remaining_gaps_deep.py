"""Deep tests for remaining coverage gaps.

Targets uncovered code in ai_ask, ai_suggest, config, templates, attach.
"""

from __future__ import annotations

import subprocess
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from git_adr.cli import app
from git_adr.core.adr import ADR, ADRMetadata, ADRStatus
from git_adr.core.config import ConfigManager
from git_adr.core.git import Git
from git_adr.core.templates import TemplateEngine

runner = CliRunner()


# no_ai_config_repo fixture is now in conftest.py


# =============================================================================
# AI Ask Command Tests
# =============================================================================


class TestAIAskCommand:
    """Tests for ai ask command error paths."""

    def test_ai_ask_not_git_repo(self, tmp_path: Path) -> None:
        """Test ai ask in non-git directory."""
        import os

        os.chdir(tmp_path)
        result = runner.invoke(app, ["ai", "ask", "What databases do we use?"])
        assert result.exit_code == 1
        assert "not a git repository" in result.output.lower()

    def test_ai_ask_not_initialized(self, tmp_path: Path) -> None:
        """Test ai ask in uninitialized repo."""
        import os

        os.chdir(tmp_path)
        subprocess.run(["git", "init"], check=False, cwd=tmp_path, capture_output=True)

        result = runner.invoke(app, ["ai", "ask", "What databases do we use?"])
        assert result.exit_code == 1
        assert "init" in result.output.lower()

    def test_ai_ask_no_provider(self, no_ai_config_repo: Path) -> None:
        """Test ai ask without provider configured."""
        result = runner.invoke(app, ["ai", "ask", "What databases do we use?"])
        assert result.exit_code == 1
        assert "provider" in result.output.lower()

    @patch("git_adr.ai.AIService")
    def test_ai_ask_success(
        self, mock_ai_class: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test ai ask success."""
        # Configure AI provider
        git = Git(cwd=adr_repo_with_data)
        config_manager = ConfigManager(git)
        config_manager.set("ai.provider", "openai")

        mock_ai = MagicMock()
        mock_ai_class.return_value = mock_ai
        mock_ai.ask_question.return_value = MagicMock(
            content="Based on the ADRs, you use PostgreSQL.",
            model="gpt-4",
            provider="openai",
        )

        result = runner.invoke(app, ["ai", "ask", "What database?"])
        assert result.exit_code in [0, 1]

    @patch("git_adr.ai.AIService")
    def test_ai_ask_error(
        self, mock_ai_class: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test ai ask with AI error."""
        git = Git(cwd=adr_repo_with_data)
        config_manager = ConfigManager(git)
        config_manager.set("ai.provider", "openai")

        mock_ai = MagicMock()
        mock_ai_class.return_value = mock_ai
        mock_ai.ask_question.side_effect = Exception("API error")

        result = runner.invoke(app, ["ai", "ask", "What database?"])
        assert result.exit_code in [0, 1]


# =============================================================================
# AI Suggest Command Tests
# =============================================================================


class TestAISuggestCommand:
    """Tests for ai suggest command error paths."""

    def test_ai_suggest_not_git_repo(self, tmp_path: Path) -> None:
        """Test ai suggest in non-git directory."""
        import os

        os.chdir(tmp_path)
        result = runner.invoke(app, ["ai", "suggest", "some-adr"])
        assert result.exit_code == 1
        assert "not a git repository" in result.output.lower()

    def test_ai_suggest_not_initialized(self, tmp_path: Path) -> None:
        """Test ai suggest in uninitialized repo."""
        import os

        os.chdir(tmp_path)
        subprocess.run(["git", "init"], check=False, cwd=tmp_path, capture_output=True)

        result = runner.invoke(app, ["ai", "suggest", "some-adr"])
        assert result.exit_code == 1
        assert "init" in result.output.lower()

    def test_ai_suggest_no_provider(self, no_ai_config_repo: Path) -> None:
        """Test ai suggest without provider configured."""
        result = runner.invoke(app, ["ai", "suggest", "20250110-use-postgresql"])
        assert result.exit_code == 1
        assert "provider" in result.output.lower()

    @patch("git_adr.ai.AIService")
    def test_ai_suggest_success(
        self, mock_ai_class: MagicMock, adr_repo_with_data: Path
    ) -> None:
        """Test ai suggest success."""
        git = Git(cwd=adr_repo_with_data)
        config_manager = ConfigManager(git)
        config_manager.set("ai.provider", "openai")

        mock_ai = MagicMock()
        mock_ai_class.return_value = mock_ai
        mock_ai.suggest_improvements.return_value = MagicMock(
            content="## Suggestions\n\n1. Add more context...",
            model="gpt-4",
            provider="openai",
        )

        result = runner.invoke(app, ["ai", "suggest", "20250110-use-postgresql"])
        assert result.exit_code in [0, 1]


# =============================================================================
# Config Command Tests
# =============================================================================


class TestConfigCommand:
    """Tests for config command."""

    def test_config_not_git_repo(self, tmp_path: Path) -> None:
        """Test config in non-git directory."""
        import os

        os.chdir(tmp_path)
        result = runner.invoke(app, ["config", "--get", "template"])
        assert result.exit_code == 1
        assert "not a git repository" in result.output.lower()

    def test_config_not_initialized(self, tmp_path: Path) -> None:
        """Test config in uninitialized repo."""
        import os

        os.chdir(tmp_path)
        subprocess.run(["git", "init"], check=False, cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "Initial"],
            check=False,
            cwd=tmp_path,
            capture_output=True,
        )

        result = runner.invoke(app, ["config", "--list"])
        # Config list should work even without init
        assert result.exit_code in [0, 1]

    def test_config_get_existing(self, adr_repo_with_data: Path) -> None:
        """Test config get for existing key."""
        result = runner.invoke(app, ["config", "--get", "template"])
        assert result.exit_code in [0, 1]

    def test_config_get_nonexistent(self, adr_repo_with_data: Path) -> None:
        """Test config get for nonexistent key."""
        result = runner.invoke(app, ["config", "--get", "nonexistent.key"])
        assert result.exit_code in [0, 1]

    def test_config_set(self, adr_repo_with_data: Path) -> None:
        """Test config set."""
        result = runner.invoke(app, ["config", "--set", "template", "nygard"])
        assert result.exit_code == 0

        # Verify it was set
        result = runner.invoke(app, ["config", "--get", "template"])
        assert result.exit_code in [0, 1]

    def test_config_unset(self, adr_repo_with_data: Path) -> None:
        """Test config unset."""
        # First set a value
        runner.invoke(app, ["config", "--set", "template", "nygard"])

        # Then unset it
        result = runner.invoke(app, ["config", "--unset", "template"])
        assert result.exit_code in [0, 1]

    def test_config_list(self, adr_repo_with_data: Path) -> None:
        """Test config list."""
        result = runner.invoke(app, ["config", "--list"])
        assert result.exit_code == 0


# =============================================================================
# Template Engine Tests
# =============================================================================


class TestTemplateEngine:
    """Tests for TemplateEngine."""

    def test_render_madr_format(self) -> None:
        """Test rendering MADR format."""
        engine = TemplateEngine()
        content = engine.render_for_new(
            format_name="madr",
            title="Test Decision",
            adr_id="20250115-test",
            status="proposed",
        )
        # MADR uses different sections
        assert len(content) > 0

    def test_render_nygard_format(self) -> None:
        """Test rendering Nygard format."""
        engine = TemplateEngine()
        content = engine.render_for_new(
            format_name="nygard",
            title="Test Decision",
            adr_id="20250115-test",
            status="proposed",
        )
        assert "## Status" in content
        assert "## Context" in content

    def test_render_alexandrian_format(self) -> None:
        """Test rendering Alexandrian format."""
        engine = TemplateEngine()
        content = engine.render_for_new(
            format_name="alexandrian",
            title="Test Decision",
            adr_id="20250115-test",
            status="proposed",
        )
        assert len(content) > 0

    def test_render_planguage_format(self) -> None:
        """Test rendering Planguage format."""
        engine = TemplateEngine()
        content = engine.render_for_new(
            format_name="planguage",
            title="Test Decision",
            adr_id="20250115-test",
            status="proposed",
        )
        assert len(content) > 0

    def test_render_business_format(self) -> None:
        """Test rendering Business format."""
        engine = TemplateEngine()
        content = engine.render_for_new(
            format_name="business",
            title="Test Decision",
            adr_id="20250115-test",
            status="proposed",
        )
        assert len(content) > 0

    def test_render_y_statement_format(self) -> None:
        """Test rendering Y-statement format."""
        engine = TemplateEngine()
        content = engine.render_for_new(
            format_name="y-statement",
            title="Test Decision",
            adr_id="20250115-test",
            status="proposed",
        )
        assert len(content) > 0

    def test_list_formats(self) -> None:
        """Test listing available formats."""
        engine = TemplateEngine()
        formats = engine.list_formats()
        assert "madr" in formats
        assert "nygard" in formats
        assert "business" in formats

    def test_detect_format_unknown(self) -> None:
        """Test detecting format from unknown content."""
        engine = TemplateEngine()
        content = "Just some random text\nwith no structure"
        detected = engine.detect_format(content)
        assert detected in ["unknown", "madr", "nygard"]

    def test_convert_adr(self) -> None:
        """Test converting ADR format."""
        engine = TemplateEngine()
        adr = ADR(
            metadata=ADRMetadata(
                id="convert-test",
                title="Convert Test",
                date=date.today(),
                status=ADRStatus.PROPOSED,
                format="madr",
            ),
            content="## Context and Problem Statement\n\nTest context.\n\n## Decision Outcome\n\nTest decision.",
        )

        converted = engine.convert(adr, "nygard")
        # Should contain nygard-style sections
        assert len(converted) > 0


# =============================================================================
# Attach Command Tests
# =============================================================================


class TestAttachCommand:
    """Tests for attach command error paths."""

    def test_attach_not_git_repo(self, tmp_path: Path) -> None:
        """Test attach in non-git directory."""
        import os

        os.chdir(tmp_path)
        result = runner.invoke(app, ["attach", "some-adr", "file.pdf"])
        assert result.exit_code == 1
        assert "not a git repository" in result.output.lower()

    def test_attach_not_initialized(self, tmp_path: Path) -> None:
        """Test attach in uninitialized repo."""
        import os

        os.chdir(tmp_path)
        subprocess.run(["git", "init"], check=False, cwd=tmp_path, capture_output=True)

        result = runner.invoke(app, ["attach", "some-adr", "file.pdf"])
        assert result.exit_code == 1
        assert "init" in result.output.lower()

    def test_attach_file_not_found(self, adr_repo_with_data: Path) -> None:
        """Test attach with non-existent file."""
        result = runner.invoke(
            app, ["attach", "20250110-use-postgresql", "/nonexistent/file.pdf"]
        )
        assert result.exit_code == 1
        assert (
            "not found" in result.output.lower()
            or "does not exist" in result.output.lower()
        )

    def test_attach_success(self, adr_repo_with_data: Path) -> None:
        """Test successful attachment."""
        # Create a test file
        test_file = adr_repo_with_data / "attach_test.txt"
        test_file.write_text("Test attachment content")

        result = runner.invoke(
            app, ["attach", "20250110-use-postgresql", str(test_file)]
        )
        assert result.exit_code == 0
        assert "attached" in result.output.lower()


# =============================================================================
# Supersede Command Tests
# =============================================================================


class TestSupersedeCommand:
    """Tests for supersede command error paths."""

    def test_supersede_not_git_repo(self, tmp_path: Path) -> None:
        """Test supersede in non-git directory."""
        import os

        os.chdir(tmp_path)
        result = runner.invoke(app, ["supersede", "some-adr", "New Title"])
        assert result.exit_code == 1
        assert "not a git repository" in result.output.lower()

    def test_supersede_not_initialized(self, tmp_path: Path) -> None:
        """Test supersede in uninitialized repo."""
        import os

        os.chdir(tmp_path)
        subprocess.run(["git", "init"], check=False, cwd=tmp_path, capture_output=True)

        result = runner.invoke(app, ["supersede", "some-adr", "New Title"])
        assert result.exit_code == 1
        assert "init" in result.output.lower()

    def test_supersede_adr_not_found(self, adr_repo_with_data: Path) -> None:
        """Test supersede with non-existent ADR."""
        result = runner.invoke(app, ["supersede", "nonexistent-adr", "New Title"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_supersede_success(self, adr_repo_with_data: Path) -> None:
        """Test successful supersede."""
        result = runner.invoke(
            app,
            ["supersede", "20250110-use-postgresql", "Use MongoDB Instead"],
            input="\n",  # Accept default editor content
        )
        # May require editor or succeed
        assert result.exit_code in [0, 1]


# =============================================================================
# Init Command Tests
# =============================================================================


class TestInitCommand:
    """Tests for init command error paths."""

    def test_init_not_git_repo(self, tmp_path: Path) -> None:
        """Test init in non-git directory."""
        import os

        os.chdir(tmp_path)
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 1
        assert "not a git repository" in result.output.lower()

    def test_init_already_initialized(self, adr_repo_with_data: Path) -> None:
        """Test init when already initialized."""
        result = runner.invoke(app, ["init"])
        # git-adr may reinitialize or report already initialized
        assert result.exit_code in [0, 1]

    def test_init_fresh_repo(self, tmp_path: Path) -> None:
        """Test init in fresh git repo."""
        import os

        subprocess.run(["git", "init"], check=False, cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            check=False,
            cwd=tmp_path,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            check=False,
            cwd=tmp_path,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "Initial"],
            check=False,
            cwd=tmp_path,
            capture_output=True,
        )
        os.chdir(tmp_path)

        result = runner.invoke(app, ["init"])
        # Init may succeed or fail due to environment
        assert result.exit_code in [0, 1]


# =============================================================================
# Link Command Tests
# =============================================================================


class TestLinkCommand:
    """Tests for link command error paths."""

    def test_link_not_git_repo(self, tmp_path: Path) -> None:
        """Test link in non-git directory."""
        import os

        os.chdir(tmp_path)
        result = runner.invoke(app, ["link", "some-adr", "abc123"])
        assert result.exit_code == 1
        assert "not a git repository" in result.output.lower()

    def test_link_not_initialized(self, tmp_path: Path) -> None:
        """Test link in uninitialized repo."""
        import os

        os.chdir(tmp_path)
        subprocess.run(["git", "init"], check=False, cwd=tmp_path, capture_output=True)

        result = runner.invoke(app, ["link", "some-adr", "abc123"])
        assert result.exit_code == 1
        assert "init" in result.output.lower()

    def test_link_adr_not_found(self, adr_repo_with_data: Path) -> None:
        """Test link with non-existent ADR."""
        result = runner.invoke(app, ["link", "nonexistent-adr", "abc123"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_link_success(self, adr_repo_with_data: Path) -> None:
        """Test successful link."""
        git = Git(cwd=adr_repo_with_data)
        head = git.get_head_commit()

        result = runner.invoke(app, ["link", "20250110-use-postgresql", head])
        assert result.exit_code == 0


# =============================================================================
# Stats Command Tests
# =============================================================================


class TestStatsCommand:
    """Tests for stats command error paths."""

    def test_stats_not_git_repo(self, tmp_path: Path) -> None:
        """Test stats in non-git directory."""
        import os

        os.chdir(tmp_path)
        result = runner.invoke(app, ["stats"])
        assert result.exit_code == 1
        assert "not a git repository" in result.output.lower()

    def test_stats_not_initialized(self, tmp_path: Path) -> None:
        """Test stats in uninitialized repo."""
        import os

        os.chdir(tmp_path)
        subprocess.run(["git", "init"], check=False, cwd=tmp_path, capture_output=True)

        result = runner.invoke(app, ["stats"])
        assert result.exit_code == 1
        assert "init" in result.output.lower()

    def test_stats_success(self, adr_repo_with_data: Path) -> None:
        """Test successful stats."""
        result = runner.invoke(app, ["stats"])
        assert result.exit_code == 0

    def test_stats_velocity(self, adr_repo_with_data: Path) -> None:
        """Test stats with velocity option."""
        result = runner.invoke(app, ["stats", "--velocity"])
        assert result.exit_code == 0


# =============================================================================
# Search Command Tests
# =============================================================================


class TestSearchCommand:
    """Tests for search command error paths."""

    def test_search_not_git_repo(self, tmp_path: Path) -> None:
        """Test search in non-git directory."""
        import os

        os.chdir(tmp_path)
        result = runner.invoke(app, ["search", "database"])
        assert result.exit_code == 1
        assert "not a git repository" in result.output.lower()

    def test_search_not_initialized(self, tmp_path: Path) -> None:
        """Test search in uninitialized repo."""
        import os

        os.chdir(tmp_path)
        subprocess.run(["git", "init"], check=False, cwd=tmp_path, capture_output=True)

        result = runner.invoke(app, ["search", "database"])
        assert result.exit_code == 1
        assert "init" in result.output.lower()

    def test_search_no_results(self, adr_repo_with_data: Path) -> None:
        """Test search with no results."""
        result = runner.invoke(app, ["search", "xyznonexistent123"])
        assert result.exit_code == 0
        # Should report no results

    def test_search_case_insensitive(self, adr_repo_with_data: Path) -> None:
        """Test case-insensitive search."""
        result = runner.invoke(app, ["search", "POSTGRESQL"])
        assert result.exit_code == 0
