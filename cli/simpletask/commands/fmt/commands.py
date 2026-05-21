"""fmt command - Format task files to canonical YAML."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated

import typer

from ...core.project import ensure_project
from ...core.yaml_parser import InvalidTaskFileError, parse_task_file_from_text, serialize_task_file
from ...utils.console import console, error_console


@dataclass
class _FmtResults:
    """Files partitioned by their canonicalization status."""

    ok_files: list[Path] = field(default_factory=list)
    dirty_files: list[tuple[Path, str]] = field(default_factory=list)  # (path, canonical_content)
    error_files: list[Path] = field(default_factory=list)


def _collect_fmt_results(task_files: list[Path]) -> _FmtResults:
    """Read and classify each task file as ok, dirty, or error.

    Each file is read exactly once to avoid double I/O and TOCTOU issues.
    Dirty files carry their canonical content so callers can write without
    a second serialization pass.

    Args:
        task_files: Sorted list of task YAML file paths to process.

    Returns:
        _FmtResults with files partitioned into ok, dirty, and error categories.
    """
    results = _FmtResults()

    for file_path in task_files:
        try:
            current = file_path.read_text(encoding="utf-8")
        except OSError as e:
            error_console.print(f"[red]✗[/red] {file_path.name}: {e}")
            results.error_files.append(file_path)
            continue

        try:
            spec = parse_task_file_from_text(current, file_path)
        except InvalidTaskFileError as e:
            error_console.print(f"[red]✗[/red] {file_path.name}: {e}")
            results.error_files.append(file_path)
            continue

        canonical = serialize_task_file(spec)
        if current == canonical:
            results.ok_files.append(file_path)
        else:
            results.dirty_files.append((file_path, canonical))

    return results


def fmt_command(
    check: Annotated[
        bool,
        typer.Option(
            "--check",
            help="Exit non-zero if any file would change, without modifying files",
        ),
    ] = False,
) -> None:
    """Format all task files to canonical YAML.

    Rewrites every .tasks/*.yml file (excluding defaults.yml) through the
    canonical parse/write pipeline, normalizing key ordering, indentation,
    and quoting. Idempotent: running twice produces identical output.

    With --check, no files are written; exit code is 1 if any file would
    change (CI-friendly). No output is produced on success.

    Examples:
        simpletask fmt              # Rewrite all task files
        simpletask fmt --check      # Check formatting without writing
    """
    try:
        project = ensure_project()
    except ValueError as e:
        error_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None

    tasks_dir: Path = project.tasks_dir

    if not tasks_dir.exists():
        if not check:
            console.print("[dim]No .tasks/ directory found. Nothing to format.[/dim]")
        return

    task_files = sorted(p for p in tasks_dir.glob("*.yml") if p.name != "defaults.yml")

    if not task_files:
        if not check:
            console.print("[dim]No task files found. Nothing to format.[/dim]")
        return

    results = _collect_fmt_results(task_files)

    if check:
        if results.dirty_files:
            console.print("[red]Would reformat:[/red]")
            for path, _ in results.dirty_files:
                console.print(f"  {path.name}")
            console.print("Run `simpletask fmt` to apply.")
        if results.error_files:
            error_console.print("[red]Parse errors (fix these first):[/red]")
            for path in results.error_files:
                error_console.print(f"  {path.name}")
        if results.dirty_files or results.error_files:
            raise typer.Exit(1)
        # All canonical - exit 0 silently (AC4: no error output on success)
    else:
        for file_path in results.ok_files:
            console.print(f"[green]✓[/green] {file_path.name}")
        for file_path, canonical in results.dirty_files:
            file_path.write_text(canonical, encoding="utf-8")
            console.print(f"[yellow]↻[/yellow] {file_path.name} (reformatted)")
        if results.error_files:
            raise typer.Exit(1)
