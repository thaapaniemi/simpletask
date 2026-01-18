"""AI integration subcommands."""

import typer

from .install import install_command
from .list import list_command

app = typer.Typer(help="AI integration commands")
app.command(name="install")(install_command)
app.command(name="update")(install_command)  # Alias for install
app.command(name="list")(list_command)
