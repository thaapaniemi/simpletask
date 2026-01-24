"""Unit tests for MCP quality and design tools.

Tests cover:
- simpletask_quality tool: check, set, get, preset actions
- simpletask_design tool: set, get, remove actions
- File I/O mocking for task file operations
- Subprocess mocking for quality check execution
"""

from datetime import UTC, datetime
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import MagicMock, patch

import pytest
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
    TypeCheckConfig,
)
from simpletask.mcp.server import design, quality


@pytest.fixture
def sample_spec_with_quality() -> SimpleTaskSpec:
    """Create a sample task spec with quality requirements."""
    return SimpleTaskSpec(
        schema_version="1.0",
        branch="test-feature",
        title="Test Feature",
        original_prompt="Test prompt",
        created=datetime.now(UTC),
        acceptance_criteria=[
            AcceptanceCriterion(id="AC1", description="Works", completed=False),
        ],
        quality_requirements=QualityRequirements(
            linting=LintingConfig(enabled=True, tool=ToolName.RUFF, args=["check", "."]),
            type_checking=TypeCheckConfig(enabled=True, tool=ToolName.MYPY, args=["cli/"]),
            testing=TestingConfig(enabled=True, tool=ToolName.PYTEST, args=[], min_coverage=80),
        ),
    )


@pytest.fixture
def sample_spec_with_design() -> SimpleTaskSpec:
    """Create a sample task spec with design section."""
    return SimpleTaskSpec(
        schema_version="1.0",
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
            architectural_constraints=["Use clean architecture"],
            security=[
                SecurityRequirement(
                    category=SecurityCategory.INPUT_VALIDATION,
                    description="Validate all user inputs",
                ),
            ],
            error_handling=ErrorHandlingStrategy.RESULT_TYPE,
        ),
    )


class TestQualityToolGet:
    """Tests for quality tool 'get' action."""

    @patch("simpletask.mcp.server.parse_task_file")
    @patch("simpletask.mcp.server.get_task_file_path")
    def test_get_returns_quality_requirements(
        self, mock_get_path, mock_parse, sample_spec_with_quality
    ):
        """Quality get action returns current quality requirements."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_quality

        result = quality(action="get")

        assert result.action == "quality_get"
        assert result.quality_requirements is not None
        assert result.quality_requirements.linting.tool == ToolName.RUFF
        assert result.quality_requirements.testing.min_coverage == 80
        assert result.check_results is None
        assert result.all_passed is None


class TestQualityToolCheck:
    """Tests for quality tool 'check' action."""

    @patch("simpletask.mcp.server.run_quality_checks")
    @patch("simpletask.mcp.server.parse_task_file")
    @patch("simpletask.mcp.server.get_task_file_path")
    def test_check_runs_all_enabled_checks(
        self, mock_get_path, mock_parse, mock_run_checks, sample_spec_with_quality
    ):
        """Quality check action runs all enabled quality checks."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_quality

        # Mock check results
        from simpletask.mcp.models import QualityCheckResult

        check_results = [
            QualityCheckResult(
                check_name="Linting", command="ruff check .", passed=True, stdout="OK", stderr=""
            ),
            QualityCheckResult(
                check_name="Type Checking", command="mypy cli/", passed=True, stdout="OK", stderr=""
            ),
            QualityCheckResult(
                check_name="Testing", command="pytest", passed=True, stdout="OK", stderr=""
            ),
        ]
        mock_run_checks.return_value = (check_results, True)

        result = quality(action="check")

        assert result.action == "quality_check"
        assert result.check_results is not None
        assert len(result.check_results) == 3  # linting, type_checking, testing
        assert result.all_passed is True
        mock_run_checks.assert_called_once()

    @patch("simpletask.mcp.server.run_quality_checks")
    @patch("simpletask.mcp.server.parse_task_file")
    @patch("simpletask.mcp.server.get_task_file_path")
    def test_check_detects_failures(
        self, mock_get_path, mock_parse, mock_run_checks, sample_spec_with_quality
    ):
        """Quality check action detects when checks fail."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_quality

        # Mock one passing and one failing check
        from simpletask.mcp.models import QualityCheckResult

        check_results = [
            QualityCheckResult(
                check_name="Linting",
                command="ruff check .",
                passed=False,
                stdout="",
                stderr="Errors found",
            ),
            QualityCheckResult(
                check_name="Type Checking", command="mypy cli/", passed=True, stdout="OK", stderr=""
            ),
            QualityCheckResult(
                check_name="Testing", command="pytest", passed=True, stdout="OK", stderr=""
            ),
        ]
        mock_run_checks.return_value = (check_results, False)

        result = quality(action="check")

        assert result.action == "quality_check"
        assert result.all_passed is False


class TestQualityToolSet:
    """Tests for quality tool 'set' action."""

    @patch("simpletask.mcp.server.write_task_file")
    @patch("simpletask.mcp.server.parse_task_file")
    @patch("simpletask.mcp.server.get_task_file_path")
    def test_set_linting_config(
        self, mock_get_path, mock_parse, mock_write, sample_spec_with_quality
    ):
        """Quality set action updates linting configuration."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_quality

        result = quality(
            action="set",
            config_type="linting",
            tool="eslint",
            args=".,--fix",
        )

        assert result.success is True
        assert result.action == "quality_set"
        assert "linting" in result.message

        # Verify write was called
        written_spec = mock_write.call_args[0][1]
        assert written_spec.quality_requirements.linting.tool == ToolName.ESLINT
        assert written_spec.quality_requirements.linting.args == [".", "--fix"]

    @patch("simpletask.mcp.server.write_task_file")
    @patch("simpletask.mcp.server.parse_task_file")
    @patch("simpletask.mcp.server.get_task_file_path")
    def test_set_testing_with_coverage(
        self, mock_get_path, mock_parse, mock_write, sample_spec_with_quality
    ):
        """Quality set action updates testing configuration with coverage."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_quality

        result = quality(
            action="set",
            config_type="testing",
            min_coverage=90,
        )

        assert result.success is True

        written_spec = mock_write.call_args[0][1]
        assert written_spec.quality_requirements.testing.min_coverage == 90

    @patch("simpletask.mcp.server.parse_task_file")
    @patch("simpletask.mcp.server.get_task_file_path")
    def test_set_requires_config_type(self, mock_get_path, mock_parse, sample_spec_with_quality):
        """Quality set action requires config_type parameter."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_quality

        with pytest.raises(ValueError, match="'config_type' is required"):
            quality(action="set", config_type=None)

    @patch("simpletask.mcp.server.parse_task_file")
    @patch("simpletask.mcp.server.get_task_file_path")
    def test_set_validates_config_type(self, mock_get_path, mock_parse, sample_spec_with_quality):
        """Quality set action validates config_type parameter."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_quality

        with pytest.raises(ValueError, match="Invalid config_type"):
            quality(action="set", config_type="invalid")

    @patch("simpletask.mcp.server.parse_task_file")
    @patch("simpletask.mcp.server.get_task_file_path")
    def test_set_validates_tool_name(self, mock_get_path, mock_parse, sample_spec_with_quality):
        """Quality set action validates tool name against ToolName enum."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_quality

        with pytest.raises(ValueError, match="Invalid tool"):
            quality(action="set", config_type="linting", tool="invalid-tool")

    @patch("simpletask.mcp.server.parse_task_file")
    @patch("simpletask.mcp.server.get_task_file_path")
    def test_set_validates_min_coverage_only_for_testing(
        self, mock_get_path, mock_parse, sample_spec_with_quality
    ):
        """Quality set action validates min_coverage can only be used with testing config."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_quality

        # Should raise error when min_coverage used with linting
        with pytest.raises(ValueError, match="min_coverage can only be used with 'testing'"):
            quality(action="set", config_type="linting", min_coverage=80)

        # Should raise error when min_coverage used with type-checking
        with pytest.raises(ValueError, match="min_coverage can only be used with 'testing'"):
            quality(action="set", config_type="type-checking", min_coverage=80)

        # Should raise error when min_coverage used with security
        with pytest.raises(ValueError, match="min_coverage can only be used with 'testing'"):
            quality(action="set", config_type="security", min_coverage=80)


class TestQualityToolPreset:
    """Tests for quality tool 'preset' action."""

    @patch("simpletask.mcp.server.write_task_file")
    @patch("simpletask.mcp.server.parse_task_file")
    @patch("simpletask.mcp.server.get_task_file_path")
    def test_preset_applies_python_preset(
        self, mock_get_path, mock_parse, mock_write, sample_spec_with_quality
    ):
        """Quality preset action applies python preset."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")

        # Create spec without type_checking to test fill-gaps behavior
        spec = sample_spec_with_quality
        spec.quality_requirements.type_checking = None
        mock_parse.return_value = spec

        result = quality(action="preset", preset_name="python")

        assert result.success is True
        assert result.action == "quality_preset_applied"
        assert "python" in result.message

        # Verify type checking was added
        written_spec = mock_write.call_args[0][1]
        assert written_spec.quality_requirements.type_checking is not None
        assert written_spec.quality_requirements.type_checking.tool == ToolName.MYPY

    @patch("simpletask.mcp.server.parse_task_file")
    @patch("simpletask.mcp.server.get_task_file_path")
    def test_preset_requires_preset_name(self, mock_get_path, mock_parse, sample_spec_with_quality):
        """Quality preset action requires preset_name parameter."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_quality

        with pytest.raises(ValueError, match="'preset_name' is required"):
            quality(action="preset", preset_name=None)


class TestDesignToolGet:
    """Tests for design tool 'get' action."""

    @patch("simpletask.mcp.server.parse_task_file")
    @patch("simpletask.mcp.server.get_task_file_path")
    def test_get_returns_design_section(self, mock_get_path, mock_parse, sample_spec_with_design):
        """Design get action returns current design section."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_design

        result = design(action="get")

        assert result.action == "design_get"
        assert result.design is not None
        assert len(result.design.patterns) == 2
        assert result.design.patterns[0].value == "repository"
        assert result.design.error_handling.value == "result_type"

    @patch("simpletask.mcp.server.parse_task_file")
    @patch("simpletask.mcp.server.get_task_file_path")
    def test_get_returns_none_when_no_design(
        self, mock_get_path, mock_parse, sample_spec_with_quality
    ):
        """Design get action returns None when no design section exists."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_quality

        result = design(action="get")

        assert result.action == "design_get"
        assert result.design is None


class TestDesignToolSet:
    """Tests for design tool 'set' action."""

    @patch("simpletask.mcp.server.write_task_file")
    @patch("simpletask.mcp.server.parse_task_file")
    @patch("simpletask.mcp.server.get_task_file_path")
    def test_set_patterns(self, mock_get_path, mock_parse, mock_write, sample_spec_with_quality):
        """Design set action adds pattern."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_quality

        result = design(
            action="set",
            field="pattern",
            value="repository",
        )

        assert result.success is True
        assert result.action == "design_set"
        assert "pattern" in result.message.lower()

        written_spec = mock_write.call_args[0][1]
        assert written_spec.design is not None
        assert len(written_spec.design.patterns) == 1
        assert written_spec.design.patterns[0].value == "repository"

    @patch("simpletask.mcp.server.write_task_file")
    @patch("simpletask.mcp.server.parse_task_file")
    @patch("simpletask.mcp.server.get_task_file_path")
    def test_set_references_with_reason(
        self, mock_get_path, mock_parse, mock_write, sample_spec_with_quality
    ):
        """Design set action adds reference with reason."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_quality

        result = design(
            action="set",
            field="reference",
            value="src/module.py",
            reason="Similar implementation",
        )

        assert result.success is True

        written_spec = mock_write.call_args[0][1]
        assert len(written_spec.design.reference_implementations) == 1
        assert written_spec.design.reference_implementations[0].path == "src/module.py"
        assert written_spec.design.reference_implementations[0].reason == "Similar implementation"

    @patch("simpletask.mcp.server.parse_task_file")
    @patch("simpletask.mcp.server.get_task_file_path")
    def test_set_references_requires_reason(
        self, mock_get_path, mock_parse, sample_spec_with_quality
    ):
        """Design set action requires reason when field='reference'."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_quality

        with pytest.raises(ValueError, match="'reason' is required"):
            design(action="set", field="reference", value="src/module.py")

    @patch("simpletask.mcp.server.write_task_file")
    @patch("simpletask.mcp.server.parse_task_file")
    @patch("simpletask.mcp.server.get_task_file_path")
    def test_set_error_handling(
        self, mock_get_path, mock_parse, mock_write, sample_spec_with_quality
    ):
        """Design set action sets error handling strategy."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_quality

        result = design(
            action="set",
            field="error-handling",
            value="result_type",
        )

        assert result.success is True

        written_spec = mock_write.call_args[0][1]
        assert written_spec.design.error_handling.value == "result_type"

    @patch("simpletask.mcp.server.parse_task_file")
    @patch("simpletask.mcp.server.get_task_file_path")
    def test_set_requires_field(self, mock_get_path, mock_parse, sample_spec_with_quality):
        """Design set action requires field parameter."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_quality

        with pytest.raises(ValueError, match="'field' is required"):
            design(action="set", field=None, value="test")

    @patch("simpletask.mcp.server.parse_task_file")
    @patch("simpletask.mcp.server.get_task_file_path")
    def test_set_validates_field(self, mock_get_path, mock_parse, sample_spec_with_quality):
        """Design set action validates field parameter."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_quality

        with pytest.raises(ValueError, match="Invalid field"):
            design(action="set", field="invalid", value="test")


class TestDesignToolRemove:
    """Tests for design tool 'remove' action."""

    @patch("simpletask.mcp.server.write_task_file")
    @patch("simpletask.mcp.server.parse_task_file")
    @patch("simpletask.mcp.server.get_task_file_path")
    def test_remove_all(self, mock_get_path, mock_parse, mock_write, sample_spec_with_design):
        """Design remove action removes entire design section with field='all'."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_design

        result = design(action="remove", field="all")

        assert result.success is True
        assert result.action == "design_remove"

        written_spec = mock_write.call_args[0][1]
        assert written_spec.design is None

    @patch("simpletask.mcp.server.write_task_file")
    @patch("simpletask.mcp.server.parse_task_file")
    @patch("simpletask.mcp.server.get_task_file_path")
    def test_remove_patterns_all(
        self, mock_get_path, mock_parse, mock_write, sample_spec_with_design
    ):
        """Design remove action clears all patterns without index."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_design

        result = design(action="remove", field="pattern", all=True)

        assert result.success is True

        written_spec = mock_write.call_args[0][1]
        # When all=True with a specific field, it clears that field
        assert written_spec.design.patterns is None
        # But the design section itself should still exist
        assert written_spec.design is not None

    @patch("simpletask.mcp.server.write_task_file")
    @patch("simpletask.mcp.server.parse_task_file")
    @patch("simpletask.mcp.server.get_task_file_path")
    def test_remove_patterns_by_index(
        self, mock_get_path, mock_parse, mock_write, sample_spec_with_design
    ):
        """Design remove action removes specific pattern by index."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_design

        initial_count = len(sample_spec_with_design.design.patterns)

        result = design(action="remove", field="pattern", index=0)

        assert result.success is True

        written_spec = mock_write.call_args[0][1]
        assert len(written_spec.design.patterns) == initial_count - 1

    @patch("simpletask.mcp.server.parse_task_file")
    @patch("simpletask.mcp.server.get_task_file_path")
    def test_remove_patterns_invalid_index(
        self, mock_get_path, mock_parse, sample_spec_with_design
    ):
        """Design remove action raises error for invalid index."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_design

        with pytest.raises(ValueError, match="Index .* out of range"):
            design(action="remove", field="pattern", index=999)

    @patch("simpletask.mcp.server.parse_task_file")
    @patch("simpletask.mcp.server.get_task_file_path")
    def test_remove_from_missing_design(self, mock_get_path, mock_parse, sample_spec_with_quality):
        """Design remove action raises error when no design section exists."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_quality

        with pytest.raises(ValueError, match="No design section found"):
            design(action="remove", field="patterns")

    @patch("simpletask.mcp.server.parse_task_file")
    @patch("simpletask.mcp.server.get_task_file_path")
    def test_remove_requires_field(self, mock_get_path, mock_parse, sample_spec_with_design):
        """Design remove action requires field parameter."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_design

        with pytest.raises(ValueError, match="'field' is required"):
            design(action="remove", field=None)

    @patch("simpletask.mcp.server.parse_task_file")
    @patch("simpletask.mcp.server.get_task_file_path")
    def test_remove_validates_field(self, mock_get_path, mock_parse, sample_spec_with_design):
        """Design remove action validates field parameter."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_design

        with pytest.raises(ValueError, match="Invalid field"):
            design(action="remove", field="invalid")
