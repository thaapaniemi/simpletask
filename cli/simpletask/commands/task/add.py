"""Add implementation task command."""

from typing import Optional

import typer

from simpletask.core.models import TaskStatus
from simpletask.core.project import get_task_file_path
from simpletask.core.task_ops import add_implementation_task
from simpletask.utils.console import error, success


def add_command(
    name: str = typer.Argument(..., help="Task name"),
    goal: Optional[str] = typer.Option(None, "--goal", "-g", help="Task goal/description"),
    branch: Optional[str] = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """Add a new implementation task to the task file.

    Examples:
        simpletask task add "Implement authentication"
        simpletask task add "Add tests" --goal "Write unit tests for auth"
        simpletask task add "Update docs" --branch feature-123
    """
    try:
        # Get file path
        file_path = get_task_file_path(branch)

        # Add task
        new_id = add_implementation_task(
            file_path=file_path,
            name=name,
            goal=goal,
            status=TaskStatus.NOT_STARTED,
        )

        success(f"Added task {new_id}: {name}")

    except ValueError as e:
        error(str(e))
    except FileNotFoundError as e:
        error(str(e))
    except Exception as e:
        error(f"Unexpected error: {e}")
