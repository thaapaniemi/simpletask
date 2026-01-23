"""Shared quality operations logic for CLI and MCP."""

from typing import TYPE_CHECKING, Any, Literal

from simpletask.core.models import (
    QualityRequirements,
    SecurityCheckConfig,
    SimpleTaskSpec,
    ToolName,
    TypeCheckConfig,
)
from simpletask.core.presets import apply_preset as apply_preset_impl
from simpletask.core.quality_checker import QualityChecker

if TYPE_CHECKING:
    from simpletask.mcp.models import QualityCheckResult
else:
    # Import at runtime to avoid circular dependency
    from simpletask.mcp.models import QualityCheckResult


def run_quality_checks(
    requirements: QualityRequirements,
    lint_only: bool = False,
    test_only: bool = False,
    type_only: bool = False,
    security_only: bool = False,
) -> tuple[list["QualityCheckResult"], bool]:
    """Run enabled quality checks based on requirements.

    Args:
        requirements: QualityRequirements configuration
        lint_only: Run only linting checks
        test_only: Run only test checks
        type_only: Run only type checking
        security_only: Run only security checks

    Returns:
        Tuple of (list of check results, all checks passed)
    """
    checker = QualityChecker(requirements)

    # Run specific checks or all checks
    if lint_only:
        return checker.run_linting_only()
    elif test_only:
        return checker.run_testing_only()
    elif type_only:
        return checker.run_type_checking_only()
    elif security_only:
        return checker.run_security_only()
    else:
        return checker.run_all()


def update_quality_config(
    spec: SimpleTaskSpec,
    config_type: Literal["linting", "type-checking", "testing", "security"],
    tool: ToolName | None = None,
    args: list[str] | None = None,
    enabled: bool | None = None,
    min_coverage: int | None = None,
    timeout: int | None = None,
) -> SimpleTaskSpec:
    """Update quality configuration in task spec.

    Args:
        spec: Task specification to update
        config_type: Type of configuration to update
        tool: Tool to use (optional)
        args: Tool arguments (optional)
        enabled: Enable/disable status (optional)
        min_coverage: Minimum coverage for testing (optional)
        timeout: Timeout in seconds (optional)

    Returns:
        Updated task specification

    Raises:
        ValueError: If invalid configuration provided
    """
    # Validate at least one option provided
    if (
        tool is None
        and args is None
        and enabled is None
        and min_coverage is None
        and timeout is None
    ):
        raise ValueError(
            "At least one option must be provided: tool, args, enabled, min_coverage, or timeout"
        )

    # Validate min_coverage only for testing
    if min_coverage is not None and config_type != "testing":
        raise ValueError("min_coverage can only be used with 'testing' config type")

    quality_reqs = spec.quality_requirements
    if quality_reqs is None:
        raise ValueError("Task spec has no quality_requirements field")

    # Build updates dict
    updates: dict[str, Any] = {}
    if tool is not None:
        updates["tool"] = tool
    if args is not None:
        updates["args"] = args
    if enabled is not None:
        updates["enabled"] = enabled
    if min_coverage is not None:
        updates["min_coverage"] = min_coverage
    if timeout is not None:
        updates["timeout"] = timeout

    # Apply updates based on config type
    if config_type == "linting":
        quality_reqs = quality_reqs.model_copy(
            update={"linting": quality_reqs.linting.model_copy(update=updates)}
        )
    elif config_type == "type-checking":
        # Type checking is optional, create if doesn't exist
        if quality_reqs.type_checking is None:
            if tool is None:
                raise ValueError("tool is required when creating a new type-checking configuration")
            quality_reqs = quality_reqs.model_copy(
                update={
                    "type_checking": TypeCheckConfig(
                        enabled=True, tool=tool, args=args if args else []
                    )
                }
            )
        else:
            quality_reqs = quality_reqs.model_copy(
                update={"type_checking": quality_reqs.type_checking.model_copy(update=updates)}
            )
    elif config_type == "testing":
        quality_reqs = quality_reqs.model_copy(
            update={"testing": quality_reqs.testing.model_copy(update=updates)}
        )
    elif config_type == "security":
        # Security check is optional, create if doesn't exist
        if quality_reqs.security_check is None:
            if tool is None:
                raise ValueError("tool is required when creating a new security configuration")
            quality_reqs = quality_reqs.model_copy(
                update={
                    "security_check": SecurityCheckConfig(
                        enabled=True, tool=tool, args=args if args else []
                    )
                }
            )
        else:
            quality_reqs = quality_reqs.model_copy(
                update={"security_check": quality_reqs.security_check.model_copy(update=updates)}
            )

    # Update spec with modified quality requirements
    spec = spec.model_copy(update={"quality_requirements": quality_reqs})

    return spec


def apply_quality_preset(
    existing: QualityRequirements | None, preset_name: str
) -> tuple[QualityRequirements, dict[str, bool]]:
    """Apply quality preset with fill-gaps-only strategy.

    Args:
        existing: Existing quality requirements (can be None)
        preset_name: Name of preset to apply

    Returns:
        Tuple of (merged requirements, dict of applied fields)

    Raises:
        ValueError: If preset_name is invalid
    """
    return apply_preset_impl(existing, preset_name)
