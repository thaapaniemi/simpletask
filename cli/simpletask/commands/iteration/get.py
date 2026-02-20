"""Get iteration command."""

from typing import Annotated

import typer

from simpletask.core.iteration_ops import get_iteration_from_spec
from simpletask.core.models import TaskStatus
from simpletask.core.project import get_task_file_path
from simpletask.core.yaml_parser import InvalidTaskFileError, parse_task_file
from simpletask.utils.console import console, error


def get_command(
    iteration_id: Annotated[int, typer.Argument(help="Iteration ID to retrieve")],
    branch: str | None = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """Get details of a specific iteration by ID.

    Examples:
        simpletask iteration get 1
        simpletask iteration get 2 --branch feature-123

    Raises:
        ValueError: If not in a git repository or branch cannot be determined
        FileNotFoundError: If task file doesn't exist for the specified branch
        InvalidTaskFileError: If task file is malformed and cannot be parsed
    """
    try:
        file_path = get_task_file_path(branch)
        spec = parse_task_file(file_path)
        iteration = get_iteration_from_spec(spec, iteration_id)
        tasks = spec.tasks or []

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

    except FileNotFoundError as e:
        error(str(e))
    except (ValueError, InvalidTaskFileError) as e:
        error(str(e))
