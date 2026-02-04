"""List notes command."""

import typer

from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.mcp.server import note
from simpletask.utils.console import console, handle_exception


def list_command(
    task: str | None = typer.Option(None, "--task", "-t", help="Show notes for specific task"),
    root_only: bool = typer.Option(False, "--root-only", "-r", help="Show only root-level notes"),
) -> None:
    """List notes from root-level and/or task-level.

    Examples:
        simpletask note list
        simpletask note list --task T003
        simpletask note list --root-only
    """
    try:
        # Call MCP tool directly
        result = note(
            action="list",
            task_id=task,
            root_only=root_only,
        )

        # Display notes
        if result.total_count == 0:
            console.print("[dim]No notes found[/dim]")
            return

        console.print(f"\n[bold]Notes[/bold] (Total: {result.total_count})\n")

        # Display root-level notes
        if result.root_notes:
            console.print("[bold cyan]Root Notes:[/bold cyan]")
            for idx, note_content in enumerate(result.root_notes):
                console.print(f"  [{idx}] {note_content}")
            console.print()

        # Display task-level notes
        if result.task_notes:
            console.print("[bold cyan]Task Notes:[/bold cyan]")
            for task_id, notes in sorted(result.task_notes.items()):
                console.print(f"  [bold]{task_id}:[/bold]")
                for idx, note_content in enumerate(notes):
                    console.print(f"    [{idx}] {note_content}")
            console.print()

    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        handle_exception(e, "listing notes")
