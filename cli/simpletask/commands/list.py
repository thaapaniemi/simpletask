"""List command - Show status summary of all tasks."""

from typing import Annotated

import typer

from ..core.project import ensure_project
from ..core.yaml_parser import InvalidTaskFileError, parse_task_file
from ..utils.console import console, create_table, error, info


def list_tasks(
    simple: Annotated[
        bool,
        typer.Option(
            "--simple",
            "-s",
            help="Output only branch names, one per line (for scripting)",
        ),
    ] = False,
) -> None:
    """Display status summary of all tasks.

    By default, shows a table with:
    - Branch name
    - Title
    - Acceptance criteria progress
    - Task progress (if tasks defined)

    Tasks are sorted by file modification time (newest first).

    With --simple flag, outputs only branch names (one per line) for scripting.

    Examples:
        simpletask list
        simpletask list --simple
        simpletask list -s | xargs -I{} simpletask show --branch {}
    """
    try:
        project = ensure_project()

        tasks_with_paths = project.list_tasks_by_mtime()

        if not tasks_with_paths:
            info("No tasks found in ./.tasks directory")
            info("Create a new task with: simpletask new <branch> <prompt>")
            return

        # Simple output for scripting
        if simple:
            for branch, _path in tasks_with_paths:
                console.print(branch)
            return

        # Rich table output (default)
        table = create_table("Task Status Summary", ["Branch", "Title", "AC Progress", "Tasks"])

        # Populate table
        for branch, task_file in tasks_with_paths:
            try:
                spec = parse_task_file(task_file)

                # Calculate AC progress
                total_ac = len(spec.acceptance_criteria)
                completed_ac = sum(1 for ac in spec.acceptance_criteria if ac.completed)
                ac_progress = f"{completed_ac}/{total_ac}"

                # Calculate task progress
                if spec.tasks:
                    total_tasks = len(spec.tasks)
                    completed_tasks = sum(1 for t in spec.tasks if t.status.value == "completed")
                    task_progress = f"{completed_tasks}/{total_tasks}"
                else:
                    task_progress = "-"

                # Truncate title if too long
                title = spec.title if len(spec.title) <= 40 else spec.title[:37] + "..."

                table.add_row(
                    branch,
                    title,
                    ac_progress,
                    task_progress,
                )

            except (FileNotFoundError, InvalidTaskFileError):
                # Skip invalid task files
                table.add_row(branch, "[red]Error[/red]", "-", "-")

        console.print()
        console.print(table)
        console.print()

    except ValueError as e:
        error(str(e))
    except Exception as e:
        error(f"Unexpected error: {e}")
