"""Shared quality operations logic for CLI and MCP."""

from typing import Any, Literal

from simpletask.core.models import (
    LintingConfig,
    QualityCheckResult,
    QualityRequirements,
    SecurityCheckConfig,
    SimpleTaskSpec,
    TestingConfig,
    ToolExecutionSpec,
    ToolName,
    TypeCheckConfig,
    WorkflowExecutionSpec,
    WorkflowRunner,
)
from simpletask.core.presets import apply_preset as apply_preset_impl
from simpletask.core.quality_checker import QualityChecker


def run_quality_checks(
    requirements: QualityRequirements,
    lint_only: bool = False,
    test_only: bool = False,
    type_only: bool = False,
    security_only: bool = False,
) -> tuple[list[QualityCheckResult], bool]:
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
    active_filters = sum((lint_only, test_only, type_only, security_only))
    if active_filters > 1:
        raise ValueError(
            "Filter flags are mutually exclusive: at most one of lint_only, test_only, "
            "type_only, security_only may be set at a time"
        )

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


def _build_updated_execution_spec(
    existing: ToolExecutionSpec | WorkflowExecutionSpec | None,
    tool: ToolName | None,
    args: list[str] | None,
    workflow_runner: WorkflowRunner | None,
    workflow_target: str | None,
) -> ToolExecutionSpec | WorkflowExecutionSpec | None:
    """Build an updated execution spec from inputs.

    Returns None when no execution-related inputs are provided (caller should
    leave existing execution spec unchanged).

    Args:
        existing: Current execution spec, if any.
        tool: Tool name for tool-mode execution.
        args: Arguments for tool-mode execution.
        workflow_runner: Runner for workflow-mode execution.
        workflow_target: Target/rule for workflow-mode execution.

    Returns:
        Updated execution spec, or None if no execution-related inputs provided.

    Raises:
        ValueError: If workflow and tool inputs are mixed, or required fields are missing.
    """
    has_workflow = workflow_runner is not None or workflow_target is not None
    has_tool = tool is not None or args is not None

    if has_workflow and has_tool:
        raise ValueError(
            "Cannot mix tool and workflow fields: provide either (tool/args) or "
            "(workflow_runner/workflow_target), not both."
        )

    if has_workflow:
        if isinstance(existing, WorkflowExecutionSpec):
            runner = workflow_runner if workflow_runner is not None else existing.runner
            target = workflow_target if workflow_target is not None else existing.target
        else:
            if workflow_runner is None or workflow_target is None:
                raise ValueError(
                    "Both workflow_runner and workflow_target are required when creating "
                    "a new workflow execution spec."
                )
            runner = workflow_runner
            target = workflow_target
        return WorkflowExecutionSpec(runner=runner, target=target)

    if has_tool:
        if isinstance(existing, ToolExecutionSpec):
            new_tool = tool if tool is not None else existing.tool
            new_args = args if args is not None else existing.args
        else:
            if tool is None:
                raise ValueError("tool is required when creating a new tool execution spec.")
            new_tool = tool
            new_args = args if args is not None else []
        return ToolExecutionSpec(tool=new_tool, args=new_args)

    return None


def update_quality_config(
    spec: SimpleTaskSpec,
    config_type: Literal["linting", "type-checking", "testing", "security"],
    tool: ToolName | None = None,
    args: list[str] | None = None,
    enabled: bool | None = None,
    min_coverage: int | None = None,
    timeout: int | None = None,
    workflow_runner: WorkflowRunner | None = None,
    workflow_target: str | None = None,
) -> SimpleTaskSpec:
    """Update quality configuration in task spec.

    Supports both tool-mode (tool/args) and workflow-mode (workflow_runner/workflow_target)
    execution specs. The resulting config always uses the canonical nested execution form.

    Args:
        spec: Task specification to update
        config_type: Type of configuration to update
        tool: Tool to use for tool-mode execution (optional)
        args: Tool arguments for tool-mode execution (optional)
        enabled: Enable/disable status (optional)
        min_coverage: Minimum coverage for testing (optional)
        timeout: Timeout in seconds (optional)
        workflow_runner: Workflow runner for workflow-mode execution (optional)
        workflow_target: Workflow target/rule name (optional)

    Returns:
        Updated task specification

    Raises:
        ValueError: If invalid configuration provided
    """
    if (
        tool is None
        and args is None
        and enabled is None
        and min_coverage is None
        and timeout is None
        and workflow_runner is None
        and workflow_target is None
    ):
        raise ValueError(
            "At least one option must be provided: tool, args, enabled, min_coverage, "
            "timeout, workflow_runner, or workflow_target"
        )

    if min_coverage is not None and config_type != "testing":
        raise ValueError("min_coverage can only be used with 'testing' config type")

    quality_reqs = spec.quality_requirements
    if quality_reqs is None:
        raise ValueError("Task spec has no quality_requirements field")

    quality_reqs = _apply_config_update(
        quality_reqs,
        config_type,
        tool=tool,
        args=args,
        enabled=enabled,
        min_coverage=min_coverage,
        timeout=timeout,
        workflow_runner=workflow_runner,
        workflow_target=workflow_target,
    )

    return spec.model_copy(update={"quality_requirements": quality_reqs})


def _apply_config_update(
    quality_reqs: QualityRequirements,
    config_type: Literal["linting", "type-checking", "testing", "security"],
    tool: ToolName | None,
    args: list[str] | None,
    enabled: bool | None,
    min_coverage: int | None,
    timeout: int | None,
    workflow_runner: WorkflowRunner | None,
    workflow_target: str | None,
) -> QualityRequirements:
    """Apply configuration updates to QualityRequirements.

    Args:
        quality_reqs: Existing quality requirements
        config_type: Which config section to update
        tool: Tool for tool-mode execution
        args: Arguments for tool-mode execution
        enabled: Enable/disable toggle
        min_coverage: Minimum test coverage
        timeout: Execution timeout
        workflow_runner: Runner for workflow-mode execution
        workflow_target: Target for workflow-mode execution

    Returns:
        Updated QualityRequirements

    Raises:
        ValueError: If configuration is invalid or incomplete
    """
    # Scalar-only updates (enabled, timeout, min_coverage)
    scalar_updates: dict[str, Any] = {}
    if enabled is not None:
        scalar_updates["enabled"] = enabled
    if timeout is not None:
        scalar_updates["timeout"] = timeout
    if min_coverage is not None:
        scalar_updates["min_coverage"] = min_coverage

    if config_type == "linting":
        existing_exec = quality_reqs.linting.execution
        new_exec = _build_updated_execution_spec(
            existing_exec, tool, args, workflow_runner, workflow_target
        )
        exec_updates: dict[str, Any] = {}
        if new_exec is not None:
            exec_updates["execution"] = new_exec
            exec_updates["tool"] = None
            exec_updates["args"] = []
        return quality_reqs.model_copy(
            update={
                "linting": quality_reqs.linting.model_copy(
                    update={**exec_updates, **scalar_updates}
                )
            }
        )

    if config_type == "type-checking":
        if quality_reqs.type_checking is None:
            new_exec = _build_updated_execution_spec(
                None, tool, args, workflow_runner, workflow_target
            )
            if new_exec is None:
                raise ValueError(
                    "tool or workflow_runner is required when creating a new type-checking configuration"
                )
            return quality_reqs.model_copy(
                update={
                    "type_checking": TypeCheckConfig(
                        enabled=scalar_updates.get("enabled", False),
                        execution=new_exec,
                        timeout=scalar_updates.get("timeout", 300),
                    )
                }
            )
        existing_exec = quality_reqs.type_checking.execution
        new_exec = _build_updated_execution_spec(
            existing_exec, tool, args, workflow_runner, workflow_target
        )
        exec_updates = {}
        if new_exec is not None:
            exec_updates["execution"] = new_exec
            exec_updates["tool"] = None
            exec_updates["args"] = []
        return quality_reqs.model_copy(
            update={
                "type_checking": quality_reqs.type_checking.model_copy(
                    update={**exec_updates, **scalar_updates}
                )
            }
        )

    if config_type == "testing":
        existing_exec = quality_reqs.testing.execution
        new_exec = _build_updated_execution_spec(
            existing_exec, tool, args, workflow_runner, workflow_target
        )
        exec_updates = {}
        if new_exec is not None:
            exec_updates["execution"] = new_exec
            exec_updates["tool"] = None
            exec_updates["args"] = []
        return quality_reqs.model_copy(
            update={
                "testing": quality_reqs.testing.model_copy(
                    update={**exec_updates, **scalar_updates}
                )
            }
        )

    if config_type == "security":
        if quality_reqs.security_check is None:
            new_exec = _build_updated_execution_spec(
                None, tool, args, workflow_runner, workflow_target
            )
            if new_exec is None:
                raise ValueError(
                    "tool or workflow_runner is required when creating a new security configuration"
                )
            return quality_reqs.model_copy(
                update={
                    "security_check": SecurityCheckConfig(
                        enabled=scalar_updates.get("enabled", False),
                        execution=new_exec,
                        timeout=scalar_updates.get("timeout", 300),
                    )
                }
            )
        existing_exec = quality_reqs.security_check.execution
        new_exec = _build_updated_execution_spec(
            existing_exec, tool, args, workflow_runner, workflow_target
        )
        exec_updates = {}
        if new_exec is not None:
            exec_updates["execution"] = new_exec
            exec_updates["tool"] = None
            exec_updates["args"] = []
        return quality_reqs.model_copy(
            update={
                "security_check": quality_reqs.security_check.model_copy(
                    update={**exec_updates, **scalar_updates}
                )
            }
        )

    raise ValueError(f"Unknown config_type: {config_type!r}")  # pragma: no cover


def update_quality_requirements(
    existing: QualityRequirements | None,
    config_type: Literal["linting", "type-checking", "testing", "security"],
    tool: ToolName | None = None,
    args: list[str] | None = None,
    enabled: bool | None = None,
    min_coverage: int | None = None,
    timeout: int | None = None,
    workflow_runner: WorkflowRunner | None = None,
    workflow_target: str | None = None,
) -> QualityRequirements:
    """Update quality requirements without wrapping in a SimpleTaskSpec.

    Equivalent to update_quality_config but operates directly on QualityRequirements.
    Used by operations that manage quality outside a task file context (e.g. defaults.yml).
    Supports both tool-mode (tool/args) and workflow-mode (workflow_runner/workflow_target)
    execution specs.

    Args:
        existing: Existing quality requirements. When None, only 'linting' and 'testing'
            config_types are accepted; 'type-checking' and 'security' require an existing
            QualityRequirements (apply a preset first) to avoid creating phantom placeholder
            linting/testing entries that would block future fill-gaps-only preset merges.
        config_type: Type of configuration to update
        tool: Tool for tool-mode execution (optional)
        args: Arguments for tool-mode execution (optional)
        enabled: Enable/disable status (optional)
        min_coverage: Minimum coverage for testing (optional)
        timeout: Timeout in seconds (optional)
        workflow_runner: Runner for workflow-mode execution (optional)
        workflow_target: Target/rule for workflow-mode execution (optional)

    Returns:
        Updated QualityRequirements

    Raises:
        ValueError: If invalid configuration provided, or existing is None and config_type
            is 'type-checking' or 'security'.
    """
    if (
        tool is None
        and args is None
        and enabled is None
        and min_coverage is None
        and timeout is None
        and workflow_runner is None
        and workflow_target is None
    ):
        raise ValueError(
            "At least one option must be provided: tool, args, enabled, min_coverage, "
            "timeout, workflow_runner, or workflow_target"
        )

    if min_coverage is not None and config_type != "testing":
        raise ValueError("min_coverage can only be used with 'testing' config type")

    quality_reqs = existing
    if quality_reqs is None:
        if config_type in ("type-checking", "security"):
            raise ValueError(
                f"Cannot configure '{config_type}' when no quality_requirements exist yet. "
                "Apply a preset first (e.g. simpletask defaults quality preset python) "
                "or configure linting/testing before adding type-checking or security."
            )
        # For linting/testing, auto-initialise with minimal placeholders so the
        # caller can configure just that section without needing a preset first.
        quality_reqs = QualityRequirements(
            linting=LintingConfig(enabled=False, tool=ToolName.RUFF, args=[]),
            testing=TestingConfig(enabled=False, tool=ToolName.PYTEST, args=[], min_coverage=0),
        )

    return _apply_config_update(
        quality_reqs,
        config_type,
        tool=tool,
        args=args,
        enabled=enabled,
        min_coverage=min_coverage,
        timeout=timeout,
        workflow_runner=workflow_runner,
        workflow_target=workflow_target,
    )


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
