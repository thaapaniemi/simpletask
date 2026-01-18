"""Status command - Show status summary of all tasks."""

import typer

from ..core.project import ensure_project
from ..core.yaml_parser import InvalidTaskFileError, parse_task_file
from ..utils.console import create_table, error, info


def status() -> None:
    """Display status summary of all tasks.

    Shows a table with:
    - Branch name
    - Title
    - Overall status
    - Acceptance criteria progress
    - Task progress (if tasks defined)

    Examples:
        simpletask status
    """
    try:
        project = ensure_project()

        tasks = project.list_tasks()

        if not tasks:
            info("No tasks found in ./tasks directory")
            info("Create a new task with: simpletask new <branch> <prompt>")
            return

        # Create table
        table = create_table(
            "Task Status Summary", ["Branch", "Title", "Status", "AC Progress", "Tasks"]
        )

        # Populate table
        for branch in tasks:
            try:
                task_file = project.get_task_file(branch)
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

                # Color status
                status_color = (
                    "green"
                    if spec.status.value == "completed"
                    else "yellow"
                    if spec.status.value == "in_progress"
                    else "red"
                    if spec.status.value == "blocked"
                    else "white"
                )

                table.add_row(
                    branch,
                    title,
                    f"[{status_color}]{spec.status.value}[/{status_color}]",
                    ac_progress,
                    task_progress,
                )

            except (FileNotFoundError, InvalidTaskFileError) as e:
                # Skip invalid task files
                table.add_row(branch, "[red]Error[/red]", "-", "-", "-")

        from ..utils.console import console

        console.print()
        console.print(table)
        console.print()

    except ValueError as e:
        error(str(e))
    except Exception as e:
        error(f"Unexpected error: {e}")
