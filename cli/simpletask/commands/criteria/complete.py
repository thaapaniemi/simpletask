"""Mark acceptance criteria as complete command."""

import typer

from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.mcp.server import criteria
from simpletask.utils.console import handle_exception, success


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
        criteria(
            action="complete",
            branch=branch,
            criterion_id=criterion_id,
            completed=not uncomplete,
        )

        if uncomplete:
            success(f"Marked {criterion_id} as not completed")
        else:
            success(f"Marked {criterion_id} as completed")

    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        handle_exception(e, "marking criterion as complete")
