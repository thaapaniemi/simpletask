"""Add iteration command."""

from typing import Annotated

import typer

from simpletask.core.iteration_ops import add_iteration
from simpletask.core.project import get_task_file_path
from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.utils.console import handle_exception, success
from simpletask.utils.output import OutputFormat, json_error, json_success, resolve_format


def add_command(
    label: str = typer.Argument(..., help="Iteration label (e.g. 'MVP', 'v2 polish')"),
    branch: str | None = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format (rich, plain, json)"),
    ] = OutputFormat.RICH,
) -> None:
    """Add a new iteration to the task file.

    Examples:
        simpletask iteration add "MVP"
        simpletask iteration add "v2 polish" --branch feature-123

    Raises:
        ValueError: If not in a git repository or branch cannot be determined
        FileNotFoundError: If task file doesn't exist for the specified branch
        InvalidTaskFileError: If task file is malformed and cannot be parsed
    """
    try:
        format = resolve_format(format)
        file_path = get_task_file_path(branch)
        new_id = add_iteration(file_path, label)

        if format == OutputFormat.JSON:
            json_success(
                {
                    "success": True,
                    "action": "iteration_added",
                    "message": f"Added iteration {new_id}: {label}",
                    "iteration_id": new_id,
                }
            )
        else:
            success(f"Added iteration {new_id}: {label}")

    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        if format == OutputFormat.JSON:
            json_error(str(e))
        else:
            handle_exception(e, "adding iteration")
        raise typer.Exit(1) from None
