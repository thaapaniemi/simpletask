"""Quality preset command."""

from typing import Annotated

import typer

from simpletask.core.presets import QUALITY_PRESETS, load_all_presets
from simpletask.core.project import get_task_file_path
from simpletask.core.quality_ops import apply_quality_preset
from simpletask.core.yaml_parser import parse_task_file, write_task_file
from simpletask.utils.console import console, error


def preset_command(
    preset_name: Annotated[
        str | None,
        typer.Argument(
            help="Preset name (python, typescript, node, go, rust). Use --list to see all presets."
        ),
    ] = None,
    list_flag: Annotated[bool, typer.Option("--list", "-l", help="List available presets")] = False,
    branch: Annotated[
        str | None,
        typer.Option("--branch", "-b", help="Branch name (defaults to current git branch)"),
    ] = None,
) -> None:
    """Apply a quality preset configuration.

    Presets provide predefined quality configurations for common tech stacks.
    Uses fill-gaps-only strategy: only sets values that are not already configured.

    Examples:
        simpletask quality preset --list
        simpletask quality preset python
        simpletask quality preset typescript --branch feature-123
    """
    try:
        # Handle --list flag
        if list_flag:
            all_presets = load_all_presets()
            builtin_names = set(QUALITY_PRESETS.keys())
            custom_names = set(all_presets.keys()) - builtin_names

            console.print("\n[bold]Available Quality Presets:[/bold]\n")

            if builtin_names:
                console.print("[bold cyan]Built-in Presets:[/bold cyan]")
                for preset in sorted(builtin_names):
                    console.print(f"  • [cyan]{preset}[/cyan]")
                console.print()

            if custom_names:
                console.print("[bold green]Custom Presets:[/bold green]")
                for preset in sorted(custom_names):
                    console.print(f"  • [green]{preset}[/green]")
                console.print()

            console.print("[dim]Use 'simpletask quality preset <name>' to apply a preset[/dim]\n")
            return

        # Require preset_name if not listing
        if not preset_name:
            error("Preset name required. Use --list to see available presets.")
            raise typer.Exit(1)

        # Get file path
        file_path = get_task_file_path(branch)

        # Parse task file
        spec = parse_task_file(file_path)

        # Get existing quality requirements
        existing_quality_reqs = spec.quality_requirements

        # Apply preset with fill-gaps-only strategy using shared logic
        merged_reqs, applied = apply_quality_preset(existing_quality_reqs, preset_name)

        # Update spec
        spec.quality_requirements = merged_reqs

        # Write back to file
        write_task_file(file_path, spec)

        # Display confirmation
        console.print(f"\n[green]✓[/green] Applied [bold]{preset_name}[/bold] preset configuration")

        # Show what was applied vs kept
        console.print("\n[bold]Changes:[/bold]")
        applied_items = [k for k, v in applied.items() if v]
        kept_items = [k for k, v in applied.items() if not v]

        if applied_items:
            console.print("[green]Applied from preset:[/green]")
            for item in applied_items:
                console.print(f"  • {item}")

        if kept_items:
            console.print("[yellow]Kept existing configuration:[/yellow]")
            for item in kept_items:
                console.print(f"  • {item}")

        console.print("\n[dim]Use 'simpletask quality show' to view current configuration[/dim]\n")

    except ValueError as e:
        error(str(e))
    except FileNotFoundError as e:
        error(str(e))
    except Exception as e:
        error(f"Unexpected error: {e}")
