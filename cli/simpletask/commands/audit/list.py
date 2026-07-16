"""List audit runs command."""

import typer

from simpletask.core.audit_ops import list_audit_runs
from simpletask.core.project import get_task_file_path
from simpletask.core.yaml_parser import InvalidTaskFileError, parse_task_file
from simpletask.utils.console import console, error


def list_command(
    branch: str | None = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """List all audit runs in the task file.

    Examples:
        simpletask audit list
        simpletask audit list --branch feature-123
    """
    try:
        file_path = get_task_file_path(branch)
        spec = parse_task_file(file_path)
        runs = list_audit_runs(spec)

        if not runs:
            console.print("[dim]No audit runs found[/dim]")
            return

        console.print(f"\n[bold]Audit Runs[/bold] ({file_path.name})\n")

        for run in runs:
            verdict_parts = ", ".join(f"{v}: {c}" for v, c in sorted(run["verdict_counts"].items()))
            console.print(
                f"  [bold cyan]Iteration {run['iteration']}[/bold cyan]"
                f"  range=[dim]{run['base_sha']}..{run['head_sha']}[/dim]"
                f"  findings={run['findings_total']}"
                f"  [{verdict_parts}]"
            )

        console.print(f"\n[dim]Total: {len(runs)} audit run(s)[/dim]\n")

    except FileNotFoundError as e:
        error(str(e))
        raise typer.Exit(1) from e
    except (ValueError, InvalidTaskFileError) as e:
        error(str(e))
        raise typer.Exit(1) from e
