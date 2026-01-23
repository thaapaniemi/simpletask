"""Quality management subcommands."""

import typer

from .check import check_command
from .preset import preset_command
from .set import set_command
from .show import show_command

app = typer.Typer(help="Manage quality requirements and run quality checks")

# Register commands
app.command(name="check")(check_command)
app.command(name="set")(set_command)
app.command(name="show")(show_command)
app.command(name="preset")(preset_command)
