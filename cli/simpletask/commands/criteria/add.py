"""Add acceptance criterion command."""

import typer

from simpletask.mcp.server import simpletask_criteria
from simpletask.utils.console import error, success


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
        result = simpletask_criteria(
            action="add",
            branch=branch,
            description=description,
        )

        # Extract criterion ID from result
        new_id = result.spec.acceptance_criteria[-1].id
        success(f"Added criterion {new_id}: {description}")

    except ValueError as e:
        error(str(e))
    except FileNotFoundError as e:
        error(str(e))
    except Exception as e:
        error(f"Unexpected error: {e}")
