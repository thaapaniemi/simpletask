"""Remove implementation task command."""

from typing import Annotated

import typer

from simpletask.core.project import get_task_file_path
from simpletask.core.task_ops import remove_implementation_task
from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.utils.console import confirm, handle_exception, success
from simpletask.utils.output import (
    OutputFormat,
    build_write_response,
    json_error,
    json_success,
    resolve_format,
)


def _print_json_task_remove(task_id: str, file_path: str, spec) -> None:
    """Print task remove result as JSON.

    Args:
        task_id: The removed task ID
        file_path: Path to the task file
        spec: The updated task spec
    """
    json_success(
        build_write_response(
            "task_removed", f"Removed task {task_id}", spec, file_path, task_id=task_id
        )
    )


def remove_command(
    task_id: str = typer.Argument(..., help="Task ID (e.g., T001)"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
    format: Annotated[
        OutputFormat,
        typer.Option("--format", help="Output format (rich, plain, json)"),
    ] = OutputFormat.RICH,
    branch: str | None = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """Remove an implementation task from the task file.

    Examples:
        simpletask task remove T003
        simpletask task remove T005 --force
        simpletask task remove T002 --branch feature-123

    Raises:
        ValueError: If not in a git repository, branch cannot be determined, or task ID not found
        FileNotFoundError: If task file doesn't exist for the specified branch
        InvalidTaskFileError: If task file is malformed and cannot be parsed
        typer.Abort: If user cancels the confirmation prompt
    """
    try:
        # Resolve format
        format = resolve_format(format)

        # Confirm removal unless --force
        if not force:
            if not confirm(f"Remove task {task_id}?"):
                raise typer.Abort()

        # Resolve task file path and remove
        file_path = get_task_file_path(branch)
        spec = remove_implementation_task(file_path, task_id)

        # Output results based on format
        if format == OutputFormat.JSON:
            _print_json_task_remove(task_id, str(file_path), spec)
        else:
            success(f"Removed task {task_id}")

    except typer.Abort:
        raise
    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        if format == OutputFormat.JSON:
            json_error(str(e))
        else:
            handle_exception(e, "removing task")
        raise typer.Exit(1) from None
