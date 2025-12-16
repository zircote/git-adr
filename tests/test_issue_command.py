"""Tests for the git adr issue command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from git_adr.commands.issue import (
    _edit_in_editor,
    _find_project_root,
    _parse_edited_content,
    _preview_and_confirm,
    _prompt_for_fields,
    _prompt_multiline,
    _save_locally,
    _save_section,
    _submit_or_save,
    run_issue,
)
from git_adr.core.issue import Issue, IssueBuilder
from git_adr.core.issue_template import (
    FormElement,
    FormElementType,
    IssueTemplate,
    TemplateSection,
)

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def simple_template() -> IssueTemplate:
    """Create a simple markdown template for testing."""
    return IssueTemplate(
        name="Bug Report",
        about="Report a bug",
        title="[Bug]: ",
        labels=["bug"],
        sections=[
            TemplateSection(header="Description", hint="Describe the bug"),
            TemplateSection(header="Steps to Reproduce", hint="List the steps"),
        ],
    )


@pytest.fixture
def yaml_template() -> IssueTemplate:
    """Create a YAML form template for testing."""
    return IssueTemplate(
        name="Feature Request",
        about="Request a feature",
        title="[Feature]: ",
        labels=["enhancement"],
        body=[
            FormElement(
                type=FormElementType.INPUT,
                id="title",
                attributes={"label": "Feature Title", "description": "Brief title"},
            ),
            FormElement(
                type=FormElementType.TEXTAREA,
                id="description",
                attributes={
                    "label": "Description",
                    "description": "Detailed description",
                },
            ),
            FormElement(
                type=FormElementType.DROPDOWN,
                id="priority",
                attributes={
                    "label": "Priority",
                    "options": ["Low", "Medium", "High"],
                },
            ),
            FormElement(
                type=FormElementType.CHECKBOXES,
                id="areas",
                attributes={
                    "label": "Affected Areas",
                    "options": ["UI", "Backend", "API"],
                },
            ),
        ],
        is_yaml_form=True,
    )


@pytest.fixture
def issue_builder(simple_template: IssueTemplate) -> IssueBuilder:
    """Create a pre-configured issue builder."""
    builder = IssueBuilder(simple_template)
    builder.set_title("Test Bug Title")
    builder.set_field("description", "Test description")
    builder.set_field("steps_to_reproduce", "Step 1\nStep 2")
    return builder


@pytest.fixture
def test_issue() -> Issue:
    """Create a test issue."""
    return Issue(
        title="Test Issue",
        body="Test body content",
        labels=["bug", "test"],
        assignees=["user1"],
    )


# =============================================================================
# Test _find_project_root
# =============================================================================


class TestFindProjectRoot:
    """Tests for _find_project_root function."""

    def test_finds_git_root(self, tmp_path: Path) -> None:
        """Test finding git root from subdirectory."""
        # Create .git in root
        (tmp_path / ".git").mkdir()
        subdir = tmp_path / "src" / "subdir"
        subdir.mkdir(parents=True)

        with patch("git_adr.commands.issue.Path.cwd", return_value=subdir):
            result = _find_project_root()
            assert result == tmp_path

    def test_returns_cwd_when_no_git(self, tmp_path: Path) -> None:
        """Test returns cwd when no .git found."""
        with patch("git_adr.commands.issue.Path.cwd", return_value=tmp_path):
            result = _find_project_root()
            assert result == tmp_path


# =============================================================================
# Test _prompt_multiline
# =============================================================================


class TestPromptMultiline:
    """Tests for _prompt_multiline function."""

    def test_collects_lines_until_double_empty(self) -> None:
        """Test multiline input collection."""
        with patch("builtins.input", side_effect=["line1", "line2", "", ""]):
            result = _prompt_multiline("Enter text")
            assert result == "line1\nline2"

    def test_handles_eof(self) -> None:
        """Test handles EOFError gracefully."""
        with patch("builtins.input", side_effect=["line1", EOFError()]):
            result = _prompt_multiline("Enter text")
            assert result == "line1"

    def test_strips_trailing_empty_lines(self) -> None:
        """Test trailing empty lines are removed."""
        with patch("builtins.input", side_effect=["line1", "", "line2", "", ""]):
            result = _prompt_multiline("Enter text")
            assert result == "line1\n\nline2"

    def test_empty_input(self) -> None:
        """Test empty input returns empty string."""
        with patch("builtins.input", side_effect=["", ""]):
            result = _prompt_multiline("Enter text")
            assert result == ""


# =============================================================================
# Test _prompt_for_fields
# =============================================================================


class TestPromptForFields:
    """Tests for _prompt_for_fields function."""

    def test_uses_provided_description(self, simple_template: IssueTemplate) -> None:
        """Test description is used for first field."""
        builder = IssueBuilder(simple_template)
        builder.set_title("Test")

        with patch("builtins.input", side_effect=["Step 1", "", ""]):
            _prompt_for_fields(builder, simple_template, description="Pre-filled desc")

        assert builder.get_field("description") == "Pre-filled desc"

    def test_prompts_for_markdown_sections(
        self, simple_template: IssueTemplate
    ) -> None:
        """Test prompts for each markdown section."""
        builder = IssueBuilder(simple_template)
        builder.set_title("Test")

        with patch(
            "builtins.input", side_effect=["Desc line", "", "", "Step 1", "", ""]
        ):
            _prompt_for_fields(builder, simple_template, description=None)

        assert builder.get_field("description") == "Desc line"
        assert builder.get_field("steps_to_reproduce") == "Step 1"

    def test_handles_yaml_input_field(self, yaml_template: IssueTemplate) -> None:
        """Test handles INPUT type fields."""
        builder = IssueBuilder(yaml_template)
        builder.set_title("Test")

        with (
            patch(
                "git_adr.commands.issue.Prompt.ask",
                side_effect=["Input Value", "1"],
            ),
            patch("builtins.input", side_effect=["Description", "", ""]),
            patch("git_adr.commands.issue.Confirm.ask", return_value=False),
        ):
            _prompt_for_fields(builder, yaml_template)

        assert builder.get_field("title") == "Input Value"

    def test_handles_yaml_dropdown(self, yaml_template: IssueTemplate) -> None:
        """Test handles DROPDOWN type fields."""
        builder = IssueBuilder(yaml_template)
        builder.set_title("Test")

        with (
            patch(
                "git_adr.commands.issue.Prompt.ask",
                side_effect=["Input", "2"],  # Input value, dropdown choice
            ),
            patch("builtins.input", side_effect=["Desc", "", ""]),
            patch("git_adr.commands.issue.Confirm.ask", return_value=False),
        ):
            _prompt_for_fields(builder, yaml_template)

        assert builder.get_field("priority") == "Medium"

    def test_handles_yaml_checkboxes(self, yaml_template: IssueTemplate) -> None:
        """Test handles CHECKBOXES type fields."""
        builder = IssueBuilder(yaml_template)
        builder.set_title("Test")

        with (
            patch(
                "git_adr.commands.issue.Prompt.ask",
                side_effect=["Input", "1"],
            ),
            patch("builtins.input", side_effect=["Desc", "", ""]),
            patch(
                "git_adr.commands.issue.Confirm.ask",
                side_effect=[True, False, True],  # UI=yes, Backend=no, API=yes
            ),
        ):
            _prompt_for_fields(builder, yaml_template)

        areas = builder.get_field("areas")
        assert "- [x] UI" in areas
        assert "- [x] API" in areas


# =============================================================================
# Test _preview_and_confirm
# =============================================================================


class TestPreviewAndConfirm:
    """Tests for _preview_and_confirm function."""

    def test_returns_submit_on_dry_run(self, issue_builder: IssueBuilder) -> None:
        """Test returns submit immediately for dry run."""
        result = _preview_and_confirm(issue_builder, dry_run=True)
        assert result == "submit"

    def test_returns_user_choice(self, issue_builder: IssueBuilder) -> None:
        """Test returns user's choice."""
        with patch("git_adr.commands.issue.Prompt.ask", return_value="edit"):
            result = _preview_and_confirm(issue_builder, dry_run=False)
            assert result == "edit"

    def test_returns_cancel(self, issue_builder: IssueBuilder) -> None:
        """Test returns cancel choice."""
        with patch("git_adr.commands.issue.Prompt.ask", return_value="cancel"):
            result = _preview_and_confirm(issue_builder, dry_run=False)
            assert result == "cancel"


# =============================================================================
# Test _parse_edited_content and _save_section
# =============================================================================


class TestParseEditedContent:
    """Tests for _parse_edited_content function."""

    def test_extracts_title(self, issue_builder: IssueBuilder) -> None:
        """Test extracts title from markdown."""
        content = "# New Title\n\n## Description\n\nNew description"
        _parse_edited_content(issue_builder, content)
        assert issue_builder.title == "New Title"

    def test_extracts_sections(self, issue_builder: IssueBuilder) -> None:
        """Test extracts section content."""
        content = "# Title\n\n## Description\n\nUpdated desc\n\n## Steps To Reproduce\n\nNew steps"
        _parse_edited_content(issue_builder, content)
        assert issue_builder.get_field("description") == "Updated desc"
        assert issue_builder.get_field("steps_to_reproduce") == "New steps"

    def test_handles_empty_sections(self, issue_builder: IssueBuilder) -> None:
        """Test handles empty section content."""
        content = "# Title\n\n## Description\n\n\n\n## Steps To Reproduce\n\nSteps here"
        _parse_edited_content(issue_builder, content)
        assert issue_builder.get_field("description") == ""


class TestSaveSection:
    """Tests for _save_section function."""

    def test_matches_template_section(self, issue_builder: IssueBuilder) -> None:
        """Test matches by header to template section."""
        _save_section(issue_builder, "Description", ["Line 1", "Line 2"])
        assert issue_builder.get_field("description") == "Line 1\nLine 2"

    def test_case_insensitive_match(self, issue_builder: IssueBuilder) -> None:
        """Test case-insensitive header matching."""
        _save_section(issue_builder, "DESCRIPTION", ["content"])
        assert issue_builder.get_field("description") == "content"

    def test_no_match_does_nothing(self, issue_builder: IssueBuilder) -> None:
        """Test unmatched header does nothing."""
        original = issue_builder.get_field("description")
        _save_section(issue_builder, "Unknown Section", ["content"])
        assert issue_builder.get_field("description") == original


# =============================================================================
# Test _edit_in_editor
# =============================================================================


class TestEditInEditor:
    """Tests for _edit_in_editor function."""

    def test_opens_editor_and_updates(self, issue_builder: IssueBuilder) -> None:
        """Test opens editor and updates builder."""
        edited_content = "# Edited Title\n\n## Description\n\nEdited description"

        with (
            patch.dict("os.environ", {"EDITOR": "cat"}),
            patch("subprocess.run") as mock_run,
            patch("pathlib.Path.read_text", return_value=edited_content),
        ):
            mock_run.return_value = MagicMock(returncode=0)
            _edit_in_editor(issue_builder)

        assert issue_builder.title == "Edited Title"

    def test_handles_editor_error(self, issue_builder: IssueBuilder) -> None:
        """Test handles editor subprocess error."""
        import subprocess

        with (
            patch.dict("os.environ", {"EDITOR": "nonexistent"}),
            patch(
                "subprocess.run",
                side_effect=subprocess.CalledProcessError(1, "nonexistent"),
            ),
        ):
            # Should not raise, just print warning
            _edit_in_editor(issue_builder)


# =============================================================================
# Test _save_locally
# =============================================================================


class TestSaveLocally:
    """Tests for _save_locally function."""

    def test_saves_issue_to_file(self, test_issue: Issue, tmp_path: Path) -> None:
        """Test saves issue to local file."""
        with patch(
            "git_adr.commands.issue.save_local_issue",
            return_value=tmp_path / "issue.md",
        ):
            _save_locally(test_issue)

    def test_handles_save_error(self, test_issue: Issue) -> None:
        """Test handles file save error."""
        import typer

        with (
            patch(
                "git_adr.commands.issue.save_local_issue",
                side_effect=OSError("Write error"),
            ),
            pytest.raises(typer.Exit),
        ):
            _save_locally(test_issue)


# =============================================================================
# Test _submit_or_save
# =============================================================================


class TestSubmitOrSave:
    """Tests for _submit_or_save function."""

    def test_saves_locally_when_gh_not_ready(self, test_issue: Issue) -> None:
        """Test saves locally when gh CLI not available."""
        with (
            patch(
                "git_adr.commands.issue.check_gh_status",
                return_value=(False, "gh not installed"),
            ),
            patch("git_adr.commands.issue._save_locally") as mock_save,
        ):
            _submit_or_save(test_issue)
            mock_save.assert_called_once_with(test_issue)

    def test_submits_when_gh_ready(self, test_issue: Issue) -> None:
        """Test submits to GitHub when gh CLI ready."""
        mock_result = MagicMock(success=True, url="https://github.com/test/1")

        with (
            patch(
                "git_adr.commands.issue.check_gh_status",
                return_value=(True, "Ready"),
            ),
            patch("git_adr.commands.issue.GitHubIssueClient") as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client.create_issue.return_value = mock_result
            mock_client_class.return_value = mock_client

            _submit_or_save(test_issue, repo="owner/repo")
            mock_client.create_issue.assert_called_once_with(test_issue)

    def test_saves_locally_on_submit_error(self, test_issue: Issue) -> None:
        """Test saves locally when submission fails."""
        mock_result = MagicMock(success=False, error="API error")

        with (
            patch(
                "git_adr.commands.issue.check_gh_status",
                return_value=(True, "Ready"),
            ),
            patch("git_adr.commands.issue.GitHubIssueClient") as mock_client_class,
            patch("git_adr.commands.issue._save_locally") as mock_save,
        ):
            mock_client = MagicMock()
            mock_client.create_issue.return_value = mock_result
            mock_client_class.return_value = mock_client

            _submit_or_save(test_issue)
            mock_save.assert_called_once_with(test_issue)


# =============================================================================
# Test run_issue - Integration tests using mocks
# =============================================================================


class TestRunIssue:
    """Tests for run_issue main function."""

    def test_unknown_type_error(self) -> None:
        """Test error for unknown issue type."""
        import typer

        mock_manager = MagicMock()
        mock_manager.get_template.return_value = None
        mock_manager.format_available_types_message.return_value = "Available: bug"

        with (
            patch("git_adr.commands.issue._find_project_root", return_value=Path("/")),
            patch("git_adr.commands.issue.TemplateManager", return_value=mock_manager),
            pytest.raises(typer.Exit) as exc_info,
        ):
            run_issue(type_="nonexistent")

        assert exc_info.value.exit_code == 1

    def test_cancel_action(self, simple_template: IssueTemplate) -> None:
        """Test cancel action exits cleanly."""
        import typer

        mock_manager = MagicMock()
        mock_manager.get_template.return_value = simple_template

        with (
            patch("git_adr.commands.issue._find_project_root", return_value=Path("/")),
            patch("git_adr.commands.issue.TemplateManager", return_value=mock_manager),
            patch("git_adr.commands.issue._prompt_for_fields"),
            patch(
                "git_adr.commands.issue._preview_and_confirm",
                return_value="cancel",
            ),
            pytest.raises(typer.Exit) as exc_info,
        ):
            run_issue(type_="bug", title="Test")

        assert exc_info.value.exit_code == 0

    def test_build_error_exits(self, simple_template: IssueTemplate) -> None:
        """Test build error causes exit."""
        import typer

        mock_manager = MagicMock()
        mock_manager.get_template.return_value = simple_template

        with (
            patch("git_adr.commands.issue._find_project_root", return_value=Path("/")),
            patch("git_adr.commands.issue.TemplateManager", return_value=mock_manager),
            patch("git_adr.commands.issue._prompt_for_fields"),
            patch(
                "git_adr.commands.issue.IssueBuilder.build",
                side_effect=ValueError("Missing required field"),
            ),
            pytest.raises(typer.Exit) as exc_info,
        ):
            run_issue(
                type_="bug",
                title="Test",
                no_edit=True,
            )

        assert exc_info.value.exit_code == 1

    def test_dry_run_mode(self, simple_template: IssueTemplate) -> None:
        """Test dry run shows preview without submitting."""
        mock_manager = MagicMock()
        mock_manager.get_template.return_value = simple_template

        with (
            patch("git_adr.commands.issue._find_project_root", return_value=Path("/")),
            patch("git_adr.commands.issue.TemplateManager", return_value=mock_manager),
            patch("git_adr.commands.issue._prompt_for_fields"),
        ):
            # dry_run should return without calling submit
            run_issue(
                type_="bug",
                title="Test Bug",
                description="Test description",
                dry_run=True,
                no_edit=True,
            )

    def test_local_only_mode(self, simple_template: IssueTemplate) -> None:
        """Test local_only saves without submitting."""
        mock_manager = MagicMock()
        mock_manager.get_template.return_value = simple_template

        mock_issue = MagicMock()
        with (
            patch("git_adr.commands.issue._find_project_root", return_value=Path("/")),
            patch("git_adr.commands.issue.TemplateManager", return_value=mock_manager),
            patch("git_adr.commands.issue._prompt_for_fields"),
            patch("git_adr.commands.issue.IssueBuilder.build", return_value=mock_issue),
            patch("git_adr.commands.issue._save_locally") as mock_save,
        ):
            run_issue(
                type_="bug",
                title="Test Bug",
                local_only=True,
                no_edit=True,
            )
            mock_save.assert_called_once_with(mock_issue)

    def test_submit_mode(self, simple_template: IssueTemplate) -> None:
        """Test default mode submits to GitHub."""
        mock_manager = MagicMock()
        mock_manager.get_template.return_value = simple_template

        mock_issue = MagicMock()
        with (
            patch("git_adr.commands.issue._find_project_root", return_value=Path("/")),
            patch("git_adr.commands.issue.TemplateManager", return_value=mock_manager),
            patch("git_adr.commands.issue._prompt_for_fields"),
            patch("git_adr.commands.issue.IssueBuilder.build", return_value=mock_issue),
            patch("git_adr.commands.issue._submit_or_save") as mock_submit,
        ):
            run_issue(
                type_="bug",
                title="Test Bug",
                repo="owner/repo",
                no_edit=True,
            )
            mock_submit.assert_called_once_with(mock_issue, "owner/repo")

    def test_edit_action_opens_editor(self, simple_template: IssueTemplate) -> None:
        """Test edit action opens external editor."""
        mock_manager = MagicMock()
        mock_manager.get_template.return_value = simple_template

        mock_issue = MagicMock()
        with (
            patch("git_adr.commands.issue._find_project_root", return_value=Path("/")),
            patch("git_adr.commands.issue.TemplateManager", return_value=mock_manager),
            patch("git_adr.commands.issue._prompt_for_fields"),
            patch("git_adr.commands.issue._edit_in_editor") as mock_edit,
            patch(
                "git_adr.commands.issue._preview_and_confirm",
                side_effect=["edit", "submit"],
            ),
            patch("git_adr.commands.issue.IssueBuilder.build", return_value=mock_issue),
            patch("git_adr.commands.issue._save_locally"),
        ):
            run_issue(type_="bug", title="Test", local_only=True)
            mock_edit.assert_called_once()

    def test_type_selection_prompt(self) -> None:
        """Test type selection when type is None."""
        mock_manager = MagicMock()
        mock_manager.get_available_types.return_value = [
            "bug_report",
            "feature_request",
        ]
        mock_manager.get_template.return_value = MagicMock(
            name="Bug Report",
            about="Report a bug",
            title="[Bug]: ",
            labels=["bug"],
            is_yaml_form=False,
            sections=[],
            body=[],
            assignees=[],
        )
        mock_manager.get_aliases_for_type.return_value = ["bug"]

        mock_issue = MagicMock()
        with (
            patch("git_adr.commands.issue._find_project_root", return_value=Path("/")),
            patch("git_adr.commands.issue.TemplateManager", return_value=mock_manager),
            patch(
                "git_adr.commands.issue.Prompt.ask",
                return_value="bug_report",
            ),
            patch("git_adr.commands.issue._prompt_for_fields"),
            patch("git_adr.commands.issue.IssueBuilder.build", return_value=mock_issue),
            patch("git_adr.commands.issue._save_locally"),
        ):
            run_issue(type_=None, title="Test", local_only=True, no_edit=True)

    def test_title_merging_with_prefix(self, simple_template: IssueTemplate) -> None:
        """Test title merging when template has prefix."""
        mock_manager = MagicMock()
        mock_manager.get_template.return_value = simple_template

        mock_issue = MagicMock()
        with (
            patch("git_adr.commands.issue._find_project_root", return_value=Path("/")),
            patch("git_adr.commands.issue.TemplateManager", return_value=mock_manager),
            patch("git_adr.commands.issue._prompt_for_fields"),
            patch("git_adr.commands.issue.IssueBuilder") as mock_builder_class,
            patch("git_adr.commands.issue._save_locally"),
        ):
            mock_builder = MagicMock()
            mock_builder.build.return_value = mock_issue
            mock_builder_class.return_value = mock_builder

            # Title doesn't start with template prefix, should be merged
            run_issue(
                type_="bug",
                title="Fix login",  # Not starting with "[Bug]: "
                local_only=True,
                no_edit=True,
            )
            # Should be called with merged title
            mock_builder.set_title.assert_called()

    def test_labels_from_flags(self, simple_template: IssueTemplate) -> None:
        """Test extra labels added from flags."""
        mock_manager = MagicMock()
        mock_manager.get_template.return_value = simple_template

        mock_issue = MagicMock()
        with (
            patch("git_adr.commands.issue._find_project_root", return_value=Path("/")),
            patch("git_adr.commands.issue.TemplateManager", return_value=mock_manager),
            patch("git_adr.commands.issue._prompt_for_fields"),
            patch("git_adr.commands.issue.IssueBuilder") as mock_builder_class,
            patch("git_adr.commands.issue._save_locally"),
        ):
            mock_builder = MagicMock()
            mock_builder.build.return_value = mock_issue
            mock_builder_class.return_value = mock_builder

            run_issue(
                type_="bug",
                title="Test",
                labels=["priority:high", "area:auth"],
                local_only=True,
                no_edit=True,
            )
            # Should call add_label for each extra label
            assert mock_builder.add_label.call_count == 2

    def test_assignees_override(self, simple_template: IssueTemplate) -> None:
        """Test assignees override from flags."""
        mock_manager = MagicMock()
        mock_manager.get_template.return_value = simple_template

        mock_issue = MagicMock()
        with (
            patch("git_adr.commands.issue._find_project_root", return_value=Path("/")),
            patch("git_adr.commands.issue.TemplateManager", return_value=mock_manager),
            patch("git_adr.commands.issue._prompt_for_fields"),
            patch("git_adr.commands.issue.IssueBuilder") as mock_builder_class,
            patch("git_adr.commands.issue._save_locally"),
        ):
            mock_builder = MagicMock()
            mock_builder.build.return_value = mock_issue
            mock_builder_class.return_value = mock_builder

            run_issue(
                type_="bug",
                title="Test",
                assignees=["user1", "user2"],
                local_only=True,
                no_edit=True,
            )
            mock_builder.set_assignees.assert_called_once_with(["user1", "user2"])

    def test_title_prompt_when_not_provided(
        self, simple_template: IssueTemplate
    ) -> None:
        """Test title is prompted when not provided via flag."""
        mock_manager = MagicMock()
        mock_manager.get_template.return_value = simple_template

        mock_issue = MagicMock()
        with (
            patch("git_adr.commands.issue._find_project_root", return_value=Path("/")),
            patch("git_adr.commands.issue.TemplateManager", return_value=mock_manager),
            patch(
                "git_adr.commands.issue.Prompt.ask",
                return_value="Prompted Title",
            ),
            patch("git_adr.commands.issue._prompt_for_fields"),
            patch("git_adr.commands.issue.IssueBuilder") as mock_builder_class,
            patch("git_adr.commands.issue._save_locally"),
        ):
            mock_builder = MagicMock()
            mock_builder.build.return_value = mock_issue
            mock_builder_class.return_value = mock_builder

            run_issue(
                type_="bug",
                title=None,  # No title provided
                local_only=True,
                no_edit=True,
            )
            mock_builder.set_title.assert_called_once_with("Prompted Title")

    def test_no_templates_found_error(self) -> None:
        """Test error when no templates available."""
        import typer

        mock_manager = MagicMock()
        mock_manager.get_available_types.return_value = []

        with (
            patch("git_adr.commands.issue._find_project_root", return_value=Path("/")),
            patch("git_adr.commands.issue.TemplateManager", return_value=mock_manager),
            pytest.raises(typer.Exit) as exc_info,
        ):
            run_issue(type_=None)  # No type, empty list

        assert exc_info.value.exit_code == 1


# =============================================================================
# Test YAML form prompting
# =============================================================================


class TestPromptForFieldsYamlForm:
    """Additional tests for YAML form field prompting."""

    def test_uses_description_for_yaml_input(
        self, yaml_template: IssueTemplate
    ) -> None:
        """Test description flag used for first INPUT field (not textarea)."""
        builder = IssueBuilder(yaml_template)
        builder.set_title("Test")

        # The yaml_template has INPUT first (title), TEXTAREA second (description)
        # When description is provided, it should be used for the first INPUT/TEXTAREA field
        with (
            patch("builtins.input", side_effect=["Textarea content", "", ""]),
            patch(
                "git_adr.commands.issue.Prompt.ask",
                side_effect=["1"],  # dropdown selection
            ),
            patch("git_adr.commands.issue.Confirm.ask", return_value=False),
        ):
            _prompt_for_fields(builder, yaml_template, description="Pre-filled input")

        # Description should be used for the first INPUT field (title)
        assert builder.get_field("title") == "Pre-filled input"


# =============================================================================
# Test _save_section with YAML form
# =============================================================================


class TestSaveSectionYaml:
    """Tests for _save_section with YAML form templates."""

    def test_matches_yaml_form_element(self, yaml_template: IssueTemplate) -> None:
        """Test matches by label to YAML form element."""
        builder = IssueBuilder(yaml_template)
        builder.set_title("Test")

        _save_section(builder, "Feature Title", ["New feature title"])
        assert builder.get_field("title") == "New feature title"


# =============================================================================
# Test _edit_in_editor with YAML form
# =============================================================================


class TestEditInEditorYaml:
    """Tests for _edit_in_editor with YAML form templates."""

    def test_writes_yaml_form_fields(self, yaml_template: IssueTemplate) -> None:
        """Test editor writes YAML form field labels."""
        builder = IssueBuilder(yaml_template)
        builder.set_title("Test Feature")
        builder.set_field("title", "My Feature")
        builder.set_field("description", "Feature desc")

        edited_content = "# Edited Feature\n\n## Feature Title\n\nUpdated title"

        with (
            patch.dict("os.environ", {"EDITOR": "cat"}),
            patch("subprocess.run") as mock_run,
            patch("pathlib.Path.read_text", return_value=edited_content),
        ):
            mock_run.return_value = MagicMock(returncode=0)
            _edit_in_editor(builder)

        assert builder.title == "Edited Feature"
        assert builder.get_field("title") == "Updated title"
