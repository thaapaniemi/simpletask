"""Quality checker abstraction for running quality checks."""

import subprocess
from typing import Protocol

from simpletask.core.models import QualityRequirements, ToolName
from simpletask.core.presets import build_command
from simpletask.mcp.models import QualityCheckResult

# Maximum output size (1MB) to prevent memory exhaustion
MAX_OUTPUT_SIZE = 1024 * 1024  # 1MB in bytes


class QualityCheckRunner(Protocol):
    """Protocol for running quality checks (for testing/mocking)."""

    def run_check(
        self, check_name: str, tool: ToolName, args: list[str], timeout: int | None
    ) -> QualityCheckResult:
        """Run a single quality check."""
        ...


class SubprocessQualityCheckRunner:
    """Default implementation that runs checks using subprocess."""

    def run_check(
        self, check_name: str, tool: ToolName, args: list[str], timeout: int | None = 300
    ) -> QualityCheckResult:
        """Run a single quality check using subprocess.

        Args:
            check_name: Name of the check (e.g., "Linting", "Type Checking")
            tool: Whitelisted tool to execute
            args: Arguments to pass to the tool
            timeout: Timeout in seconds (default: 300)

        Returns:
            QualityCheckResult with execution details
        """
        try:
            command = build_command(tool, args)
            command_str = " ".join(command)

            result = subprocess.run(
                command,
                shell=False,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            # Truncate output if it exceeds maximum size
            stdout = result.stdout
            stderr = result.stderr
            truncated = False

            if len(stdout) > MAX_OUTPUT_SIZE:
                stdout = stdout[:MAX_OUTPUT_SIZE]
                truncated = True

            if len(stderr) > MAX_OUTPUT_SIZE:
                stderr = stderr[:MAX_OUTPUT_SIZE]
                truncated = True

            if truncated:
                truncation_msg = "\n\n[Output truncated - exceeded 1MB limit]"
                if stdout:
                    stdout += truncation_msg
                if stderr:
                    stderr += truncation_msg

            return QualityCheckResult(
                check_name=check_name,
                passed=result.returncode == 0,
                stdout=stdout,
                stderr=stderr,
                command=command_str,
            )
        except subprocess.TimeoutExpired:
            timeout_minutes = timeout // 60 if timeout else 0
            timeout_seconds = timeout % 60 if timeout else 0
            timeout_str = (
                f"{timeout_minutes}m {timeout_seconds}s"
                if timeout_minutes
                else f"{timeout_seconds}s"
            )
            return QualityCheckResult(
                check_name=check_name,
                passed=False,
                stdout="",
                stderr=f"{check_name} timed out after {timeout_str}",
                command=" ".join(build_command(tool, args)),
            )
        except FileNotFoundError:
            return QualityCheckResult(
                check_name=check_name,
                passed=False,
                stdout="",
                stderr=f"{check_name} failed: tool '{tool.value}' not found in PATH",
                command=" ".join(build_command(tool, args)),
            )
        except PermissionError:
            return QualityCheckResult(
                check_name=check_name,
                passed=False,
                stdout="",
                stderr=f"{check_name} failed: tool '{tool.value}' found but not executable (check permissions)",
                command=" ".join(build_command(tool, args)),
            )
        except OSError as e:
            return QualityCheckResult(
                check_name=check_name,
                passed=False,
                stdout="",
                stderr=f"{check_name} failed: OS error - {e!s} (possible resource limit exceeded)",
                command=" ".join(build_command(tool, args)),
            )
        except UnicodeDecodeError:
            return QualityCheckResult(
                check_name=check_name,
                passed=False,
                stdout="",
                stderr=f"{check_name} failed: tool produced invalid UTF-8 output",
                command=" ".join(build_command(tool, args)),
            )
        except Exception as e:
            return QualityCheckResult(
                check_name=check_name,
                passed=False,
                stdout="",
                stderr=f"{check_name} failed to execute: {e!s}",
                command=" ".join(build_command(tool, args)),
            )


class QualityChecker:
    """Abstraction for running quality checks on a codebase.

    This class encapsulates the logic for running quality checks based on
    QualityRequirements configuration. It supports running all checks or
    specific subsets (linting only, testing only, etc.).

    Example:
        checker = QualityChecker(requirements)
        results, all_passed = checker.run_all()
        if not all_passed:
            for result in results:
                if not result.passed:
                    print(f"Failed: {result.check_name}")
    """

    def __init__(
        self,
        requirements: QualityRequirements,
        runner: QualityCheckRunner | None = None,
    ):
        """Initialize quality checker.

        Args:
            requirements: Quality requirements configuration
            runner: Optional custom runner (for testing). Defaults to subprocess runner.
        """
        self.requirements = requirements
        self.runner = runner or SubprocessQualityCheckRunner()

    def run_all(self) -> tuple[list[QualityCheckResult], bool]:
        """Run all enabled quality checks.

        Returns:
            Tuple of (list of check results, all checks passed boolean)
        """
        return self._run_checks(
            lint=True,
            type_check=True,
            test=True,
            security=True,
        )

    def run_linting_only(self) -> tuple[list[QualityCheckResult], bool]:
        """Run only linting checks.

        Returns:
            Tuple of (list of check results, all checks passed boolean)
        """
        return self._run_checks(lint=True)

    def run_type_checking_only(self) -> tuple[list[QualityCheckResult], bool]:
        """Run only type checking.

        Returns:
            Tuple of (list of check results, all checks passed boolean)
        """
        return self._run_checks(type_check=True)

    def run_testing_only(self) -> tuple[list[QualityCheckResult], bool]:
        """Run only tests.

        Returns:
            Tuple of (list of check results, all checks passed boolean)
        """
        return self._run_checks(test=True)

    def run_security_only(self) -> tuple[list[QualityCheckResult], bool]:
        """Run only security checks.

        Returns:
            Tuple of (list of check results, all checks passed boolean)
        """
        return self._run_checks(security=True)

    def _run_checks(
        self,
        lint: bool = False,
        type_check: bool = False,
        test: bool = False,
        security: bool = False,
    ) -> tuple[list[QualityCheckResult], bool]:
        """Internal method to run selected quality checks.

        Args:
            lint: Run linting checks
            type_check: Run type checking
            test: Run tests
            security: Run security checks

        Returns:
            Tuple of (list of check results, all checks passed boolean)
        """
        results: list[QualityCheckResult] = []

        # Run linting
        if lint and self.requirements.linting.enabled:
            result = self.runner.run_check(
                "Linting",
                self.requirements.linting.tool,
                self.requirements.linting.args,
                self.requirements.linting.timeout,
            )
            results.append(result)

        # Run type checking
        if type_check and self.requirements.type_checking:
            if self.requirements.type_checking.enabled:
                result = self.runner.run_check(
                    "Type Checking",
                    self.requirements.type_checking.tool,
                    self.requirements.type_checking.args,
                    self.requirements.type_checking.timeout,
                )
                results.append(result)

        # Run testing
        if test and self.requirements.testing.enabled:
            result = self.runner.run_check(
                "Testing",
                self.requirements.testing.tool,
                self.requirements.testing.args,
                self.requirements.testing.timeout,
            )
            results.append(result)

        # Run security checks
        if security and self.requirements.security_check:
            if self.requirements.security_check.enabled and self.requirements.security_check.tool:
                result = self.runner.run_check(
                    "Security Check",
                    self.requirements.security_check.tool,
                    self.requirements.security_check.args,
                    self.requirements.security_check.timeout,
                )
                results.append(result)

        all_passed = all(result.passed for result in results)
        return results, all_passed
