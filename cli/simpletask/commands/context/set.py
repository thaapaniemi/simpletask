"""Set context command."""

import typer

from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.mcp.server import context
from simpletask.utils.console import handle_exception, success


def set_command(
    key: str = typer.Argument(..., help="Context key"),
    value: str = typer.Argument(..., help="Context value"),
) -> None:
    """Set a context key-value pair.

    Examples:
        simpletask context set framework django
        simpletask context set database postgresql
    """
    try:
        # Call MCP tool directly
        context(
            action="set",
            key=key,
            value=value,
        )

        success(f"Set context key '{key}'")

    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        handle_exception(e, "setting context")
