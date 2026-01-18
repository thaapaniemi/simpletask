"""Criteria management subcommands."""

import typer
from .add import add_command
from .complete import complete_command
from .remove import remove_command
from .list import list_command

app = typer.Typer(help="Manage acceptance criteria")
app.command(name="add")(add_command)
app.command(name="complete")(complete_command)
app.command(name="remove")(remove_command)
app.command(name="list")(list_command)
