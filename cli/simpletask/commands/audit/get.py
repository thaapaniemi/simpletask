"""Get a specific audit run command."""

import typer

from simpletask.core.audit_ops import get_audit_run
from simpletask.core.project import get_task_file_path
from simpletask.core.yaml_parser import InvalidTaskFileError, parse_task_file
from simpletask.utils.console import console, error


def get_command(
    iteration: int = typer.Option(..., "--iteration", "-i", help="Audit iteration number"),
    branch: str | None = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """Get details of a specific audit run.

    Examples:
        simpletask audit get --iteration 1
        simpletask audit get --iteration 2 --branch feature-123
    """
    try:
        file_path = get_task_file_path(branch)
        spec = parse_task_file(file_path)
        run = get_audit_run(spec, iteration)

        console.print(f"\n[bold]Audit Run - Iteration {run.iteration}[/bold]\n")
        console.print(f"  [dim]Base SHA:[/dim] {run.base_sha}")
        console.print(f"  [dim]Head SHA:[/dim] {run.head_sha}")
        console.print(f"  [dim]Findings:[/dim] {len(run.findings)}\n")

        for finding in run.findings:
            corrected = ""
            if finding.corrected_severity or finding.corrected_category:
                corrected = (
                    f" -> {finding.corrected_severity.value if finding.corrected_severity else '?'}"
                    f"/{finding.corrected_category.value if finding.corrected_category else '?'}"
                )
            console.print(
                f"  [bold]{finding.id}[/bold]  [{finding.verdict.value}]"
                f"  {finding.original_severity.value}/{finding.original_category.value}{corrected}"
                f"  [dim]{finding.file}[/dim]"
            )
            console.print(f"    {finding.summary}")
            if finding.task_id:
                console.print(f"    [dim]task: {finding.task_id}[/dim]")
            console.print()

    except FileNotFoundError as e:
        error(str(e))
        raise typer.Exit(1) from e
    except (ValueError, InvalidTaskFileError) as e:
        error(str(e))
        raise typer.Exit(1) from e
