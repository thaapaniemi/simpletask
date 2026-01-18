"""List OpenCode and Qwen command templates."""

import typer

from simpletask.core.ai_templates import (
    get_bundled_qwen_templates,
    get_bundled_templates,
    get_global_commands_dir,
    get_global_qwen_commands_dir,
    get_installed_status,
    get_local_commands_dir,
    get_local_qwen_commands_dir,
    get_qwen_installed_status,
)
from simpletask.utils.console import console, create_table


def list_command() -> None:
    """List available and installed OpenCode and Qwen commands.

    Shows which command templates are bundled with simpletask
    and whether they are installed globally or locally.

    Examples:
        simpletask ai list
    """
    try:
        # Get OpenCode templates
        opencode_templates = get_bundled_templates()
        opencode_status = get_installed_status()

        # Get Qwen templates
        qwen_templates = get_bundled_qwen_templates()
        qwen_status = get_qwen_installed_status()

        if not opencode_templates and not qwen_templates:
            console.print("[dim]No templates found[/dim]")
            return

        # OpenCode table
        if opencode_templates:
            table = create_table(
                title="OpenCode Commands",
                columns=["Command", "Global", "Local"],
            )

            for template_path in opencode_templates:
                name = template_path.stem  # Remove .md extension
                template_status = opencode_status[template_path.name]

                global_icon = "[green]✓[/green]" if template_status["global"] else "[dim]-[/dim]"
                local_icon = "[green]✓[/green]" if template_status["local"] else "[dim]-[/dim]"

                table.add_row(name, global_icon, local_icon)

            console.print(table)

            # Show OpenCode locations
            global_dir = get_global_commands_dir()
            local_dir = get_local_commands_dir()

            console.print("\n[bold]OpenCode Locations:[/bold]")
            console.print(f"  Global: {global_dir}")
            console.print(f"  Local:  {local_dir}\n")

        # Qwen table
        if qwen_templates:
            table = create_table(
                title="Qwen Commands",
                columns=["Command", "Global", "Local"],
            )

            for template_path in qwen_templates:
                name = template_path.stem  # Remove .toml extension
                template_status = qwen_status[template_path.name]

                global_icon = "[green]✓[/green]" if template_status["global"] else "[dim]-[/dim]"
                local_icon = "[green]✓[/green]" if template_status["local"] else "[dim]-[/dim]"

                table.add_row(name, global_icon, local_icon)

            console.print(table)

            # Show Qwen locations
            global_dir = get_global_qwen_commands_dir()
            local_dir = get_local_qwen_commands_dir()

            console.print("\n[bold]Qwen Locations:[/bold]")
            console.print(f"  Global: {global_dir}")
            console.print(f"  Local:  {local_dir}\n")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e
