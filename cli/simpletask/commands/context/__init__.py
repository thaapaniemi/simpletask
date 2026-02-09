"""CLI commands for context management."""

import typer

from .remove import remove_command
from .set import set_command
from .show import show_command

app = typer.Typer(help="Manage context key-value pairs")
app.command(name="set")(set_command)
app.command(name="remove")(remove_command)
app.command(name="show")(show_command)

__all__ = ["app"]
