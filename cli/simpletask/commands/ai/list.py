"""List OpenCode command templates."""

import typer

from simpletask.core.ai_templates import (
    get_bundled_templates,
    get_global_commands_dir,
    get_installed_status,
    get_local_commands_dir,
)
from simpletask.utils.console import console, create_table


def list_command() -> None:
    """List available and installed OpenCode commands.

    Shows which command templates are bundled with simpletask
    and whether they are installed globally or locally.

    Examples:
        simpletask ai list
    """
    try:
        # Get template names
        templates = get_bundled_templates()

        if not templates:
            console.print("[dim]No templates found[/dim]")
            return

        # Get installation status
        status = get_installed_status()

        # Create table
        table = create_table(
            title="OpenCode Commands",
            columns=["Command", "Global", "Local"],
        )

        # Add rows
        for template_path in templates:
            name = template_path.stem  # Remove .md extension
            template_status = status[template_path.name]

            global_icon = "[green]✓[/green]" if template_status["global"] else "[dim]-[/dim]"
            local_icon = "[green]✓[/green]" if template_status["local"] else "[dim]-[/dim]"

            table.add_row(name, global_icon, local_icon)

        console.print(table)

        # Show locations
        global_dir = get_global_commands_dir()
        local_dir = get_local_commands_dir()

        console.print("\n[bold]Locations:[/bold]")
        console.print(f"  Global: {global_dir}")
        console.print(f"  Local:  {local_dir}\n")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e
