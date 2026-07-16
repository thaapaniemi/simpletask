"""Tests for QualityChecker abstraction."""

from unittest.mock import Mock

import pytest
from simpletask.core.models import (
    LintingConfig,
    QualityCheckResult,
    QualityRequirements,
    SecurityCheckConfig,
    TestingConfig,
    ToolName,
    TypeCheckConfig,
    WorkflowExecutionSpec,
    WorkflowRunner,
)
from simpletask.core.quality_checker import QualityChecker, extract_tool_and_args_from_execution


@pytest.fixture
def mock_runner():
    """Create a mock runner for testing."""
    return Mock()


@pytest.fixture
def sample_requirements():
    """Create sample quality requirements."""
    return QualityRequirements(
        linting=LintingConfig(enabled=True, tool=ToolName.RUFF, args=["check", "."], timeout=300),
        type_checking=TypeCheckConfig(enabled=True, tool=ToolName.MYPY, args=["cli/"], timeout=300),
        testing=TestingConfig(
            enabled=True,
            tool=ToolName.PYTEST,
            args=["--cov=cli/simpletask"],
            min_coverage=80,
            timeout=600,
        ),
        security_check=SecurityCheckConfig(
            enabled=False, tool=ToolName.BANDIT, args=["-r", "."], timeout=300
        ),
    )


class TestQualityChecker:
    """Tests for QualityChecker class."""

    def test_run_all_calls_enabled_checks(self, sample_requirements, mock_runner):
        """QualityChecker.run_all() runs all enabled checks."""
        # Setup mock responses
        mock_runner.run_check.side_effect = [
            QualityCheckResult(
                check_name="Linting", passed=True, stdout="OK", stderr="", command="ruff check ."
            ),
            QualityCheckResult(
                check_name="Type Checking",
                passed=True,
                stdout="OK",
                stderr="",
                command="mypy cli/",
            ),
            QualityCheckResult(
                check_name="Testing",
                passed=True,
                stdout="OK",
                stderr="",
                command="pytest --cov=cli/simpletask",
            ),
        ]

        checker = QualityChecker(sample_requirements, runner=mock_runner)
        results, all_passed = checker.run_all()

        # Should call run_check 3 times (security is disabled)
        assert mock_runner.run_check.call_count == 3
        assert len(results) == 3
        assert all_passed is True

        # Verify calls
        calls = mock_runner.run_check.call_args_list
        assert calls[0][0] == ("Linting", ToolName.RUFF, ["check", "."], 300)
        assert calls[1][0] == ("Type Checking", ToolName.MYPY, ["cli/"], 300)
        assert calls[2][0] == ("Testing", ToolName.PYTEST, ["--cov=cli/simpletask"], 600)

    def test_run_all_detects_failures(self, sample_requirements, mock_runner):
        """QualityChecker.run_all() detects when checks fail."""
        mock_runner.run_check.side_effect = [
            QualityCheckResult(
                check_name="Linting",
                passed=False,
                stdout="",
                stderr="Errors found",
                command="ruff check .",
            ),
            QualityCheckResult(
                check_name="Type Checking",
                passed=True,
                stdout="OK",
                stderr="",
                command="mypy cli/",
            ),
            QualityCheckResult(
                check_name="Testing",
                passed=True,
                stdout="OK",
                stderr="",
                command="pytest --cov=cli/simpletask",
            ),
        ]

        checker = QualityChecker(sample_requirements, runner=mock_runner)
        results, all_passed = checker.run_all()

        assert len(results) == 3
        assert all_passed is False
        assert results[0].passed is False
        assert results[1].passed is True
        assert results[2].passed is True

    def test_run_linting_only(self, sample_requirements, mock_runner):
        """QualityChecker.run_linting_only() runs only linting check."""
        mock_runner.run_check.return_value = QualityCheckResult(
            check_name="Linting", passed=True, stdout="OK", stderr="", command="ruff check ."
        )

        checker = QualityChecker(sample_requirements, runner=mock_runner)
        results, all_passed = checker.run_linting_only()

        assert mock_runner.run_check.call_count == 1
        assert len(results) == 1
        assert results[0].check_name == "Linting"
        assert all_passed is True

    def test_run_type_checking_only(self, sample_requirements, mock_runner):
        """QualityChecker.run_type_checking_only() runs only type checking."""
        mock_runner.run_check.return_value = QualityCheckResult(
            check_name="Type Checking", passed=True, stdout="OK", stderr="", command="mypy cli/"
        )

        checker = QualityChecker(sample_requirements, runner=mock_runner)
        results, all_passed = checker.run_type_checking_only()

        assert mock_runner.run_check.call_count == 1
        assert len(results) == 1
        assert results[0].check_name == "Type Checking"
        assert all_passed is True

    def test_run_testing_only(self, sample_requirements, mock_runner):
        """QualityChecker.run_testing_only() runs only tests."""
        mock_runner.run_check.return_value = QualityCheckResult(
            check_name="Testing",
            passed=True,
            stdout="OK",
            stderr="",
            command="pytest --cov=cli/simpletask",
        )

        checker = QualityChecker(sample_requirements, runner=mock_runner)
        results, all_passed = checker.run_testing_only()

        assert mock_runner.run_check.call_count == 1
        assert len(results) == 1
        assert results[0].check_name == "Testing"
        assert all_passed is True

    def test_run_security_only(self, sample_requirements, mock_runner):
        """QualityChecker.run_security_only() runs only security checks when enabled."""
        # Enable security check
        sample_requirements.security_check.enabled = True

        mock_runner.run_check.return_value = QualityCheckResult(
            check_name="Security Check",
            passed=True,
            stdout="OK",
            stderr="",
            command="bandit -r .",
        )

        checker = QualityChecker(sample_requirements, runner=mock_runner)
        results, all_passed = checker.run_security_only()

        assert mock_runner.run_check.call_count == 1
        assert len(results) == 1
        assert results[0].check_name == "Security Check"
        assert all_passed is True

    def test_run_security_only_when_disabled(self, sample_requirements, mock_runner):
        """QualityChecker.run_security_only() returns empty when security disabled."""
        checker = QualityChecker(sample_requirements, runner=mock_runner)
        results, all_passed = checker.run_security_only()

        assert mock_runner.run_check.call_count == 0
        assert len(results) == 0
        assert all_passed is True  # No checks ran, so vacuously true

    def test_skips_disabled_linting(self, sample_requirements, mock_runner):
        """QualityChecker skips linting when disabled."""
        sample_requirements.linting.enabled = False

        mock_runner.run_check.side_effect = [
            QualityCheckResult(
                check_name="Type Checking",
                passed=True,
                stdout="OK",
                stderr="",
                command="mypy cli/",
            ),
            QualityCheckResult(
                check_name="Testing",
                passed=True,
                stdout="OK",
                stderr="",
                command="pytest --cov=cli/simpletask",
            ),
        ]

        checker = QualityChecker(sample_requirements, runner=mock_runner)
        results, all_passed = checker.run_all()

        # Should call run_check 2 times (linting disabled, security disabled)
        assert mock_runner.run_check.call_count == 2
        assert len(results) == 2
        assert all_passed is True

    def test_skips_none_type_checking(self, sample_requirements, mock_runner):
        """QualityChecker skips type checking when None."""
        sample_requirements.type_checking = None

        mock_runner.run_check.side_effect = [
            QualityCheckResult(
                check_name="Linting", passed=True, stdout="OK", stderr="", command="ruff check ."
            ),
            QualityCheckResult(
                check_name="Testing",
                passed=True,
                stdout="OK",
                stderr="",
                command="pytest --cov=cli/simpletask",
            ),
        ]

        checker = QualityChecker(sample_requirements, runner=mock_runner)
        results, all_passed = checker.run_all()

        # Should call run_check 2 times (type_checking is None, security disabled)
        assert mock_runner.run_check.call_count == 2
        assert len(results) == 2
        assert all_passed is True

    def test_uses_timeout_from_config(self, sample_requirements, mock_runner):
        """QualityChecker passes timeout from config to runner."""
        mock_runner.run_check.return_value = QualityCheckResult(
            check_name="Testing",
            passed=True,
            stdout="OK",
            stderr="",
            command="pytest --cov=cli/simpletask",
        )

        checker = QualityChecker(sample_requirements, runner=mock_runner)
        checker.run_testing_only()

        # Verify timeout of 600 was passed (from sample_requirements)
        calls = mock_runner.run_check.call_args_list
        assert calls[0][0][3] == 600  # timeout is 4th argument


class TestExtractToolAndArgsFromExecutionMoonly:
    """Tests for the WorkflowRunner.MOONLY branch in extract_tool_and_args_from_execution."""

    def _make_spec(self, target: str, no_cache: bool = False, extra_args: list | None = None):
        return WorkflowExecutionSpec(
            runner=WorkflowRunner.MOONLY,
            target=target,
            no_cache=no_cache,
            extra_args=extra_args or [],
        )

    def test_moonly_no_cache_false_returns_correct_tool_and_args(self):
        """MOONLY runner with no_cache=False returns ToolName.MOONLY and [target]."""
        spec = self._make_spec(target="+test", no_cache=False)
        tool, args = extract_tool_and_args_from_execution(spec)
        assert tool == ToolName.MOONLY
        assert args == ["+test"]

    def test_moonly_no_cache_true_prepends_no_cache_flag(self):
        """MOONLY runner with no_cache=True prepends --no-cache before target."""
        spec = self._make_spec(target="+test", no_cache=True)
        tool, args = extract_tool_and_args_from_execution(spec)
        assert tool == ToolName.MOONLY
        assert args == ["--no-cache", "+test"]

    def test_moonly_extra_args_inserted_before_target(self):
        """MOONLY runner with extra_args inserts them between --no-cache (if any) and target."""
        spec = self._make_spec(target="+test", no_cache=False, extra_args=["--verbose"])
        tool, args = extract_tool_and_args_from_execution(spec)
        assert tool == ToolName.MOONLY
        assert args == ["--verbose", "+test"]

    def test_moonly_no_cache_and_extra_args_combined(self):
        """MOONLY runner with both no_cache and extra_args produces correct arg order."""
        spec = self._make_spec(target="+lint", no_cache=True, extra_args=["--push"])
        tool, args = extract_tool_and_args_from_execution(spec)
        assert tool == ToolName.MOONLY
        assert args == ["--no-cache", "--push", "+lint"]
