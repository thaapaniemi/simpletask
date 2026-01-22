"""Add acceptance criterion command."""

import typer

from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.mcp.server import criteria
from simpletask.utils.console import handle_exception, success


def add_command(
    description: str = typer.Argument(..., help="Criterion description"),
    branch: str | None = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """Add a new acceptance criterion to the task file.

    Examples:
        simpletask criteria add "Feature works correctly"
        simpletask criteria add "Documentation updated" --branch feature-123
    """
    try:
        # Call MCP tool directly
        result = criteria(
            action="add",
            branch=branch,
            description=description,
        )

        # Extract criterion ID from result
        new_id = result.spec.acceptance_criteria[-1].id
        success(f"Added criterion {new_id}: {description}")

    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        handle_exception(e, "adding acceptance criterion")
