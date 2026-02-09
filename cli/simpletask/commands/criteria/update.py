"""Update acceptance criterion description command."""

import typer

from simpletask.core.criteria_ops import update_acceptance_criterion
from simpletask.core.project import get_task_file_path
from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.utils.console import handle_exception, success


def update_command(
    criterion_id: str = typer.Argument(..., help="Criterion ID (e.g., AC1)"),
    description: str = typer.Argument(..., help="New criterion description"),
    branch: str | None = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """Update an acceptance criterion's description.

    Examples:
        simpletask criteria update AC1 "Updated description"
        simpletask criteria update AC2 "New text" --branch feature-123

    Raises:
        ValueError: If not in a git repository, branch cannot be determined, or criterion ID not found
        FileNotFoundError: If task file doesn't exist for the specified branch
        InvalidTaskFileError: If task file is malformed and cannot be parsed
    """
    try:
        file_path = get_task_file_path(branch)
        update_acceptance_criterion(file_path, criterion_id, description)
        success(f"Updated {criterion_id} description")

    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        handle_exception(e, "updating criterion")
