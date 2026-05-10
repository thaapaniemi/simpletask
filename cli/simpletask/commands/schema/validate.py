"""Schema validate command."""

from pathlib import Path
from typing import Annotated

import typer

from ...core.project import get_task_file_path
from ...core.validation import validate_task_file
from ...utils.console import error, success
from ...utils.output import OutputFormat, json_error, json_success, resolve_format


def _print_json_validate_single(file_path: Path, errors: list[str] | None) -> None:
    """Print validation result for single file as JSON.

    Args:
        file_path: Path to the validated file
        errors: List of error messages, or None if valid
    """
    output = {
        "file": str(file_path),
        "valid": errors is None or len(errors) == 0,
        "errors": errors or [],
    }
    json_success(output)


def _print_json_validate_all(results: list[dict]) -> None:
    """Print validation results for all files as JSON.

    Args:
        results: List of validation result dicts
    """
    all_valid = all(r["valid"] for r in results)
    output = {
        "results": results,
        "all_valid": all_valid,
    }
    json_success(output)


def validate(
    file: str | None = typer.Argument(
        None, help="Task file to validate (defaults to current branch)"
    ),
    all_files: bool = typer.Option(False, "--all", help="Validate all task files"),
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format (rich, plain, json)"),
    ] = OutputFormat.RICH,
) -> None:
    """Validate task file(s) against JSON schema.

    Examples:
        simpletask schema validate                    # Validate current task
        simpletask schema validate add-dark-mode      # Validate specific task
        simpletask schema validate --all              # Validate all tasks
    """
    try:
        # Resolve format
        format = resolve_format(format)

        if all_files:
            # Validate all task files
            from ...core.project import ensure_project

            project = ensure_project()
            tasks = project.list_tasks()

            if not tasks:
                msg = "No tasks found in .tasks directory"
                if format == OutputFormat.JSON:
                    json_error(msg)
                else:
                    error(msg)
                raise typer.Exit(1)

            errors_found = False
            results = []
            for branch in tasks:
                task_file = project.get_task_file(branch)
                errors = validate_task_file(task_file)
                file_path_rel = task_file.relative_to(project.root)
                is_valid = not errors
                results.append(
                    {
                        "file": str(file_path_rel),
                        "valid": is_valid,
                        "errors": errors or [],
                    }
                )
                if not is_valid:
                    errors_found = True
                    if format != OutputFormat.JSON:
                        from ...utils.console import error_console

                        error_console.print(f"\n[red]Errors in {file_path_rel}:[/red]")
                        for err in errors:
                            error_console.print(f"  {err}")
                else:
                    if format != OutputFormat.JSON:
                        success(f"{file_path_rel}: Valid")

            if format == OutputFormat.JSON:
                _print_json_validate_all(results)
                if errors_found:
                    raise typer.Exit(1)
                return
            else:
                if errors_found:
                    raise typer.Exit(1)
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

            if format == OutputFormat.JSON:
                _print_json_validate_single(task_file, errors)
            elif errors:
                from ...utils.console import error_console

                error_console.print("\n[red]Validation errors:[/red]")
                for err in errors:
                    error_console.print(f"  {err}")
                error("Schema validation failed")
            else:
                success(f"{task_file.name}: Valid")

            if errors:
                raise typer.Exit(1)

    except typer.Exit:
        raise
    except ValueError as e:
        if format == OutputFormat.JSON:
            json_error(str(e))
            raise typer.Exit(1) from None
        else:
            error(str(e))
    except Exception as e:
        if format == OutputFormat.JSON:
            json_error(f"Unexpected error: {e}")
            raise typer.Exit(1) from None
        else:
            error(f"Unexpected error: {e}")
