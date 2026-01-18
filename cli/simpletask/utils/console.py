"""Console utility functions using Rich."""

import sys

from rich.console import Console
from rich.table import Table

console = Console()
error_console = Console(stderr=True, style="red")


def error(message: str, exit_code: int = 1) -> None:
    """Print error message to stderr and exit.

    Args:
        message: Error message to display
        exit_code: Exit code (default: 1)
    """
    error_console.print(f"[red]Error:[/red] {message}")
    sys.exit(exit_code)


def success(message: str) -> None:
    """Print success message.

    Args:
        message: Success message to display
    """
    console.print(f"[green]✓[/green] {message}")


def info(message: str) -> None:
    """Print info message.

    Args:
        message: Info message to display
    """
    console.print(f"[blue]ℹ[/blue] {message}")


def warning(message: str) -> None:
    """Print warning message.

    Args:
        message: Warning message to display
    """
    console.print(f"[yellow]⚠[/yellow] {message}")


def confirm(message: str, default: bool = True) -> bool:
    """Ask user for confirmation.

    Args:
        message: Confirmation prompt
        default: Default response if user just presses Enter

    Returns:
        True if user confirmed, False otherwise
    """
    prompt = f"{message} ({'Y/n' if default else 'y/N'}): "
    response = input(prompt).strip().lower()

    if response in ("y", "yes"):
        return True
    elif response in ("n", "no"):
        return False
    else:
        return default


def create_table(title: str, columns: list[str]) -> Table:
    """Create a Rich table with the given title and columns.

    Args:
        title: Table title
        columns: List of column names

    Returns:
        Rich Table object
    """
    table = Table(title=title, show_header=True, header_style="bold magenta")
    for col in columns:
        table.add_column(col)
    return table


# Export public API
__all__ = [
    "console",
    "error_console",
    "error",
    "success",
    "info",
    "warning",
    "confirm",
    "create_table",
]
