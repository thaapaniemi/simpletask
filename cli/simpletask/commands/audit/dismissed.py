"""Get dismissed findings command."""

import typer

from simpletask.core.audit_ops import get_dismissed_findings
from simpletask.core.project import get_task_file_path
from simpletask.core.yaml_parser import InvalidTaskFileError, parse_task_file
from simpletask.utils.console import console, error


def dismissed_command(
    branch: str | None = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """List all dismissed findings (false_positive or uncertain) across all audit runs.

    Examples:
        simpletask audit dismissed
        simpletask audit dismissed --branch feature-123
    """
    try:
        file_path = get_task_file_path(branch)
        spec = parse_task_file(file_path)
        dismissed = get_dismissed_findings(spec)

        if not dismissed:
            console.print("[dim]No dismissed findings found[/dim]")
            return

        console.print(f"\n[bold]Dismissed Findings[/bold] ({file_path.name})\n")

        for finding in dismissed:
            console.print(
                f"  [bold]{finding.id}[/bold]  [{finding.verdict.value}]"
                f"  {finding.original_severity.value}/{finding.original_category.value}"
                f"  [dim]{finding.file}[/dim]"
            )
            console.print(f"    {finding.summary}")
            console.print()

        console.print(f"[dim]Total dismissed: {len(dismissed)}[/dim]\n")

    except FileNotFoundError as e:
        error(str(e))
        raise typer.Exit(1) from e
    except (ValueError, InvalidTaskFileError) as e:
        error(str(e))
        raise typer.Exit(1) from e
