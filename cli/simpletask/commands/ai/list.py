"""List OpenCode, Qwen, Gemini, and Vibe CLI command templates."""

from pathlib import Path

import typer

from simpletask.core.ai_templates import (
    EDITOR_CONFIGS,
    get_agents_installed_status,
    get_bundled_agents,
    get_bundled_gemini_templates,
    get_bundled_qwen_templates,
    get_bundled_templates,
    get_bundled_vibe_templates,
    get_gemini_installed_status,
    get_global_agents_dir,
    get_global_commands_dir,
    get_global_gemini_commands_dir,
    get_global_qwen_commands_dir,
    get_global_vibe_commands_dir,
    get_installed_status,
    get_local_agents_dir,
    get_local_commands_dir,
    get_local_gemini_commands_dir,
    get_local_qwen_commands_dir,
    get_local_vibe_commands_dir,
    get_qwen_installed_status,
    get_vibe_installed_status,
)
from simpletask.utils.console import console, create_table


def _render_editor_table(
    title: str,
    editor_name: str,
    templates: list[Path],
    status: dict[str, dict[str, bool]],
    name_label: str = "Command",
) -> None:
    """Render a table showing template installation status.

    Args:
        title: Table title (e.g., "OpenCode Commands" or "Qwen Commands").
        editor_name: Display name for the editor (e.g., "OpenCode" or "Qwen").
        templates: List of template file paths.
        status: Installation status dict mapping filename to global/local bools.
        name_label: Column label for the template type (e.g., "Command" or "Agent").
    """
    table = create_table(
        title=title,
        columns=[name_label, "Global", "Local"],
    )

    for template_path in templates:
        name = template_path.stem  # Remove file extension
        template_status = status[template_path.name]

        global_icon = "[green]✓[/green]" if template_status["global"] else "[dim]-[/dim]"
        local_icon = "[green]✓[/green]" if template_status["local"] else "[dim]-[/dim]"

        table.add_row(name, global_icon, local_icon)

    console.print(table)


def list_command() -> None:
    """List available and installed OpenCode, Qwen, Gemini, and Vibe CLI commands.

    Shows which command templates are bundled with simpletask
    and whether they are installed globally or locally.

    Examples:
        simpletask ai list
    """
    try:
        # Get OpenCode templates
        opencode_templates = get_bundled_templates()
        opencode_status = get_installed_status()

        # Get OpenCode agents
        opencode_agents = get_bundled_agents()
        opencode_agents_status = get_agents_installed_status()

        # Get Qwen templates
        qwen_templates = get_bundled_qwen_templates()
        qwen_status = get_qwen_installed_status()

        # Get Gemini CLI templates
        gemini_templates = get_bundled_gemini_templates()
        gemini_status = get_gemini_installed_status()

        # Get Vibe skills
        vibe_templates = get_bundled_vibe_templates()
        vibe_status = get_vibe_installed_status()

        if (
            not opencode_templates
            and not opencode_agents
            and not qwen_templates
            and not gemini_templates
            and not vibe_templates
        ):
            console.print("[dim]No templates or agents found[/dim]")
            return

        # OpenCode commands table
        if opencode_templates:
            _render_editor_table(
                title="OpenCode Commands",
                editor_name=EDITOR_CONFIGS["opencode"].display_name,
                templates=opencode_templates,
                status=opencode_status,
            )

        # OpenCode agents table
        if opencode_agents:
            _render_editor_table(
                title="OpenCode Agents",
                editor_name=EDITOR_CONFIGS["opencode"].display_name,
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

        # Qwen table
        if qwen_templates:
            _render_editor_table(
                title="Qwen Commands",
                editor_name=EDITOR_CONFIGS["qwen"].display_name,
                templates=qwen_templates,
                status=qwen_status,
            )
            console.print(f"\n[bold]{EDITOR_CONFIGS['qwen'].display_name} Locations:[/bold]")
            console.print(f"  Global: {get_global_qwen_commands_dir()}")
            console.print(f"  Local:  {get_local_qwen_commands_dir()}\n")

        # Gemini CLI table
        if gemini_templates:
            _render_editor_table(
                title="Gemini CLI Commands",
                editor_name=EDITOR_CONFIGS["gemini"].display_name,
                templates=gemini_templates,
                status=gemini_status,
            )
            console.print(f"\n[bold]{EDITOR_CONFIGS['gemini'].display_name} Locations:[/bold]")
            console.print(f"  Global: {get_global_gemini_commands_dir()}")
            console.print(f"  Local:  {get_local_gemini_commands_dir()}\n")

        # Vibe skills table
        if vibe_templates:
            _render_editor_table(
                title="Mistral Vibe Skills",
                editor_name=EDITOR_CONFIGS["vibe"].display_name,
                templates=vibe_templates,
                status=vibe_status,
                name_label="Skill",
            )
            console.print(f"\n[bold]{EDITOR_CONFIGS['vibe'].display_name} Locations:[/bold]")
            console.print(f"  Global: {get_global_vibe_commands_dir()}")
            console.print(f"  Local:  {get_local_vibe_commands_dir()}\n")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e
