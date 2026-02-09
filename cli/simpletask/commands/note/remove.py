"""Remove note command."""

import typer

from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.mcp.server import note
from simpletask.utils.console import handle_exception, success


def remove_command(
    index: int | None = typer.Argument(None, help="Note index to remove (0-based)"),
    task: str | None = typer.Option(None, "--task", "-t", help="Task ID to remove note from"),
    all: bool = typer.Option(False, "--all", "-a", help="Remove all notes"),
) -> None:
    """Remove a note from root-level or task-level.

    Examples:
        simpletask note remove 0
        simpletask note remove 1 --task T003
        simpletask note remove --all --task T003
    """
    try:
        # Call MCP tool directly
        note(
            action="remove",
            index=index,
            task_id=task,
            all=all,
        )

        location = f"task {task}" if task else "root"
        if all:
            success(f"Removed all notes from {location}")
        else:
            success(f"Removed note {index} from {location}")

    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        handle_exception(e, "removing note")
