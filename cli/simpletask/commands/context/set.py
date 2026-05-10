"""Set context command."""

from typing import Annotated

import typer

from simpletask.core.context_ops import set_context
from simpletask.core.project import get_task_file_path
from simpletask.core.yaml_parser import InvalidTaskFileError, parse_task_file, write_task_file
from simpletask.utils.console import handle_exception, success
from simpletask.utils.output import OutputFormat, json_error, json_success, resolve_format


def set_command(
    key: str = typer.Argument(..., help="Context key"),
    value: str = typer.Argument(..., help="Context value"),
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format (rich, plain, json)"),
    ] = OutputFormat.RICH,
    branch: str | None = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """Set a context key-value pair.

    Examples:
        simpletask context set framework django
        simpletask context set database postgresql

    Raises:
        ValueError: If not in a git repository or branch cannot be determined
        FileNotFoundError: If task file doesn't exist for the specified branch
        InvalidTaskFileError: If task file is malformed and cannot be parsed
    """
    try:
        # Resolve format
        format = resolve_format(format)

        file_path = get_task_file_path(branch)
        spec = parse_task_file(file_path)
        spec = set_context(spec=spec, key=key, value=value)
        write_task_file(file_path, spec)

        # Output results based on format
        if format == OutputFormat.JSON:
            total_count = len(spec.context) if spec.context else 0
            json_success(
                {
                    "success": True,
                    "action": "context_set",
                    "key": key,
                    "value": value,
                    "message": f"Set context key '{key}'",
                    "summary": {"context_total": total_count},
                }
            )
        else:
            success(f"Set context key '{key}'")

    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        if format == OutputFormat.JSON:
            json_error(str(e))
        else:
            handle_exception(e, "setting context")
        raise typer.Exit(1) from None
