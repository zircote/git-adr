"""Tests for git_adr.core.utils module."""

from __future__ import annotations

from git_adr.core.utils import ensure_list


class TestEnsureList:
    """Comprehensive tests for the ensure_list utility function."""

    def test_none_returns_empty_list(self) -> None:
        """Test that None returns empty list."""
        assert ensure_list(None) == []

    def test_empty_string_returns_list_with_empty_string(self) -> None:
        """Test that empty string returns list with empty string."""
        assert ensure_list("") == [""]

    def test_single_string_returns_list(self) -> None:
        """Test that single string returns list with that string."""
        assert ensure_list("tag") == ["tag"]

    def test_string_with_spaces(self) -> None:
        """Test that string with spaces is preserved."""
        assert ensure_list("hello world") == ["hello world"]

    def test_empty_list_returns_empty_list(self) -> None:
        """Test that empty list returns empty list."""
        assert ensure_list([]) == []

    def test_list_of_strings(self) -> None:
        """Test that list of strings returns same list."""
        assert ensure_list(["a", "b", "c"]) == ["a", "b", "c"]

    def test_list_with_integers_converts_to_strings(self) -> None:
        """Test that integers in list are converted to strings."""
        assert ensure_list([1, 2, 3]) == ["1", "2", "3"]

    def test_mixed_types_in_list(self) -> None:
        """Test that mixed types are all converted to strings."""
        assert ensure_list([1, "two", 3.0]) == ["1", "two", "3.0"]

    def test_integer_returns_empty_list(self) -> None:
        """Test that integer returns empty list."""
        assert ensure_list(123) == []

    def test_float_returns_empty_list(self) -> None:
        """Test that float returns empty list."""
        assert ensure_list(3.14) == []

    def test_dict_returns_empty_list(self) -> None:
        """Test that dict returns empty list."""
        assert ensure_list({"key": "value"}) == []

    def test_set_returns_empty_list(self) -> None:
        """Test that set returns empty list."""
        assert ensure_list({"a", "b"}) == []

    def test_tuple_returns_empty_list(self) -> None:
        """Test that tuple returns empty list (not a list)."""
        # Tuple is not a list, so should return empty list
        assert ensure_list(("a", "b")) == []

    def test_list_with_none_values(self) -> None:
        """Test that None values in list are converted to string 'None'."""
        result = ensure_list([None, "a", None])
        assert result == ["None", "a", "None"]

    def test_list_with_bool_values(self) -> None:
        """Test that bool values in list are converted to strings."""
        result = ensure_list([True, False, "maybe"])
        assert result == ["True", "False", "maybe"]


class TestEnsureListExport:
    """Test that ensure_list is properly exported from git_adr.core."""

    def test_import_from_core(self) -> None:
        """Test that ensure_list can be imported from git_adr.core."""
        from git_adr.core import ensure_list as imported_ensure_list

        assert imported_ensure_list(["test"]) == ["test"]
