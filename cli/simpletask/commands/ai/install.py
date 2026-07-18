"""Install OpenCode, GitHub Copilot, and Pi AI templates."""

import typer

from simpletask.core.ai_templates import (
    EditorType,
    get_global_agents_dir,
    get_global_commands_dir,
    get_global_copilot_commands_dir,
    get_global_pi_commands_dir,
    get_local_agents_dir,
    get_local_commands_dir,
    get_local_copilot_commands_dir,
    get_local_pi_commands_dir,
    install_agents,
    install_copilot_templates,
    install_pi_templates,
    install_templates,
    is_editor_installed,
)
from simpletask.utils.console import error, info, success, warning


def _should_install(
    editor: EditorType,
    display_name: str,
    explicit: bool,
    local: bool,
    install_by_default: bool = False,
) -> bool:
    """Determine whether installation should proceed for an editor."""
    if local or install_by_default:
        return True
    if is_editor_installed(editor):
        return True
    if explicit:
        return typer.confirm(
            f"{display_name} config directory not found. Install anyway?",
            default=False,
        )
    info(f"{display_name} not detected — skipping")
    return False


def _report_installation_results(
    installed: list[str],
    skipped: list[str],
    overwritten: list[str],
) -> bool:
    """Report installation results and return whether anything was skipped."""
    for name in overwritten:
        warning(f"  Overwriting: {name}")
    for name in installed:
        success(f"  Installed: {name}")
    for name in skipped:
        warning(f"  Skipped (already exists): {name}")

    total = len(installed) + len(skipped) + len(overwritten)
    if overwritten:
        info(f"  Summary: {total} processed ({len(overwritten)} overwritten)\n")
    else:
        info(f"  Summary: {total} processed\n")
    return bool(skipped)


def install_command(
    local: bool = typer.Option(
        False,
        "--local",
        help="Install to project-local directories instead of global",
    ),
    no_overwrite: bool = typer.Option(
        False,
        "--no-overwrite",
        help="Skip existing files instead of overwriting",
    ),
    opencode: bool = typer.Option(
        False,
        "--opencode",
        help="Install OpenCode templates only",
    ),
    copilot: bool = typer.Option(
        False,
        "--copilot",
        help="Install GitHub Copilot prompts only",
    ),
    pi: bool = typer.Option(
        False,
        "--pi",
        help="Install Pi prompts only",
    ),
) -> None:
    """Install OpenCode, GitHub Copilot, and Pi AI templates.

    By default, installs all three supported integrations globally. Use an editor flag
    to install only that integration. OpenCode agents are installed with its commands.

    Examples:
        simpletask ai install                 # Install supported integrations globally
        simpletask ai install --local         # Install supported integrations locally
        simpletask ai install --opencode      # Install OpenCode only
        simpletask ai install --copilot       # Install GitHub Copilot only
        simpletask ai install --pi            # Install Pi only
    """
    none_specified = not opencode and not copilot and not pi
    install_opencode = opencode or none_specified
    install_copilot = copilot or none_specified
    install_pi = pi or none_specified

    any_skipped = False
    opencode_installed = False

    if install_opencode and _should_install(
        "opencode", "OpenCode", opencode, local, none_specified
    ):
        try:
            target_dir = get_local_commands_dir() if local else get_global_commands_dir()
            info(f"Installing OpenCode commands to {target_dir}")
            result = install_templates(target_dir=target_dir, no_overwrite=no_overwrite)
            any_skipped = _report_installation_results(*result) or any_skipped
            opencode_installed = True
        except FileNotFoundError as error_value:
            warning(f"Skipping OpenCode installation: {error_value}")
        except Exception as error_value:
            error(f"Unexpected error installing OpenCode: {error_value}")

    if install_copilot and _should_install(
        "copilot", "GitHub Copilot", copilot, local, none_specified
    ):
        try:
            target_dir = (
                get_local_copilot_commands_dir() if local else get_global_copilot_commands_dir()
            )
            info(f"Installing GitHub Copilot prompts to {target_dir}")
            result = install_copilot_templates(target_dir=target_dir, no_overwrite=no_overwrite)
            any_skipped = _report_installation_results(*result) or any_skipped
        except FileNotFoundError as error_value:
            warning(f"Skipping GitHub Copilot installation: {error_value}")
        except Exception as error_value:
            error(f"Unexpected error installing GitHub Copilot: {error_value}")

    if install_pi and _should_install("pi", "Pi", pi, local, none_specified):
        try:
            target_dir = get_local_pi_commands_dir() if local else get_global_pi_commands_dir()
            info(f"Installing Pi prompts to {target_dir}")
            result = install_pi_templates(target_dir=target_dir, no_overwrite=no_overwrite)
            any_skipped = _report_installation_results(*result) or any_skipped
        except FileNotFoundError as error_value:
            warning(f"Skipping Pi installation: {error_value}")
        except Exception as error_value:
            error(f"Unexpected error installing Pi: {error_value}")

    if install_opencode and opencode_installed:
        try:
            agents_dir = get_local_agents_dir() if local else get_global_agents_dir()
            info(f"Installing OpenCode agents to {agents_dir}")
            result = install_agents(target_dir=agents_dir, no_overwrite=no_overwrite)
            any_skipped = _report_installation_results(*result) or any_skipped
        except FileNotFoundError as error_value:
            warning(f"Skipping agents installation: {error_value}")
        except Exception as error_value:
            warning(f"Warning installing agents: {error_value}")

    if any_skipped:
        info("Tip: Use --no-overwrite to preserve existing files")
