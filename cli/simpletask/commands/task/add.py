"""Add implementation task command."""

import typer

from simpletask.core.project import get_task_file_path
from simpletask.core.task_ops import add_implementation_task
from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.utils.console import handle_exception, success


def add_command(
    name: str = typer.Argument(..., help="Task name"),
    goal: str | None = typer.Option(None, "--goal", "-g", help="Task goal/description"),
    iteration: int | None = typer.Option(
        None, "--iteration", "-i", help="Assign task to iteration by ID"
    ),
    branch: str | None = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """Add a new implementation task to the task file.

    Examples:
        simpletask task add "Implement authentication"
        simpletask task add "Add tests" --goal "Write unit tests for auth"
        simpletask task add "Fix bug" --iteration 1
        simpletask task add "Update docs" --branch feature-123

    Raises:
        ValueError: If not in a git repository or branch cannot be determined
        FileNotFoundError: If task file doesn't exist for the specified branch
        InvalidTaskFileError: If task file is malformed and cannot be parsed
    """
    try:
        # Resolve task file path
        file_path = get_task_file_path(branch)
        new_id, _ = add_implementation_task(file_path, name, goal, iteration=iteration)

        iter_suffix = f" (iteration {iteration})" if iteration is not None else ""
        success(f"Added task {new_id}: {name}{iter_suffix}")

    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        handle_exception(e, "adding implementation task")
