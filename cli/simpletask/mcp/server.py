"""MCP server implementation for simpletask.

Exposes task file operations as MCP tools for AI editor integration.
"""

import builtins  # noqa: I001
from typing import Literal, cast

from mcp.server.fastmcp import FastMCP

from ..core.constraint_ops import add_constraint, list_constraints, remove_constraint
from ..core.context_ops import remove_context, set_context, show_context
from ..core.criteria_ops import (
    add_acceptance_criterion,
    mark_criterion_complete,
    remove_acceptance_criterion,
    update_acceptance_criterion,
)
from ..core.design_ops import remove_design_field
from ..core.iteration_ops import (
    add_iteration_to_spec,
    get_iteration_from_spec,
    remove_iteration_from_spec,
)
from ..core.models import (
    ArchitecturalPattern,
    CodeExample,
    Design,
    DesignReference,
    ErrorHandlingStrategy,
    FileAction,
    SecurityCategory,
    SecurityRequirement,
    TaskStatus,
    ToolName,
)
from ..core.note_ops import add_note, list_notes, remove_note
from ..core.project import ensure_project, get_current_task_file_path
from ..core.quality_ops import (
    apply_quality_preset,
    run_quality_checks,
    update_quality_config,
)
from ..core.task_file_ops import create_task_file
from ..core.task_ops import (
    _UNSET as _TASK_UNSET,
    _UnsetType as _TaskUnsetType,
)
from ..core.task_ops import (
    add_implementation_task,
    batch_tasks,
    remove_implementation_task,
    update_implementation_task,
)
from ..core.validation import validate_task_file
from ..core.yaml_parser import parse_task_file, write_task_file
from .models import (
    BatchTaskOperation,
    CompactStatusSummary,
    QualityCheckResult,
    SimpleTaskBatchResponse,
    SimpleTaskConstraintResponse,
    SimpleTaskContextResponse,
    SimpleTaskDesignResponse,
    SimpleTaskGetResponse,
    SimpleTaskItemResponse,
    SimpleTaskIterationResponse,
    SimpleTaskNoteResponse,
    SimpleTaskQualityResponse,
    SimpleTaskWriteResponse,
    StatusSummary,
    ValidationResult,
    compute_compact_status_summary,
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
    "iteration",
    "list",
    "mcp",
    "new",
    "note",
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
                 If None or empty list, adds default criterion.
                 If provided with items, must contain at least one item.

    Returns:
        SimpleTaskWriteResponse with minimal confirmation and summary.

    Raises:
        ValueError: If task already exists or not in git repository.
    """
    project = ensure_project()
    spec = create_task_file(project, branch, title, prompt, criteria)
    file_path = project.get_task_file(branch)
    summary = compute_compact_status_summary(spec)

    return SimpleTaskWriteResponse(
        success=True,
        action="task_file_created",
        message=f"Created task file for '{title}' with {len(spec.acceptance_criteria)} criteria",
        file_path=str(file_path),
        summary=summary,
        new_item_ids=[],
    )


@mcp.tool()
def task(
    action: Literal["add", "update", "remove", "get", "batch"],
    task_id: str | None = None,
    name: str | None = None,
    goal: str | None = None,
    status: str | None = None,
    steps: _list[str] | None = None,
    done_when: _list[str] | None = None,
    prerequisites: _list[str] | None = None,
    files: _list[FileAction] | None = None,
    code_examples: _list[CodeExample] | None = None,
    operations: _list[BatchTaskOperation] | None = None,
    iteration: int | None = None,
    unassign_iteration: bool = False,
) -> SimpleTaskWriteResponse | SimpleTaskItemResponse | SimpleTaskBatchResponse:
    """Manage implementation tasks.

    Args:
        action: Operation to perform ('add', 'update', 'remove', 'get', 'batch')
        task_id: Task ID (required for update/remove/get)
        name: Task name (required for add)
        goal: Task goal/description
        status: Task status for 'update' only: not_started, in_progress, completed, blocked, paused
               Note: 'add' action ignores this - new tasks always start as not_started
        steps: List of detailed task steps (optional for add). None or [] adds placeholder step ['To be defined'].
               Only applies to action='add'.
        done_when: List of completion verification conditions (optional for add/update)
        prerequisites: List of prerequisite task IDs (optional for add/update)
        files: List of FileAction objects with path and action fields (optional for add/update)
        code_examples: List of CodeExample objects with language, code, and description fields (optional for add/update)
        operations: List of BatchTaskOperation objects (required for batch action)
        iteration: Iteration ID (int) to assign the task to (for add/update). Omit or pass None to
            preserve existing assignment. Use unassign_iteration=True to explicitly remove assignment.
        unassign_iteration: Set True to explicitly remove the task's iteration assignment (update only).
            Cannot be combined with an integer iteration value.

    Returns:
        SimpleTaskWriteResponse for write operations (add/update/remove).
        SimpleTaskItemResponse for get operations.
        SimpleTaskBatchResponse for batch operations.

    Raises:
        ValueError: If required parameters missing or invalid values provided.
    """
    file_path = get_current_task_file_path()
    summary: StatusSummary | CompactStatusSummary

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

            new_id, spec = add_implementation_task(
                file_path,
                name,
                goal,
                steps=steps,
                done_when=done_when,
                prerequisites=prerequisites,
                files=files,
                code_examples=code_examples,
                iteration=iteration,
            )
            summary = compute_compact_status_summary(spec)
            return SimpleTaskWriteResponse(
                success=True,
                action="task_added",
                message=f"Added task '{name}' ({new_id})",
                file_path=str(file_path),
                summary=summary,
                new_item_ids=[new_id],
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

            # Resolve iteration sentinel — three distinct states over MCP JSON:
            #   unassign_iteration=True   → explicitly remove assignment (set to None)
            #   iteration=<int>           → assign to that iteration ID
            #   neither (default)         → preserve existing assignment (_TASK_UNSET)
            # We need unassign_iteration because MCP JSON cannot distinguish "omit" from "null":
            # both arrive as iteration=None, so None alone is ambiguous.
            if unassign_iteration and iteration is not None:
                raise ValueError("'unassign_iteration' and 'iteration' are mutually exclusive")
            iteration_value: int | None | _TaskUnsetType = _TASK_UNSET
            if unassign_iteration:
                iteration_value = None
            elif iteration is not None:
                iteration_value = iteration

            spec = update_implementation_task(
                file_path,
                task_id,
                name,
                goal,
                task_status,
                steps,
                done_when,
                prerequisites,
                files,
                code_examples,
                iteration=iteration_value,
            )
            summary = compute_compact_status_summary(spec)
            return SimpleTaskWriteResponse(
                success=True,
                action="task_updated",
                message=f"Updated task {task_id}",
                file_path=str(file_path),
                summary=summary,
                new_item_ids=[],
            )

        case "remove":
            if not task_id:
                raise ValueError("'task_id' is required for action='remove'")
            spec = remove_implementation_task(file_path, task_id)
            summary = compute_compact_status_summary(spec)
            return SimpleTaskWriteResponse(
                success=True,
                action="task_removed",
                message=f"Removed task {task_id}",
                file_path=str(file_path),
                summary=summary,
                new_item_ids=[],
            )

        case "batch":
            if not operations:
                raise ValueError("'operations' is required for action='batch'")
            # FastMCP deserializes list[BatchTaskOperation] automatically; operations are
            # already validated BatchTaskOperation instances at this point.
            # Execute batch operations atomically; returns (new_ids, updated spec)
            new_task_ids, spec = batch_tasks(file_path, operations)
            summary = compute_compact_status_summary(spec)
            return SimpleTaskBatchResponse(
                success=True,
                action="batch_tasks_applied",
                message=f"Applied {len(operations)} batch operations",
                file_path=str(file_path),
                summary=summary,
                new_item_ids=new_task_ids,
            )


@mcp.tool()
def criteria(
    action: Literal["add", "complete", "remove", "get", "update"],
    criterion_id: str | None = None,
    description: str | None = None,
    completed: bool = True,
) -> SimpleTaskWriteResponse | SimpleTaskItemResponse:
    """Manage acceptance criteria.

    Args:
        action: Operation to perform ('add', 'complete', 'remove', 'get', 'update')
        criterion_id: Criterion ID (required for complete/remove/get/update)
        description: Criterion description (required for add/update)
        completed: Completion status for 'complete' action (default: True)

    Returns:
        SimpleTaskWriteResponse for write operations (add/complete/remove/update).
        SimpleTaskItemResponse for get operations.

    Raises:
        ValueError: If required parameters missing or criterion not found.
        Note: Removing the last criterion fails due to min_length=1 schema constraint.
    """
    file_path = get_current_task_file_path()
    summary: StatusSummary | CompactStatusSummary

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
            new_id, spec = add_acceptance_criterion(file_path, description)
            summary = compute_compact_status_summary(spec)
            return SimpleTaskWriteResponse(
                success=True,
                action="criterion_added",
                message=f"Added criterion ({new_id}): {description}",
                file_path=str(file_path),
                summary=summary,
                new_item_ids=[new_id],
            )

        case "complete":
            if not criterion_id:
                raise ValueError("'criterion_id' is required for action='complete'")
            spec = mark_criterion_complete(file_path, criterion_id, completed)
            summary = compute_compact_status_summary(spec)
            status_word = "completed" if completed else "incomplete"
            return SimpleTaskWriteResponse(
                success=True,
                action="criterion_completed" if completed else "criterion_uncompleted",
                message=f"Marked criterion {criterion_id} as {status_word}",
                file_path=str(file_path),
                summary=summary,
                new_item_ids=[],
            )

        case "remove":
            if not criterion_id:
                raise ValueError("'criterion_id' is required for action='remove'")
            spec = remove_acceptance_criterion(file_path, criterion_id)
            summary = compute_compact_status_summary(spec)
            return SimpleTaskWriteResponse(
                success=True,
                action="criterion_removed",
                message=f"Removed criterion {criterion_id}",
                file_path=str(file_path),
                summary=summary,
                new_item_ids=[],
            )

        case "update":
            if not criterion_id:
                raise ValueError("'criterion_id' is required for action='update'")
            if not description:
                raise ValueError("'description' is required for action='update'")
            spec = update_acceptance_criterion(file_path, criterion_id, description)
            summary = compute_compact_status_summary(spec)
            return SimpleTaskWriteResponse(
                success=True,
                action="criterion_updated",
                message=f"Updated criterion {criterion_id}: {description}",
                file_path=str(file_path),
                summary=summary,
                new_item_ids=[],
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
    lint_only: bool = False,
    test_only: bool = False,
    type_only: bool = False,
    security_only: bool = False,
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
        lint_only: Only run linting check (for 'check' action). Raises ValueError
            if combined with a non-check action or combined with another filter flag.
        test_only: Only run testing check (for 'check' action). Raises ValueError
            if combined with a non-check action or combined with another filter flag.
        type_only: Only run type-checking check (for 'check' action). Raises
            ValueError if combined with a non-check action or another filter flag.
        security_only: Only run security check (for 'check' action). Raises
            ValueError if combined with a non-check action or another filter flag.

    Note:
        lint_only, test_only, type_only, and security_only are mutually exclusive.
        Pass at most one. They are only valid with action='check'.

    Returns:
        SimpleTaskQualityResponse for check/get actions.
        SimpleTaskWriteResponse for set/preset actions.

    Raises:
        ValueError: If required parameters missing, invalid values provided,
            or filter flags (lint_only, test_only, type_only, security_only)
            are used with a non-check action or combined together.
    """
    file_path = get_current_task_file_path()
    spec = parse_task_file(file_path)
    summary: StatusSummary | CompactStatusSummary

    # Validate that filter flags are only used with action='check'
    if action != "check" and any((lint_only, test_only, type_only, security_only)):
        raise ValueError(
            "Filter flags (lint_only, test_only, type_only, security_only) "
            "are only valid with action='check'"
        )

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
                raise ValueError(
                    "No quality_requirements configuration found in task file. "
                    "Use action='set' or action='preset' to configure quality checks first."
                )
            check_results, all_passed = run_quality_checks(
                quality_reqs,
                lint_only=lint_only,
                test_only=test_only,
                type_only=type_only,
                security_only=security_only,
            )

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
            summary = compute_compact_status_summary(spec)

            return SimpleTaskWriteResponse(
                success=True,
                action="quality_set",
                message=f"Updated quality configuration for {config_type}",
                file_path=str(file_path),
                summary=summary,
                new_item_ids=[],
            )

        case "preset":
            if not preset_name:
                raise ValueError("'preset_name' is required for action='preset'")

            # Apply preset using shared function
            merged, _applied = apply_quality_preset(spec.quality_requirements, preset_name)
            spec.quality_requirements = merged

            write_task_file(file_path, spec)
            summary = compute_compact_status_summary(spec)

            return SimpleTaskWriteResponse(
                success=True,
                action="quality_preset_applied",
                message=f"Applied preset '{preset_name}' (filled gaps only)",
                file_path=str(file_path),
                summary=summary,
                new_item_ids=[],
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
    summary: StatusSummary | CompactStatusSummary

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
            summary = compute_compact_status_summary(spec)

            return SimpleTaskWriteResponse(
                success=True,
                action="design_set",
                message=message,
                file_path=str(file_path),
                summary=summary,
                new_item_ids=[],
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
            summary = compute_compact_status_summary(spec)

            return SimpleTaskWriteResponse(
                success=True,
                action="design_remove",
                message=message,
                file_path=str(file_path),
                summary=summary,
                new_item_ids=[],
            )


@mcp.tool()
def note(
    action: Literal["add", "remove", "list"],
    content: str | None = None,
    task_id: str | None = None,
    index: int | None = None,
    all: bool = False,
    root_only: bool = False,
) -> SimpleTaskWriteResponse | SimpleTaskNoteResponse:
    """Manage notes for root-level and task-level.

    Args:
        action: Operation to perform ('add', 'remove', 'list')
        content: Note content (required for add)
        task_id: Optional task ID. If provided, operates on task-level notes; otherwise root-level
        index: Note index to remove (0-based, required for remove unless all=True)
        all: Remove all notes (for remove action)
        root_only: Only return root-level notes (for list action)

    Returns:
        SimpleTaskWriteResponse for write operations (add/remove).
        SimpleTaskNoteResponse for list operations.

    Raises:
        ValueError: If required parameters missing, task not found, or invalid index.
    """
    file_path = get_current_task_file_path()
    summary: StatusSummary | CompactStatusSummary

    match action:
        case "list":
            spec = parse_task_file(file_path)
            root_notes, task_notes_dict = list_notes(
                spec=spec,
                task_id=task_id,
                root_only=root_only,
            )

            # Count total notes
            total_count = len(root_notes) if root_notes else 0
            for notes in task_notes_dict.values():
                total_count += len(notes)

            summary = compute_status_summary(spec)
            return SimpleTaskNoteResponse(
                action="note_list",
                root_notes=root_notes,
                task_notes=task_notes_dict,
                total_count=total_count,
                file_path=str(file_path),
                summary=summary,
            )

        case "add":
            if not content:
                raise ValueError("'content' is required for action='add'")
            spec = parse_task_file(file_path)
            spec = add_note(spec=spec, content=content, task_id=task_id)
            write_task_file(file_path, spec)
            summary = compute_compact_status_summary(spec)

            location = f"task {task_id}" if task_id else "root"
            return SimpleTaskWriteResponse(
                success=True,
                action="note_added",
                message=f"Added note to {location}",
                file_path=str(file_path),
                summary=summary,
                new_item_ids=[],
            )

        case "remove":
            if not all and index is None:
                raise ValueError("Either 'index' or 'all=True' is required for action='remove'")
            spec = parse_task_file(file_path)
            spec = remove_note(spec=spec, index=index, task_id=task_id, all=all)
            write_task_file(file_path, spec)
            summary = compute_compact_status_summary(spec)

            location = f"task {task_id}" if task_id else "root"
            if all:
                message = f"Removed all notes from {location}"
            else:
                message = f"Removed note {index} from {location}"

            return SimpleTaskWriteResponse(
                success=True,
                action="note_removed",
                message=message,
                file_path=str(file_path),
                summary=summary,
                new_item_ids=[],
            )


@mcp.tool()
def constraint(
    action: Literal["add", "remove", "list"],
    value: str | None = None,
    index: int | None = None,
    all: bool = False,
) -> SimpleTaskWriteResponse | SimpleTaskConstraintResponse:
    """Manage implementation constraints.

    Args:
        action: Operation to perform ('add', 'remove', 'list')
        value: Constraint text (required for add)
        index: Constraint index to remove (0-based, required for remove unless all=True)
        all: Remove all constraints (for remove action)

    Returns:
        SimpleTaskWriteResponse for write operations (add/remove).
        SimpleTaskConstraintResponse for list operations.

    Raises:
        ValueError: If required parameters missing or invalid index.
    """
    file_path = get_current_task_file_path()
    summary: StatusSummary | CompactStatusSummary

    match action:
        case "list":
            spec = parse_task_file(file_path)
            constraints = list_constraints(spec=spec)
            summary = compute_status_summary(spec)

            return SimpleTaskConstraintResponse(
                action="constraint_list",
                constraints=constraints,
                file_path=str(file_path),
                summary=summary,
            )

        case "add":
            if value is None:
                raise ValueError("'value' is required for action='add'")
            spec = parse_task_file(file_path)
            spec = add_constraint(spec=spec, value=value)
            write_task_file(file_path, spec)
            summary = compute_compact_status_summary(spec)

            return SimpleTaskWriteResponse(
                success=True,
                action="constraint_added",
                message="Added constraint",
                file_path=str(file_path),
                summary=summary,
                new_item_ids=[],
            )

        case "remove":
            if not all and index is None:
                raise ValueError("Either 'index' or 'all=True' is required for action='remove'")
            spec = parse_task_file(file_path)
            spec = remove_constraint(spec=spec, index=index, all=all)
            write_task_file(file_path, spec)
            summary = compute_compact_status_summary(spec)

            message = "Removed all constraints" if all else f"Removed constraint {index}"

            return SimpleTaskWriteResponse(
                success=True,
                action="constraint_removed",
                message=message,
                file_path=str(file_path),
                summary=summary,
                new_item_ids=[],
            )


@mcp.tool()
def context(
    action: Literal["set", "remove", "show"],
    key: str | None = None,
    value: str | None = None,
    all: bool = False,
) -> SimpleTaskWriteResponse | SimpleTaskContextResponse:
    """Manage context key-value pairs.

    Args:
        action: Operation to perform ('set', 'remove', 'show')
        key: Context key (required for set/remove)
        value: Context value (required for set)
        all: Remove all context entries (for remove action)

    Returns:
        SimpleTaskWriteResponse for write operations (set/remove).
        SimpleTaskContextResponse for show operations.

    Raises:
        ValueError: If required parameters missing or invalid key.
    """
    file_path = get_current_task_file_path()
    summary: StatusSummary | CompactStatusSummary

    match action:
        case "show":
            spec = parse_task_file(file_path)
            context_data = show_context(spec=spec)
            summary = compute_status_summary(spec)

            return SimpleTaskContextResponse(
                action="context_show",
                context=context_data,
                file_path=str(file_path),
                summary=summary,
            )

        case "set":
            if not key:
                raise ValueError("'key' is required for action='set'")
            if value is None:
                raise ValueError("'value' is required for action='set'")
            spec = parse_task_file(file_path)
            spec = set_context(spec=spec, key=key, value=value)
            write_task_file(file_path, spec)
            summary = compute_compact_status_summary(spec)

            return SimpleTaskWriteResponse(
                success=True,
                action="context_set",
                message=f"Set context key '{key}'",
                file_path=str(file_path),
                summary=summary,
                new_item_ids=[],
            )

        case "remove":
            if not all and not key:
                raise ValueError("Either 'key' or 'all=True' is required for action='remove'")
            spec = parse_task_file(file_path)
            spec = remove_context(spec=spec, key=key, all=all)
            write_task_file(file_path, spec)
            summary = compute_compact_status_summary(spec)

            message = "Removed all context entries" if all else f"Removed context key '{key}'"

            return SimpleTaskWriteResponse(
                success=True,
                action="context_removed",
                message=message,
                file_path=str(file_path),
                summary=summary,
                new_item_ids=[],
            )


@mcp.tool()
def iteration(
    action: Literal["add", "list", "get", "remove"],
    label: str | None = None,
    iteration_id: int | None = None,
) -> SimpleTaskIterationResponse | SimpleTaskWriteResponse:
    """Manage task iterations for semantic separation of development rounds.

    Args:
        action: Operation to perform ('add', 'list', 'get', 'remove')
        label: Human-readable label for the iteration (required for add)
        iteration_id: Iteration ID (required for get/remove)

    Returns:
        SimpleTaskIterationResponse for list/get actions.
        SimpleTaskWriteResponse for add/remove actions.

    Raises:
        ValueError: If required parameters missing or iteration not found.
    """
    file_path = get_current_task_file_path()
    spec = parse_task_file(file_path)
    summary: StatusSummary | CompactStatusSummary

    match action:
        case "list":
            iterations = spec.iterations or []
            summary = compute_status_summary(spec)
            return SimpleTaskIterationResponse(
                action="iteration_list",
                iterations=iterations,
                file_path=str(file_path),
                summary=summary,
            )

        case "get":
            if iteration_id is None:
                raise ValueError("'iteration_id' is required for action='get'")
            iter_obj = get_iteration_from_spec(spec, iteration_id)
            summary = compute_status_summary(spec)
            return SimpleTaskIterationResponse(
                action="iteration_get",
                iterations=[iter_obj],
                file_path=str(file_path),
                summary=summary,
            )

        case "add":
            if not label:
                raise ValueError("'label' is required for action='add'")
            spec, new_id = add_iteration_to_spec(spec, label)
            write_task_file(file_path, spec)
            summary = compute_compact_status_summary(spec)
            return SimpleTaskWriteResponse(
                success=True,
                action="iteration_added",
                message=f"Added iteration {new_id}: {label}",
                file_path=str(file_path),
                summary=summary,
                new_item_ids=[str(new_id)],
            )

        case "remove":
            if iteration_id is None:
                raise ValueError("'iteration_id' is required for action='remove'")
            spec = remove_iteration_from_spec(spec, iteration_id)
            write_task_file(file_path, spec)
            summary = compute_compact_status_summary(spec)
            return SimpleTaskWriteResponse(
                success=True,
                action="iteration_removed",
                message=f"Removed iteration {iteration_id}",
                file_path=str(file_path),
                summary=summary,
                new_item_ids=[],
            )


def run_server() -> None:
    """Run the MCP server on stdio transport.

    This is the entry point called by the 'simpletask serve' command.
    The server runs until the client disconnects or the process is terminated.
    """
    mcp.run()
