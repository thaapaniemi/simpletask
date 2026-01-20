"""Show command - Display task details."""

import typer

from ..core.project import ensure_project, get_task_file_path
from ..core.yaml_parser import InvalidTaskFileError, parse_task_file
from ..utils.console import console, error


def show(
    branch: str | None = typer.Argument(None, help="Branch name (defaults to current git branch)"),
) -> None:
    """Show detailed information about a task.

    Displays:
    - Task file location
    - Title and branch
    - Acceptance criteria with completion status
    - Implementation tasks (if defined)
    - Constraints (if defined)

    Examples:
        simpletask show                    # Uses current git branch
        simpletask show add-dark-mode      # Explicit branch
    """
    task_file = None
    try:
        task_file = get_task_file_path(branch)
        project = ensure_project()

        # Parse task file
        spec = parse_task_file(task_file)

        # Display file location (relative to project root)
        relative_path = task_file.relative_to(project.root)
        console.print(f"\n[bold]Task File:[/bold] {relative_path}")
        console.print()

        # Display task information
        console.print(f"[bold cyan]Task:[/bold cyan] {spec.title}")
        console.print(f"[bold]Branch:[/bold] {spec.branch}")
        console.print(f"[bold]Created:[/bold] {spec.created.strftime('%Y-%m-%d %H:%M:%S UTC')}")

        # Acceptance criteria
        console.print("\n[bold magenta]Acceptance Criteria:[/bold magenta]")
        for criterion in spec.acceptance_criteria:
            status_icon = "✓" if criterion.completed else "○"
            status_color = "green" if criterion.completed else "white"
            console.print(
                f"  [{status_color}]{status_icon}[/{status_color}] {criterion.id}: {criterion.description}"
            )

        # Constraints
        if spec.constraints:
            console.print("\n[bold yellow]Constraints:[/bold yellow]")
            for constraint in spec.constraints:
                console.print(f"  • {constraint}")

        # Tasks
        if spec.tasks:
            console.print("\n[bold green]Implementation Tasks:[/bold green]")
            for task in spec.tasks:
                status_icon = "✓" if task.status.value == "completed" else "○"
                status_color = (
                    "green"
                    if task.status.value == "completed"
                    else (
                        "yellow"
                        if task.status.value == "in_progress"
                        else "red" if task.status.value == "blocked" else "white"
                    )
                )
                console.print(
                    f"  [{status_color}]{status_icon}[/{status_color}] {task.id}: {task.name} ({task.status.value})"
                )
        else:
            console.print("\n[dim]No implementation tasks defined yet[/dim]")

        console.print()

    except FileNotFoundError:
        error(f"Task file not found: {task_file}")
    except InvalidTaskFileError as e:
        error(f"Invalid task file: {e}")
    except ValueError as e:
        error(str(e))
    except Exception as e:
        error(f"Unexpected error: {e}")
