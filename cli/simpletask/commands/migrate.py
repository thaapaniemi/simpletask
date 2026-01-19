"""Migrate command - Move nested task files to flat normalized structure."""

from pathlib import Path

import typer

from ..core.project import ensure_project, normalize_branch_name
from ..core.yaml_parser import parse_task_file, write_task_file
from ..utils.console import console, error, info, success, warning


def _validate_path_safety(path: Path, tasks_dir: Path) -> None:
    """Ensure path is within tasks directory (prevents symlink attacks).

    Resolves symlinks and validates the real path is within tasks_dir.

    Args:
        path: Path to validate
        tasks_dir: Expected parent directory

    Raises:
        ValueError: If resolved path is outside tasks_dir
    """
    resolved_path = path.resolve()
    resolved_tasks_dir = tasks_dir.resolve()

    if not resolved_path.is_relative_to(resolved_tasks_dir):
        raise ValueError(f"Security: Path outside tasks directory: {path}")


def migrate(
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Show what would be done without making changes"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing normalized files"),
) -> None:
    """Migrate task files to flat normalized structure.

    Scans .tasks/ directory recursively for YAML files and moves them to the root
    of .tasks/ with normalized filenames.

    Examples:
        simpletask migrate --dry-run    # Preview changes
        simpletask migrate              # Perform migration
        simpletask migrate --force      # Overwrite conflicts
    """
    try:
        project = ensure_project()
        tasks_dir = project.tasks_dir

        if not tasks_dir.exists():
            info("No .tasks directory found")
            return

        # Find all YAML files (including nested)
        yaml_files = list(tasks_dir.rglob("*.yml"))

        if not yaml_files:
            info("No task files found to migrate")
            return

        migrations = []
        conflicts = []

        # Analyze all files
        console.print(f"\n[bold]Scanning {len(yaml_files)} task file(s)...[/bold]\n")

        for old_path in yaml_files:
            try:
                # Parse to get branch name
                spec = parse_task_file(old_path)
                normalized = normalize_branch_name(spec.branch)
                new_path = tasks_dir / f"{normalized}.yml"

                # Check if already in correct location
                if old_path == new_path:
                    continue

                # Check for conflicts
                if new_path.exists() and not force:
                    conflicts.append((old_path, new_path, spec.branch))
                else:
                    migrations.append((old_path, new_path, spec))

            except Exception as e:
                warning(f"Skipping {old_path.relative_to(project.root)}: {e}")

        # Report findings
        if not migrations and not conflicts:
            success("All task files already in normalized locations")
            return

        if conflicts:
            console.print("[bold red]Branch name collisions detected:[/bold red]\n")
            for old_path, new_path, old_branch in conflicts:
                try:
                    # Parse the existing file to show which branch it belongs to
                    existing_spec = parse_task_file(new_path)
                    rel_path = old_path.relative_to(project.root)
                    console.print(f"  [yellow]Branch '{old_branch}'[/yellow] ({rel_path})")
                    console.print(f"    collides with [yellow]'{existing_spec.branch}'[/yellow]")
                    console.print(f"    → both normalize to: {new_path.name}\n")
                except Exception:
                    # Fallback if can't parse existing file
                    rel_path = old_path.relative_to(project.root)
                    console.print(f"  [yellow]Branch '{old_branch}'[/yellow] ({rel_path})")
                    console.print(
                        f"    → {new_path.relative_to(project.root)} [red](exists)[/red]\n"
                    )

            if not force:
                error(
                    f"Found {len(conflicts)} conflict(s). Use --force to overwrite existing files."
                )
                return

        # Show migration plan
        console.print(f"[bold]Migration plan:[/bold] {len(migrations)} file(s)\n")
        for old_path, new_path, spec in migrations:
            console.print(f"  [cyan]{old_path.relative_to(project.root)}[/cyan]")
            console.print(f"    → {new_path.relative_to(project.root)}\n")

        if dry_run:
            info("Dry-run mode - no changes made")
            return

        # Perform migration
        migrated = 0
        for old_path, new_path, spec in migrations:
            try:
                # Security: validate paths are within tasks directory
                _validate_path_safety(old_path, tasks_dir)
                _validate_path_safety(new_path, tasks_dir)

                # Write to new location (preserves content)
                write_task_file(new_path, spec, update_timestamp=False)

                # Remove old file
                old_path.unlink()

                # Remove empty parent directories
                parent = old_path.parent
                while parent != tasks_dir and parent.exists():
                    try:
                        if not any(parent.iterdir()):
                            parent.rmdir()
                            parent = parent.parent
                        else:
                            break
                    except OSError:
                        break

                migrated += 1

            except Exception as e:
                warning(f"Failed to migrate {old_path.relative_to(project.root)}: {e}")

        # Summary
        console.print()
        success(f"Migrated {migrated}/{len(migrations)} file(s)")

        if migrated > 0:
            info(
                "\nNext steps:\n"
                "  - Review migrated files\n"
                "  - Test with: simpletask list\n"
                "  - Commit changes"
            )

    except ValueError as e:
        error(str(e))
    except Exception as e:
        error(f"Unexpected error: {e}")
