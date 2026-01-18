"""Add acceptance criterion command."""

from typing import Optional
import typer

from simpletask.core.project import get_task_file_path
from simpletask.core.criteria_ops import add_acceptance_criterion
from simpletask.utils.console import success, error


def add_command(
    description: str = typer.Argument(..., help="Criterion description"),
    branch: Optional[str] = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """Add a new acceptance criterion to the task file.

    Examples:
        simpletask criteria add "Feature works correctly"
        simpletask criteria add "Documentation updated" --branch feature-123
    """
    try:
        # Get file path
        file_path = get_task_file_path(branch)

        # Add criterion
        new_id = add_acceptance_criterion(file_path, description)

        success(f"Added criterion {new_id}: {description}")

    except ValueError as e:
        error(str(e))
        raise typer.Exit(1)
    except FileNotFoundError as e:
        error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        error(f"Unexpected error: {e}")
        raise typer.Exit(1)
