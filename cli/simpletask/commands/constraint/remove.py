"""Remove constraint command."""

from typing import Annotated

import typer

from simpletask.core.constraint_ops import remove_constraint
from simpletask.core.project import get_task_file_path
from simpletask.core.yaml_parser import InvalidTaskFileError, parse_task_file, write_task_file
from simpletask.utils.console import handle_exception, success
from simpletask.utils.output import OutputFormat, json_error, json_success, resolve_format


def remove_command(
    index: int | None = typer.Argument(None, help="Constraint index to remove (0-based)"),
    all: bool = typer.Option(False, "--all", "-a", help="Remove all constraints"),
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format (rich, plain, json)"),
    ] = OutputFormat.RICH,
) -> None:
    """Remove a constraint.

    Examples:
        simpletask constraint remove 0
        simpletask constraint remove --all

    Raises:
        ValueError: If not in a git repository or branch cannot be determined
        FileNotFoundError: If task file doesn't exist for the specified branch
        InvalidTaskFileError: If task file is malformed and cannot be parsed
    """
    try:
        # Resolve format
        format = resolve_format(format)

        file_path = get_task_file_path(None)
        spec = parse_task_file(file_path)
        spec = remove_constraint(spec=spec, index=index, all=all)
        write_task_file(file_path, spec)

        # Output results based on format
        if format == OutputFormat.JSON:
            total_count = len(spec.constraints) if spec.constraints else 0
            json_success(
                {
                    "success": True,
                    "action": "constraint_removed",
                    "message": "Removed constraint",
                    "summary": {"constraints_total": total_count},
                }
            )
        else:
            if all:
                success("Removed all constraints")
            else:
                success(f"Removed constraint {index}")

    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        if format == OutputFormat.JSON:
            json_error(str(e))
        else:
            handle_exception(e, "removing constraint")
        raise typer.Exit(1) from None
