"""Mark acceptance criteria as complete command."""

import typer

from simpletask.mcp.server import simpletask_criteria
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
        # Call MCP tool directly
        simpletask_criteria(
            action="complete",
            branch=branch,
            criterion_id=criterion_id,
            completed=not uncomplete,
        )

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
