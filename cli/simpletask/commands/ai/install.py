"""Install OpenCode and Qwen command templates."""

import typer

from simpletask.core.ai_templates import (
    get_global_commands_dir,
    get_global_qwen_commands_dir,
    get_local_commands_dir,
    get_local_qwen_commands_dir,
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
) -> None:
    """Install OpenCode and Qwen command templates.

    By default, installs BOTH OpenCode and Qwen templates globally.
    Use --opencode or --qwen to install only specific editor templates.

    Examples:
        simpletask ai install                 # Install both editors globally
        simpletask ai install --local         # Install both editors locally
        simpletask ai install --opencode      # Install OpenCode only
        simpletask ai install --qwen          # Install Qwen only
        simpletask ai install --opencode --qwen --local  # Both, locally
    """
    # If neither flag is specified, install both
    install_opencode = opencode or (not opencode and not qwen)
    install_qwen = qwen or (not opencode and not qwen)

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

        if any_skipped:
            info("Tip: Use --no-overwrite to preserve existing files")

    except FileNotFoundError as e:
        error(str(e))
    except Exception as e:
        error(f"Unexpected error: {e}")
