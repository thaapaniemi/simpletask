"""Mark acceptance criteria as complete command."""

from typing import Annotated

import typer

from simpletask.core.criteria_ops import mark_criterion_complete
from simpletask.core.project import get_task_file_path
from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.utils.console import handle_exception, success
from simpletask.utils.output import (
    OutputFormat,
    build_write_response,
    json_error,
    json_success,
    resolve_format,
)


def _print_json_criterion_complete(
    criterion_id: str, file_path: str, spec, completed: bool = True
) -> None:
    """Print criterion complete result as JSON.

    Args:
        criterion_id: The criterion ID
        file_path: Path to the task file
        spec: The updated task spec
        completed: Whether the criterion was marked as completed (True) or uncompleted (False)
    """
    if completed:
        action = "criterion_completed"
        message = f"Marked {criterion_id} as completed"
    else:
        action = "criterion_uncompleted"
        message = f"Marked {criterion_id} as not completed"
    json_success(build_write_response(action, message, spec, file_path, criterion_id=criterion_id))


def complete_command(
    criterion_id: str = typer.Argument(..., help="Criterion ID (e.g., AC1)"),
    uncomplete: bool = typer.Option(
        False, "--uncomplete", "-u", help="Mark as not completed instead"
    ),
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format (rich, plain, json)"),
    ] = OutputFormat.RICH,
    branch: str | None = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """Mark an acceptance criterion as completed (or not completed with --uncomplete).

    Examples:
        simpletask criteria complete AC1
        simpletask criteria complete AC2 --branch feature-123
        simpletask criteria complete AC1 --uncomplete

    Raises:
        ValueError: If not in a git repository, branch cannot be determined, or criterion ID not found
        FileNotFoundError: If task file doesn't exist for the specified branch
        InvalidTaskFileError: If task file is malformed and cannot be parsed
    """
    try:
        # Resolve format
        format = resolve_format(format)

        # Resolve task file path and mark complete
        file_path = get_task_file_path(branch)
        spec = mark_criterion_complete(file_path, criterion_id, completed=not uncomplete)

        # Output results based on format
        if format == OutputFormat.JSON:
            _print_json_criterion_complete(
                criterion_id, str(file_path), spec, completed=not uncomplete
            )
        elif uncomplete:
            success(f"Marked {criterion_id} as not completed")
        else:
            success(f"Marked {criterion_id} as completed")

    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        if format == OutputFormat.JSON:
            json_error(str(e))
        else:
            handle_exception(e, "marking criterion as complete")
        raise typer.Exit(1) from None
