"""Install OpenCode, Qwen, Gemini, and Vibe CLI command templates and agents."""

import typer

from simpletask.core.ai_templates import (
    EditorType,
    get_global_agents_dir,
    get_global_commands_dir,
    get_global_gemini_commands_dir,
    get_global_qwen_commands_dir,
    get_global_vibe_commands_dir,
    get_local_agents_dir,
    get_local_commands_dir,
    get_local_gemini_commands_dir,
    get_local_qwen_commands_dir,
    get_local_vibe_commands_dir,
    install_agents,
    install_gemini_templates,
    install_qwen_templates,
    install_templates,
    install_vibe_templates,
    is_editor_installed,
)
from simpletask.utils.console import error, info, success, warning


def _should_install(editor: EditorType, display_name: str, explicit: bool, local: bool) -> bool:
    """Determine whether to install templates for an editor.

    Truth table for global installs:
    - local=True  → always install (bypass detection)
    - editor detected (base dir exists) → install
    - editor not detected, explicit flag → prompt user
    - editor not detected, implicit (all-editors default) → skip with info message

    Args:
        editor: Editor type identifier.
        display_name: Human-readable editor name for messages.
        explicit: True if the user passed this editor's flag explicitly.
        local: True if --local flag was used (bypasses detection).

    Returns:
        True if installation should proceed, False otherwise.
    """
    if local:
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
    """Report installation results with colored output.

    Args:
        installed: List of installed template names.
        skipped: List of skipped template names.
        overwritten: List of overwritten template names.

    Returns:
        True if any templates were skipped (useful for showing tip message).
    """
    # Report results
    for name in overwritten:
        warning(f"  Overwriting: {name}")

    for name in installed:
        success(f"  Installed: {name}")

    for name in skipped:
        warning(f"  Skipped (already exists): {name}")

    # Summary
    total = len(installed) + len(skipped) + len(overwritten)
    overwrite_count = len(overwritten)

    if overwrite_count > 0:
        info(f"  Summary: {total} processed ({overwrite_count} overwritten)\n")
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
    qwen: bool = typer.Option(
        False,
        "--qwen",
        help="Install Qwen templates only",
    ),
    gemini: bool = typer.Option(
        False,
        "--gemini",
        help="Install Gemini CLI templates only",
    ),
    vibe: bool = typer.Option(
        False,
        "--vibe",
        help="Install Mistral Vibe skills only",
    ),
) -> None:
    """Install OpenCode, Qwen, Gemini, and Vibe CLI command templates and agents.

    By default, installs ALL templates (OpenCode, Qwen, Gemini CLI, and Vibe) globally. OpenCode
    agents are installed alongside OpenCode command templates.
    Use --opencode, --qwen, --gemini, or --vibe to install only specific editor templates.

    Examples:
        simpletask ai install                 # Install all four editors globally
        simpletask ai install --local         # Install all four editors locally
        simpletask ai install --opencode      # Install OpenCode only
        simpletask ai install --qwen          # Install Qwen only
        simpletask ai install --gemini        # Install Gemini CLI only
        simpletask ai install --vibe          # Install Mistral Vibe only
        simpletask ai install --opencode --qwen --gemini --vibe --local  # All four, locally
    """
    # If no flags specified, install all four (implicit mode)
    none_specified = not opencode and not qwen and not gemini and not vibe
    install_opencode = opencode or none_specified
    install_qwen = qwen or none_specified
    install_gemini = gemini or none_specified
    install_vibe = vibe or none_specified

    # Track whether each editor was explicitly requested by the user
    opencode_explicit = bool(opencode)
    qwen_explicit = bool(qwen)
    gemini_explicit = bool(gemini)
    vibe_explicit = bool(vibe)

    any_skipped = False
    opencode_installed = False

    # Install OpenCode templates
    if install_opencode and _should_install("opencode", "OpenCode", opencode_explicit, local):
        try:
            target_dir = get_local_commands_dir() if local else get_global_commands_dir()

            info(f"Installing OpenCode commands to {target_dir}")

            installed, skipped, overwritten = install_templates(
                target_dir=target_dir,
                no_overwrite=no_overwrite,
            )

            any_skipped = (
                _report_installation_results(installed, skipped, overwritten) or any_skipped
            )
            opencode_installed = True
        except FileNotFoundError as e:
            warning(f"Skipping OpenCode installation: {e}")
        except Exception as e:
            error(f"Unexpected error installing OpenCode: {e}")

    # Install Qwen templates
    if install_qwen and _should_install("qwen", "Qwen", qwen_explicit, local):
        try:
            target_dir = get_local_qwen_commands_dir() if local else get_global_qwen_commands_dir()

            info(f"Installing Qwen commands to {target_dir}")

            installed, skipped, overwritten = install_qwen_templates(
                target_dir=target_dir,
                no_overwrite=no_overwrite,
            )

            any_skipped = (
                _report_installation_results(installed, skipped, overwritten) or any_skipped
            )
        except FileNotFoundError as e:
            warning(f"Skipping Qwen installation: {e}")
        except Exception as e:
            error(f"Unexpected error installing Qwen: {e}")

    # Install Gemini CLI templates
    if install_gemini and _should_install("gemini", "Gemini CLI", gemini_explicit, local):
        try:
            target_dir = (
                get_local_gemini_commands_dir() if local else get_global_gemini_commands_dir()
            )

            info(f"Installing Gemini CLI commands to {target_dir}")

            installed, skipped, overwritten = install_gemini_templates(
                target_dir=target_dir,
                no_overwrite=no_overwrite,
            )

            any_skipped = (
                _report_installation_results(installed, skipped, overwritten) or any_skipped
            )
        except FileNotFoundError as e:
            warning(f"Skipping Gemini installation: {e}")
        except Exception as e:
            error(f"Unexpected error installing Gemini: {e}")

    # Install Vibe skills
    if install_vibe and _should_install("vibe", "Mistral Vibe", vibe_explicit, local):
        try:
            target_dir = get_local_vibe_commands_dir() if local else get_global_vibe_commands_dir()

            info(f"Installing Mistral Vibe skills to {target_dir}")

            installed, skipped, overwritten = install_vibe_templates(
                target_dir=target_dir,
                no_overwrite=no_overwrite,
            )

            any_skipped = (
                _report_installation_results(installed, skipped, overwritten) or any_skipped
            )
        except FileNotFoundError as e:
            warning(f"Skipping Vibe installation: {e}")
        except Exception as e:
            error(f"Unexpected error installing Vibe: {e}")

    # Install OpenCode agents alongside OpenCode commands
    if install_opencode and opencode_installed:
        try:
            agents_dir = get_local_agents_dir() if local else get_global_agents_dir()

            info(f"Installing OpenCode agents to {agents_dir}")

            installed, skipped, overwritten = install_agents(
                target_dir=agents_dir,
                no_overwrite=no_overwrite,
            )

            any_skipped = (
                _report_installation_results(installed, skipped, overwritten) or any_skipped
            )

        except FileNotFoundError as e:
            warning(f"Skipping agents installation: {e}")
        except Exception as e:
            warning(f"Warning installing agents: {e}")

    if any_skipped:
        info("Tip: Use --no-overwrite to preserve existing files")
