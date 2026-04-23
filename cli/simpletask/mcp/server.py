"""MCP server implementation for simpletask.

Exposes task file operations as MCP tools for AI editor integration.

WithJsonSchema Usage (Architectural Debt):
    This module uses Pydantic's WithJsonSchema to override the JSON Schema that FastMCP
    advertises to MCP clients. This is a pragmatic but imperfect solution to a design issue:

    DESIGN PROBLEM:
      - The task() and criteria() tools use polymorphic dispatch (single function, action-
        dependent parameters) for ergonomic API design in Python.
      - This means some parameters are optional at the Python level (str | None) but are
        contextually required based on the 'action' argument.
      - Example: task(action='get', task_id='T001') requires task_id; task(action='add',
        name='...') requires name but task_id is optional.

    SCHEMA ADVERTISEMENT:
      - Pydantic normally generates anyOf:[string, null] for str | None type hints.
      - Weaker LLMs read "null is valid" and call task(action='get', task_id=None),
        causing infinite retry loops when the error message doesn't fully explain the
        context-dependent requirement.
      - WithJsonSchema overrides advertise {type: string} (no null branch) to prevent
        this confusion.

    THE DECEPTION:
      - The advertised schema ({type: string}) is stricter than the Python type (str | None).
      - Clients that validate responses bidirectionally may see mismatches.
      - This is a known limitation; the correct fix is per-action tools or discriminated
        unions, which were rejected in favor of a simpler API surface.
      - See GitHub issue #14 and related discussions for context.

    RISK MITIGATION:
      - Error messages include concrete call examples so models can self-correct.
      - Runtime validation uses explicit is None / not x checks to handle both None and
        empty strings with distinct error messages.
      - Regression tests (TestSchemaOverrides) verify the advertised schema actually
        reaches the MCP wire protocol.
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
from ..core.defaults import DEFAULTS_FILENAME, load_defaults, save_defaults
from ..core.design_ops import remove_design_field, remove_from_design
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
    ProjectDefaults,
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
    update_quality_requirements,
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
    BatchTaskOperation,  # noqa: F401 — required in module namespace for Pydantic forward-ref resolution at @mcp.tool() registration
    CompactStatusSummary,
    CriterionIdAnnotation,
    OperationsAnnotation,
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
    TaskIdAnnotation,
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

# TargetType for tools that support operating on defaults.yml vs branch task file
TargetType = Literal["branch", "defaults"]


# ---------------------------------------------------------------------------
# Private helpers for defaults-target operations
# ---------------------------------------------------------------------------


def _load_defaults_for_write() -> tuple[ProjectDefaults, str]:
    """Load ProjectDefaults from defaults.yml, creating empty one if missing.

    Used by write operations (set/add/remove) when target='defaults'.

    Returns:
        Tuple of (ProjectDefaults, str path to defaults file)
    """
    project = ensure_project()
    path = project.tasks_dir / DEFAULTS_FILENAME
    defaults = load_defaults(project) or ProjectDefaults()
    return defaults, str(path)


def _commit_defaults(defaults: ProjectDefaults) -> str:
    """Save ProjectDefaults back to defaults.yml and return the path as str."""
    project = ensure_project()
    return str(save_defaults(project, defaults))


def _defaults_compact_summary(_path: object = None) -> CompactStatusSummary:
    """Return a dummy CompactStatusSummary for defaults target responses."""
    return CompactStatusSummary(
        branch="defaults",
        title="Project Defaults",
        overall_status=TaskStatus.NOT_STARTED,
    )


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
    iteration: int | str | None = None,
    status: str | None = None,
    include_completed: bool = False,
    include_design: bool = False,
    include_quality: bool = False,
    full: bool = False,
) -> SimpleTaskGetResponse:
    """Get complete task specification with status summary.

    Returns the full task specification from .tasks/<branch>.yml with
    pre-computed status counts. Optionally validates against JSON schema.

    By default, the response is filtered to reduce context bloat for AI consumers:
    - Only non-completed tasks are returned (exclude completed unless include_completed=True)
    - design section is excluded (include with include_design=True)
    - quality_requirements section is excluded (include with include_quality=True)
    - summary always reflects the FULL unfiltered spec (all task counts)

    Use full=True to bypass all filtering and retrieve the complete unmodified spec.
    This is the equivalent of the pre-filter behavior.

    Args:
        validate: Whether to include schema validation result (default: False).
                  Opt-in to reduce overhead for simple queries.
        iteration: Filter tasks to only those assigned to this iteration ID.
                   Accepts int or string integer (e.g. "2") for Qwen CLI compatibility.
                   Combined with include_completed filter (AND logic).
                   Raises ValueError if the iteration ID does not exist in the spec.
        status: Filter tasks to only those with this status value.
                Valid values: not_started, in_progress, completed, blocked, paused.
                Raises ValueError if the value is not a valid TaskStatus.
        include_completed: Include completed tasks in the response (default: False).
                           When False, tasks with status='completed' are excluded.
        include_design: Include the design section in the response (default: False).
                        When False, spec.design is set to None to reduce payload size.
        include_quality: Include quality_requirements in the response (default: False).
                         When False, spec.quality_requirements is set to None.
        full: Return the complete unfiltered spec (default: False).
              When True, all other filter parameters are ignored and filters_applied is None.
              Equivalent to include_completed=True, include_design=True, include_quality=True
              with no iteration or status filter.

    Returns:
        SimpleTaskGetResponse with spec, file_path, summary, validation, and filters_applied.

    Raises:
        ValueError: If not in a git repository, or branch is None and not on a git branch.
        ValueError: If status is not a valid TaskStatus value.
        ValueError: If iteration ID does not exist in the spec.
        FileNotFoundError: If task file doesn't exist for the specified branch.
        InvalidTaskFileError: If YAML file is malformed or invalid.
    """
    # Coerce iteration string to int (Qwen CLI compat)
    iteration_int: int | None = None
    if iteration is not None:
        try:
            iteration_int = int(iteration)
        except (ValueError, TypeError):
            raise ValueError(f"'iteration' must be an integer, got: {iteration!r}") from None

    # Get file path (normalizes branch name and validates git repo)
    file_path = get_current_task_file_path()

    # Parse task file
    spec = parse_task_file(file_path)

    # Compute status summary BEFORE any filtering — summary always reflects full spec
    summary = compute_status_summary(spec)

    # Optionally validate
    validation = None
    if validate:
        errors = validate_task_file(file_path)
        validation = ValidationResult(valid=len(errors) == 0, errors=errors)

    # Determine filtered spec and filters_applied metadata
    if full:
        # full=True: bypass all filtering, return spec as-is
        filters_applied: dict[str, object] | None = None
        filtered_spec = spec
    else:
        # Validate status parameter
        status_enum: TaskStatus | None = None
        if status is not None:
            try:
                status_enum = TaskStatus(status)
            except ValueError:
                valid = [s.value for s in TaskStatus]
                raise ValueError(f"Invalid status '{status}'. Valid values: {valid}") from None

        # Validate iteration parameter
        if iteration_int is not None:
            existing_ids = {it.id for it in spec.iterations} if spec.iterations else set()
            if iteration_int not in existing_ids:
                raise ValueError(
                    f"Iteration {iteration_int!r} does not exist in the spec. "
                    f"Existing iteration IDs: {sorted(existing_ids)}"
                )

        # Apply task filters (AND logic: all predicates must match)
        total_tasks = len(spec.tasks) if spec.tasks else 0
        filtered_tasks = spec.tasks or []

        if not include_completed:
            filtered_tasks = [t for t in filtered_tasks if t.status != TaskStatus.COMPLETED]
        if status_enum is not None:
            filtered_tasks = [t for t in filtered_tasks if t.status == status_enum]
        if iteration_int is not None:
            filtered_tasks = [t for t in filtered_tasks if t.iteration == iteration_int]

        tasks_returned = len(filtered_tasks)
        tasks_excluded = total_tasks - tasks_returned

        # Build filtered copy without mutating original
        filtered_spec = spec.model_copy(
            update={
                "tasks": filtered_tasks,
                "design": spec.design if include_design else None,
                "quality_requirements": spec.quality_requirements if include_quality else None,
            }
        )

        filters_applied = {
            "include_completed": include_completed,
            "include_design": include_design,
            "include_quality": include_quality,
            "tasks_returned": tasks_returned,
            "tasks_excluded": tasks_excluded,
        }

    return SimpleTaskGetResponse(
        spec=filtered_spec,
        file_path=str(file_path),
        summary=summary,
        validation=validation,
        filters_applied=filters_applied,
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


# DESIGN NOTE: Polymorphic dispatch — single function, action-dependent required parameters.
# task_id is optional at the Python level (str | None) so 'add' and 'batch' can omit it, but
# 'update', 'remove', and 'get' treat it as required and raise ValueError if absent.
# The WithJsonSchema override on task_id advertises {type: string} to MCP clients (rather than
# anyOf:[string,null]) so weaker models cannot infer null is a valid value for those actions.
# Long-term alternative: split into per-action tools or use discriminated unions — rejected
# because it would create verbose tool names (simpletask_task_update, etc.) and break clients.


@mcp.tool()
def task(
    action: Literal["add", "update", "remove", "get", "batch"],
    task_id: TaskIdAnnotation = None,
    name: str | None = None,
    goal: str | None = None,
    status: str | None = None,
    steps: _list[str] | None = None,
    done_when: _list[str] | None = None,
    prerequisites: _list[str] | None = None,
    files: _list[FileAction] | None = None,
    code_examples: _list[CodeExample] | None = None,
    operations: OperationsAnnotation = None,
    iteration: int | str | None = None,
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
            String integers (e.g. "3") are accepted and coerced to int for compatibility with Qwen CLI.
        unassign_iteration: Set True to explicitly remove the task's iteration assignment (update only).
            Cannot be combined with an integer iteration value.

    Returns:
        SimpleTaskWriteResponse for write operations (add/update/remove).
        SimpleTaskItemResponse for get operations.
        SimpleTaskBatchResponse for batch operations.

    Raises:
         ValueError: If required parameters missing or invalid values provided.
    """
    # Coerce string integers to int — Qwen CLI passes integers as strings (e.g. "3" instead of 3),
    # which fails client-side JSON schema validation unless the schema accepts strings too.
    # We accept int | str | None in the signature and coerce here before any logic uses the value.
    iteration_int: int | None = None
    if iteration is not None:
        try:
            iteration_int = int(iteration)
        except (ValueError, TypeError):
            raise ValueError(f"'iteration' must be an integer, got: {iteration!r}") from None

    file_path = get_current_task_file_path()
    summary: StatusSummary | CompactStatusSummary

    match action:
        case "get":
            # Dual guards distinguish None (missing) from "" (empty string) for better
            # error messages. AC8 requires empty strings to be rejected distinctly.
            if task_id is None:
                raise ValueError(
                    "'task_id' is required for action='get'. "
                    "Example: task(action='get', task_id='T001')"
                )
            if not task_id:
                raise ValueError(
                    "'task_id' cannot be empty. Example: task(action='get', task_id='T001')"
                )
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
                iteration=iteration_int,
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
            # Dual guards distinguish None (missing) from "" (empty string) for better
            # error messages. AC8 requires empty strings to be rejected distinctly.
            if task_id is None:
                raise ValueError(
                    "'task_id' is required for action='update'. "
                    "Example: task(action='update', task_id='T001', status='completed')"
                )
            if not task_id:
                raise ValueError(
                    "'task_id' cannot be empty. "
                    "Example: task(action='update', task_id='T001', status='completed')"
                )
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
            elif iteration_int is not None:
                iteration_value = iteration_int

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
            # Dual guards distinguish None (missing) from "" (empty string) for better
            # error messages. AC8 requires empty strings to be rejected distinctly.
            if task_id is None:
                raise ValueError(
                    "'task_id' is required for action='remove'. "
                    "Example: task(action='remove', task_id='T001')"
                )
            if not task_id:
                raise ValueError(
                    "'task_id' cannot be empty. Example: task(action='remove', task_id='T001')"
                )
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
            if operations is None:
                raise ValueError(
                    "'operations' is required for action='batch'. Example: task(action='batch', "
                    'operations=[{"action": "update", "task_id": "T001", "status": "completed"}])'
                )
            if not operations:
                raise ValueError(
                    "'operations' cannot be empty for action='batch'. Example: task(action='batch', "
                    'operations=[{"action": "update", "task_id": "T001", "status": "completed"}])'
                )
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


# DESIGN NOTE: Same polymorphic dispatch pattern as task() above.
# criterion_id is optional at the Python level so 'add' can omit it, but 'complete', 'remove',
# 'get', and 'update' require it. WithJsonSchema advertises {type: string} to prevent models
# from passing null for those actions.


@mcp.tool()
def criteria(
    action: Literal["add", "complete", "remove", "get", "update"],
    criterion_id: CriterionIdAnnotation = None,
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
            # Dual guards distinguish None (missing) from "" (empty string) for better
            # error messages. AC8 requires empty strings to be rejected distinctly.
            if criterion_id is None:
                raise ValueError(
                    "'criterion_id' is required for action='get'. "
                    "Example: criteria(action='get', criterion_id='AC1')"
                )
            if not criterion_id:
                raise ValueError(
                    "'criterion_id' cannot be empty. "
                    "Example: criteria(action='get', criterion_id='AC1')"
                )
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
            # Dual guards distinguish None (missing) from "" (empty string) for better
            # error messages. AC8 requires empty strings to be rejected distinctly.
            if criterion_id is None:
                raise ValueError(
                    "'criterion_id' is required for action='complete'. "
                    "Example: criteria(action='complete', criterion_id='AC1', completed=True)"
                )
            if not criterion_id:
                raise ValueError(
                    "'criterion_id' cannot be empty. "
                    "Example: criteria(action='complete', criterion_id='AC1', completed=True)"
                )
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
            # Dual guards distinguish None (missing) from "" (empty string) for better
            # error messages. AC8 requires empty strings to be rejected distinctly.
            if criterion_id is None:
                raise ValueError(
                    "'criterion_id' is required for action='remove'. "
                    "Example: criteria(action='remove', criterion_id='AC1')"
                )
            if not criterion_id:
                raise ValueError(
                    "'criterion_id' cannot be empty. "
                    "Example: criteria(action='remove', criterion_id='AC1')"
                )
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
            # Dual guards distinguish None (missing) from "" (empty string) for better
            # error messages. AC8 requires empty strings to be rejected distinctly.
            if criterion_id is None:
                raise ValueError(
                    "'criterion_id' is required for action='update'. "
                    "Example: criteria(action='update', criterion_id='AC1', description='New description')"
                )
            if not criterion_id:
                raise ValueError(
                    "'criterion_id' cannot be empty. "
                    "Example: criteria(action='update', criterion_id='AC1', description='New description')"
                )
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
    target: TargetType = "branch",
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
        target: Whether to operate on the current branch task file ('branch', default)
            or the project defaults file ('defaults').

    Note:
        lint_only, test_only, type_only, and security_only are mutually exclusive.
        Pass at most one. They are only valid with action='check'.
        The 'check' action is not supported when target='defaults'.

    Returns:
        SimpleTaskQualityResponse for check/get actions.
        SimpleTaskWriteResponse for set/preset actions.

    Raises:
        ValueError: If required parameters missing, invalid values provided,
            or filter flags (lint_only, test_only, type_only, security_only)
            are used with a non-check action or combined together.
    """
    summary: StatusSummary | CompactStatusSummary

    # Validate that filter flags are only used with action='check'
    if action != "check" and any((lint_only, test_only, type_only, security_only)):
        raise ValueError(
            "Filter flags (lint_only, test_only, type_only, security_only) "
            "are only valid with action='check'"
        )

    # 'check' action is not meaningful for defaults
    if action == "check" and target == "defaults":
        raise ValueError(
            "Quality checks can only run against branch task files, not defaults. "
            "Use target='branch' for action='check'."
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

    # ------------------------------------------------------------------ #
    # Defaults target path
    # ------------------------------------------------------------------ #
    if target == "defaults":
        match action:
            case "get":
                project = ensure_project()
                defaults = load_defaults(project) or ProjectDefaults()
                defaults_path = project.tasks_dir / DEFAULTS_FILENAME
                return SimpleTaskQualityResponse(
                    action="quality_get",
                    quality_requirements=defaults.quality_requirements,
                    check_results=None,
                    all_passed=None,
                    applied_fields=None,
                    file_path=str(defaults_path),
                    summary=_defaults_compact_summary(defaults_path),
                )

            case "set":
                if not config_type:
                    raise ValueError("'config_type' is required for action='set'")
                if config_type not in ["linting", "type-checking", "testing", "security"]:
                    raise ValueError(
                        f"Invalid config_type '{config_type}'. "
                        "Valid options: linting, type-checking, testing, security"
                    )
                if min_coverage is not None and config_type != "testing":
                    raise ValueError("min_coverage can only be used with 'testing' config type")

                validated_config_type = cast(
                    Literal["linting", "type-checking", "testing", "security"], config_type
                )
                defaults, _path = _load_defaults_for_write()
                defaults.quality_requirements = update_quality_requirements(
                    existing=defaults.quality_requirements,
                    config_type=validated_config_type,
                    tool=tool_enum,
                    args=args_list if args_list else None,
                    enabled=enabled,
                    min_coverage=min_coverage,
                    timeout=timeout,
                )
                set_defaults_path: str = _commit_defaults(defaults)
                return SimpleTaskWriteResponse(
                    success=True,
                    action="quality_set",
                    message=f"Updated quality configuration for {config_type} in project defaults",
                    file_path=set_defaults_path,
                    summary=_defaults_compact_summary(set_defaults_path),
                    new_item_ids=[],
                )

            case "preset":
                if not preset_name:
                    raise ValueError("'preset_name' is required for action='preset'")
                defaults, _path = _load_defaults_for_write()
                merged, _applied = apply_quality_preset(defaults.quality_requirements, preset_name)
                defaults.quality_requirements = merged
                preset_defaults_path: str = _commit_defaults(defaults)
                return SimpleTaskWriteResponse(
                    success=True,
                    action="quality_preset_applied",
                    message=f"Applied preset '{preset_name}' (filled gaps only) to project defaults",
                    file_path=preset_defaults_path,
                    summary=_defaults_compact_summary(preset_defaults_path),
                    new_item_ids=[],
                )

    # ------------------------------------------------------------------ #
    # Branch target path (existing behaviour)
    # ------------------------------------------------------------------ #
    file_path = get_current_task_file_path()
    spec = parse_task_file(file_path)

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
    target: TargetType = "branch",
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
        target: Whether to operate on the current branch task file ('branch', default)
            or the project defaults file ('defaults').

    Returns:
        SimpleTaskDesignResponse for get action.
        SimpleTaskWriteResponse for set/remove actions.

    Raises:
        ValueError: If required parameters missing or invalid values provided.
    """
    summary: StatusSummary | CompactStatusSummary

    # ------------------------------------------------------------------ #
    # Defaults target path
    # ------------------------------------------------------------------ #
    if target == "defaults":
        project = ensure_project()
        defaults_path = project.tasks_dir / DEFAULTS_FILENAME

        match action:
            case "get":
                defaults = load_defaults(project) or ProjectDefaults()
                return SimpleTaskDesignResponse(
                    action="design_get",
                    design=defaults.design,
                    file_path=str(defaults_path),
                    summary=_defaults_compact_summary(defaults_path),
                )

            case "set":
                if not field:
                    raise ValueError("'field' is required for action='set'")
                if not value:
                    raise ValueError("'value' is required for action='set'")

                defaults = load_defaults(project) or ProjectDefaults()
                if not defaults.design:
                    defaults.design = Design(
                        patterns=None,
                        reference_implementations=None,
                        architectural_constraints=None,
                        security=None,
                        error_handling=None,
                    )

                if field == "pattern":
                    try:
                        pattern = ArchitecturalPattern(value)
                    except ValueError:
                        valid_patterns = ", ".join([p.value for p in ArchitecturalPattern])
                        raise ValueError(
                            f"Invalid pattern: {value}. Valid patterns: {valid_patterns}"
                        ) from None
                    if not defaults.design.patterns:
                        defaults.design.patterns = []
                    defaults.design.patterns.append(pattern)
                    message = f"Added pattern: {pattern.value}"

                elif field == "reference":
                    if not reason:
                        raise ValueError("'reason' is required when field='reference'")
                    if not defaults.design.reference_implementations:
                        defaults.design.reference_implementations = []
                    ref = DesignReference(path=value, reason=reason)
                    defaults.design.reference_implementations.append(ref)
                    message = f"Added reference: {value}"

                elif field == "constraint":
                    if not defaults.design.architectural_constraints:
                        defaults.design.architectural_constraints = []
                    defaults.design.architectural_constraints.append(value)
                    message = "Added constraint"

                elif field == "security":
                    if not category:
                        raise ValueError("'category' is required when field='security'")
                    try:
                        cat = SecurityCategory(category)
                    except ValueError:
                        valid_categories = ", ".join([c.value for c in SecurityCategory])
                        raise ValueError(
                            f"Invalid category: {category}. Valid categories: {valid_categories}"
                        ) from None
                    if not defaults.design.security:
                        defaults.design.security = []
                    req = SecurityRequirement(category=cat, description=value)
                    defaults.design.security.append(req)
                    message = f"Added security requirement: {cat.value}"

                elif field == "error-handling":
                    try:
                        strategy = ErrorHandlingStrategy(value)
                    except ValueError:
                        valid_strategies = ", ".join([s.value for s in ErrorHandlingStrategy])
                        raise ValueError(
                            f"Invalid strategy: {value}. Valid strategies: {valid_strategies}"
                        ) from None
                    defaults.design.error_handling = strategy
                    message = f"Set error handling strategy: {strategy.value}"

                else:
                    raise ValueError(
                        f"Invalid field: {field}. "
                        "Valid options: pattern, reference, constraint, security, error-handling"
                    )

                save_defaults(project, defaults)
                return SimpleTaskWriteResponse(
                    success=True,
                    action="design_set",
                    message=message,
                    file_path=str(defaults_path),
                    summary=_defaults_compact_summary(defaults_path),
                    new_item_ids=[],
                )

            case "remove":
                if not field:
                    raise ValueError("'field' is required for action='remove'")

                defaults = load_defaults(project) or ProjectDefaults()
                updated_design, message = remove_from_design(
                    defaults.design, field, index=index, all_items=all
                )
                defaults.design = updated_design
                save_defaults(project, defaults)
                return SimpleTaskWriteResponse(
                    success=True,
                    action="design_remove",
                    message=message,
                    file_path=str(defaults_path),
                    summary=_defaults_compact_summary(defaults_path),
                    new_item_ids=[],
                )

    # ------------------------------------------------------------------ #
    # Branch target path (existing behaviour)
    # ------------------------------------------------------------------ #
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
    target: TargetType = "branch",
) -> SimpleTaskWriteResponse | SimpleTaskConstraintResponse:
    """Manage implementation constraints.

    Args:
        action: Operation to perform ('add', 'remove', 'list')
        value: Constraint text (required for add)
        index: Constraint index to remove (0-based, required for remove unless all=True)
        all: Remove all constraints (for remove action)
        target: Whether to operate on the current branch task file ('branch', default)
            or the project defaults file ('defaults').

    Returns:
        SimpleTaskWriteResponse for write operations (add/remove).
        SimpleTaskConstraintResponse for list operations.

    Raises:
        ValueError: If required parameters missing or invalid index.
    """
    summary: StatusSummary | CompactStatusSummary

    # ------------------------------------------------------------------ #
    # Defaults target path
    # ------------------------------------------------------------------ #
    if target == "defaults":
        project = ensure_project()
        defaults_path = project.tasks_dir / DEFAULTS_FILENAME

        match action:
            case "list":
                defaults = load_defaults(project) or ProjectDefaults()
                return SimpleTaskConstraintResponse(
                    action="constraint_list",
                    constraints=defaults.constraints,
                    file_path=str(defaults_path),
                    summary=_defaults_compact_summary(defaults_path),
                )

            case "add":
                if value is None:
                    raise ValueError("'value' is required for action='add'")
                defaults = load_defaults(project) or ProjectDefaults()
                if defaults.constraints is None:
                    defaults.constraints = []
                defaults.constraints.append(value)
                save_defaults(project, defaults)
                return SimpleTaskWriteResponse(
                    success=True,
                    action="constraint_added",
                    message="Added constraint to project defaults",
                    file_path=str(defaults_path),
                    summary=_defaults_compact_summary(defaults_path),
                    new_item_ids=[],
                )

            case "remove":
                if not all and index is None:
                    raise ValueError("Either 'index' or 'all=True' is required for action='remove'")
                defaults = load_defaults(project) or ProjectDefaults()
                constraints = defaults.constraints or []
                if all:
                    defaults.constraints = None
                    message = "Removed all constraints from project defaults"
                else:
                    if index is None or index < 0 or index >= len(constraints):
                        raise ValueError(
                            f"Invalid index {index}. Valid range: 0-{len(constraints) - 1}"
                        )
                    constraints.pop(index)
                    defaults.constraints = constraints if constraints else None
                    message = f"Removed constraint {index} from project defaults"
                save_defaults(project, defaults)
                return SimpleTaskWriteResponse(
                    success=True,
                    action="constraint_removed",
                    message=message,
                    file_path=str(defaults_path),
                    summary=_defaults_compact_summary(defaults_path),
                    new_item_ids=[],
                )

    # ------------------------------------------------------------------ #
    # Branch target path (existing behaviour)
    # ------------------------------------------------------------------ #
    file_path = get_current_task_file_path()

    match action:
        case "list":
            spec = parse_task_file(file_path)
            branch_constraints = list_constraints(spec=spec)
            summary = compute_status_summary(spec)

            return SimpleTaskConstraintResponse(
                action="constraint_list",
                constraints=branch_constraints,
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
    target: TargetType = "branch",
) -> SimpleTaskWriteResponse | SimpleTaskContextResponse:
    """Manage context key-value pairs.

    Args:
        action: Operation to perform ('set', 'remove', 'show')
        key: Context key (required for set/remove)
        value: Context value (required for set)
        all: Remove all context entries (for remove action)
        target: Whether to operate on the current branch task file ('branch', default)
            or the project defaults file ('defaults').

    Returns:
        SimpleTaskWriteResponse for write operations (set/remove).
        SimpleTaskContextResponse for show operations.

    Raises:
        ValueError: If required parameters missing or invalid key.
    """
    summary: StatusSummary | CompactStatusSummary

    # ------------------------------------------------------------------ #
    # Defaults target path
    # ------------------------------------------------------------------ #
    if target == "defaults":
        project = ensure_project()
        defaults_path = project.tasks_dir / DEFAULTS_FILENAME

        match action:
            case "show":
                defaults = load_defaults(project) or ProjectDefaults()
                return SimpleTaskContextResponse(
                    action="context_show",
                    context=defaults.context,
                    file_path=str(defaults_path),
                    summary=_defaults_compact_summary(defaults_path),
                )

            case "set":
                if not key:
                    raise ValueError("'key' is required for action='set'")
                if value is None:
                    raise ValueError("'value' is required for action='set'")
                defaults = load_defaults(project) or ProjectDefaults()
                if defaults.context is None:
                    defaults.context = {}
                defaults.context[key] = value
                save_defaults(project, defaults)
                return SimpleTaskWriteResponse(
                    success=True,
                    action="context_set",
                    message=f"Set context key '{key}' in project defaults",
                    file_path=str(defaults_path),
                    summary=_defaults_compact_summary(defaults_path),
                    new_item_ids=[],
                )

            case "remove":
                if not all and not key:
                    raise ValueError("Either 'key' or 'all=True' is required for action='remove'")
                defaults = load_defaults(project) or ProjectDefaults()
                ctx = defaults.context or {}
                if all:
                    defaults.context = None
                    message = "Removed all context entries from project defaults"
                else:
                    if key not in ctx:
                        raise ValueError(f"Context key '{key}' not found in project defaults")
                    del ctx[key]
                    defaults.context = ctx if ctx else None
                    message = f"Removed context key '{key}' from project defaults"
                save_defaults(project, defaults)
                return SimpleTaskWriteResponse(
                    success=True,
                    action="context_removed",
                    message=message,
                    file_path=str(defaults_path),
                    summary=_defaults_compact_summary(defaults_path),
                    new_item_ids=[],
                )

    # ------------------------------------------------------------------ #
    # Branch target path (existing behaviour)
    # ------------------------------------------------------------------ #
    file_path = get_current_task_file_path()

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
    iteration_id: int | str | None = None,
) -> SimpleTaskIterationResponse | SimpleTaskWriteResponse:
    """Manage task iterations for semantic separation of development rounds.

    Args:
        action: Operation to perform ('add', 'list', 'get', 'remove')
        label: Human-readable label for the iteration (required for add)
        iteration_id: Iteration ID (required for get/remove).
            String integers (e.g. "1") are accepted and coerced to int for compatibility with Qwen CLI.

    Returns:
        SimpleTaskIterationResponse for list/get actions.
        SimpleTaskWriteResponse for add/remove actions.

    Raises:
        ValueError: If required parameters missing or iteration not found.
    """
    # Coerce string integers to int — Qwen CLI passes integers as strings.
    iteration_id_int: int | None = None
    if iteration_id is not None:
        try:
            iteration_id_int = int(iteration_id)
        except (ValueError, TypeError):
            raise ValueError(f"'iteration_id' must be an integer, got: {iteration_id!r}") from None

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
            if iteration_id_int is None:
                raise ValueError("'iteration_id' is required for action='get'")
            iter_obj = get_iteration_from_spec(spec, iteration_id_int)
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
            if iteration_id_int is None:
                raise ValueError("'iteration_id' is required for action='remove'")
            spec = remove_iteration_from_spec(spec, iteration_id_int)
            write_task_file(file_path, spec)
            summary = compute_compact_status_summary(spec)
            return SimpleTaskWriteResponse(
                success=True,
                action="iteration_removed",
                message=f"Removed iteration {iteration_id_int}",
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
