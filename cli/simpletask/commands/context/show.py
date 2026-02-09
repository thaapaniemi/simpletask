"""Show context command."""

from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.mcp.server import context
from simpletask.utils.console import console, handle_exception


def show_command() -> None:
    """Show all context key-value pairs.

    Examples:
        simpletask context show
    """
    try:
        # Call MCP tool directly
        result = context(action="show")

        # Display context
        if not result.context:
            console.print("[dim]No context defined[/dim]")
            return

        console.print(f"\n[bold]Context[/bold] (Total: {len(result.context)} keys)\n")

        for key, value in sorted(result.context.items()):
            console.print(f"  [cyan]{key}:[/cyan] {value}")
        console.print()

    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        handle_exception(e, "showing context")
