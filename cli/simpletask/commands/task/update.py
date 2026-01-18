"""Update implementation task command."""

from typing import Optional
import typer

from simpletask.core.project import get_task_file_path
from simpletask.core.task_ops import update_implementation_task
from simpletask.core.models import TaskStatus
from simpletask.utils.console import success, error


def update_command(
    task_id: str = typer.Argument(..., help="Task ID (e.g., T001)"),
    status: Optional[str] = typer.Option(
        None, "--status", "-s", help="New status (not_started, in_progress, completed, blocked)"
    ),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="New task name"),
    goal: Optional[str] = typer.Option(None, "--goal", "-g", help="New task goal"),
    branch: Optional[str] = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """Update an implementation task's properties.

    Examples:
        simpletask task update T001 --status completed
        simpletask task update T002 --name "New name" --goal "Updated goal"
        simpletask task update T003 --status in_progress --branch feature-123
    """
    try:
        # Get file path
        file_path = get_task_file_path(branch)

        # Parse status if provided
        status_enum = None
        if status:
            try:
                status_enum = TaskStatus(status)
            except ValueError:
                error(
                    f"Invalid status: {status}. Valid values: not_started, in_progress, completed, blocked"
                )
                raise typer.Exit(1)

        # Update task
        update_implementation_task(
            file_path=file_path,
            task_id=task_id,
            name=name,
            goal=goal,
            status=status_enum,
        )

        success(f"Updated task {task_id}")

    except ValueError as e:
        error(str(e))
        raise typer.Exit(1)
    except FileNotFoundError as e:
        error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        error(f"Unexpected error: {e}")
        raise typer.Exit(1)
