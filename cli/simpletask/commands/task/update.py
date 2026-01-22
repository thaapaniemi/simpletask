"""Update implementation task command."""

import typer

from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.mcp.server import task
from simpletask.utils.console import handle_exception, success


def update_command(
    task_id: str = typer.Argument(..., help="Task ID (e.g., T001)"),
    status: str | None = typer.Option(
        None, "--status", "-s", help="New status (not_started, in_progress, completed, blocked)"
    ),
    name: str | None = typer.Option(None, "--name", "-n", help="New task name"),
    goal: str | None = typer.Option(None, "--goal", "-g", help="New task goal"),
    branch: str | None = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """Update an implementation task's properties.

    Examples:
        simpletask task update T001 --status completed
        simpletask task update T002 --name "New name" --goal "Updated goal"
        simpletask task update T003 --status in_progress --branch feature-123
    """
    try:
        # Call MCP tool directly
        task(
            action="update",
            branch=branch,
            task_id=task_id,
            name=name,
            goal=goal,
            status=status,
        )

        success(f"Updated task {task_id}")

    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        handle_exception(e, "updating task")
