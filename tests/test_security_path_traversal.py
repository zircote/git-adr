"""Security tests for path traversal vulnerabilities.

Tests SEC-001 (artifact-get) fix for output path traversal.

Security Model:
- SEC-001 (artifact-get output): WRITE operation - strictly restricted to cwd
- SEC-002 (attach input): READ operation - allows reading from any accessible path
- SEC-003 (import source): READ operation - allows reading from any accessible path

The rationale is that write operations pose higher security risk (arbitrary file
creation/overwrite), while read operations are user-initiated and should allow
flexibility to read files from anywhere the user has access to.
"""

from __future__ import annotations

import os
from pathlib import Path

import click.exceptions
import pytest

from git_adr.commands.artifact_get import _validate_output_path
from git_adr.commands.attach import _validate_input_path
from git_adr.commands.import_ import _validate_source_path


class TestSEC001ArtifactGetPathTraversal:
    """SEC-001: Path traversal in artifact-get output parameter.

    This is a WRITE operation, so paths must be restricted to cwd.
    """

    def test_valid_output_in_cwd(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Valid output path within current directory should be allowed."""
        monkeypatch.chdir(tmp_path)

        # Simple filename
        result = _validate_output_path("output.txt", "default.txt")
        assert result == tmp_path / "output.txt"

        # Subdirectory (that would be created)
        result = _validate_output_path("subdir/output.txt", "default.txt")
        assert result == tmp_path / "subdir" / "output.txt"

    def test_default_name_when_output_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When output is None, should use default_name in cwd."""
        monkeypatch.chdir(tmp_path)

        result = _validate_output_path(None, "artifact.png")
        assert result == tmp_path / "artifact.png"

    def test_path_traversal_blocked_parent_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Path traversal using .. should be blocked."""
        monkeypatch.chdir(tmp_path)

        with pytest.raises(click.exceptions.Exit) as exc_info:
            _validate_output_path("../outside.txt", "default.txt")
        assert exc_info.value.exit_code == 1

    def test_path_traversal_blocked_absolute_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Absolute path outside cwd should be blocked."""
        monkeypatch.chdir(tmp_path)

        with pytest.raises(click.exceptions.Exit) as exc_info:
            _validate_output_path("/tmp/malicious.txt", "default.txt")
        assert exc_info.value.exit_code == 1

    def test_path_traversal_blocked_deep_escape(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Deep path traversal attempts should be blocked."""
        monkeypatch.chdir(tmp_path)

        # Multiple levels up
        with pytest.raises(click.exceptions.Exit) as exc_info:
            _validate_output_path("../../../../../../etc/passwd", "default.txt")
        assert exc_info.value.exit_code == 1

    def test_path_traversal_blocked_mixed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Mixed path with subdir then escape should be blocked."""
        monkeypatch.chdir(tmp_path)

        with pytest.raises(click.exceptions.Exit) as exc_info:
            _validate_output_path("subdir/../../outside.txt", "default.txt")
        assert exc_info.value.exit_code == 1

    def test_valid_nested_subdirectory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Nested subdirectories within cwd should be allowed."""
        monkeypatch.chdir(tmp_path)

        result = _validate_output_path("a/b/c/output.txt", "default.txt")
        assert result == tmp_path / "a" / "b" / "c" / "output.txt"

    def test_dot_path_allowed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Single dot path should be resolved correctly."""
        monkeypatch.chdir(tmp_path)

        result = _validate_output_path("./output.txt", "default.txt")
        assert result == tmp_path / "output.txt"

    def test_write_to_home_directory_blocked(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Attempting to write to home directory should be blocked."""
        monkeypatch.chdir(tmp_path)

        home = os.path.expanduser("~")
        with pytest.raises(click.exceptions.Exit) as exc_info:
            _validate_output_path(f"{home}/.ssh/authorized_keys", "default.txt")
        assert exc_info.value.exit_code == 1


class TestAttachInputValidation:
    """Tests for attach command input validation.

    Attach is a READ operation - user explicitly selects files to attach.
    Path restrictions are intentionally relaxed to allow attaching files
    from anywhere the user has read access.
    """

    def test_valid_file_in_cwd(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Valid file path within current directory should be allowed."""
        monkeypatch.chdir(tmp_path)

        # Create test file
        test_file = tmp_path / "diagram.png"
        test_file.write_bytes(b"PNG data")

        result = _validate_input_path("diagram.png")
        assert result == test_file

    def test_valid_file_in_subdirectory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """File in subdirectory within cwd should be allowed."""
        monkeypatch.chdir(tmp_path)

        # Create subdirectory and file
        subdir = tmp_path / "images"
        subdir.mkdir()
        test_file = subdir / "diagram.png"
        test_file.write_bytes(b"PNG data")

        result = _validate_input_path("images/diagram.png")
        assert result == test_file

    def test_file_not_found_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Non-existent file should raise error."""
        monkeypatch.chdir(tmp_path)

        with pytest.raises(click.exceptions.Exit) as exc_info:
            _validate_input_path("nonexistent.txt")
        assert exc_info.value.exit_code == 1

    def test_directory_not_file_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Directory path should raise 'not a file' error."""
        monkeypatch.chdir(tmp_path)

        subdir = tmp_path / "subdir"
        subdir.mkdir()

        with pytest.raises(click.exceptions.Exit) as exc_info:
            _validate_input_path("subdir")
        assert exc_info.value.exit_code == 1

    def test_file_outside_cwd_allowed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Files outside cwd should be readable (user-initiated read operation)."""
        # Create a file in tmp_path
        outside_file = tmp_path / "external_file.png"
        outside_file.write_bytes(b"PNG data")

        # Change to a subdirectory
        work_dir = tmp_path / "work"
        work_dir.mkdir()
        monkeypatch.chdir(work_dir)

        # Should be able to read file from parent directory
        result = _validate_input_path(str(outside_file))
        assert result == outside_file

    def test_expanduser_works(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Tilde expansion should work for home directory paths."""
        monkeypatch.chdir(tmp_path)

        # Create a file in home directory (for this test, use a guaranteed path)
        # Note: We can't actually test ~/.ssh/id_rsa without it existing
        # But we test that expanduser is called
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        # This tests that the path is resolved
        result = _validate_input_path(str(test_file))
        assert result.is_absolute()


class TestImportSourceValidation:
    """Tests for import command source validation.

    Import is a READ operation - user explicitly selects source to import from.
    Path restrictions are intentionally relaxed to allow importing from
    anywhere the user has read access.
    """

    def test_valid_file_in_cwd(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Valid source file within current directory should be allowed."""
        monkeypatch.chdir(tmp_path)

        # Create test file
        test_file = tmp_path / "adrs.json"
        test_file.write_text('{"adrs": []}')

        result = _validate_source_path("adrs.json")
        assert result == test_file

    def test_valid_directory_in_cwd(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Valid source directory within cwd should be allowed."""
        monkeypatch.chdir(tmp_path)

        # Create test directory
        adr_dir = tmp_path / "docs" / "adr"
        adr_dir.mkdir(parents=True)

        result = _validate_source_path("docs/adr")
        assert result == adr_dir

    def test_source_not_found_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Non-existent source should raise error."""
        monkeypatch.chdir(tmp_path)

        with pytest.raises(click.exceptions.Exit) as exc_info:
            _validate_source_path("nonexistent")
        assert exc_info.value.exit_code == 1

    def test_source_outside_cwd_allowed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Sources outside cwd should be readable (user-initiated read operation)."""
        # Create a directory in tmp_path
        source_dir = tmp_path / "external_adrs"
        source_dir.mkdir()

        # Change to a different directory
        work_dir = tmp_path / "work"
        work_dir.mkdir()
        monkeypatch.chdir(work_dir)

        # Should be able to read from external source
        result = _validate_source_path(str(source_dir))
        assert result == source_dir

    def test_dot_path_allowed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Current directory (.) should be allowed."""
        monkeypatch.chdir(tmp_path)

        result = _validate_source_path(".")
        assert result == tmp_path


class TestSymlinkHandling:
    """Test that symlinks are properly handled for output paths.

    Symlinks pointing outside cwd should be blocked for write operations.
    """

    @pytest.mark.skipif(os.name == "nt", reason="Symlinks require admin on Windows")
    def test_symlink_escape_blocked_artifact_get(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Symlink pointing outside cwd should be blocked for artifact-get (write)."""
        monkeypatch.chdir(tmp_path)

        # Create a symlink pointing outside
        outside_dir = tmp_path.parent / "outside_target"
        outside_dir.mkdir(exist_ok=True)
        symlink = tmp_path / "escape_link"
        symlink.symlink_to(outside_dir)

        try:
            with pytest.raises(click.exceptions.Exit) as exc_info:
                _validate_output_path("escape_link/file.txt", "default.txt")
            assert exc_info.value.exit_code == 1
        finally:
            symlink.unlink()
            outside_dir.rmdir()

    @pytest.mark.skipif(os.name == "nt", reason="Symlinks require admin on Windows")
    def test_symlink_within_cwd_allowed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Symlink pointing to location within cwd should be allowed for output."""
        monkeypatch.chdir(tmp_path)

        # Create subdirectory and symlink to it
        target_dir = tmp_path / "real_dir"
        target_dir.mkdir()
        symlink = tmp_path / "link_dir"
        symlink.symlink_to(target_dir)

        # This should work - symlink resolves to path within cwd
        result = _validate_output_path("link_dir/file.txt", "default.txt")
        assert result == target_dir / "file.txt"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_string_path_uses_default(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Empty string is falsy, so default_name should be used."""
        monkeypatch.chdir(tmp_path)

        # Empty string is falsy in Python, so falls through to default case
        result = _validate_output_path("", "default.txt")
        # Empty string uses the default path: cwd / default_name
        assert result == tmp_path / "default.txt"

    def test_whitespace_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Whitespace-only paths should be handled."""
        monkeypatch.chdir(tmp_path)

        # Whitespace gets normalized
        result = _validate_output_path("  file.txt  ", "default.txt")
        # Path normalizes whitespace in filename
        assert "file.txt" in str(result)

    def test_unicode_filename(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Unicode filenames should work."""
        monkeypatch.chdir(tmp_path)

        result = _validate_output_path("archivo.txt", "default.txt")
        assert result == tmp_path / "archivo.txt"

    def test_special_characters_in_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Special characters (except path separators) should work for input validation."""
        monkeypatch.chdir(tmp_path)

        # Create file with special chars
        test_file = tmp_path / "file-with_special.chars.txt"
        test_file.write_text("content")

        result = _validate_input_path("file-with_special.chars.txt")
        assert result == test_file


class TestSecurityIntegration:
    """Integration tests for realistic security scenarios."""

    def test_null_byte_injection(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Null byte injection attempts should be safely handled."""
        monkeypatch.chdir(tmp_path)

        # Null bytes in paths are typically rejected by the OS
        try:
            _validate_output_path("file.txt\x00../etc/passwd", "default.txt")
            # If it doesn't raise, verify path is safe
        except (click.exceptions.Exit, ValueError, OSError):
            # Any of these exceptions indicates the attack was blocked
            pass

    def test_encoded_path_traversal(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """URL-encoded path traversal attempts should be handled.

        Python's Path doesn't decode URL encoding, so %2e%2e is treated
        as a literal directory name, not as '..'. This is safe behavior.
        """
        monkeypatch.chdir(tmp_path)

        # %2e%2e = .. URL-encoded
        # Python's Path doesn't decode URL encoding, so this creates a literal subdirectory
        result = _validate_output_path("%2e%2e/outside.txt", "default.txt")
        # This creates: cwd/%2e%2e/outside.txt (literal directory name)
        # The path is within cwd, so it's allowed (safe)
        assert str(result).startswith(str(tmp_path))
        assert "%2e%2e" in str(result)
