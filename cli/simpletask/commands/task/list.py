"""List implementation tasks command."""

import typer

from simpletask.core.models import TaskStatus
from simpletask.core.project import get_task_file_path
from simpletask.core.yaml_parser import parse_task_file
from simpletask.utils.console import console, error


def _get_status_icon(status: TaskStatus) -> str:
    """Get icon for task status."""
    if status == TaskStatus.COMPLETED:
        return "[green]✓[/green]"
    elif status == TaskStatus.IN_PROGRESS:
        return "[yellow]▶[/yellow]"
    elif status == TaskStatus.BLOCKED:
        return "[red]✗[/red]"
    elif status == TaskStatus.PAUSED:
        return "[blue]⏸[/blue]"
    else:  # not_started
        return "[dim]○[/dim]"


def list_command(
    status: str | None = typer.Option(
        None,
        "--status",
        "-s",
        help="Filter by status (not_started, in_progress, completed, blocked, paused)",
    ),
    branch: str | None = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """List implementation tasks with optional filtering.

    Examples:
        simpletask task list
        simpletask task list --status completed
        simpletask task list --status in_progress --branch feature-123
    """
    try:
        # Get file path
        file_path = get_task_file_path(branch)

        # Parse task file
        spec = parse_task_file(file_path)

        # Get tasks
        tasks = spec.tasks or []

        # Apply status filter if provided
        if status:
            try:
                status_enum = TaskStatus(status)
                tasks = [t for t in tasks if t.status == status_enum]
            except ValueError:
                error(
                    f"Invalid status: {status}. Valid values: not_started, in_progress, completed, blocked, paused"
                )

        # Display tasks
        if not tasks:
            console.print("[dim]No tasks found[/dim]")
            return

        console.print(f"\n[bold]Implementation Tasks[/bold] ({file_path.name})\n")

        for task in tasks:
            icon = _get_status_icon(task.status)
            name_text = f"[bold]{task.name}[/bold]"

            # Build output line
            line = f"{icon} {task.id} {name_text}"
            if task.goal:
                line += f" [dim]- {task.goal}[/dim]"

            console.print(line)

        console.print(f"\n[dim]Total: {len(tasks)} task(s)[/dim]\n")

    except FileNotFoundError as e:
        error(str(e))
    except Exception as e:
        error(f"Unexpected error: {e}")
