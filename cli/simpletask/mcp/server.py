"""MCP server implementation for simpletask.

Exposes task file operations as MCP tools for AI editor integration.
"""

from typing import Literal

from mcp.server.fastmcp import FastMCP

from ..core.criteria_ops import (
    add_acceptance_criterion,
    mark_criterion_complete,
    remove_acceptance_criterion,
)
from ..core.models import TaskStatus
from ..core.project import ensure_project, get_task_file_path
from ..core.task_file_ops import create_task_file
from ..core.task_ops import (
    add_implementation_task,
    remove_implementation_task,
    update_implementation_task,
)
from ..core.validation import validate_task_file
from ..core.yaml_parser import parse_task_file
from .models import (
    SimpleTaskGetResponse,
    SimpleTaskItemResponse,
    SimpleTaskWriteResponse,
    ValidationResult,
    compute_status_summary,
)

# Initialize FastMCP server
mcp = FastMCP("simpletask")

__all__ = [
    "mcp",
    "run_server",
    "simpletask_criteria",
    "simpletask_get",
    "simpletask_list",
    "simpletask_new",
    "simpletask_task",
]


@mcp.tool()
def simpletask_get(
    branch: str | None = None,
    validate: bool = False,
) -> SimpleTaskGetResponse:
    """Get complete task specification with status summary.

    Returns the full task specification from .tasks/<branch>.yml with
    pre-computed status counts. Optionally validates against JSON schema.

    Args:
        branch: Branch name, or None to use current git branch. The branch name
                will be normalized to a safe filename (e.g., 'feature/auth' -> 'feature-auth.yml').
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
    file_path = get_task_file_path(branch)

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
def simpletask_list() -> list[str]:
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
def simpletask_new(
    branch: str,
    title: str,
    prompt: str,
    criteria: list[str] | None = None,
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
    )


@mcp.tool()
def simpletask_task(
    action: Literal["add", "update", "remove", "get"],
    branch: str | None = None,
    task_id: str | None = None,
    name: str | None = None,
    goal: str | None = None,
    status: str | None = None,
) -> SimpleTaskWriteResponse | SimpleTaskItemResponse:
    """Manage implementation tasks.

    Args:
        action: Operation to perform ('add', 'update', 'remove', 'get')
        branch: Branch name, or None for current git branch
        task_id: Task ID (required for update/remove/get)
        name: Task name (required for add)
        goal: Task goal/description
        status: Task status for 'update' only: not_started, in_progress, completed, blocked
               Note: 'add' action ignores this - new tasks always start as not_started

    Returns:
        SimpleTaskWriteResponse for write operations (add/update/remove).
        SimpleTaskItemResponse for get operations.

    Raises:
        ValueError: If required parameters missing or invalid values provided.
    """
    file_path = get_task_file_path(branch)

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
            add_implementation_task(file_path, name, goal)
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
            )


@mcp.tool()
def simpletask_criteria(
    action: Literal["add", "complete", "remove", "get"],
    branch: str | None = None,
    criterion_id: str | None = None,
    description: str | None = None,
    completed: bool = True,
) -> SimpleTaskWriteResponse | SimpleTaskItemResponse:
    """Manage acceptance criteria.

    Args:
        action: Operation to perform ('add', 'complete', 'remove', 'get')
        branch: Branch name, or None for current git branch
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
    file_path = get_task_file_path(branch)

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
            )


def run_server() -> None:
    """Run the MCP server on stdio transport.

    This is the entry point called by the 'simpletask serve' command.
    The server runs until the client disconnects or the process is terminated.
    """
    mcp.run()
