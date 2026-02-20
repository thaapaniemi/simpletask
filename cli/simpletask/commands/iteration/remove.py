"""Remove iteration command."""

import typer

from simpletask.core.iteration_ops import remove_iteration
from simpletask.core.project import get_task_file_path
from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.utils.console import handle_exception, success


def remove_command(
    iteration_id: int = typer.Argument(..., help="Iteration ID to remove"),
    branch: str | None = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """Remove an iteration from the task file.

    Tasks assigned to this iteration will have their iteration field cleared.

    Examples:
        simpletask iteration remove 1
        simpletask iteration remove 2 --branch feature-123

    Raises:
        ValueError: If not in a git repository, branch cannot be determined,
                    or iteration ID does not exist
        FileNotFoundError: If task file doesn't exist for the specified branch
        InvalidTaskFileError: If task file is malformed and cannot be parsed
    """
    try:
        file_path = get_task_file_path(branch)
        remove_iteration(file_path, iteration_id)

        success(f"Removed iteration {iteration_id}")

    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        handle_exception(e, "removing iteration")
