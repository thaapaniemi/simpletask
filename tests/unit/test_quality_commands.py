"""Unit tests for quality CLI commands.

Tests cover:
- quality check command with various flags
- quality set command for all config types
- quality show command
- quality preset command including fill-gaps behavior
- Subprocess mocking for command execution
- File I/O mocking for task file operations
"""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import typer
from simpletask.commands.quality.check import check_command
from simpletask.commands.quality.preset import preset_command
from simpletask.commands.quality.set import ConfigType, set_command
from simpletask.commands.quality.show import show_command
from simpletask.core.models import (
    AcceptanceCriterion,
    LintingConfig,
    QualityRequirements,
    SecurityCheckConfig,
    SimpleTaskSpec,
    TestingConfig,
    ToolName,
    TypeCheckConfig,
)


@pytest.fixture
def sample_spec_with_quality() -> SimpleTaskSpec:
    """Create a sample task spec with quality requirements."""
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
            type_checking=TypeCheckConfig(enabled=True, tool=ToolName.MYPY, args=["cli/"]),
            testing=TestingConfig(enabled=True, tool=ToolName.PYTEST, args=[], min_coverage=80),
            security_check=SecurityCheckConfig(enabled=False, tool=None, args=[]),
        ),
    )


class TestCheckCommand:
    """Test quality check command."""

    @patch("simpletask.commands.quality.check.parse_task_file")
    @patch("simpletask.commands.quality.check.get_task_file_path")
    @patch("simpletask.commands.quality.check.run_quality_checks")
    def test_check_all_passing(
        self, mock_run_checks, mock_get_path, mock_parse, sample_spec_with_quality
    ):
        """All checks passing exits with code 0."""
        from simpletask.mcp.models import QualityCheckResult

        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_quality

        # Mock all checks passing
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

        with pytest.raises(typer.Exit) as exc_info:
            check_command()

        # Verify run_quality_checks was called
        mock_run_checks.assert_called_once()

    @patch("simpletask.commands.quality.check.parse_task_file")
    @patch("simpletask.commands.quality.check.get_task_file_path")
    @patch("simpletask.commands.quality.check.run_quality_checks")
    def test_check_some_failing(
        self, mock_run_checks, mock_get_path, mock_parse, sample_spec_with_quality
    ):
        """Some checks failing exits with code 1."""
        from simpletask.mcp.models import QualityCheckResult

        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_quality

        # Mock one check failing
        check_results = [
            QualityCheckResult(
                check_name="Linting", command="ruff check .", passed=True, stdout="OK", stderr=""
            ),
            QualityCheckResult(
                check_name="Type Checking",
                command="mypy cli/",
                passed=False,
                stdout="",
                stderr="Type errors found",
            ),
            QualityCheckResult(
                check_name="Testing", command="pytest", passed=True, stdout="OK", stderr=""
            ),
        ]
        mock_run_checks.return_value = (check_results, False)

        with pytest.raises(typer.Exit) as exc_info:
            check_command()

        assert exc_info.value.exit_code == 1

    @patch("simpletask.commands.quality.check.parse_task_file")
    @patch("simpletask.commands.quality.check.get_task_file_path")
    @patch("simpletask.commands.quality.check.run_quality_checks")
    def test_check_lint_only(
        self, mock_run_checks, mock_get_path, mock_parse, sample_spec_with_quality
    ):
        """--lint-only flag runs only linting check."""
        from simpletask.mcp.models import QualityCheckResult

        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_quality

        # Mock only linting check
        check_results = [
            QualityCheckResult(
                check_name="Linting", command="ruff check .", passed=True, stdout="OK", stderr=""
            ),
        ]
        mock_run_checks.return_value = (check_results, True)

        with pytest.raises(typer.Exit):
            check_command(lint_only=True)

        # Verify lint_only was passed
        mock_run_checks.assert_called_once()
        call_args = mock_run_checks.call_args
        assert call_args[1]["lint_only"] is True

    @patch("simpletask.commands.quality.check.parse_task_file")
    @patch("simpletask.commands.quality.check.get_task_file_path")
    @patch("simpletask.commands.quality.check.run_quality_checks")
    def test_check_test_only(
        self, mock_run_checks, mock_get_path, mock_parse, sample_spec_with_quality
    ):
        """--test-only flag runs only testing check."""
        from simpletask.mcp.models import QualityCheckResult

        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_quality

        # Mock only testing check
        check_results = [
            QualityCheckResult(
                check_name="Testing", command="pytest", passed=True, stdout="OK", stderr=""
            ),
        ]
        mock_run_checks.return_value = (check_results, True)

        with pytest.raises(typer.Exit):
            check_command(test_only=True)

        # Verify test_only was passed
        mock_run_checks.assert_called_once()
        call_args = mock_run_checks.call_args
        assert call_args[1]["test_only"] is True

    @patch("simpletask.commands.quality.check.parse_task_file")
    @patch("simpletask.commands.quality.check.get_task_file_path")
    def test_check_no_enabled_checks(self, mock_get_path, mock_parse):
        """No enabled checks prints warning and returns."""
        spec = SimpleTaskSpec(
            schema_version="1.3",
            branch="test-feature",
            title="Test Feature",
            original_prompt="Test prompt",
            created=datetime.now(UTC),
            acceptance_criteria=[
                AcceptanceCriterion(id="AC1", description="Works", completed=False),
            ],
            quality_requirements=QualityRequirements(
                linting=LintingConfig(enabled=False, tool=ToolName.RUFF, args=["check", "."]),
                type_checking=None,
                testing=TestingConfig(enabled=False, tool=ToolName.PYTEST, args=[]),
                security_check=None,
            ),
        )
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = spec

        # Should return without raising Exit
        check_command()


class TestSetCommand:
    """Test quality set command."""

    @patch("simpletask.commands.quality.set.write_task_file")
    @patch("simpletask.commands.quality.set.parse_task_file")
    @patch("simpletask.commands.quality.set.get_task_file_path")
    def test_set_linting_tool(
        self, mock_get_path, mock_parse, mock_write, sample_spec_with_quality
    ):
        """Setting linting tool updates configuration."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_quality

        set_command(ConfigType.LINTING, tool=ToolName.PYLINT)

        # Verify write_task_file was called
        mock_write.assert_called_once()
        updated_spec = mock_write.call_args[0][1]
        assert updated_spec.quality_requirements.linting.tool == ToolName.PYLINT

    @patch("simpletask.commands.quality.set.write_task_file")
    @patch("simpletask.commands.quality.set.parse_task_file")
    @patch("simpletask.commands.quality.set.get_task_file_path")
    def test_set_testing_coverage(
        self, mock_get_path, mock_parse, mock_write, sample_spec_with_quality
    ):
        """Setting min_coverage for testing updates configuration."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_quality

        set_command(ConfigType.TESTING, min_coverage=90)

        mock_write.assert_called_once()
        updated_spec = mock_write.call_args[0][1]
        assert updated_spec.quality_requirements.testing.min_coverage == 90

    @patch("simpletask.commands.quality.set.write_task_file")
    @patch("simpletask.commands.quality.set.parse_task_file")
    @patch("simpletask.commands.quality.set.get_task_file_path")
    def test_set_enable_disable(
        self, mock_get_path, mock_parse, mock_write, sample_spec_with_quality
    ):
        """Enable/disable flags update enabled field."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_quality

        # Test enable
        set_command(ConfigType.LINTING, enable=True)
        updated_spec = mock_write.call_args[0][1]
        assert updated_spec.quality_requirements.linting.enabled is True

        # Test disable
        mock_parse.return_value = sample_spec_with_quality
        set_command(ConfigType.LINTING, disable=True)
        updated_spec = mock_write.call_args[0][1]
        assert updated_spec.quality_requirements.linting.enabled is False

    @patch("simpletask.commands.quality.set.write_task_file")
    @patch("simpletask.commands.quality.set.parse_task_file")
    @patch("simpletask.commands.quality.set.get_task_file_path")
    def test_set_args(self, mock_get_path, mock_parse, mock_write, sample_spec_with_quality):
        """Setting args updates argument list."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_quality

        # Need to provide tool to avoid validation error
        set_command(ConfigType.LINTING, tool=ToolName.RUFF, args="check,src,--fix")

        mock_write.assert_called_once()
        updated_spec = mock_write.call_args[0][1]
        assert updated_spec.quality_requirements.linting.args == ["check", "src", "--fix"]

    @patch("simpletask.commands.quality.set.get_task_file_path")
    def test_set_coverage_non_testing_error(self, mock_get_path):
        """Setting min_coverage for non-testing config raises error."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")

        with pytest.raises(typer.Exit):
            set_command(ConfigType.LINTING, min_coverage=80)

    @patch("simpletask.commands.quality.set.get_task_file_path")
    def test_set_enable_disable_conflict(self, mock_get_path):
        """Both --enable and --disable raises error."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")

        with pytest.raises(typer.Exit):
            set_command(ConfigType.LINTING, enable=True, disable=True)


class TestShowCommand:
    """Test quality show command."""

    @patch("simpletask.commands.quality.show.parse_task_file")
    @patch("simpletask.commands.quality.show.get_task_file_path")
    def test_show_displays_all_configs(self, mock_get_path, mock_parse, sample_spec_with_quality):
        """Show command displays all quality configurations."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_quality

        # Should not raise any errors
        show_command()

        # Verify file was parsed
        mock_parse.assert_called_once()

    @patch("simpletask.commands.quality.show.parse_task_file")
    @patch("simpletask.commands.quality.show.get_task_file_path")
    def test_show_with_branch_option(self, mock_get_path, mock_parse, sample_spec_with_quality):
        """Show command accepts branch option."""
        mock_get_path.return_value = Path(".tasks/other-branch.yml")
        mock_parse.return_value = sample_spec_with_quality

        show_command(branch="other-branch")

        mock_get_path.assert_called_once_with("other-branch")


class TestPresetCommand:
    """Test quality preset command."""

    @patch("simpletask.commands.quality.preset.write_task_file")
    @patch("simpletask.commands.quality.preset.parse_task_file")
    @patch("simpletask.commands.quality.preset.get_task_file_path")
    def test_preset_apply_python(self, mock_get_path, mock_parse, mock_write):
        """Applying python preset fills gaps."""
        # Spec with no type checking
        spec = SimpleTaskSpec(
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
                type_checking=None,  # Will be filled by preset
                testing=TestingConfig(enabled=True, tool=ToolName.PYTEST, args=[]),
                security_check=None,
            ),
        )
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = spec

        preset_command(preset_name="python")

        mock_write.assert_called_once()
        updated_spec = mock_write.call_args[0][1]
        # Type checking should be filled from preset
        assert updated_spec.quality_requirements.type_checking is not None
        assert updated_spec.quality_requirements.type_checking.tool == ToolName.MYPY

    @patch("simpletask.commands.quality.preset.write_task_file")
    @patch("simpletask.commands.quality.preset.parse_task_file")
    @patch("simpletask.commands.quality.preset.get_task_file_path")
    def test_preset_preserves_existing(
        self, mock_get_path, mock_parse, mock_write, sample_spec_with_quality
    ):
        """Applying preset preserves existing configurations."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")
        mock_parse.return_value = sample_spec_with_quality
        original_tool = sample_spec_with_quality.quality_requirements.linting.tool

        preset_command(preset_name="python")

        mock_write.assert_called_once()
        updated_spec = mock_write.call_args[0][1]
        # Linting should be preserved (not replaced)
        assert updated_spec.quality_requirements.linting.tool == original_tool

    @patch("simpletask.commands.quality.preset.load_all_presets")
    @patch("simpletask.commands.quality.preset.QUALITY_PRESETS")
    def test_preset_list(self, mock_builtin_presets, mock_load_all):
        """--list flag displays available presets."""
        # Mock built-in presets
        mock_builtin_presets.keys.return_value = ["python", "typescript", "node"]

        # Mock all presets (built-in + custom)
        mock_load_all.return_value = {
            "python": None,
            "typescript": None,
            "node": None,
            "custom-preset": None,
        }

        preset_command(preset_name=None, list_flag=True)

        mock_load_all.assert_called_once()

    @patch("simpletask.commands.quality.preset.get_task_file_path")
    def test_preset_invalid_name(self, mock_get_path):
        """Invalid preset name raises error."""
        mock_get_path.return_value = Path(".tasks/test-feature.yml")

        with pytest.raises(typer.Exit):
            preset_command(preset_name="invalid-preset")
