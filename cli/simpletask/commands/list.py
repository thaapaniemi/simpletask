"""List command - List all task files."""

import typer

from ..core.project import ensure_project
from ..utils.console import console, error, info


def list_tasks() -> None:
    """List all task files in ./tasks directory.

    Shows all available task branches.

    Examples:
        simpletask list
    """
    try:
        project = ensure_project()

        tasks = project.list_tasks()

        if not tasks:
            info("No tasks found in ./tasks directory")
            info("Create a new task with: simpletask new <branch> <prompt>")
            return

        console.print(f"\n[bold]Tasks in {project.tasks_dir.relative_to(project.root)}:[/bold]\n")
        for branch in tasks:
            console.print(f"  • {branch}")

        console.print(f"\n[dim]Total: {len(tasks)} task(s)[/dim]")

    except ValueError as e:
        error(str(e))
    except Exception as e:
        error(f"Unexpected error: {e}")
