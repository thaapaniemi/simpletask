"""Add note command."""

import typer

from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.mcp.server import note
from simpletask.utils.console import handle_exception, success


def add_command(
    content: str = typer.Argument(..., help="Note content"),
    task: str | None = typer.Option(None, "--task", "-t", help="Task ID to add note to"),
) -> None:
    """Add a note to root-level or task-level.

    Examples:
        simpletask note add "Remember to update docs"
        simpletask note add "This task needs refactoring" --task T003
    """
    try:
        # Call MCP tool directly
        note(
            action="add",
            content=content,
            task_id=task,
        )

        location = f"task {task}" if task else "root"
        success(f"Added note to {location}")

    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        handle_exception(e, "adding note")
