"""List acceptance criteria command."""

from typing import Optional
import typer

from simpletask.core.project import get_task_file_path
from simpletask.core.yaml_parser import parse_task_file
from simpletask.utils.console import error, console


def list_command(
    completed_only: bool = typer.Option(
        False, "--completed", "-c", help="Show only completed criteria"
    ),
    incomplete_only: bool = typer.Option(
        False, "--incomplete", "-i", help="Show only incomplete criteria"
    ),
    branch: Optional[str] = typer.Option(
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

        # Get criteria
        criteria = list(spec.acceptance_criteria)

        # Apply filters
        if completed_only and incomplete_only:
            error("Cannot use both --completed and --incomplete")
            raise typer.Exit(1)

        if completed_only:
            criteria = [c for c in criteria if c.completed]
        elif incomplete_only:
            criteria = [c for c in criteria if not c.completed]

        # Display criteria
        if not criteria:
            console.print("[dim]No acceptance criteria found[/dim]")
            return

        console.print(f"\n[bold]Acceptance Criteria[/bold] ({file_path.name})\n")

        for criterion in criteria:
            icon = "[green]✓[/green]" if criterion.completed else "[dim]○[/dim]"
            console.print(f"{icon} {criterion.id} {criterion.description}")

        # Summary
        completed_count = sum(1 for c in spec.acceptance_criteria if c.completed)
        total_count = len(spec.acceptance_criteria)
        console.print(f"\n[dim]Completed: {completed_count}/{total_count}[/dim]\n")

    except FileNotFoundError as e:
        error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        error(f"Unexpected error: {e}")
        raise typer.Exit(1)
