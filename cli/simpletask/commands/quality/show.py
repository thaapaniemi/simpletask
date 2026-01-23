"""Quality show command."""

from typing import Annotated

import typer
from rich.table import Table

from simpletask.core.models import ToolName
from simpletask.core.project import get_task_file_path
from simpletask.core.yaml_parser import parse_task_file
from simpletask.utils.console import console, error


def _format_tool_command(tool: ToolName | None, args: list[str]) -> str:
    """Format tool and args into a human-readable command string."""
    if tool is None:
        return ""

    if not args:
        return tool.value

    return f"{tool.value} {' '.join(args)}"


def show_command(
    branch: Annotated[
        str | None,
        typer.Option("--branch", "-b", help="Branch name (defaults to current git branch)"),
    ] = None,
) -> None:
    """Show current quality requirements configuration.

    Displays all quality check configurations including enabled status,
    commands, and coverage thresholds.

    Examples:
        simpletask quality show
        simpletask quality show --branch feature-123
    """
    try:
        # Get file path
        file_path = get_task_file_path(branch)

        # Parse task file
        spec = parse_task_file(file_path)

        # Get quality requirements
        quality_reqs = spec.quality_requirements

        if quality_reqs is None:
            error("No quality requirements configured in task file")
            raise typer.Exit(1)

        console.print(f"\n[bold]Quality Requirements[/bold] ({file_path.name})\n")

        # Create table
        table = Table(show_header=True, header_style="bold")
        table.add_column("Check Type", style="cyan")
        table.add_column("Enabled", justify="center")
        table.add_column("Command", style="dim")
        table.add_column("Options")

        # Add linting row
        enabled_icon = "[green]✓[/green]" if quality_reqs.linting.enabled else "[red]✗[/red]"
        table.add_row(
            "Linting",
            enabled_icon,
            _format_tool_command(quality_reqs.linting.tool, quality_reqs.linting.args),
            "",
        )

        # Add type checking row
        if quality_reqs.type_checking:
            enabled_icon = (
                "[green]✓[/green]" if quality_reqs.type_checking.enabled else "[red]✗[/red]"
            )
            table.add_row(
                "Type Checking",
                enabled_icon,
                _format_tool_command(
                    quality_reqs.type_checking.tool, quality_reqs.type_checking.args
                ),
                "",
            )
        else:
            table.add_row("Type Checking", "[dim]not configured[/dim]", "", "")

        # Add testing row
        enabled_icon = "[green]✓[/green]" if quality_reqs.testing.enabled else "[red]✗[/red]"
        options = ""
        if quality_reqs.testing.min_coverage is not None:
            options = f"min_coverage: {quality_reqs.testing.min_coverage}%"
        table.add_row(
            "Testing",
            enabled_icon,
            _format_tool_command(quality_reqs.testing.tool, quality_reqs.testing.args),
            options,
        )

        # Add security check row
        if quality_reqs.security_check:
            enabled_icon = (
                "[green]✓[/green]" if quality_reqs.security_check.enabled else "[red]✗[/red]"
            )
            cmd = _format_tool_command(
                quality_reqs.security_check.tool, quality_reqs.security_check.args
            )
            table.add_row(
                "Security Check",
                enabled_icon,
                cmd,
                "",
            )
        else:
            table.add_row("Security Check", "[dim]not configured[/dim]", "", "")

        console.print(table)
        console.print("")

    except FileNotFoundError as e:
        error(str(e))
    except Exception as e:
        error(f"Unexpected error: {e}")
