"""Design show command."""

from typing import Annotated

import typer
from rich.panel import Panel
from rich.text import Text

from simpletask.core.project import get_task_file_path
from simpletask.core.yaml_parser import parse_task_file
from simpletask.utils.console import console, error


def show_command(
    branch: Annotated[
        str | None,
        typer.Option("--branch", "-b", help="Branch name (defaults to current git branch)"),
    ] = None,
) -> None:
    """Show design guidance and architectural context.

    Displays patterns to follow, reference implementations, architectural
    constraints, security considerations, and error handling patterns.

    Examples:
        simpletask design show
        simpletask design show --branch feature-123
    """
    try:
        # Get file path
        file_path = get_task_file_path(branch)

        # Parse task file
        spec = parse_task_file(file_path)

        # Check if design section exists
        if not spec.design:
            console.print(f"\n[yellow]No design section found in {file_path.name}[/yellow]")
            console.print("\nUse [cyan]simpletask design set[/cyan] to add design guidance.\n")
            return

        design = spec.design

        console.print(f"\n[bold]Design Guidance[/bold] ({file_path.name})\n")

        # Architectural patterns
        if design.patterns:
            text = Text()
            for pattern in design.patterns:
                text.append(f"• {pattern.value}\n")
            console.print(
                Panel(text, title="[cyan]Architectural Patterns[/cyan]", border_style="cyan")
            )

        # Reference implementations
        if design.reference_implementations:
            text = Text()
            for ref in design.reference_implementations:
                text.append("• ", style="bold")
                text.append(f"{ref.path}\n", style="cyan")
                text.append(f"  {ref.reason}\n\n")
            console.print(
                Panel(
                    text,
                    title="[cyan]Reference Implementations[/cyan]",
                    border_style="cyan",
                )
            )

        # Architectural constraints
        if design.architectural_constraints:
            text = Text()
            for constraint in design.architectural_constraints:
                text.append(f"• {constraint}\n")
            console.print(
                Panel(
                    text,
                    title="[cyan]Architectural Constraints[/cyan]",
                    border_style="cyan",
                )
            )

        # Security requirements
        if design.security:
            text = Text()
            for req in design.security:
                text.append("• ", style="bold")
                text.append(f"{req.category.value}: ", style="yellow")
                text.append(f"{req.description}\n")
            console.print(
                Panel(
                    text,
                    title="[yellow]Security Requirements[/yellow]",
                    border_style="yellow",
                )
            )

        # Error handling strategy
        if design.error_handling:
            console.print(
                Panel(
                    design.error_handling.value,
                    title="[cyan]Error Handling Strategy[/cyan]",
                    border_style="cyan",
                )
            )

        # If all fields are empty
        if not any(
            [
                design.patterns,
                design.reference_implementations,
                design.architectural_constraints,
                design.security,
                design.error_handling,
            ]
        ):
            console.print("[dim]Design section exists but all fields are empty.[/dim]\n")

        console.print("")

    except FileNotFoundError as e:
        error(str(e))
    except Exception as e:
        error(f"Unexpected error: {e}")
