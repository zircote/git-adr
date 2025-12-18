"""Deep tests for import_.py remaining gaps.

Targets specific uncovered lines in import_.py.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from git_adr.cli import app
from git_adr.core.git import Git, GitError

runner = CliRunner()


class TestImportNotGitRepo:
    """Tests for import in non-git directory (lines 53-54)."""

    def test_import_not_git_repo(self, tmp_path: Path) -> None:
        """Test import in non-git directory."""
        import os

        os.chdir(tmp_path)
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test ADR\n")

        result = runner.invoke(app, ["import", str(test_file)])
        assert result.exit_code == 1
        assert "not a git repository" in result.output.lower()


class TestImportNotInitialized:
    """Tests for import in uninitialized repo (lines 60-63)."""

    def test_import_not_initialized(self, tmp_path: Path) -> None:
        """Test import in uninitialized repo."""
        import os

        os.chdir(tmp_path)
        subprocess.run(["git", "init"], check=False, cwd=tmp_path, capture_output=True)

        test_file = tmp_path / "test.md"
        test_file.write_text("# Test ADR\n")

        result = runner.invoke(app, ["import", str(test_file)])
        assert result.exit_code == 1
        assert "init" in result.output.lower()


class TestImportNoAdrsFound:
    """Tests for import with no ADRs found (lines 87-88)."""

    def test_import_empty_json(self, adr_repo_with_data: Path) -> None:
        """Test import with empty JSON array."""
        json_file = adr_repo_with_data / "empty.json"
        json_file.write_text('{"adrs": []}')

        result = runner.invoke(app, ["import", str(json_file)])
        assert result.exit_code == 0
        assert "no adr" in result.output.lower()


class TestImportAlreadyExists:
    """Tests for import when ADR already exists (lines 108-111)."""

    def test_import_existing_adr_skipped(self, adr_repo_with_data: Path) -> None:
        """Test import skips existing ADR."""
        # Create JSON with existing ADR ID
        json_file = adr_repo_with_data / "existing.json"
        json_file.write_text(
            json.dumps(
                {
                    "adrs": [
                        {
                            "id": "20250110-use-postgresql",
                            "title": "Use PostgreSQL Duplicate",
                            "date": "2025-01-10",
                            "status": "proposed",
                            "content": "Duplicate content",
                        }
                    ]
                }
            )
        )

        result = runner.invoke(app, ["import", str(json_file)])
        assert result.exit_code == 0
        assert (
            "skipping" in result.output.lower()
            or "already exists" in result.output.lower()
        )


class TestImportGitError:
    """Tests for import with GitError (lines 121-122)."""

    def test_import_git_error(self, adr_repo_with_data: Path) -> None:
        """Test import when GitError is raised."""
        json_file = adr_repo_with_data / "test.json"
        json_file.write_text(
            json.dumps(
                {
                    "adrs": [
                        {
                            "id": "new-adr-test",
                            "title": "New ADR",
                            "date": "2025-01-15",
                            "status": "draft",
                            "content": "Content",
                        }
                    ]
                }
            )
        )

        with patch("git_adr.commands._shared.get_git") as mock_get_git:
            mock_git = MagicMock()
            mock_get_git.return_value = mock_git
            mock_git.is_repository.return_value = True

            with patch("git_adr.commands._shared.ConfigManager") as mock_cm:
                mock_cm_instance = MagicMock()
                mock_cm.return_value = mock_cm_instance
                mock_cm_instance.get.return_value = True
                mock_cm_instance.load.side_effect = GitError(
                    "Config error", ["git", "config"], 1
                )

                result = runner.invoke(app, ["import", str(json_file)])
                assert result.exit_code == 1
                assert "error" in result.output.lower()


class TestImportFormatDetection:
    """Tests for format detection."""

    def test_detect_json_format(self, adr_repo_with_data: Path) -> None:
        """Test auto-detecting JSON format (line 129)."""
        json_file = adr_repo_with_data / "test.json"
        json_file.write_text(
            json.dumps(
                {
                    "adrs": [
                        {
                            "id": "json-test",
                            "title": "JSON Test",
                            "date": "2025-01-15",
                            "status": "draft",
                            "content": "Content",
                        }
                    ]
                }
            )
        )

        result = runner.invoke(app, ["import", str(json_file)])
        assert result.exit_code == 0
        # Should detect as JSON format
        if "detected format" in result.output.lower():
            assert "json" in result.output.lower()

    def test_detect_adr_tools_format(self, adr_repo_with_data: Path) -> None:
        """Test auto-detecting adr-tools format (line 137)."""
        adr_dir = adr_repo_with_data / "adr-tools-dir"
        adr_dir.mkdir()

        # Create adr-tools style files
        (adr_dir / "0001-use-docker.md").write_text("""# 1. Use Docker

## Status

Accepted

## Date

2025-01-15

## Context

We need containerization.

## Decision

Use Docker.

## Consequences

Need Docker expertise.
""")

        result = runner.invoke(app, ["import", str(adr_dir)])
        assert result.exit_code == 0


class TestImportMarkdownParsing:
    """Tests for markdown parsing edge cases."""

    def test_import_markdown_date_string(self, adr_repo_with_data: Path) -> None:
        """Test markdown import with string date (line 160)."""
        md_file = adr_repo_with_data / "test-date.md"
        md_file.write_text("""---
title: Date String Test
date: "2025-01-15"
status: draft
---

# Date String Test

Content.
""")

        result = runner.invoke(app, ["import", str(md_file)])
        assert result.exit_code == 0

    def test_import_markdown_datetime_date(self, adr_repo_with_data: Path) -> None:
        """Test markdown import with datetime date (lines 161-164)."""

        md_file = adr_repo_with_data / "test-datetime.md"
        md_file.write_text("""---
title: DateTime Test
date: 2025-01-15T12:30:00
status: draft
---

# DateTime Test

Content.
""")

        result = runner.invoke(app, ["import", str(md_file)])
        assert result.exit_code == 0

    def test_import_markdown_no_date(self, adr_repo_with_data: Path) -> None:
        """Test markdown import with no date (line 166)."""
        md_file = adr_repo_with_data / "test-no-date.md"
        md_file.write_text("""---
title: No Date Test
status: draft
---

# No Date Test

Content.
""")

        result = runner.invoke(app, ["import", str(md_file)])
        assert result.exit_code == 0

    def test_import_markdown_invalid_status(self, adr_repo_with_data: Path) -> None:
        """Test markdown import with invalid status (lines 176-177)."""
        md_file = adr_repo_with_data / "test-invalid-status.md"
        md_file.write_text("""---
title: Invalid Status Test
date: 2025-01-15
status: totally-invalid-status
---

# Invalid Status Test

Content.
""")

        result = runner.invoke(app, ["import", str(md_file)])
        # Should succeed, defaulting to draft
        assert result.exit_code == 0

    def test_import_markdown_parse_error(self, adr_repo_with_data: Path) -> None:
        """Test markdown import with parse error (lines 193-194)."""
        md_file = adr_repo_with_data / "test-parse-error.md"
        # Write malformed frontmatter
        md_file.write_text("""---
title: [Invalid YAML
date: not-a-date
---

# Parse Error Test
""")

        result = runner.invoke(app, ["import", str(md_file)])
        # Should warn but continue
        assert result.exit_code == 0


class TestImportJson:
    """Tests for JSON import edge cases."""

    def test_import_json_no_date(self, adr_repo_with_data: Path) -> None:
        """Test JSON import with no date (line 212)."""
        json_file = adr_repo_with_data / "no-date.json"
        json_file.write_text(
            json.dumps(
                {
                    "id": "no-date-test",
                    "title": "No Date Test",
                    "status": "draft",
                    "content": "Content",
                }
            )
        )

        result = runner.invoke(app, ["import", str(json_file)])
        assert result.exit_code == 0

    def test_import_json_invalid_status(self, adr_repo_with_data: Path) -> None:
        """Test JSON import with invalid status (lines 222-223)."""
        json_file = adr_repo_with_data / "invalid-status.json"
        json_file.write_text(
            json.dumps(
                {
                    "id": "invalid-status-json",
                    "title": "Invalid Status Test",
                    "date": "2025-01-15",
                    "status": "not-a-real-status",
                    "content": "Content",
                }
            )
        )

        result = runner.invoke(app, ["import", str(json_file)])
        # Should succeed, defaulting to draft
        assert result.exit_code == 0

    def test_import_json_with_linked_commits(self, adr_repo_with_data: Path) -> None:
        """Test JSON import with linked commits."""
        git = Git(cwd=adr_repo_with_data)
        head = git.get_head_commit()

        json_file = adr_repo_with_data / "linked.json"
        json_file.write_text(
            json.dumps(
                {
                    "id": "linked-commits-test",
                    "title": "Linked Commits Test",
                    "date": "2025-01-15",
                    "status": "accepted",
                    "content": "Content",
                    "linked_commits": [head],
                }
            )
        )

        result = runner.invoke(app, ["import", str(json_file)])
        assert result.exit_code == 0

    def test_import_json_with_supersedes(self, adr_repo_with_data: Path) -> None:
        """Test JSON import with supersedes relationship."""
        json_file = adr_repo_with_data / "supersedes.json"
        json_file.write_text(
            json.dumps(
                {
                    "id": "supersedes-test",
                    "title": "Supersedes Test",
                    "date": "2025-01-15",
                    "status": "accepted",
                    "content": "Content",
                    "supersedes": "old-adr-id",
                }
            )
        )

        result = runner.invoke(app, ["import", str(json_file)])
        assert result.exit_code == 0


class TestImportAdrTools:
    """Tests for adr-tools format import."""

    def test_import_adr_tools_no_match(self, adr_repo_with_data: Path) -> None:
        """Test adr-tools import with non-matching files (line 253)."""
        adr_dir = adr_repo_with_data / "adr-tools-no-match"
        adr_dir.mkdir()

        # File doesn't match NNNN-slug.md pattern - but will be detected as markdown
        (adr_dir / "readme.md").write_text("# README\n\nJust a readme.")
        (adr_dir / "some-file.md").write_text("# Some File\n\nNot an ADR.")

        # Force adr-tools format which won't match these files
        result = runner.invoke(app, ["import", str(adr_dir), "--format", "adr-tools"])
        assert result.exit_code == 0
        # With adr-tools format, files that don't match NNNN-slug.md are skipped
        if "no adr" in result.output.lower():
            assert True
        else:
            # May import 0 or report something else
            assert result.exit_code == 0

    def test_import_adr_tools_with_date(self, adr_repo_with_data: Path) -> None:
        """Test adr-tools import extracting date (line 278)."""
        adr_dir = adr_repo_with_data / "adr-tools-date"
        adr_dir.mkdir()

        (adr_dir / "0001-use-kubernetes.md").write_text("""# 1. Use Kubernetes

## Status

Accepted

## Date

2025-01-15

## Context

Need orchestration.

## Decision

Use Kubernetes.

## Consequences

More complexity.
""")

        result = runner.invoke(app, ["import", str(adr_dir)])
        assert result.exit_code == 0

    def test_import_adr_tools_invalid_status(self, adr_repo_with_data: Path) -> None:
        """Test adr-tools import with invalid status (lines 290-291)."""
        adr_dir = adr_repo_with_data / "adr-tools-invalid-status"
        adr_dir.mkdir()

        (adr_dir / "0001-bad-status.md").write_text("""# 1. Bad Status

## Status

NotARealStatus

## Context

Testing.

## Decision

Test.

## Consequences

Test.
""")

        result = runner.invoke(app, ["import", str(adr_dir)])
        # Should succeed with default status
        assert result.exit_code == 0


class TestEnsureList:
    """Tests for ensure_list helper (now in core.utils)."""

    def test_ensure_list_with_none(self) -> None:
        """Test ensure_list with None."""
        from git_adr.core.utils import ensure_list

        result = ensure_list(None)
        assert result == []

    def test_ensure_list_with_string(self) -> None:
        """Test ensure_list with string."""
        from git_adr.core.utils import ensure_list

        result = ensure_list("single-value")
        assert result == ["single-value"]

    def test_ensure_list_with_list(self) -> None:
        """Test ensure_list with list."""
        from git_adr.core.utils import ensure_list

        result = ensure_list(["a", "b", "c"])
        assert result == ["a", "b", "c"]

    def test_ensure_list_with_mixed_types(self) -> None:
        """Test ensure_list with mixed types."""
        from git_adr.core.utils import ensure_list

        result = ensure_list([1, 2, "three"])
        assert result == ["1", "2", "three"]

    def test_ensure_list_with_other(self) -> None:
        """Test ensure_list with other type."""
        from git_adr.core.utils import ensure_list

        result = ensure_list(123)  # Not list, string, or None
        assert result == []


class TestImportDryRun:
    """Tests for import dry run."""

    def test_import_dry_run(self, adr_repo_with_data: Path) -> None:
        """Test import with dry run."""
        json_file = adr_repo_with_data / "dry-run.json"
        json_file.write_text(
            json.dumps(
                {
                    "adrs": [
                        {
                            "id": "dry-run-test",
                            "title": "Dry Run Test",
                            "date": "2025-01-15",
                            "status": "draft",
                            "content": "Content",
                        }
                    ]
                }
            )
        )

        result = runner.invoke(app, ["import", str(json_file), "--dry-run"])
        assert result.exit_code == 0
        assert (
            "would import" in result.output.lower()
            or "dry-run" in result.output.lower()
        )


class TestImportWithFormat:
    """Tests for import with explicit format."""

    def test_import_with_explicit_format(self, adr_repo_with_data: Path) -> None:
        """Test import with explicit format option."""
        json_file = adr_repo_with_data / "explicit.json"
        json_file.write_text(
            json.dumps(
                {
                    "id": "explicit-format",
                    "title": "Explicit Format Test",
                    "date": "2025-01-15",
                    "status": "draft",
                    "content": "Content",
                }
            )
        )

        result = runner.invoke(app, ["import", str(json_file), "--format", "json"])
        assert result.exit_code == 0
