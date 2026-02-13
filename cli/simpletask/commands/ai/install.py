"""Install OpenCode, Qwen, and Gemini CLI command templates and agents."""

import typer

from simpletask.core.ai_templates import (
    get_global_agents_dir,
    get_global_commands_dir,
    get_global_gemini_commands_dir,
    get_global_qwen_commands_dir,
    get_local_agents_dir,
    get_local_commands_dir,
    get_local_gemini_commands_dir,
    get_local_qwen_commands_dir,
    install_agents,
    install_gemini_templates,
    install_qwen_templates,
    install_templates,
)
from simpletask.utils.console import error, info, success, warning


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
) -> None:
    """Install OpenCode, Qwen, and Gemini CLI command templates and agents.

    By default, installs ALL templates (OpenCode, Qwen, and Gemini CLI) globally. OpenCode
    agents are installed alongside OpenCode command templates.
    Use --opencode, --qwen, or --gemini to install only specific editor templates.

    Examples:
        simpletask ai install                 # Install all three editors globally
        simpletask ai install --local         # Install all three editors locally
        simpletask ai install --opencode      # Install OpenCode only
        simpletask ai install --qwen          # Install Qwen only
        simpletask ai install --gemini        # Install Gemini CLI only
        simpletask ai install --opencode --qwen --gemini --local  # All three, locally
    """
    # If no flags specified, install all three
    none_specified = not opencode and not qwen and not gemini
    install_opencode = opencode or none_specified
    install_qwen = qwen or none_specified
    install_gemini = gemini or none_specified

    any_skipped = False

    try:
        # Install OpenCode templates
        if install_opencode:
            target_dir = get_local_commands_dir() if local else get_global_commands_dir()

            info(f"Installing OpenCode commands to {target_dir}")

            installed, skipped, overwritten = install_templates(
                target_dir=target_dir,
                no_overwrite=no_overwrite,
            )

            any_skipped = (
                _report_installation_results(installed, skipped, overwritten) or any_skipped
            )

        # Install Qwen templates
        if install_qwen:
            target_dir = get_local_qwen_commands_dir() if local else get_global_qwen_commands_dir()

            info(f"Installing Qwen commands to {target_dir}")

            installed, skipped, overwritten = install_qwen_templates(
                target_dir=target_dir,
                no_overwrite=no_overwrite,
            )

            any_skipped = (
                _report_installation_results(installed, skipped, overwritten) or any_skipped
            )

        # Install Gemini CLI templates
        if install_gemini:
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
        error(str(e))
    except Exception as e:
        error(f"Unexpected error: {e}")

    # Install OpenCode agents separately with independent error handling
    if install_opencode:
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
