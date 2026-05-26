"""Add an audit run command."""

import json
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from simpletask.core.audit_ops import add_audit_run
from simpletask.core.models import AuditFinding
from simpletask.core.project import get_task_file_path
from simpletask.core.yaml_parser import InvalidTaskFileError, parse_task_file, write_task_file
from simpletask.utils.console import console, error


def add_run_command(
    iteration: Annotated[int, typer.Option("--iteration", "-i", help="Audit iteration number")],
    base_sha: Annotated[str, typer.Option("--base-sha", help="Git SHA of the base commit audited")],
    head_sha: Annotated[str, typer.Option("--head-sha", help="Git SHA of the HEAD commit audited")],
    findings_file: Annotated[
        Path,
        typer.Option(
            "--findings",
            "-f",
            help="Path to JSON file containing audit findings array",
            exists=True,
            readable=True,
        ),
    ],
    branch: str | None = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """Add an audit run from a JSON findings file.

    The findings file must be a JSON array of finding objects. Each finding must have:
    id, file, original_severity, original_category, verdict, summary.

    When verdict=reclassified, corrected_severity and corrected_category are also required.

    Examples:
        simpletask audit add-run --iteration 1 --base-sha abc1234 --head-sha def5678 --findings findings.json
    """
    try:
        file_path = get_task_file_path(branch)
        spec = parse_task_file(file_path)

        try:
            raw = json.loads(findings_file.read_text())
        except json.JSONDecodeError as exc:
            error(f"Invalid JSON in findings file '{findings_file}': {exc}")
            raise typer.Exit(1) from exc

        if not isinstance(raw, list):
            error("findings file must contain a JSON array of finding objects")
            raise typer.Exit(1)

        parsed_findings: list[AuditFinding] = []
        for idx, f in enumerate(raw):
            try:
                parsed_findings.append(AuditFinding(**f))
            except (ValidationError, TypeError) as exc:
                error(f"Invalid finding at index {idx}: {exc}")
                raise typer.Exit(1) from exc

        if not parsed_findings:
            error("findings array must contain at least one finding")
            raise typer.Exit(1)

        spec = add_audit_run(spec, iteration, base_sha, head_sha, parsed_findings)
        write_task_file(file_path, spec)

        console.print(
            f"[green]Added audit run for iteration {iteration}[/green] "
            f"({len(parsed_findings)} findings, range={base_sha}..{head_sha})"
        )

    except FileNotFoundError as e:
        error(str(e))
        raise typer.Exit(1) from e
    except (ValueError, InvalidTaskFileError) as e:
        error(str(e))
        raise typer.Exit(1) from e
