"""MCP server implementation for simpletask.

Exposes task file operations as MCP tools for AI editor integration.
"""

from __future__ import annotations

import builtins
from typing import Literal, cast

from mcp.server.fastmcp import FastMCP

from ..core.criteria_ops import (
    add_acceptance_criterion,
    mark_criterion_complete,
    remove_acceptance_criterion,
)
from ..core.design_ops import remove_design_field
from ..core.models import (
    ArchitecturalPattern,
    Design,
    DesignReference,
    ErrorHandlingStrategy,
    SecurityCategory,
    SecurityRequirement,
    TaskStatus,
    ToolName,
)
from ..core.project import ensure_project, get_current_task_file_path
from ..core.quality_ops import (
    apply_quality_preset,
    run_quality_checks,
    update_quality_config,
)
from ..core.task_file_ops import create_task_file
from ..core.task_ops import (
    add_implementation_task,
    remove_implementation_task,
    update_implementation_task,
)
from ..core.validation import validate_task_file
from ..core.yaml_parser import parse_task_file, write_task_file
from .models import (
    QualityCheckResult,
    SimpleTaskDesignResponse,
    SimpleTaskGetResponse,
    SimpleTaskItemResponse,
    SimpleTaskQualityResponse,
    SimpleTaskWriteResponse,
    ValidationResult,
    compute_status_summary,
)

# ============================================================================
# IMPORTANT: list() function shadows Python's built-in
# ============================================================================
# This module defines a function named list() which shadows the built-in list.
# This is an intentional design choice to follow MCP naming conventions where
# tool names should be simple and intuitive (get, list, new, task, criteria).
#
# CRITICAL: The _list alias below MUST be preserved for type hints to work.
# Without it, type hints like list[str] would fail after the list() function
# is defined. The from __future__ import annotations at the top of this file
# defers type hint evaluation, allowing us to use list[T] safely.
#
# Architectural tradeoff:
# - PRO: Clean MCP tool names (clients see simpletask_list, not simpletask_list_tasks)
# - PRO: Consistent with Python conventions for module-level functions
# - CON: Shadows built-in list in this module scope
# - CON: Requires _list workaround for type hints
#
# Alternative considered: Use list_tasks() to avoid shadowing
# - Rejected because it creates verbose MCP tool name (simpletask_list_tasks)
# ============================================================================

# Preserve reference to built-in list type before defining list() function
# This allows type hints to use list[T] even after list() function is defined
_list = builtins.list

# Initialize FastMCP server
mcp = FastMCP("simpletask")

__all__ = [
    "criteria",
    "design",
    "get",
    "list",
    "mcp",
    "new",
    "quality",
    "run_server",
    "task",
]


@mcp.tool()
def get(
    validate: bool = False,
) -> SimpleTaskGetResponse:
    """Get complete task specification with status summary.

    Returns the full task specification from .tasks/<branch>.yml with
    pre-computed status counts. Optionally validates against JSON schema.

    Args:
        validate: Whether to include schema validation result (default: False).
                  Opt-in to reduce overhead for simple queries.

    Returns:
        SimpleTaskGetResponse with spec, file_path, summary, and optional validation.

    Raises:
        ValueError: If not in a git repository, or branch is None and not on a git branch.
        FileNotFoundError: If task file doesn't exist for the specified branch.
        InvalidTaskFileError: If YAML file is malformed or invalid.
    """
    # Get file path (normalizes branch name and validates git repo)
    file_path = get_current_task_file_path()

    # Parse task file
    spec = parse_task_file(file_path)

    # Compute status summary
    summary = compute_status_summary(spec)

    # Optionally validate
    validation = None
    if validate:
        errors = validate_task_file(file_path)
        validation = ValidationResult(valid=len(errors) == 0, errors=errors)

    return SimpleTaskGetResponse(
        spec=spec,
        file_path=str(file_path),
        summary=summary,
        validation=validation,
    )


@mcp.tool()
def list() -> _list[str]:
    """List all task file branch names in the project.

    Returns the original branch names (not normalized filenames) from
    all task files in .tasks/ directory.

    Returns:
        List of branch names, sorted alphabetically.

    Raises:
        ValueError: If not in a git repository.
    """
    project = ensure_project()
    return project.list_tasks()


@mcp.tool()
def new(
    branch: str,
    title: str,
    prompt: str,
    criteria: _list[str] | None = None,
) -> SimpleTaskWriteResponse:
    """Create a new task file.

    Creates task file at .tasks/<branch>.yml without creating git branch.
    MCP tools should be atomic - git operations are separate concerns.

    Args:
        branch: Branch/task identifier (e.g., 'feature/user-auth')
        title: Human-readable task title
        prompt: Original user prompt/request
        criteria: Optional list of acceptance criteria descriptions.
                 If None, adds placeholder criterion.
                 If empty list, no criteria added.

    Returns:
        SimpleTaskWriteResponse with minimal confirmation and summary.

    Raises:
        ValueError: If task already exists or not in git repository.
    """
    project = ensure_project()
    spec = create_task_file(project, branch, title, prompt, criteria)
    file_path = project.get_task_file(branch)
    summary = compute_status_summary(spec)

    return SimpleTaskWriteResponse(
        success=True,
        action="task_file_created",
        message=f"Created task file for '{title}' with {len(spec.acceptance_criteria)} criteria",
        file_path=str(file_path),
        summary=summary,
        new_item_id=None,
    )


@mcp.tool()
def task(
    action: Literal["add", "update", "remove", "get"],
    task_id: str | None = None,
    name: str | None = None,
    goal: str | None = None,
    status: str | None = None,
    steps: _list[str] | None = None,
) -> SimpleTaskWriteResponse | SimpleTaskItemResponse:
    """Manage implementation tasks.

    Args:
        action: Operation to perform ('add', 'update', 'remove', 'get')
        task_id: Task ID (required for update/remove/get)
        name: Task name (required for add)
        goal: Task goal/description
        status: Task status for 'update' only: not_started, in_progress, completed, blocked, paused
               Note: 'add' action ignores this - new tasks always start as not_started
        steps: List of detailed task steps (optional for add). None or [] adds placeholder step ['To be defined'].
               Only applies to action='add'.

    Returns:
        SimpleTaskWriteResponse for write operations (add/update/remove).
        SimpleTaskItemResponse for get operations.

    Raises:
        ValueError: If required parameters missing or invalid values provided.
    """
    file_path = get_current_task_file_path()

    match action:
        case "get":
            if not task_id:
                raise ValueError("'task_id' is required for action='get'")
            spec = parse_task_file(file_path)
            task = next((t for t in spec.tasks or [] if t.id == task_id), None)
            if not task:
                raise ValueError(f"Task '{task_id}' not found")
            summary = compute_status_summary(spec)
            return SimpleTaskItemResponse(
                task=task,
                criterion=None,
                file_path=str(file_path),
                summary=summary,
            )

        case "add":
            if task_id is not None:
                raise ValueError(
                    "'task_id' cannot be specified for action='add' (IDs are auto-generated)"
                )
            if not name:
                raise ValueError("'name' is required for action='add'")
            # Note: status param intentionally ignored for add - new tasks start as not_started
            add_implementation_task(file_path, name, goal, steps=steps)
            spec = parse_task_file(file_path)
            summary = compute_status_summary(spec)
            # Find the newly added task (should be last one)
            new_task = spec.tasks[-1] if spec.tasks else None
            return SimpleTaskWriteResponse(
                success=True,
                action="task_added",
                message=f"Added task '{name}' ({new_task.id if new_task else 'unknown'})",
                file_path=str(file_path),
                summary=summary,
                new_item_id=new_task.id if new_task else None,
            )

        case "update":
            if not task_id:
                raise ValueError("'task_id' is required for action='update'")
            task_status = None
            if status:
                try:
                    task_status = TaskStatus(status)
                except ValueError:
                    valid = [s.value for s in TaskStatus]
                    raise ValueError(f"Invalid status '{status}'. Valid: {valid}") from None
            update_implementation_task(file_path, task_id, name, goal, task_status)
            spec = parse_task_file(file_path)
            summary = compute_status_summary(spec)
            return SimpleTaskWriteResponse(
                success=True,
                action="task_updated",
                message=f"Updated task {task_id}",
                file_path=str(file_path),
                summary=summary,
                new_item_id=None,
            )

        case "remove":
            if not task_id:
                raise ValueError("'task_id' is required for action='remove'")
            remove_implementation_task(file_path, task_id)
            spec = parse_task_file(file_path)
            summary = compute_status_summary(spec)
            return SimpleTaskWriteResponse(
                success=True,
                action="task_removed",
                message=f"Removed task {task_id}",
                file_path=str(file_path),
                summary=summary,
                new_item_id=None,
            )


@mcp.tool()
def criteria(
    action: Literal["add", "complete", "remove", "get"],
    criterion_id: str | None = None,
    description: str | None = None,
    completed: bool = True,
) -> SimpleTaskWriteResponse | SimpleTaskItemResponse:
    """Manage acceptance criteria.

    Args:
        action: Operation to perform ('add', 'complete', 'remove', 'get')
        criterion_id: Criterion ID (required for complete/remove/get)
        description: Criterion description (required for add)
        completed: Completion status for 'complete' action (default: True)

    Returns:
        SimpleTaskWriteResponse for write operations (add/complete/remove).
        SimpleTaskItemResponse for get operations.

    Raises:
        ValueError: If required parameters missing or criterion not found.
        Note: Removing the last criterion fails due to min_length=1 schema constraint.
    """
    file_path = get_current_task_file_path()

    match action:
        case "get":
            if not criterion_id:
                raise ValueError("'criterion_id' is required for action='get'")
            spec = parse_task_file(file_path)
            criterion = next((c for c in spec.acceptance_criteria if c.id == criterion_id), None)
            if not criterion:
                raise ValueError(f"Criterion '{criterion_id}' not found")
            summary = compute_status_summary(spec)
            return SimpleTaskItemResponse(
                task=None,
                criterion=criterion,
                file_path=str(file_path),
                summary=summary,
            )

        case "add":
            if criterion_id is not None:
                raise ValueError(
                    "'criterion_id' cannot be specified for action='add' (IDs are auto-generated)"
                )
            if not description:
                raise ValueError("'description' is required for action='add'")
            add_acceptance_criterion(file_path, description)
            spec = parse_task_file(file_path)
            summary = compute_status_summary(spec)
            # Find the newly added criterion (should be last one)
            new_criterion = spec.acceptance_criteria[-1] if spec.acceptance_criteria else None
            return SimpleTaskWriteResponse(
                success=True,
                action="criterion_added",
                message=f"Added criterion ({new_criterion.id if new_criterion else 'unknown'}): {description}",
                file_path=str(file_path),
                summary=summary,
                new_item_id=new_criterion.id if new_criterion else None,
            )

        case "complete":
            if not criterion_id:
                raise ValueError("'criterion_id' is required for action='complete'")
            mark_criterion_complete(file_path, criterion_id, completed)
            spec = parse_task_file(file_path)
            summary = compute_status_summary(spec)
            status_word = "completed" if completed else "incomplete"
            return SimpleTaskWriteResponse(
                success=True,
                action="criterion_completed" if completed else "criterion_uncompleted",
                message=f"Marked criterion {criterion_id} as {status_word}",
                file_path=str(file_path),
                summary=summary,
                new_item_id=None,
            )

        case "remove":
            if not criterion_id:
                raise ValueError("'criterion_id' is required for action='remove'")
            remove_acceptance_criterion(file_path, criterion_id)
            spec = parse_task_file(file_path)
            summary = compute_status_summary(spec)
            return SimpleTaskWriteResponse(
                success=True,
                action="criterion_removed",
                message=f"Removed criterion {criterion_id}",
                file_path=str(file_path),
                summary=summary,
                new_item_id=None,
            )


@mcp.tool()
def quality(
    action: Literal["check", "set", "get", "preset"],
    config_type: str | None = None,
    tool: str | None = None,
    args: str | None = None,
    enabled: bool | None = None,
    min_coverage: int | None = None,
    timeout: int | None = None,
    preset_name: str | None = None,
) -> SimpleTaskQualityResponse | SimpleTaskWriteResponse:
    """Manage quality requirements and run quality checks.

    Args:
        action: Operation to perform ('check', 'set', 'get', 'preset')
        config_type: Config type for 'set' action ('linting', 'type-checking', 'testing', 'security')
        tool: Tool name for 'set' action (e.g., 'ruff', 'mypy', 'pytest')
        args: Comma-separated tool arguments for 'set' action (e.g., 'check,.,--fix')
        enabled: Enable/disable status for 'set' action
        min_coverage: Minimum coverage for 'set' action with testing type
        timeout: Timeout in seconds for 'set' action (default: 300)
        preset_name: Preset name for 'preset' action

    Returns:
        SimpleTaskQualityResponse for check/get actions.
        SimpleTaskWriteResponse for set/preset actions.

    Raises:
        ValueError: If required parameters missing or invalid values provided.
    """
    file_path = get_current_task_file_path()
    spec = parse_task_file(file_path)

    # Parse args if provided
    args_list: _list[str] = []
    if args:
        args_list = [arg.strip() for arg in args.split(",")]

    # Convert tool string to ToolName enum if provided
    tool_enum: ToolName | None = None
    if tool:
        try:
            tool_enum = ToolName(tool)
        except ValueError:
            valid_tools = ", ".join([t.value for t in ToolName])
            raise ValueError(f"Invalid tool '{tool}'. Valid tools: {valid_tools}") from None

    match action:
        case "get":
            summary = compute_status_summary(spec)
            return SimpleTaskQualityResponse(
                action="quality_get",
                quality_requirements=spec.quality_requirements,
                check_results=None,
                all_passed=None,
                applied_fields=None,
                file_path=str(file_path),
                summary=summary,
            )

        case "check":
            # Run all enabled quality checks using shared function
            quality_reqs = spec.quality_requirements
            check_results: _list[QualityCheckResult]
            if quality_reqs is None:
                check_results = []
                all_passed = True
            else:
                check_results, all_passed = run_quality_checks(quality_reqs)

            summary = compute_status_summary(spec)

            return SimpleTaskQualityResponse(
                action="quality_check",
                quality_requirements=None,
                check_results=check_results,
                all_passed=all_passed,
                applied_fields=None,
                file_path=str(file_path),
                summary=summary,
            )

        case "set":
            if not config_type:
                raise ValueError("'config_type' is required for action='set'")
            if config_type not in ["linting", "type-checking", "testing", "security"]:
                raise ValueError(
                    f"Invalid config_type '{config_type}'. "
                    "Valid options: linting, type-checking, testing, security"
                )

            # Validate min_coverage only for testing
            if min_coverage is not None and config_type != "testing":
                raise ValueError("min_coverage can only be used with 'testing' config type")

            # Type narrowing using cast after validation
            validated_config_type = cast(
                Literal["linting", "type-checking", "testing", "security"], config_type
            )

            # Use shared function to update quality config
            spec = update_quality_config(
                spec=spec,
                config_type=validated_config_type,
                tool=tool_enum,
                args=args_list if args_list else None,
                enabled=enabled,
                min_coverage=min_coverage,
                timeout=timeout,
            )

            write_task_file(file_path, spec)
            summary = compute_status_summary(spec)

            return SimpleTaskWriteResponse(
                success=True,
                action="quality_set",
                message=f"Updated quality configuration for {config_type}",
                file_path=str(file_path),
                summary=summary,
                new_item_id=None,
            )

        case "preset":
            if not preset_name:
                raise ValueError("'preset_name' is required for action='preset'")

            # Apply preset using shared function
            merged, _applied = apply_quality_preset(spec.quality_requirements, preset_name)
            spec.quality_requirements = merged

            write_task_file(file_path, spec)
            summary = compute_status_summary(spec)

            return SimpleTaskWriteResponse(
                success=True,
                action="quality_preset_applied",
                message=f"Applied preset '{preset_name}' (filled gaps only)",
                file_path=str(file_path),
                summary=summary,
                new_item_id=None,
            )


@mcp.tool()
def design(
    action: Literal["set", "get", "remove"],
    field: str | None = None,
    value: str | None = None,
    reason: str | None = None,
    category: str | None = None,
    index: int | None = None,
    all: bool = False,
) -> SimpleTaskDesignResponse | SimpleTaskWriteResponse:
    """Manage design guidance and architectural context.

    Args:
        action: Operation to perform ('set', 'get', 'remove')
        field: Field to set/remove ('pattern', 'reference', 'constraint', 'security', 'error-handling')
        value: Value to set (enum value for pattern/error-handling, free text for others)
        reason: Reason for reference (required when field='reference')
        category: Security category (required when field='security')
        index: Index of item to remove (for list fields in 'remove' action)
        all: Remove all items from field or entire design section (for 'remove' action)

    Returns:
        SimpleTaskDesignResponse for get action.
        SimpleTaskWriteResponse for set/remove actions.

    Raises:
        ValueError: If required parameters missing or invalid values provided.
    """
    file_path = get_current_task_file_path()
    spec = parse_task_file(file_path)

    match action:
        case "get":
            summary = compute_status_summary(spec)
            return SimpleTaskDesignResponse(
                action="design_get",
                design=spec.design,
                file_path=str(file_path),
                summary=summary,
            )

        case "set":
            if not field:
                raise ValueError("'field' is required for action='set'")
            if not value:
                raise ValueError("'value' is required for action='set'")

            # Initialize design section if it doesn't exist
            if not spec.design:
                spec.design = Design(
                    patterns=None,
                    reference_implementations=None,
                    architectural_constraints=None,
                    security=None,
                    error_handling=None,
                )

            if field == "pattern":
                # Parse enum value
                try:
                    pattern = ArchitecturalPattern(value)
                except ValueError:
                    valid_patterns = ", ".join([p.value for p in ArchitecturalPattern])
                    raise ValueError(
                        f"Invalid pattern: {value}. Valid patterns: {valid_patterns}"
                    ) from None
                if not spec.design.patterns:
                    spec.design.patterns = []
                spec.design.patterns.append(pattern)
                message = f"Added pattern: {pattern.value}"

            elif field == "reference":
                if not reason:
                    raise ValueError("'reason' is required when field='reference'")
                if not spec.design.reference_implementations:
                    spec.design.reference_implementations = []
                ref = DesignReference(path=value, reason=reason)
                spec.design.reference_implementations.append(ref)
                message = f"Added reference: {value}"

            elif field == "constraint":
                if not spec.design.architectural_constraints:
                    spec.design.architectural_constraints = []
                spec.design.architectural_constraints.append(value)
                message = "Added constraint"

            elif field == "security":
                if not category:
                    raise ValueError("'category' is required when field='security'")
                # Parse category enum
                try:
                    cat = SecurityCategory(category)
                except ValueError:
                    valid_categories = ", ".join([c.value for c in SecurityCategory])
                    raise ValueError(
                        f"Invalid category: {category}. Valid categories: {valid_categories}"
                    ) from None
                if not spec.design.security:
                    spec.design.security = []
                req = SecurityRequirement(category=cat, description=value)
                spec.design.security.append(req)
                message = f"Added security requirement: {cat.value}"

            elif field == "error-handling":
                # Parse enum value
                try:
                    strategy = ErrorHandlingStrategy(value)
                except ValueError:
                    valid_strategies = ", ".join([s.value for s in ErrorHandlingStrategy])
                    raise ValueError(
                        f"Invalid strategy: {value}. Valid strategies: {valid_strategies}"
                    ) from None
                spec.design.error_handling = strategy
                message = f"Set error handling strategy: {strategy.value}"

            else:
                raise ValueError(
                    f"Invalid field: {field}. "
                    "Valid options: pattern, reference, constraint, security, error-handling"
                )

            write_task_file(file_path, spec)
            summary = compute_status_summary(spec)

            return SimpleTaskWriteResponse(
                success=True,
                action="design_set",
                message=message,
                file_path=str(file_path),
                summary=summary,
                new_item_id=None,
            )

        case "remove":
            if not field:
                raise ValueError("'field' is required for action='remove'")

            # Use shared design operations logic
            spec, message = remove_design_field(
                spec=spec,
                field=field,
                index=index,
                all_items=all,  # MCP uses explicit all=True parameter
            )

            write_task_file(file_path, spec)
            summary = compute_status_summary(spec)

            return SimpleTaskWriteResponse(
                success=True,
                action="design_remove",
                message=message,
                file_path=str(file_path),
                summary=summary,
                new_item_id=None,
            )


def run_server() -> None:
    """Run the MCP server on stdio transport.

    This is the entry point called by the 'simpletask serve' command.
    The server runs until the client disconnects or the process is terminated.
    """
    mcp.run()
