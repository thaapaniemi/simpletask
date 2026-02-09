"""Remove context command."""

import typer

from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.mcp.server import context
from simpletask.utils.console import handle_exception, success


def remove_command(
    key: str | None = typer.Argument(None, help="Context key to remove"),
    all: bool = typer.Option(False, "--all", "-a", help="Remove all context entries"),
) -> None:
    """Remove a context key or all entries.

    Examples:
        simpletask context remove framework
        simpletask context remove --all
    """
    try:
        # Call MCP tool directly
        context(
            action="remove",
            key=key,
            all=all,
        )

        if all:
            success("Removed all context entries")
        else:
            success(f"Removed context key '{key}'")

    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        handle_exception(e, "removing context")
