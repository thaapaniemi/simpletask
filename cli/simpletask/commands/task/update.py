"""Update implementation task command."""

import typer

from simpletask.core.models import TaskStatus
from simpletask.core.project import get_task_file_path
from simpletask.core.task_ops import update_implementation_task
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
    branch: str | None = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """Update an implementation task's properties.

    Examples:
        simpletask task update T001 --status completed
        simpletask task update T002 --name "New name" --goal "Updated goal"
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

        # Resolve task file path and update
        file_path = get_task_file_path(branch)
        update_implementation_task(
            file_path,
            task_id,
            name=name,
            goal=goal,
            status=task_status,
        )

        success(f"Updated task {task_id}")

    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        handle_exception(e, "updating task")
