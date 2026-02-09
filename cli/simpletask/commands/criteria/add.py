"""Add acceptance criterion command."""

import typer

from simpletask.core.criteria_ops import add_acceptance_criterion
from simpletask.core.project import get_task_file_path
from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.utils.console import handle_exception, success


def add_command(
    description: str = typer.Argument(..., help="Criterion description"),
    branch: str | None = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """Add a new acceptance criterion to the task file.

    Examples:
        simpletask criteria add "Feature works correctly"
        simpletask criteria add "Documentation updated" --branch feature-123

    Raises:
        ValueError: If not in a git repository or branch cannot be determined
        FileNotFoundError: If task file doesn't exist for the specified branch
        InvalidTaskFileError: If task file is malformed and cannot be parsed
    """
    try:
        # Resolve task file path
        file_path = get_task_file_path(branch)
        new_id = add_acceptance_criterion(file_path, description)

        success(f"Added criterion {new_id}: {description}")

    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        handle_exception(e, "adding acceptance criterion")
