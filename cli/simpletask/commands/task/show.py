"""Show details for one implementation task."""

from typing import Annotated

import typer

from simpletask.core.models import Task
from simpletask.core.project import ensure_project, get_task_file_path
from simpletask.core.yaml_parser import InvalidTaskFileError, parse_task_file
from simpletask.utils.console import console, error
from simpletask.utils.output import OutputFormat, json_error, json_success, resolve_format


def _print_task(task: Task) -> None:
    """Render all task fields as human-readable output."""
    console.print(f"\n[bold]Task {task.id}: {task.name}[/bold]")
    console.print(f"  Status: {task.status.value}")
    console.print(f"  Goal: {task.goal}")
    console.print("  Steps:")
    for step in task.steps:
        console.print(f"    • {step}")

    fields = {
        "Completion conditions": task.done_when,
        "Prerequisites": task.prerequisites,
        "Files": task.files,
        "Code examples": task.code_examples,
        "Notes": task.notes,
        "Iteration": task.iteration,
    }
    for label, value in fields.items():
        console.print(f"  {label}: {value if value is not None else 'None'}")


def show_command(
    task_id: str = typer.Argument(..., help="Task ID (e.g., T001)"),
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format (rich, plain, json)"),
    ] = OutputFormat.RICH,
    branch: str | None = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """Show all details for one implementation task."""
    format = resolve_format(format)
    try:
        project = ensure_project()
        file_path = get_task_file_path(branch)
        relative_path = str(file_path.relative_to(project.root))
        spec = parse_task_file(file_path)
        task = next((item for item in (spec.tasks or []) if item.id == task_id), None)
        if task is None:
            raise ValueError(f"Task {task_id} not found")

        if format == OutputFormat.JSON:
            json_success({"file_path": relative_path, "task": task.model_dump(mode="json")})
        else:
            _print_task(task)
    except FileNotFoundError:
        message = "Task file not found"
        if format == OutputFormat.JSON:
            json_error(message)
        else:
            error(message)
        raise typer.Exit(1) from None
    except (ValueError, InvalidTaskFileError) as exc:
        if format == OutputFormat.JSON:
            json_error(str(exc))
        else:
            error(str(exc))
        raise typer.Exit(1) from None
