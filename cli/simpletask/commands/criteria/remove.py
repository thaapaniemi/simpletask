"""Remove acceptance criterion command."""

from typing import Optional
import typer

from simpletask.core.project import get_task_file_path
from simpletask.core.criteria_ops import remove_acceptance_criterion
from simpletask.utils.console import success, error, confirm


def remove_command(
    criterion_id: str = typer.Argument(..., help="Criterion ID (e.g., AC1)"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
    branch: Optional[str] = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """Remove an acceptance criterion from the task file.

    Examples:
        simpletask criteria remove AC3
        simpletask criteria remove AC5 --force
        simpletask criteria remove AC2 --branch feature-123
    """
    try:
        # Confirm removal unless --force
        if not force:
            if not confirm(f"Remove criterion {criterion_id}?"):
                raise typer.Abort()

        # Get file path
        file_path = get_task_file_path(branch)

        # Remove criterion
        remove_acceptance_criterion(file_path, criterion_id)

        success(f"Removed criterion {criterion_id}")

    except typer.Abort:
        raise
    except ValueError as e:
        error(str(e))
        raise typer.Exit(1)
    except FileNotFoundError as e:
        error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        error(f"Unexpected error: {e}")
        raise typer.Exit(1)
