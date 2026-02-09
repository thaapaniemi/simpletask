"""Remove implementation task command."""

import typer

from simpletask.core.project import get_task_file_path
from simpletask.core.task_ops import remove_implementation_task
from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.utils.console import confirm, handle_exception, success


def remove_command(
    task_id: str = typer.Argument(..., help="Task ID (e.g., T001)"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
    branch: str | None = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """Remove an implementation task from the task file.

    Examples:
        simpletask task remove T003
        simpletask task remove T005 --force
        simpletask task remove T002 --branch feature-123

    Raises:
        ValueError: If not in a git repository, branch cannot be determined, or task ID not found
        FileNotFoundError: If task file doesn't exist for the specified branch
        InvalidTaskFileError: If task file is malformed and cannot be parsed
        typer.Abort: If user cancels the confirmation prompt
    """
    try:
        # Confirm removal unless --force
        if not force:
            if not confirm(f"Remove task {task_id}?"):
                raise typer.Abort()

        # Resolve task file path and remove
        file_path = get_task_file_path(branch)
        remove_implementation_task(file_path, task_id)

        success(f"Removed task {task_id}")

    except typer.Abort:
        raise
    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        handle_exception(e, "removing task")
