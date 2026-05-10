"""Add acceptance criterion command."""

from typing import Annotated

import typer

from simpletask.core.criteria_ops import add_acceptance_criterion
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


def _print_json_criterion_add(criterion_id: str, file_path: str, spec) -> None:
    """Print criterion add result as JSON.

    Args:
        criterion_id: The new criterion ID
        file_path: Path to the task file
        spec: The updated task spec
    """
    json_success(
        build_write_response(
            "criterion_added",
            f"Added criterion {criterion_id}",
            spec,
            file_path,
            criterion_id=criterion_id,
        )
    )


def add_command(
    description: str = typer.Argument(..., help="Criterion description"),
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format (rich, plain, json)"),
    ] = OutputFormat.RICH,
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
        # Resolve format
        format = resolve_format(format)

        # Resolve task file path
        file_path = get_task_file_path(branch)
        new_id, spec = add_acceptance_criterion(file_path, description)

        # Output results based on format
        if format == OutputFormat.JSON:
            _print_json_criterion_add(new_id, str(file_path), spec)
        else:
            success(f"Added criterion {new_id}: {description}")

    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        if format == OutputFormat.JSON:
            json_error(str(e))
        else:
            handle_exception(e, "adding acceptance criterion")
        raise typer.Exit(1) from None
