"""Remove acceptance criterion command."""

import typer

from simpletask.mcp.server import simpletask_criteria
from simpletask.utils.console import confirm, error, success


def remove_command(
    criterion_id: str = typer.Argument(..., help="Criterion ID (e.g., AC1)"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
    branch: str | None = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """Remove an acceptance criterion from the task file.

    Examples:
        simpletask criteria remove AC3
        simpletask criteria remove AC5 --force
        simpletask criteria remove AC2 --branch feature-123
    """
    try:
        # Confirm removal unless --force
        if not force:
            if not confirm(f"Remove criterion {criterion_id}?"):
                raise typer.Abort()

        # Call MCP tool directly
        simpletask_criteria(
            action="remove",
            branch=branch,
            criterion_id=criterion_id,
        )

        success(f"Removed criterion {criterion_id}")

    except typer.Abort:
        raise
    except ValueError as e:
        error(str(e))
    except FileNotFoundError as e:
        error(str(e))
    except Exception as e:
        error(f"Unexpected error: {e}")
