"""Task management subcommands."""

import typer
from .add import add_command
from .update import update_command
from .remove import remove_command
from .list import list_command

app = typer.Typer(help="Manage implementation tasks")
app.command(name="add")(add_command)
app.command(name="update")(update_command)
app.command(name="remove")(remove_command)
app.command(name="list")(list_command)
