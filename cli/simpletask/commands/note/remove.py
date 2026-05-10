"""Remove note command."""

from typing import Annotated

import typer

from simpletask.core.note_ops import remove_note
from simpletask.core.project import get_task_file_path
from simpletask.core.yaml_parser import InvalidTaskFileError, parse_task_file, write_task_file
from simpletask.utils.console import handle_exception, success
from simpletask.utils.output import OutputFormat, json_error, json_success, resolve_format


def remove_command(
    index: int | None = typer.Argument(None, help="Note index to remove (0-based)"),
    task: str | None = typer.Option(None, "--task", "-t", help="Task ID to remove note from"),
    all: bool = typer.Option(False, "--all", "-a", help="Remove all notes"),
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format (rich, plain, json)"),
    ] = OutputFormat.RICH,
) -> None:
    """Remove a note from root-level or task-level.

    Examples:
        simpletask note remove 0
        simpletask note remove 1 --task T003
        simpletask note remove --all --task T003

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
        spec = remove_note(spec=spec, index=index, task_id=task, all=all)
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
                    "action": "note_removed",
                    "message": "Removed note",
                    "summary": {"notes_total": notes_total},
                }
            )
        else:
            location = f"task {task}" if task else "root"
            if all:
                success(f"Removed all notes from {location}")
            else:
                success(f"Removed note {index} from {location}")

    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        if format == OutputFormat.JSON:
            json_error(str(e))
        else:
            handle_exception(e, "removing note")
        raise typer.Exit(1) from None
