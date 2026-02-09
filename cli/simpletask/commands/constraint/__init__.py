"""CLI commands for constraint management."""

import typer

from .add import add_command
from .list import list_command
from .remove import remove_command

app = typer.Typer(help="Manage implementation constraints")
app.command(name="add")(add_command)
app.command(name="remove")(remove_command)
app.command(name="list")(list_command)

__all__ = ["app"]
