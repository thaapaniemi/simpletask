"""simpletask: A Python CLI for managing AI-friendly task definition YAML files."""

__version__ = "0.17.1"

import typer

# Import top-level commands
# Import subcommand groups
from .commands import ai, criteria, design, new, quality, schema, serve, show, task
from .commands import list as list_cmd


def version_callback(value: bool):
    """Print version and exit."""
    if value:
        typer.echo(f"simpletask version {__version__}")
        raise typer.Exit()


# Create main app
app = typer.Typer(
    name="simpletask",
    help="Manage AI-friendly task definition YAML files in a branch-based workflow",
    no_args_is_help=True,
)


# Add version option
@app.callback()
def main(
    version: bool | None = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
):
    """simpletask: Manage AI-friendly task definition YAML files."""


# Register top-level commands
app.command(name="new")(new.new)
app.command(name="list")(list_cmd.list_tasks)
app.command(name="show")(show.show)
app.command(name="serve")(serve.serve)

# Register subcommand groups
app.add_typer(schema.app, name="schema")
app.add_typer(task.app, name="task")
app.add_typer(criteria.app, name="criteria")
app.add_typer(quality.app, name="quality")
app.add_typer(design.app, name="design")
app.add_typer(ai.app, name="ai")


def main_cli():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main_cli()
