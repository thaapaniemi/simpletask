"""Mark acceptance criteria as complete command."""

import typer

from simpletask.core.criteria_ops import mark_criterion_complete
from simpletask.core.project import get_task_file_path
from simpletask.utils.console import error, success


def complete_command(
    criterion_id: str = typer.Argument(..., help="Criterion ID (e.g., AC1)"),
    uncomplete: bool = typer.Option(
        False, "--uncomplete", "-u", help="Mark as not completed instead"
    ),
    branch: str | None = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """Mark an acceptance criterion as completed (or not completed with --uncomplete).

    Examples:
        simpletask criteria complete AC1
        simpletask criteria complete AC2 --branch feature-123
        simpletask criteria complete AC1 --uncomplete
    """
    try:
        # Get file path
        file_path = get_task_file_path(branch)

        # Mark criterion
        mark_criterion_complete(file_path, criterion_id, completed=not uncomplete)

        if uncomplete:
            success(f"Marked {criterion_id} as not completed")
        else:
            success(f"Marked {criterion_id} as completed")

    except ValueError as e:
        error(str(e))
    except FileNotFoundError as e:
        error(str(e))
    except Exception as e:
        error(f"Unexpected error: {e}")
