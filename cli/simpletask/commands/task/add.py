"""Add implementation task command."""

import typer

from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.mcp.server import task
from simpletask.utils.console import handle_exception, success


def add_command(
    name: str = typer.Argument(..., help="Task name"),
    goal: str | None = typer.Option(None, "--goal", "-g", help="Task goal/description"),
    branch: str | None = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """Add a new implementation task to the task file.

    Examples:
        simpletask task add "Implement authentication"
        simpletask task add "Add tests" --goal "Write unit tests for auth"
        simpletask task add "Update docs" --branch feature-123
    """
    try:
        # Call MCP tool directly
        result = task(
            action="add",
            branch=branch,
            name=name,
            goal=goal,
        )

        # Extract task ID from result
        new_id = result.spec.tasks[-1].id
        success(f"Added task {new_id}: {name}")

    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        handle_exception(e, "adding implementation task")
