"""Iteration management subcommands."""

import typer

from .add import add_command
from .get import get_command
from .list import list_command
from .remove import remove_command

app = typer.Typer(help="Manage task iterations")
app.command(name="add")(add_command)
app.command(name="get")(get_command)
app.command(name="list")(list_command)
app.command(name="remove")(remove_command)
