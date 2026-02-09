"""Add constraint command."""

import typer

from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.mcp.server import constraint
from simpletask.utils.console import handle_exception, success


def add_command(
    value: str = typer.Argument(..., help="Constraint description"),
) -> None:
    """Add an implementation constraint.

    Examples:
        simpletask constraint add "Use Pydantic models with extra='forbid'"
        simpletask constraint add "No shell=True in subprocess calls"
    """
    try:
        # Call MCP tool directly
        constraint(
            action="add",
            value=value,
        )

        success("Added constraint")

    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        handle_exception(e, "adding constraint")
