"""Add iteration command."""

import typer

from simpletask.core.iteration_ops import add_iteration
from simpletask.core.project import get_task_file_path
from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.utils.console import handle_exception, success


def add_command(
    label: str = typer.Argument(..., help="Iteration label (e.g. 'MVP', 'v2 polish')"),
    branch: str | None = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """Add a new iteration to the task file.

    Examples:
        simpletask iteration add "MVP"
        simpletask iteration add "v2 polish" --branch feature-123

    Raises:
        ValueError: If not in a git repository or branch cannot be determined
        FileNotFoundError: If task file doesn't exist for the specified branch
        InvalidTaskFileError: If task file is malformed and cannot be parsed
    """
    try:
        file_path = get_task_file_path(branch)
        new_id = add_iteration(file_path, label)

        success(f"Added iteration {new_id}: {label}")

    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        handle_exception(e, "adding iteration")
