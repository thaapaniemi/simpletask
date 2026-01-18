"""Install OpenCode command templates."""

import typer

from simpletask.core.ai_templates import (
    get_global_commands_dir,
    get_local_commands_dir,
    install_templates,
)
from simpletask.utils.console import error, info, success, warning


def install_command(
    local: bool = typer.Option(
        False,
        "--local",
        help="Install to .opencode/commands/ (project-local) instead of global",
    ),
    no_overwrite: bool = typer.Option(
        False,
        "--no-overwrite",
        help="Skip existing files instead of overwriting",
    ),
) -> None:
    """Install OpenCode command templates.

    By default, installs to ~/.config/opencode/commands/ (global).
    Use --local to install to .opencode/commands/ (project-local).

    Examples:
        simpletask ai install
        simpletask ai install --local
        simpletask ai install --no-overwrite
    """
    try:
        # Determine target directory
        target_dir = get_local_commands_dir() if local else get_global_commands_dir()

        info(f"Installing OpenCode commands to {target_dir}")

        # Install templates
        installed, skipped, overwritten = install_templates(
            target_dir=target_dir,
            no_overwrite=no_overwrite,
        )

        # Report results
        for name in overwritten:
            warning(f"Overwriting: {name}")

        for name in installed:
            if name not in overwritten:
                success(f"Installed: {name}")

        for name in skipped:
            warning(f"Skipped (already exists): {name}")

        # Summary
        total = len(installed) + len(skipped)
        overwrite_count = len(overwritten)

        if overwrite_count > 0:
            info(f"\nSummary: {total} processed ({overwrite_count} overwritten)")
        else:
            info(f"\nSummary: {total} processed")

        if skipped:
            info("Tip: Use --no-overwrite to skip existing files")

    except FileNotFoundError as e:
        error(str(e))
    except Exception as e:
        error(f"Unexpected error: {e}")
