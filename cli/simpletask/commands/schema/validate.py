"""Schema validate command."""

from pathlib import Path

import typer

from ...core.project import get_task_file_path
from ...core.validation import validate_task_file
from ...utils.console import error, success


def validate(
    file: str | None = typer.Argument(
        None, help="Task file to validate (defaults to current branch)"
    ),
    all_files: bool = typer.Option(False, "--all", help="Validate all task files"),
) -> None:
    """Validate task file(s) against JSON schema.

    Examples:
        simpletask schema validate                    # Validate current task
        simpletask schema validate add-dark-mode      # Validate specific task
        simpletask schema validate --all              # Validate all tasks
    """
    try:
        if all_files:
            # Validate all task files
            from ...core.project import ensure_project

            project = ensure_project()
            tasks = project.list_tasks()

            if not tasks:
                error("No tasks found in ./tasks directory")

            errors_found = False
            for branch in tasks:
                task_file = project.get_task_file(branch)
                errors = validate_task_file(task_file)
                if errors:
                    error_console = __import__(
                        "...utils.console", fromlist=["error_console"]
                    ).error_console
                    error_console.print(
                        f"\n[red]Errors in {task_file.relative_to(project.root)}:[/red]"
                    )
                    for err in errors:
                        error_console.print(f"  {err}")
                    errors_found = True
                else:
                    success(f"{task_file.relative_to(project.root)}: Valid")

            if errors_found:
                raise typer.Exit(1)
            else:
                success("All task files are valid")

        else:
            # Validate single file
            if file:
                task_file = Path(file)
                if not task_file.is_absolute():
                    task_file = Path.cwd() / task_file
            else:
                task_file = get_task_file_path(None)

            errors = validate_task_file(task_file)

            if errors:
                from ...utils.console import error_console

                error_console.print("\n[red]Validation errors:[/red]")
                for err in errors:
                    error_console.print(f"  {err}")
                error("Schema validation failed")
            else:
                success(f"{task_file.name}: Valid")

    except ValueError as e:
        error(str(e))
    except Exception as e:
        error(f"Unexpected error: {e}")
