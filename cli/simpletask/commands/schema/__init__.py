"""Schema validation subcommands."""

import typer
from .validate import validate

app = typer.Typer(help="Schema validation commands")
app.command(name="validate")(validate)
