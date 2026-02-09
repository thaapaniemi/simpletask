"""List constraints command."""

from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.mcp.server import constraint
from simpletask.utils.console import console, handle_exception


def list_command() -> None:
    """List all implementation constraints.

    Examples:
        simpletask constraint list
    """
    try:
        # Call MCP tool directly
        result = constraint(action="list")

        # Display constraints
        if not result.constraints:
            console.print("[dim]No constraints defined[/dim]")
            return

        console.print(f"\n[bold]Constraints[/bold] (Total: {len(result.constraints)})\n")

        for idx, constraint_desc in enumerate(result.constraints):
            console.print(f"  [{idx}] {constraint_desc}")
        console.print()

    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        handle_exception(e, "listing constraints")
