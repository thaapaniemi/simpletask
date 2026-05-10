"""Add note command."""

from typing import Annotated

import typer

from simpletask.core.note_ops import add_note
from simpletask.core.project import get_task_file_path
from simpletask.core.yaml_parser import InvalidTaskFileError, parse_task_file, write_task_file
from simpletask.utils.console import handle_exception, success
from simpletask.utils.output import OutputFormat, json_error, json_success, resolve_format


def add_command(
    content: str = typer.Argument(..., help="Note content"),
    task: str | None = typer.Option(None, "--task", "-t", help="Task ID to add note to"),
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format (rich, plain, json)"),
    ] = OutputFormat.RICH,
) -> None:
    """Add a note to root-level or task-level.

    Examples:
        simpletask note add "Remember to update docs"
        simpletask note add "This task needs refactoring" --task T003

    Raises:
        ValueError: If not in a git repository or branch cannot be determined
        FileNotFoundError: If task file doesn't exist for the specified branch
        InvalidTaskFileError: If task file is malformed and cannot be parsed
    """
    try:
        # Resolve format
        format = resolve_format(format)

        file_path = get_task_file_path(None)
        spec = parse_task_file(file_path)
        spec = add_note(spec=spec, content=content, task_id=task)
        write_task_file(file_path, spec)

        # Compute notes_total (root + all task notes)
        notes_total = len(spec.notes or []) + sum(
            len(t.notes) for t in (spec.tasks or []) if t.notes
        )

        # Output results based on format
        if format == OutputFormat.JSON:
            json_success(
                {
                    "success": True,
                    "action": "note_added",
                    "message": "Added note",
                    "summary": {"notes_total": notes_total},
                }
            )
        else:
            location = f"task {task}" if task else "root"
            success(f"Added note to {location}")

    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        if format == OutputFormat.JSON:
            json_error(str(e))
        else:
            handle_exception(e, "adding note")
        raise typer.Exit(1) from None
