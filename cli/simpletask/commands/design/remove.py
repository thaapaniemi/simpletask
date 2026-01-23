"""Design remove command."""

from typing import Annotated

import typer

from simpletask.core.design_ops import remove_design_field
from simpletask.core.project import get_task_file_path
from simpletask.core.yaml_parser import parse_task_file, write_task_file
from simpletask.utils.console import console, error


def remove_command(
    field: Annotated[
        str,
        typer.Argument(
            help="Field to clear: patterns, references, constraints, security, error-handling, all"
        ),
    ],
    branch: Annotated[
        str | None,
        typer.Option("--branch", "-b", help="Branch name (defaults to current git branch)"),
    ] = None,
    index: Annotated[
        int | None,
        typer.Option(
            "--index",
            "-i",
            help="Index of item to remove (0-based, for list fields)",
        ),
    ] = None,
) -> None:
    """Remove or clear design guidance fields.

    Field options:
        patterns         - Clear all patterns (or single item with --index)
        references       - Clear all references (or single item with --index)
        constraints      - Clear all constraints (or single item with --index)
        security         - Clear all security considerations (or single item with --index)
        error-handling   - Clear error handling pattern
        all              - Remove entire design section

    Examples:
        simpletask design remove patterns --index 0
        simpletask design remove references --index 1
        simpletask design remove error-handling
        simpletask design remove all
    """
    try:
        # Get file path
        file_path = get_task_file_path(branch)

        # Parse task file
        spec = parse_task_file(file_path)

        # Use shared design operations logic
        try:
            updated_spec, message = remove_design_field(
                spec=spec,
                field=field,
                index=index,
                all_items=False,  # CLI doesn't require explicit all flag
            )
            spec = updated_spec
            console.print(f"[green]✓[/green] {message}")
        except ValueError as e:
            # Friendly messages for user-facing CLI
            if "No design section found" in str(e):
                console.print("[yellow]No design section found[/yellow]\n")
                return
            elif "found" in str(e) and ("No" in str(e) or "not found" in str(e)):
                # e.g., "No patterns found", "No error handling strategy found"
                console.print(f"[yellow]{e}[/yellow]\n")
                return
            elif "out of range" in str(e) or "Invalid field" in str(e):
                error(str(e))
                raise typer.Exit(1) from None
            else:
                raise

        # Write back to file
        write_task_file(file_path, spec)
        console.print(f"[dim]Updated {file_path.name}[/dim]\n")

    except FileNotFoundError as e:
        error(str(e))
    except typer.Exit:
        raise
    except Exception as e:
        error(f"Unexpected error: {e}")
