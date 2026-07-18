"""List OpenCode, GitHub Copilot, and Pi AI templates."""

from pathlib import Path

import typer

from simpletask.core.ai_templates import (
    EDITOR_CONFIGS,
    get_agents_installed_status,
    get_bundled_agents,
    get_bundled_copilot_templates,
    get_bundled_pi_templates,
    get_bundled_templates,
    get_copilot_installed_status,
    get_global_agents_dir,
    get_global_commands_dir,
    get_global_copilot_commands_dir,
    get_global_pi_commands_dir,
    get_installed_status,
    get_local_agents_dir,
    get_local_commands_dir,
    get_local_copilot_commands_dir,
    get_local_pi_commands_dir,
    get_pi_installed_status,
)
from simpletask.utils.console import console, create_table


def _render_editor_table(
    title: str,
    templates: list[Path],
    status: dict[str, dict[str, bool]],
    name_label: str = "Command",
) -> None:
    """Render a table showing template installation status."""
    table = create_table(title=title, columns=[name_label, "Global", "Local"])
    for template_path in templates:
        name = template_path.name if template_path.is_dir() else template_path.stem
        template_status = status[template_path.name]
        global_icon = "[green]✓[/green]" if template_status["global"] else "[dim]-[/dim]"
        local_icon = "[green]✓[/green]" if template_status["local"] else "[dim]-[/dim]"
        table.add_row(name, global_icon, local_icon)
    console.print(table)


def list_command() -> None:
    """List bundled and installed resources for the supported integrations."""
    try:
        opencode_templates = get_bundled_templates()
        opencode_status = get_installed_status()
        opencode_agents = get_bundled_agents()
        opencode_agents_status = get_agents_installed_status()
        copilot_templates = get_bundled_copilot_templates()
        copilot_status = get_copilot_installed_status()
        pi_templates = get_bundled_pi_templates()
        pi_status = get_pi_installed_status()

        if (
            not opencode_templates
            and not opencode_agents
            and not copilot_templates
            and not pi_templates
        ):
            console.print("[dim]No templates or agents found[/dim]")
            return

        if opencode_templates:
            _render_editor_table(
                title="OpenCode Commands",
                templates=opencode_templates,
                status=opencode_status,
            )
        if opencode_agents:
            _render_editor_table(
                title="OpenCode Agents",
                templates=opencode_agents,
                status=opencode_agents_status,
                name_label="Agent",
            )
        if opencode_templates or opencode_agents:
            console.print(f"\n[bold]{EDITOR_CONFIGS['opencode'].display_name} Locations:[/bold]")
            if opencode_templates:
                console.print(f"  Commands Global: {get_global_commands_dir()}")
                console.print(f"  Commands Local:  {get_local_commands_dir()}")
            if opencode_agents:
                console.print(f"  Agents Global:   {get_global_agents_dir()}")
                console.print(f"  Agents Local:    {get_local_agents_dir()}")
            console.print("")

        if copilot_templates:
            _render_editor_table(
                title="GitHub Copilot Prompts",
                templates=copilot_templates,
                status=copilot_status,
                name_label="Prompt",
            )
            console.print(f"\n[bold]{EDITOR_CONFIGS['copilot'].display_name} Locations:[/bold]")
            console.print(f"  Global: {get_global_copilot_commands_dir()}")
            console.print(f"  Local:  {get_local_copilot_commands_dir()}\n")

        if pi_templates:
            _render_editor_table(
                title="Pi Prompts",
                templates=pi_templates,
                status=pi_status,
                name_label="Prompt",
            )
            console.print(f"\n[bold]{EDITOR_CONFIGS['pi'].display_name} Locations:[/bold]")
            console.print(f"  Global: {get_global_pi_commands_dir()}")
            console.print(f"  Local:  {get_local_pi_commands_dir()}\n")
    except Exception as error:
        console.print(f"[red]Error: {error}[/red]")
        raise typer.Exit(1) from error
