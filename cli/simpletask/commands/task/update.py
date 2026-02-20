"""Update implementation task command."""

import typer

from simpletask.core.models import TaskStatus
from simpletask.core.project import get_task_file_path
from simpletask.core.task_ops import _UNSET, _UnsetType, update_implementation_task
from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.utils.console import handle_exception, success


def update_command(
    task_id: str = typer.Argument(..., help="Task ID (e.g., T001)"),
    status: str | None = typer.Option(
        None,
        "--status",
        "-s",
        help="New status (not_started, in_progress, completed, blocked, paused)",
    ),
    name: str | None = typer.Option(None, "--name", "-n", help="New task name"),
    goal: str | None = typer.Option(None, "--goal", "-g", help="New task goal"),
    iteration: int | None = typer.Option(
        None,
        "--iteration",
        "-r",
        help="Assign task to iteration ID",
    ),
    unassign_iteration: bool = typer.Option(
        False,
        "--unassign-iteration",
        help="Remove task from its current iteration",
    ),
    branch: str | None = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """Update an implementation task's properties.

    Examples:
        simpletask task update T001 --status completed
        simpletask task update T002 --name "New name" --goal "Updated goal"
        simpletask task update T003 --iteration 2
        simpletask task update T003 --unassign-iteration
        simpletask task update T003 --status in_progress --branch feature-123

    Raises:
        ValueError: If not in a git repository, branch cannot be determined,
                   task ID not found, or invalid status value provided
        FileNotFoundError: If task file doesn't exist for the specified branch
        InvalidTaskFileError: If task file is malformed and cannot be parsed
    """
    try:
        # Convert status string to enum if provided
        task_status = None
        if status is not None:
            try:
                task_status = TaskStatus(status)
            except ValueError:
                valid = [s.value for s in TaskStatus]
                raise ValueError(f"Invalid status '{status}'. Valid: {valid}") from None

        # Validate mutually exclusive options
        if unassign_iteration and iteration is not None:
            raise ValueError("--unassign-iteration and --iteration are mutually exclusive")

        # Resolve iteration value:
        #   --iteration N         → assign to iteration N
        #   --unassign-iteration  → set to None (remove from iteration)
        #   (neither)             → _UNSET (preserve existing value)
        iteration_value: int | None | _UnsetType
        if unassign_iteration:
            iteration_value = None
        elif iteration is not None:
            iteration_value = iteration
        else:
            iteration_value = _UNSET

        file_path = get_task_file_path(branch)
        update_implementation_task(
            file_path,
            task_id,
            name=name,
            goal=goal,
            status=task_status,
            iteration=iteration_value,
        )

        success(f"Updated task {task_id}")

    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        handle_exception(e, "updating task")
