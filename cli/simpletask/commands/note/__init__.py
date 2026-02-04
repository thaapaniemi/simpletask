"""CLI commands for note management."""

import typer

from .add import add_command
from .list import list_command
from .remove import remove_command

app = typer.Typer(help="Manage notes in task files")
app.command(name="add")(add_command)
app.command(name="remove")(remove_command)
app.command(name="list")(list_command)

__all__ = ["app"]
