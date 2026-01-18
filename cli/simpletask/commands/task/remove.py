"""Remove implementation task command."""

from typing import Optional

import typer

from simpletask.core.project import get_task_file_path
from simpletask.core.task_ops import remove_implementation_task
from simpletask.utils.console import confirm, error, success


def remove_command(
    task_id: str = typer.Argument(..., help="Task ID (e.g., T001)"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
    branch: Optional[str] = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """Remove an implementation task from the task file.

    Examples:
        simpletask task remove T003
        simpletask task remove T005 --force
        simpletask task remove T002 --branch feature-123
    """
    try:
        # Confirm removal unless --force
        if not force:
            if not confirm(f"Remove task {task_id}?"):
                raise typer.Abort()

        # Get file path
        file_path = get_task_file_path(branch)

        # Remove task
        remove_implementation_task(file_path, task_id)

        success(f"Removed task {task_id}")

    except typer.Abort:
        raise
    except ValueError as e:
        error(str(e))
    except FileNotFoundError as e:
        error(str(e))
    except Exception as e:
        error(f"Unexpected error: {e}")
