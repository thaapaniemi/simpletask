"""List OpenCode, Qwen, and Gemini CLI command templates."""

from pathlib import Path

import typer

from simpletask.core.ai_templates import (
    EDITOR_CONFIGS,
    get_bundled_gemini_templates,
    get_bundled_qwen_templates,
    get_bundled_templates,
    get_gemini_installed_status,
    get_global_commands_dir,
    get_global_gemini_commands_dir,
    get_global_qwen_commands_dir,
    get_installed_status,
    get_local_commands_dir,
    get_local_gemini_commands_dir,
    get_local_qwen_commands_dir,
    get_qwen_installed_status,
)
from simpletask.utils.console import console, create_table


def _render_editor_table(
    title: str,
    editor_name: str,
    templates: list[Path],
    status: dict[str, dict[str, bool]],
    global_dir: Path,
    local_dir: Path,
) -> None:
    """Render a table showing template installation status.

    Args:
        title: Table title (e.g., "OpenCode Commands" or "Qwen Commands").
        editor_name: Display name for the editor (e.g., "OpenCode" or "Qwen").
        templates: List of template file paths.
        status: Installation status dict mapping filename to global/local bools.
        global_dir: Path to global installation directory.
        local_dir: Path to local installation directory.
    """
    table = create_table(
        title=title,
        columns=["Command", "Global", "Local"],
    )

    for template_path in templates:
        name = template_path.stem  # Remove file extension
        template_status = status[template_path.name]

        global_icon = "[green]✓[/green]" if template_status["global"] else "[dim]-[/dim]"
        local_icon = "[green]✓[/green]" if template_status["local"] else "[dim]-[/dim]"

        table.add_row(name, global_icon, local_icon)

    console.print(table)

    # Show locations
    console.print(f"\n[bold]{editor_name} Locations:[/bold]")
    console.print(f"  Global: {global_dir}")
    console.print(f"  Local:  {local_dir}\n")


def list_command() -> None:
    """List available and installed OpenCode, Qwen, and Gemini CLI commands.

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

        # Get Gemini CLI templates
        gemini_templates = get_bundled_gemini_templates()
        gemini_status = get_gemini_installed_status()

        if not opencode_templates and not qwen_templates and not gemini_templates:
            console.print("[dim]No templates found[/dim]")
            return

        # OpenCode table
        if opencode_templates:
            _render_editor_table(
                title="OpenCode Commands",
                editor_name=EDITOR_CONFIGS["opencode"].display_name,
                templates=opencode_templates,
                status=opencode_status,
                global_dir=get_global_commands_dir(),
                local_dir=get_local_commands_dir(),
            )

        # Qwen table
        if qwen_templates:
            _render_editor_table(
                title="Qwen Commands",
                editor_name=EDITOR_CONFIGS["qwen"].display_name,
                templates=qwen_templates,
                status=qwen_status,
                global_dir=get_global_qwen_commands_dir(),
                local_dir=get_local_qwen_commands_dir(),
            )

        # Gemini CLI table
        if gemini_templates:
            _render_editor_table(
                title="Gemini CLI Commands",
                editor_name=EDITOR_CONFIGS["gemini"].display_name,
                templates=gemini_templates,
                status=gemini_status,
                global_dir=get_global_gemini_commands_dir(),
                local_dir=get_local_gemini_commands_dir(),
            )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e
