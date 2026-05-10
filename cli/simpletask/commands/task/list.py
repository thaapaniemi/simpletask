"""List implementation tasks command."""

from typing import Annotated

import typer

from simpletask.core.models import Task, TaskStatus
from simpletask.core.project import ensure_project, get_task_file_path
from simpletask.core.yaml_parser import InvalidTaskFileError, parse_task_file
from simpletask.utils.console import console, error
from simpletask.utils.output import OutputFormat, json_error, json_success, resolve_format


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


def _print_task_line(task: Task, iter_label: str | None = None, indent: bool = True) -> None:
    """Print a single task line.

    Args:
        task: The task to print.
        iter_label: Optional iteration label to append (flat list mode).
        indent: Whether to indent the line with two leading spaces (grouped mode).
    """
    icon = _get_status_icon(task.status)
    name_text = f"[bold]{task.name}[/bold]"
    prefix = "  " if indent else ""
    line = f"{prefix}{icon} {task.id} {name_text}"
    if task.goal:
        line += f" [dim]- {task.goal}[/dim]"
    if iter_label is not None:
        line += f" [cyan dim][{iter_label}][/cyan dim]"
    console.print(line)


def _print_json_task_list(tasks: list[Task], file_path: str, total_count: int) -> None:
    """Print tasks as JSON.

    Args:
        tasks: List of tasks to print
        file_path: Path to the task file
        total_count: Total count of tasks in file
    """
    output = {
        "file_path": file_path,
        "tasks": [
            {
                "id": t.id,
                "name": t.name,
                "status": t.status.value,
                "goal": t.goal,
                "iteration": t.iteration,
            }
            for t in tasks
        ],
        "returned": len(tasks),
        "total": total_count,
    }
    json_success(output)


def list_command(
    status: str | None = typer.Option(
        None,
        "--status",
        "-s",
        help="Filter by status (not_started, in_progress, completed, blocked, paused)",
    ),
    iteration: int | None = typer.Option(
        None,
        "--iteration",
        "-i",
        help="Filter tasks by iteration ID",
    ),
    flat: bool = typer.Option(
        False,
        "--flat",
        help="Display flat list without iteration grouping",
    ),
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format (rich, plain, json)"),
    ] = OutputFormat.RICH,
    branch: str | None = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """List implementation tasks with optional filtering and iteration grouping.

    By default, tasks are grouped by iteration when iterations exist.
    Use --flat to display a simple flat list instead.

    Examples:
        simpletask task list
        simpletask task list --status completed
        simpletask task list --iteration 1
        simpletask task list --status in_progress --flat
        simpletask task list --status in_progress --branch feature-123
    """
    try:
        # Get file path
        project = ensure_project()
        file_path = get_task_file_path(branch)
        relative_path = file_path.relative_to(project.root)

        # Parse task file
        spec = parse_task_file(file_path)

        # Resolve format
        format = resolve_format(format)

        # Get tasks
        tasks = spec.tasks or []
        total_count = len(tasks)

        # Apply status filter if provided
        if status:
            try:
                status_enum = TaskStatus(status)
                tasks = [t for t in tasks if t.status == status_enum]
            except ValueError:
                msg = f"Invalid status: {status}. Valid values: not_started, in_progress, completed, blocked, paused"
                if format == OutputFormat.JSON:
                    json_error(msg)
                else:
                    error(msg)
                raise typer.Exit(1) from None

        # Apply iteration filter if provided
        if iteration is not None:
            valid_iter_ids = {it.id for it in (spec.iterations or [])}
            if iteration not in valid_iter_ids:
                msg = f"Iteration {iteration} not found. Valid IDs: {sorted(valid_iter_ids)}"
                if format == OutputFormat.JSON:
                    json_error(msg)
                    error(msg)
                raise typer.Exit(1) from None
                return
            tasks = [t for t in tasks if t.iteration == iteration]

        # JSON output path
        if format == OutputFormat.JSON:
            _print_json_task_list(tasks, str(relative_path), total_count)
            return

        # Display tasks
        if not tasks:
            console.print("[dim]No tasks found[/dim]")
            return

        console.print(f"\n[bold]Implementation Tasks[/bold] ({file_path.name})\n")

        # Check if we should group by iteration
        iterations = spec.iterations or []
        has_iterations = len(iterations) > 0
        iter_map = {it.id: it for it in iterations}

        if has_iterations and not flat and iteration is None:
            # Group tasks by iteration
            # Collect unassigned tasks (iteration=None)
            unassigned = [t for t in tasks if t.iteration is None]

            # Print each iteration group
            for it in iterations:
                iter_tasks = [t for t in tasks if t.iteration == it.id]
                if iter_tasks:
                    console.print(f"[bold cyan]Iteration {it.id}: {it.label}[/bold cyan]")
                    for task in iter_tasks:
                        _print_task_line(task)
                    console.print()

            # Print unassigned tasks if any
            if unassigned:
                console.print("[bold dim]Unassigned[/bold dim]")
                for task in unassigned:
                    _print_task_line(task)
                console.print()
        else:
            # Flat list display
            for task in tasks:
                iter_label = (
                    iter_map[task.iteration].label
                    if has_iterations and task.iteration is not None and task.iteration in iter_map
                    else None
                )
                _print_task_line(task, iter_label=iter_label, indent=False)

        console.print(f"[dim]Total: {len(tasks)} task(s)[/dim]\n")

    except FileNotFoundError:
        if format == OutputFormat.JSON:
            json_error("Task file not found")
        else:
            error("Task file not found")
        raise typer.Exit(1) from None
    except (ValueError, InvalidTaskFileError) as e:
        if format == OutputFormat.JSON:
            json_error(str(e))
        else:
            error(str(e))
        raise typer.Exit(1) from None
