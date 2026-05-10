"""Remove acceptance criterion command."""

from typing import Annotated

import typer

from simpletask.core.criteria_ops import remove_acceptance_criterion
from simpletask.core.project import get_task_file_path
from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.utils.console import confirm, handle_exception, success
from simpletask.utils.output import (
    OutputFormat,
    build_write_response,
    json_error,
    json_success,
    resolve_format,
)


def _print_json_criterion_remove(criterion_id: str, file_path: str, spec) -> None:
    """Print criterion remove result as JSON.

    Args:
        criterion_id: The removed criterion ID
        file_path: Path to the task file
        spec: The updated task spec
    """
    json_success(
        build_write_response(
            "criterion_removed",
            f"Removed criterion {criterion_id}",
            spec,
            file_path,
            criterion_id=criterion_id,
        )
    )


def remove_command(
    criterion_id: str = typer.Argument(..., help="Criterion ID (e.g., AC1)"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
    format: Annotated[
        OutputFormat,
        typer.Option("--format", help="Output format (rich, plain, json)"),
    ] = OutputFormat.RICH,
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
        # Resolve format
        format = resolve_format(format)

        # Confirm removal unless --force
        if not force:
            if not confirm(f"Remove criterion {criterion_id}?"):
                raise typer.Abort()

        # Resolve task file path and remove
        file_path = get_task_file_path(branch)
        spec = remove_acceptance_criterion(file_path, criterion_id)

        # Output results based on format
        if format == OutputFormat.JSON:
            _print_json_criterion_remove(criterion_id, str(file_path), spec)
        else:
            success(f"Removed criterion {criterion_id}")

    except typer.Abort:
        raise
    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        if format == OutputFormat.JSON:
            json_error(str(e))
        else:
            handle_exception(e, "removing acceptance criterion")
        raise typer.Exit(1) from None
