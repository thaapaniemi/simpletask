"""Quality set command."""

from enum import Enum
from typing import Annotated

import typer

from simpletask.core.models import ToolName
from simpletask.core.project import get_task_file_path
from simpletask.core.quality_ops import update_quality_config
from simpletask.core.yaml_parser import parse_task_file, write_task_file
from simpletask.utils.console import console, error


class ConfigType(str, Enum):
    """Valid quality configuration types."""

    LINTING = "linting"
    TYPE_CHECKING = "type-checking"
    TESTING = "testing"
    SECURITY = "security"


def set_command(
    config_type: Annotated[
        ConfigType,
        typer.Argument(
            help="Config type: linting, type-checking, testing, security",
        ),
    ],
    tool: Annotated[
        ToolName | None,
        typer.Option("--tool", "-t", help="Tool to execute (e.g., ruff, mypy, pytest)"),
    ] = None,
    args: Annotated[
        str | None,
        typer.Option(
            "--args", "-a", help="Tool arguments as comma-separated list (e.g., 'check,.,--fix')"
        ),
    ] = None,
    enable: Annotated[bool, typer.Option("--enable", help="Enable this quality check")] = False,
    disable: Annotated[bool, typer.Option("--disable", help="Disable this quality check")] = False,
    min_coverage: Annotated[
        int | None,
        typer.Option(
            "--min-coverage",
            help="Minimum test coverage percentage (0-100, testing only)",
            min=0,
            max=100,
        ),
    ] = None,
    timeout: Annotated[
        int | None,
        typer.Option(
            "--timeout",
            help="Timeout in seconds for this check (default: 300)",
            min=1,
        ),
    ] = None,
    branch: Annotated[
        str | None,
        typer.Option("--branch", "-b", help="Branch name (defaults to current git branch)"),
    ] = None,
) -> None:
    """Set quality requirements configuration.

    Configure individual quality check settings including tools, arguments, enable/disable status,
    coverage thresholds, and timeouts.

    Examples:
        simpletask quality set linting --tool ruff --args "check,."
        simpletask quality set testing --enable --min-coverage 80 --timeout 600
        simpletask quality set type-checking --disable
        simpletask quality set security --enable --tool bandit --args "-r,." --timeout 120
    """
    try:
        # Parse args string into list if provided
        args_list: list[str] | None = None
        if args:
            args_list = [arg.strip() for arg in args.split(",")]

        # Determine enabled status
        enabled_status: bool | None = None
        if enable:
            enabled_status = True
        elif disable:
            enabled_status = False

        # Validate enable/disable conflict
        if enable and disable:
            error("Cannot specify both --enable and --disable")

        # Parse task file
        file_path = get_task_file_path(branch)
        spec = parse_task_file(file_path)

        # Map ConfigType enum to string for quality_ops
        config_type_str = config_type.value  # "linting", "type-checking", "testing", "security"

        # Convert ToolName enum value
        tool_enum = tool  # Already a ToolName enum from Typer

        # Update using shared logic
        try:
            updated_spec = update_quality_config(
                spec,
                config_type_str,  # type: ignore
                tool=tool_enum,
                args=args_list,
                enabled=enabled_status,
                min_coverage=min_coverage,
                timeout=timeout,
            )
        except ValueError as e:
            error(str(e))

        # Write back to file
        write_task_file(file_path, updated_spec)

        # Display confirmation
        console.print(
            f"\n[green]✓[/green] Updated quality configuration for [bold]{config_type.value}[/bold]"
        )

        # Show what was changed
        changes: list[str] = []
        if tool:
            changes.append(f"tool: {tool.value}")
        if args_list:
            changes.append(f"args: {', '.join(args_list)}")
        if enabled_status is not None:
            changes.append(f"enabled: {str(enabled_status).lower()}")
        if min_coverage is not None:
            changes.append(f"min_coverage: {min_coverage}%")
        if timeout is not None:
            changes.append(f"timeout: {timeout}s")

        if changes:
            console.print(f"[dim]Changes: {', '.join(changes)}[/dim]\n")

    except FileNotFoundError as e:
        error(str(e))
    except Exception as e:
        error(f"Unexpected error: {e}")
