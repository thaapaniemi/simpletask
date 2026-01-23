"""Design section management subcommands."""

import typer

from simpletask.commands.design.remove import remove_command
from simpletask.commands.design.set import set_command
from simpletask.commands.design.show import show_command

app = typer.Typer(help="Manage design guidance and architectural context")

# Register commands
app.command(name="show")(show_command)
app.command(name="set")(set_command)
app.command(name="remove")(remove_command)
