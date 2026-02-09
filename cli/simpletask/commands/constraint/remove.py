"""Remove constraint command."""

import typer

from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.mcp.server import constraint
from simpletask.utils.console import handle_exception, success


def remove_command(
    index: int | None = typer.Argument(None, help="Constraint index to remove (0-based)"),
    all: bool = typer.Option(False, "--all", "-a", help="Remove all constraints"),
) -> None:
    """Remove a constraint.

    Examples:
        simpletask constraint remove 0
        simpletask constraint remove --all
    """
    try:
        # Call MCP tool directly
        constraint(
            action="remove",
            index=index,
            all=all,
        )

        if all:
            success("Removed all constraints")
        else:
            success(f"Removed constraint {index}")

    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        handle_exception(e, "removing constraint")
