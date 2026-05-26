"""Audit management subcommands."""

# Naming convention note:
# CLI subcommands use terse, user-facing verb names (list, get, dismissed, add-run)
# that are idiomatic for shell usage.
# MCP tool actions use explicit snake_case identifiers (list_runs, get_run,
# get_dismissed, add_run) for unambiguous programmatic use.
# Both interfaces expose the same underlying operations.

import typer

from .add_run import add_run_command
from .dismissed import dismissed_command
from .get import get_command
from .list import list_command

app = typer.Typer(help="Manage code audit history")
app.command(name="list")(list_command)
app.command(name="get")(get_command)
app.command(name="dismissed")(dismissed_command)
app.command(name="add-run")(add_run_command)
