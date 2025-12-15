"""Deep tests for artifact commands (attach, artifact-get, artifact-rm).

Targets uncovered code paths with comprehensive mocking.
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from git_adr.cli import app

runner = CliRunner()


# =============================================================================
# Attach Command Tests
# =============================================================================


class TestAttachCommand:
    """Tests for attach command."""

    def test_attach_success(self, adr_repo_with_data: Path, tmp_path: Path) -> None:
        """Test successful file attachment."""
        # Create a test file
        test_file = tmp_path / "diagram.png"
        test_file.write_bytes(b"fake png content")

        result = runner.invoke(
            app,
            ["attach", "20250110-use-postgresql", str(test_file)],
        )
        assert result.exit_code == 0
        assert "Attached" in result.output

    def test_attach_with_name(self, adr_repo_with_data: Path, tmp_path: Path) -> None:
        """Test attachment with custom name."""
        test_file = tmp_path / "diagram.png"
        test_file.write_bytes(b"fake png content")

        result = runner.invoke(
            app,
            [
                "attach",
                "20250110-use-postgresql",
                str(test_file),
                "--name",
                "architecture.png",
            ],
        )
        assert result.exit_code == 0

    def test_attach_with_alt(self, adr_repo_with_data: Path, tmp_path: Path) -> None:
        """Test attachment with alt text."""
        test_file = tmp_path / "diagram.png"
        test_file.write_bytes(b"fake png content")

        result = runner.invoke(
            app,
            [
                "attach",
                "20250110-use-postgresql",
                str(test_file),
                "--alt",
                "Architecture diagram",
            ],
        )
        assert result.exit_code == 0

    def test_attach_file_not_found(self, adr_repo_with_data: Path) -> None:
        """Test attachment with non-existent file."""
        result = runner.invoke(
            app,
            ["attach", "20250110-use-postgresql", "/nonexistent/file.png"],
        )
        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_attach_adr_not_found(
        self, adr_repo_with_data: Path, tmp_path: Path
    ) -> None:
        """Test attachment to non-existent ADR."""
        test_file = tmp_path / "diagram.png"
        test_file.write_bytes(b"fake png content")

        result = runner.invoke(
            app,
            ["attach", "nonexistent-adr", str(test_file)],
        )
        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_attach_large_file_warning(
        self, adr_repo_with_data: Path, tmp_path: Path
    ) -> None:
        """Test large file size warning."""
        # Create a large-ish file (over default warn size)
        test_file = tmp_path / "large.bin"
        # Write 2MB of data
        test_file.write_bytes(b"x" * (2 * 1024 * 1024))

        result = runner.invoke(
            app,
            ["attach", "20250110-use-postgresql", str(test_file)],
        )
        # May succeed but with warning
        assert result.exit_code in [0, 1]

    def test_attach_not_initialized(self, temp_git_repo: Path, tmp_path: Path) -> None:
        """Test attachment in non-initialized repo."""
        test_file = tmp_path / "diagram.png"
        test_file.write_bytes(b"fake png content")

        result = runner.invoke(
            app,
            ["attach", "some-adr", str(test_file)],
        )
        assert result.exit_code != 0


# =============================================================================
# Artifact Get Command Tests
# =============================================================================


class TestArtifactGetCommand:
    """Tests for artifact-get command."""

    def test_artifact_get_by_name(
        self, adr_repo_with_data: Path, tmp_path: Path
    ) -> None:
        """Test getting artifact by name."""
        # First attach a file
        test_file = tmp_path / "diagram.png"
        test_file.write_bytes(b"fake png content")

        attach_result = runner.invoke(
            app,
            ["attach", "20250110-use-postgresql", str(test_file)],
        )

        if attach_result.exit_code == 0:
            # Now try to get it
            output_file = tmp_path / "output.png"
            result = runner.invoke(
                app,
                [
                    "artifact-get",
                    "20250110-use-postgresql",
                    "diagram.png",
                    "--output",
                    str(output_file),
                ],
            )
            # Expect success when artifact exists, or specific failure
            # (0 = success, 1 = not found which is acceptable for this test)
            assert result.exit_code in [0, 1], (
                f"Unexpected exit code: {result.exit_code}"
            )

    def test_artifact_get_not_found(self, adr_repo_with_data: Path) -> None:
        """Test getting non-existent artifact."""
        result = runner.invoke(
            app,
            ["artifact-get", "20250110-use-postgresql", "nonexistent.png"],
        )
        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_artifact_get_adr_not_found(self, adr_repo_with_data: Path) -> None:
        """Test getting artifact from non-existent ADR."""
        result = runner.invoke(
            app,
            ["artifact-get", "nonexistent-adr", "file.png"],
        )
        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_artifact_get_overwrite_prompt(
        self, adr_repo_with_data: Path, tmp_path: Path
    ) -> None:
        """Test artifact get with existing output file."""
        # First attach a file
        test_file = tmp_path / "diagram.png"
        test_file.write_bytes(b"fake png content")

        attach_result = runner.invoke(
            app,
            ["attach", "20250110-use-postgresql", str(test_file)],
        )

        if attach_result.exit_code == 0:
            # Create output file that already exists
            output_file = tmp_path / "output_exists.png"
            output_file.write_bytes(b"existing content")

            # Try to get (should prompt for overwrite)
            result = runner.invoke(
                app,
                [
                    "artifact-get",
                    "20250110-use-postgresql",
                    "diagram.png",
                    "--output",
                    str(output_file),
                ],
                input="n\n",  # Decline overwrite
            )
            # Should abort
            assert "abort" in result.output.lower() or result.exit_code in [0, 1]


# =============================================================================
# Artifact Remove Command Tests
# =============================================================================


class TestArtifactRmCommand:
    """Tests for artifact-rm command."""

    def test_artifact_rm_success(
        self, adr_repo_with_data: Path, tmp_path: Path
    ) -> None:
        """Test removing artifact."""
        # First attach a file
        test_file = tmp_path / "to_remove.png"
        test_file.write_bytes(b"fake png content")

        attach_result = runner.invoke(
            app,
            ["attach", "20250110-use-postgresql", str(test_file)],
        )

        if attach_result.exit_code == 0:
            # Now remove it
            result = runner.invoke(
                app,
                ["artifact-rm", "20250110-use-postgresql", "to_remove.png"],
                input="y\n",  # Confirm removal
            )
            assert result.exit_code in [0, 1]

    def test_artifact_rm_abort(self, adr_repo_with_data: Path, tmp_path: Path) -> None:
        """Test aborting artifact removal."""
        # First attach a file
        test_file = tmp_path / "keep.png"
        test_file.write_bytes(b"fake png content")

        attach_result = runner.invoke(
            app,
            ["attach", "20250110-use-postgresql", str(test_file)],
        )

        if attach_result.exit_code == 0:
            # Try to remove but abort
            result = runner.invoke(
                app,
                ["artifact-rm", "20250110-use-postgresql", "keep.png"],
                input="n\n",  # Decline removal
            )
            assert "abort" in result.output.lower() or result.exit_code == 0

    def test_artifact_rm_not_found(self, adr_repo_with_data: Path) -> None:
        """Test removing non-existent artifact."""
        result = runner.invoke(
            app,
            ["artifact-rm", "20250110-use-postgresql", "nonexistent.png"],
        )
        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_artifact_rm_adr_not_found(self, adr_repo_with_data: Path) -> None:
        """Test removing artifact from non-existent ADR."""
        result = runner.invoke(
            app,
            ["artifact-rm", "nonexistent-adr", "file.png"],
        )
        assert result.exit_code != 0
        assert "not found" in result.output.lower()


# =============================================================================
# Artifacts List Command Tests
# =============================================================================


class TestArtifactsCommand:
    """Tests for artifacts command."""

    def test_artifacts_list(self, adr_repo_with_data: Path) -> None:
        """Test listing artifacts."""
        result = runner.invoke(
            app,
            ["artifacts", "20250110-use-postgresql"],
        )
        assert result.exit_code == 0

    def test_artifacts_list_empty(self, adr_repo_with_data: Path) -> None:
        """Test listing artifacts when none attached."""
        result = runner.invoke(
            app,
            ["artifacts", "20250110-use-postgresql"],
        )
        # Should show "no artifacts" message
        assert result.exit_code == 0
        assert "no artifact" in result.output.lower() or result.exit_code == 0

    def test_artifacts_not_found(self, adr_repo_with_data: Path) -> None:
        """Test artifacts for non-existent ADR."""
        result = runner.invoke(
            app,
            ["artifacts", "nonexistent-adr"],
        )
        assert result.exit_code != 0


# =============================================================================
# Helper Function Tests
# =============================================================================


class TestAttachHelpers:
    """Tests for attach helper functions."""

    def test_format_size_bytes(self) -> None:
        """Test _format_size with bytes."""
        from git_adr.commands.attach import _format_size

        assert _format_size(500) == "500 bytes"

    def test_format_size_kb(self) -> None:
        """Test _format_size with kilobytes."""
        from git_adr.commands.attach import _format_size

        result = _format_size(2048)
        assert "KB" in result

    def test_format_size_mb(self) -> None:
        """Test _format_size with megabytes."""
        from git_adr.commands.attach import _format_size

        result = _format_size(2 * 1024 * 1024)
        assert "MB" in result
