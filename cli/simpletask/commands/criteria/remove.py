"""Remove acceptance criterion command."""

import typer

from simpletask.core.criteria_ops import remove_acceptance_criterion
from simpletask.core.project import get_task_file_path
from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.utils.console import confirm, handle_exception, success


def remove_command(
    criterion_id: str = typer.Argument(..., help="Criterion ID (e.g., AC1)"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
    branch: str | None = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """Remove an acceptance criterion from the task file.

    Examples:
        simpletask criteria remove AC3
        simpletask criteria remove AC5 --force
        simpletask criteria remove AC2 --branch feature-123

    Raises:
        ValueError: If not in a git repository, branch cannot be determined, or criterion ID not found
        FileNotFoundError: If task file doesn't exist for the specified branch
        InvalidTaskFileError: If task file is malformed and cannot be parsed
        typer.Abort: If user cancels the confirmation prompt
    """
    try:
        # Confirm removal unless --force
        if not force:
            if not confirm(f"Remove criterion {criterion_id}?"):
                raise typer.Abort()

        # Resolve task file path and remove
        file_path = get_task_file_path(branch)
        remove_acceptance_criterion(file_path, criterion_id)

        success(f"Removed criterion {criterion_id}")

    except typer.Abort:
        raise
    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        handle_exception(e, "removing acceptance criterion")
