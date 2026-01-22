"""Remove implementation task command."""

import typer

from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.mcp.server import task
from simpletask.utils.console import confirm, handle_exception, success


def remove_command(
    task_id: str = typer.Argument(..., help="Task ID (e.g., T001)"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
    branch: str | None = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """Remove an implementation task from the task file.

    Examples:
        simpletask task remove T003
        simpletask task remove T005 --force
        simpletask task remove T002 --branch feature-123
    """
    try:
        # Confirm removal unless --force
        if not force:
            if not confirm(f"Remove task {task_id}?"):
                raise typer.Abort()

        # Call MCP tool directly
        task(
            action="remove",
            branch=branch,
            task_id=task_id,
        )

        success(f"Removed task {task_id}")

    except typer.Abort:
        raise
    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        handle_exception(e, "removing task")
