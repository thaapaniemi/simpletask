"""List iterations command."""

import typer

from simpletask.core.models import TaskStatus
from simpletask.core.project import get_task_file_path
from simpletask.core.yaml_parser import InvalidTaskFileError, parse_task_file
from simpletask.utils.console import console, error


def list_command(
    branch: str | None = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """List all iterations in the task file.

    Examples:
        simpletask iteration list
        simpletask iteration list --branch feature-123
    """
    try:
        file_path = get_task_file_path(branch)
        spec = parse_task_file(file_path)
        iterations = spec.iterations or []
        tasks = spec.tasks or []

        if not iterations:
            console.print("[dim]No iterations found[/dim]")
            return

        console.print(f"\n[bold]Iterations[/bold] ({file_path.name})\n")

        for iteration in iterations:
            # Count tasks assigned to this iteration
            iter_tasks = [t for t in tasks if t.iteration == iteration.id]
            task_count = len(iter_tasks)
            completed = sum(1 for t in iter_tasks if t.status == TaskStatus.COMPLETED)

            created_str = iteration.created.strftime("%Y-%m-%d")
            count_str = (
                f"[dim]{completed}/{task_count} tasks[/dim]" if task_count else "[dim]0 tasks[/dim]"
            )

            console.print(
                f"  [bold cyan]{iteration.id}[/bold cyan]  [bold]{iteration.label}[/bold]"
                f"  {count_str}  [dim]({created_str})[/dim]"
            )

        console.print(f"\n[dim]Total: {len(iterations)} iteration(s)[/dim]\n")

    except FileNotFoundError as e:
        error(str(e))
    except (ValueError, InvalidTaskFileError) as e:
        error(str(e))
