"""List acceptance criteria command."""

from typing import Annotated

import typer

from simpletask.core.project import get_task_file_path
from simpletask.core.yaml_parser import parse_task_file
from simpletask.utils.console import console, error
from simpletask.utils.output import OutputFormat, json_error, json_success, resolve_format


def _print_json_criteria_list(
    criteria, completed_count: int, total_count: int, file_path: str
) -> None:
    """Print criteria as JSON.

    Args:
        criteria: List of criteria to print
        completed_count: Number of completed criteria
        total_count: Total number of criteria
        file_path: Path to the task file
    """
    output = {
        "file_path": file_path,
        "criteria": [
            {
                "id": c.id,
                "description": c.description,
                "completed": c.completed,
            }
            for c in criteria
        ],
        "completed": completed_count,
        "total": total_count,
    }
    json_success(output)


def list_command(
    completed_only: bool = typer.Option(
        False, "--completed", "-c", help="Show only completed criteria"
    ),
    incomplete_only: bool = typer.Option(
        False, "--incomplete", "-i", help="Show only incomplete criteria"
    ),
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format (rich, plain, json)"),
    ] = OutputFormat.RICH,
    branch: str | None = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """List acceptance criteria with optional filtering.

    Examples:
        simpletask criteria list
        simpletask criteria list --completed
        simpletask criteria list --incomplete --branch feature-123
    """
    try:
        # Get file path
        file_path = get_task_file_path(branch)

        # Parse task file
        spec = parse_task_file(file_path)

        # Resolve format
        format = resolve_format(format)

        # Get criteria
        criteria = list(spec.acceptance_criteria)

        # Apply filters
        if completed_only and incomplete_only:
            error("Cannot use both --completed and --incomplete")

        if completed_only:
            criteria = [c for c in criteria if c.completed]
        elif incomplete_only:
            criteria = [c for c in criteria if not c.completed]

        # Get counts before filtering for display
        completed_count = sum(1 for c in spec.acceptance_criteria if c.completed)
        total_count = len(spec.acceptance_criteria)

        # JSON output path
        if format == OutputFormat.JSON:
            _print_json_criteria_list(criteria, completed_count, total_count, str(file_path))
            return

        # Display criteria
        if not criteria:
            console.print("[dim]No acceptance criteria found[/dim]")
            return

        console.print(f"\n[bold]Acceptance Criteria[/bold] ({file_path.name})\n")

        for criterion in criteria:
            icon = "[green]✓[/green]" if criterion.completed else "[dim]○[/dim]"
            console.print(f"{icon} {criterion.id} {criterion.description}")

        # Summary
        console.print(f"\n[dim]Completed: {completed_count}/{total_count}[/dim]\n")

    except FileNotFoundError:
        if format == OutputFormat.JSON:
            json_error("Task file not found")
        else:
            error("Task file not found")
    except Exception as e:
        if format == OutputFormat.JSON:
            json_error(f"Unexpected error: {e}")
        else:
            error(f"Unexpected error: {e}")
