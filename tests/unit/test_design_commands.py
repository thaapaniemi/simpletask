"""Unit tests for design CLI commands.

Tests cover:
- design show command with various design field combinations
- design set command for all field types
- design remove command with and without index
- File I/O mocking for task file operations
"""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import typer
from simpletask.commands.design.remove import remove_command
from simpletask.commands.design.set import set_command
from simpletask.commands.design.show import show_command
from simpletask.core.models import (
    AcceptanceCriterion,
    ArchitecturalPattern,
    Design,
    DesignReference,
    ErrorHandlingStrategy,
    LintingConfig,
    QualityRequirements,
    SecurityCategory,
    SecurityRequirement,
    SimpleTaskSpec,
    TestingConfig,
    ToolName,
)


@pytest.fixture
def sample_spec_with_design() -> SimpleTaskSpec:
    """Create a sample task spec with design section."""
    return SimpleTaskSpec(
        schema_version="1.3",
        branch="test-feature",
        title="Test Feature",
        original_prompt="Test prompt",
        created=datetime.now(UTC),
        acceptance_criteria=[
            AcceptanceCriterion(id="AC1", description="Works", completed=False),
        ],
        quality_requirements=QualityRequirements(
            linting=LintingConfig(enabled=True, tool=ToolName.RUFF, args=["check", "."]),
            testing=TestingConfig(enabled=True, tool=ToolName.PYTEST, args=[], min_coverage=80),
        ),
        design=Design(
            patterns=[ArchitecturalPattern.REPOSITORY, ArchitecturalPattern.DEPENDENCY_INJECTION],
            reference_implementations=[
                DesignReference(path="src/existing/module.py", reason="Similar functionality")
            ],
            architectural_constraints=["Use clean architecture", "No circular dependencies"],
            security=[
                SecurityRequirement(
                    category=SecurityCategory.INPUT_VALIDATION,
                    description="Validate all user inputs",
                ),
                SecurityRequirement(
                    category=SecurityCategory.DATA_PROTECTION,
                    description="Use parameterized queries",
                ),
            ],
            error_handling=ErrorHandlingStrategy.RESULT_TYPE,
        ),
    )


@pytest.fixture
def sample_spec_without_design() -> SimpleTaskSpec:
    """Create a sample task spec without design section."""
    return SimpleTaskSpec(
        schema_version="1.3",
        branch="test-feature",
        title="Test Feature",
        original_prompt="Test prompt",
        created=datetime.now(UTC),
        acceptance_criteria=[
            AcceptanceCriterion(id="AC1", description="Works", completed=False),
        ],
        quality_requirements=QualityRequirements(
            linting=LintingConfig(enabled=True, tool=ToolName.RUFF, args=["check", "."]),
            testing=TestingConfig(enabled=True, tool=ToolName.PYTEST, args=[], min_coverage=80),
        ),
        design=None,
    )


class TestShowCommand:
    """Tests for design show command."""

    @patch("simpletask.commands.design.show.parse_task_file")
    @patch("simpletask.commands.design.show.get_task_file_path")
    def test_show_with_full_design(
        self, mock_get_path, mock_parse, sample_spec_with_design, capsys
    ):
        """Show displays all design fields when present."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_design

        show_command()

        captured = capsys.readouterr()
        assert "Design Guidance" in captured.out
        assert "repository" in captured.out
        assert "dependency_injection" in captured.out
        assert "src/existing/module.py" in captured.out
        assert "Similar functionality" in captured.out
        assert "Use clean architecture" in captured.out
        assert "input_validation" in captured.out
        assert "Validate all user inputs" in captured.out
        assert "result_type" in captured.out

    @patch("simpletask.commands.design.show.parse_task_file")
    @patch("simpletask.commands.design.show.get_task_file_path")
    def test_show_without_design(self, mock_get_path, mock_parse, sample_spec_without_design):
        """Show displays message when no design section exists."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_without_design

        show_command()

        # Should display message about no design section and not raise exception

    @patch("simpletask.commands.design.show.parse_task_file")
    @patch("simpletask.commands.design.show.get_task_file_path")
    def test_show_with_empty_design(self, mock_get_path, mock_parse, sample_spec_without_design):
        """Show displays message when design section exists but all fields are empty."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        spec = sample_spec_without_design
        spec.design = Design()  # Empty design section
        mock_parse.return_value = spec

        show_command()

        # Should display message about empty design section

    @patch("simpletask.commands.design.show.parse_task_file")
    @patch("simpletask.commands.design.show.get_task_file_path")
    def test_show_with_branch_option(self, mock_get_path, mock_parse, sample_spec_with_design):
        """Show command respects --branch option."""
        mock_get_path.return_value = Path(".tasks/other-branch.yml")
        mock_parse.return_value = sample_spec_with_design

        show_command(branch="other-branch")

        mock_get_path.assert_called_once_with("other-branch")

    @patch("simpletask.commands.design.show.get_task_file_path")
    def test_show_file_not_found(self, mock_get_path):
        """Show command handles file not found gracefully."""
        mock_get_path.side_effect = FileNotFoundError("Task file not found")

        with pytest.raises(typer.Exit):
            show_command()

        # Should handle exception gracefully by calling error() which raises typer.Exit


class TestSetCommand:
    """Tests for design set command."""

    @patch("simpletask.commands.design.set.write_task_file")
    @patch("simpletask.commands.design.set.parse_task_file")
    @patch("simpletask.commands.design.set.get_task_file_path")
    def test_set_patterns(self, mock_get_path, mock_parse, mock_write, sample_spec_without_design):
        """Set command adds patterns to design section."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_without_design

        # Add first pattern
        set_command(field="pattern", value="repository")

        # Verify design section was created with first pattern
        written_spec = mock_write.call_args[0][1]
        assert written_spec.design is not None
        assert len(written_spec.design.patterns) == 1
        assert written_spec.design.patterns[0].value == "repository"

        # Add second pattern
        mock_parse.return_value = written_spec  # Parse returns updated spec
        set_command(field="pattern", value="dependency_injection")

        # Verify both patterns exist
        written_spec = mock_write.call_args[0][1]
        assert len(written_spec.design.patterns) == 2
        assert written_spec.design.patterns[0].value == "repository"
        assert written_spec.design.patterns[1].value == "dependency_injection"

    @patch("simpletask.commands.design.set.write_task_file")
    @patch("simpletask.commands.design.set.parse_task_file")
    @patch("simpletask.commands.design.set.get_task_file_path")
    def test_set_references_with_reason(
        self, mock_get_path, mock_parse, mock_write, sample_spec_without_design
    ):
        """Set command adds reference with reason."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_without_design

        set_command(
            field="reference",
            value="src/module.py",
            reference_reason="Similar implementation",
        )

        written_spec = mock_write.call_args[0][1]
        assert written_spec.design is not None
        assert len(written_spec.design.reference_implementations) == 1
        assert written_spec.design.reference_implementations[0].path == "src/module.py"
        assert written_spec.design.reference_implementations[0].reason == "Similar implementation"

    @patch("simpletask.commands.design.set.get_task_file_path")
    @patch("simpletask.commands.design.set.parse_task_file")
    def test_set_references_without_reason_fails(
        self, mock_parse, mock_get_path, sample_spec_without_design
    ):
        """Set command requires --reason when adding references."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_without_design

        with pytest.raises(typer.Exit):
            set_command(field="reference", value="src/module.py", reference_reason=None)

    @patch("simpletask.commands.design.set.write_task_file")
    @patch("simpletask.commands.design.set.parse_task_file")
    @patch("simpletask.commands.design.set.get_task_file_path")
    def test_set_constraints(
        self, mock_get_path, mock_parse, mock_write, sample_spec_without_design
    ):
        """Set command adds architectural constraints."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_without_design

        # Add first constraint
        set_command(field="constraint", value="Use clean architecture")

        written_spec = mock_write.call_args[0][1]
        assert written_spec.design is not None
        assert len(written_spec.design.architectural_constraints) == 1
        assert written_spec.design.architectural_constraints[0] == "Use clean architecture"

        # Add second constraint
        mock_parse.return_value = written_spec
        set_command(field="constraint", value="No circular deps")

        written_spec = mock_write.call_args[0][1]
        assert len(written_spec.design.architectural_constraints) == 2

    @patch("simpletask.commands.design.set.write_task_file")
    @patch("simpletask.commands.design.set.parse_task_file")
    @patch("simpletask.commands.design.set.get_task_file_path")
    def test_set_security(self, mock_get_path, mock_parse, mock_write, sample_spec_without_design):
        """Set command adds security requirements."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_without_design

        # Add first security requirement
        set_command(
            field="security",
            value="Validate inputs",
            security_category="input_validation",
        )

        written_spec = mock_write.call_args[0][1]
        assert written_spec.design is not None
        assert len(written_spec.design.security) == 1
        assert written_spec.design.security[0].category.value == "input_validation"
        assert written_spec.design.security[0].description == "Validate inputs"

        # Add second security requirement
        mock_parse.return_value = written_spec
        set_command(
            field="security",
            value="Use parameterized queries",
            security_category="data_protection",
        )

        written_spec = mock_write.call_args[0][1]
        assert len(written_spec.design.security) == 2

    @patch("simpletask.commands.design.set.write_task_file")
    @patch("simpletask.commands.design.set.parse_task_file")
    @patch("simpletask.commands.design.set.get_task_file_path")
    def test_set_error_handling(
        self, mock_get_path, mock_parse, mock_write, sample_spec_without_design
    ):
        """Set command sets error handling strategy."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_without_design

        set_command(field="error-handling", value="result_type")

        written_spec = mock_write.call_args[0][1]
        assert written_spec.design is not None
        assert written_spec.design.error_handling.value == "result_type"

    @patch("simpletask.commands.design.set.get_task_file_path")
    @patch("simpletask.commands.design.set.parse_task_file")
    def test_set_invalid_field(self, mock_parse, mock_get_path, sample_spec_without_design):
        """Set command rejects invalid field names."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_without_design

        with pytest.raises(typer.Exit):
            set_command(field="invalid-field", value="some value")

    @patch("simpletask.commands.design.set.write_task_file")
    @patch("simpletask.commands.design.set.parse_task_file")
    @patch("simpletask.commands.design.set.get_task_file_path")
    def test_set_appends_to_existing(
        self, mock_get_path, mock_parse, mock_write, sample_spec_with_design
    ):
        """Set command appends to existing lists."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_design

        initial_count = len(sample_spec_with_design.design.patterns)

        set_command(field="pattern", value="factory")

        written_spec = mock_write.call_args[0][1]
        assert len(written_spec.design.patterns) == initial_count + 1
        assert written_spec.design.patterns[-1].value == "factory"

    @patch("simpletask.commands.design.set.write_task_file")
    @patch("simpletask.commands.design.set.parse_task_file")
    @patch("simpletask.commands.design.set.get_task_file_path")
    def test_set_constraint_with_commas(
        self, mock_get_path, mock_parse, mock_write, sample_spec_without_design
    ):
        """Set command handles values containing commas correctly.

        This verifies that T033 (Fix design set command CSV parsing) is complete.
        Values with commas are treated as a single value, not split into multiple values.
        """
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_without_design

        # Add constraint with commas in the value
        set_command(
            field="constraint", value="Use interfaces: IRepository, IService, IFactory pattern"
        )

        written_spec = mock_write.call_args[0][1]
        assert written_spec.design is not None
        assert len(written_spec.design.architectural_constraints) == 1
        # The entire string should be stored as one constraint, not split by commas
        assert (
            written_spec.design.architectural_constraints[0]
            == "Use interfaces: IRepository, IService, IFactory pattern"
        )

    @patch("simpletask.commands.design.set.write_task_file")
    @patch("simpletask.commands.design.set.parse_task_file")
    @patch("simpletask.commands.design.set.get_task_file_path")
    def test_set_security_with_commas(
        self, mock_get_path, mock_parse, mock_write, sample_spec_without_design
    ):
        """Set command handles security descriptions with commas correctly."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_without_design

        # Add security requirement with commas in the description
        set_command(
            field="security",
            value="Sanitize user inputs: forms, URLs, headers, cookies",
            security_category="input_validation",
        )

        written_spec = mock_write.call_args[0][1]
        assert written_spec.design is not None
        assert len(written_spec.design.security) == 1
        # The entire description should be stored as one value
        assert (
            written_spec.design.security[0].description
            == "Sanitize user inputs: forms, URLs, headers, cookies"
        )


class TestRemoveCommand:
    """Tests for design remove command."""

    @patch("simpletask.commands.design.remove.write_task_file")
    @patch("simpletask.commands.design.remove.parse_task_file")
    @patch("simpletask.commands.design.remove.get_task_file_path")
    def test_remove_all(self, mock_get_path, mock_parse, mock_write, sample_spec_with_design):
        """Remove command clears entire design section with 'all'."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_design

        remove_command(field="all")

        written_spec = mock_write.call_args[0][1]
        assert written_spec.design is None

    @patch("simpletask.commands.design.remove.write_task_file")
    @patch("simpletask.commands.design.remove.parse_task_file")
    @patch("simpletask.commands.design.remove.get_task_file_path")
    def test_remove_patterns_all(
        self, mock_get_path, mock_parse, mock_write, sample_spec_with_design
    ):
        """Remove command clears all patterns without index."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_design

        remove_command(field="patterns")

        written_spec = mock_write.call_args[0][1]
        assert written_spec.design.patterns is None

    @patch("simpletask.commands.design.remove.write_task_file")
    @patch("simpletask.commands.design.remove.parse_task_file")
    @patch("simpletask.commands.design.remove.get_task_file_path")
    def test_remove_patterns_by_index(
        self, mock_get_path, mock_parse, mock_write, sample_spec_with_design
    ):
        """Remove command removes specific pattern by index."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_design

        initial_count = len(sample_spec_with_design.design.patterns)

        remove_command(field="patterns", index=0)

        written_spec = mock_write.call_args[0][1]
        assert len(written_spec.design.patterns) == initial_count - 1

    @patch("simpletask.commands.design.remove.parse_task_file")
    @patch("simpletask.commands.design.remove.get_task_file_path")
    def test_remove_patterns_invalid_index(
        self, mock_get_path, mock_parse, sample_spec_with_design
    ):
        """Remove command handles invalid index gracefully."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_design

        with pytest.raises(typer.Exit):
            remove_command(field="patterns", index=999)

    @patch("simpletask.commands.design.remove.write_task_file")
    @patch("simpletask.commands.design.remove.parse_task_file")
    @patch("simpletask.commands.design.remove.get_task_file_path")
    def test_remove_references_by_index(
        self, mock_get_path, mock_parse, mock_write, sample_spec_with_design
    ):
        """Remove command removes specific reference by index."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_design

        remove_command(field="references", index=0)

        written_spec = mock_write.call_args[0][1]
        assert len(written_spec.design.reference_implementations) == 0

    @patch("simpletask.commands.design.remove.write_task_file")
    @patch("simpletask.commands.design.remove.parse_task_file")
    @patch("simpletask.commands.design.remove.get_task_file_path")
    def test_remove_constraints_all(
        self, mock_get_path, mock_parse, mock_write, sample_spec_with_design
    ):
        """Remove command clears all constraints."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_design

        remove_command(field="constraints")

        written_spec = mock_write.call_args[0][1]
        assert written_spec.design.architectural_constraints is None

    @patch("simpletask.commands.design.remove.write_task_file")
    @patch("simpletask.commands.design.remove.parse_task_file")
    @patch("simpletask.commands.design.remove.get_task_file_path")
    def test_remove_security_all(
        self, mock_get_path, mock_parse, mock_write, sample_spec_with_design
    ):
        """Remove command clears all security requirements."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_design

        remove_command(field="security")

        written_spec = mock_write.call_args[0][1]
        assert written_spec.design.security is None

    @patch("simpletask.commands.design.remove.write_task_file")
    @patch("simpletask.commands.design.remove.parse_task_file")
    @patch("simpletask.commands.design.remove.get_task_file_path")
    def test_remove_error_handling(
        self, mock_get_path, mock_parse, mock_write, sample_spec_with_design
    ):
        """Remove command clears error handling strategy."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_design

        remove_command(field="error-handling")

        written_spec = mock_write.call_args[0][1]
        assert written_spec.design.error_handling is None

    @patch("simpletask.commands.design.remove.parse_task_file")
    @patch("simpletask.commands.design.remove.get_task_file_path")
    def test_remove_invalid_field(self, mock_get_path, mock_parse, sample_spec_with_design):
        """Remove command rejects invalid field names."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_design

        with pytest.raises(typer.Exit):
            remove_command(field="invalid-field")

    @patch("simpletask.commands.design.remove.parse_task_file")
    @patch("simpletask.commands.design.remove.get_task_file_path")
    def test_remove_from_empty_design(self, mock_get_path, mock_parse, sample_spec_without_design):
        """Remove command handles missing design section gracefully."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_without_design

        remove_command(field="patterns")

        # Should not raise exception

    @patch("simpletask.commands.design.remove.parse_task_file")
    @patch("simpletask.commands.design.remove.get_task_file_path")
    def test_remove_empty_list_field(self, mock_get_path, mock_parse, sample_spec_with_design):
        """Remove command handles empty list fields gracefully."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        spec = sample_spec_with_design
        spec.design.patterns = []  # Empty list
        mock_parse.return_value = spec

        remove_command(field="patterns")

        # Should not raise exception
