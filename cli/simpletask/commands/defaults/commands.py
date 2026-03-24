"""Defaults subcommand group — manage project-level defaults in .tasks/defaults.yml."""

from enum import Enum
from typing import Annotated

import typer
from rich.panel import Panel
from rich.text import Text

from simpletask.core.defaults import (
    DEFAULTS_FILENAME,
    get_defaults_path,
    load_defaults,
    save_defaults,
)
from simpletask.core.models import (
    ArchitecturalPattern,
    Design,
    DesignReference,
    ErrorHandlingStrategy,
    ProjectDefaults,
    SecurityCategory,
    SecurityRequirement,
    ToolName,
)
from simpletask.core.presets import (
    QUALITY_PRESETS,
    load_all_presets,
)
from simpletask.core.project import ensure_project
from simpletask.core.quality_ops import apply_quality_preset, update_quality_requirements
from simpletask.utils.console import console, error, success

# ---------------------------------------------------------------------------
# App definitions (nested Typers)
# ---------------------------------------------------------------------------

app = typer.Typer(help="Manage project-level defaults injected into new task files")
design_app = typer.Typer(help="Manage design defaults")
quality_app = typer.Typer(help="Manage quality defaults")
constraint_app = typer.Typer(help="Manage constraint defaults")
context_app = typer.Typer(help="Manage context defaults")

app.add_typer(design_app, name="design")
app.add_typer(quality_app, name="quality")
app.add_typer(constraint_app, name="constraint")
app.add_typer(context_app, name="context")


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _load_or_empty(project) -> ProjectDefaults:  # type: ignore[no-untyped-def]
    """Load defaults file or return a fresh empty ProjectDefaults."""
    defaults = load_defaults(project)
    return defaults if defaults is not None else ProjectDefaults()


# ---------------------------------------------------------------------------
# simpletask defaults show
# ---------------------------------------------------------------------------


@app.command(name="show")
def show_command() -> None:
    """Show current project-level defaults from .tasks/defaults.yml.

    Examples:
        simpletask defaults show
    """
    try:
        project = ensure_project()
        defaults = load_defaults(project)

        defaults_path = get_defaults_path(project)

        if defaults is None:
            console.print(
                f"\n[yellow]No project defaults configured.[/yellow]"
                f"\n[dim]File not found: {defaults_path}[/dim]\n"
            )
            console.print(
                "Use [cyan]simpletask defaults design set[/cyan], "
                "[cyan]simpletask defaults quality set[/cyan], "
                "[cyan]simpletask defaults constraint add[/cyan], or "
                "[cyan]simpletask defaults context set[/cyan] to add defaults.\n"
            )
            return

        console.print(f"\n[bold]Project Defaults[/bold] ({defaults_path.name})\n")

        any_content = False

        # ---- Design ----
        if defaults.design:
            any_content = True
            d = defaults.design

            if d.patterns:
                text = Text()
                for p in d.patterns:
                    text.append(f"• {p.value}\n")
                console.print(
                    Panel(text, title="[cyan]Design › Patterns[/cyan]", border_style="cyan")
                )

            if d.reference_implementations:
                text = Text()
                for ref in d.reference_implementations:
                    text.append("• ", style="bold")
                    text.append(f"{ref.path}\n", style="cyan")
                    text.append(f"  {ref.reason}\n\n")
                console.print(
                    Panel(
                        text,
                        title="[cyan]Design › References[/cyan]",
                        border_style="cyan",
                    )
                )

            if d.architectural_constraints:
                text = Text()
                for c in d.architectural_constraints:
                    text.append(f"• {c}\n")
                console.print(
                    Panel(
                        text,
                        title="[cyan]Design › Constraints[/cyan]",
                        border_style="cyan",
                    )
                )

            if d.security:
                text = Text()
                for req in d.security:
                    text.append("• ", style="bold")
                    text.append(f"{req.category.value}: ", style="yellow")
                    text.append(f"{req.description}\n")
                console.print(
                    Panel(
                        text,
                        title="[yellow]Design › Security[/yellow]",
                        border_style="yellow",
                    )
                )

            if d.error_handling:
                console.print(
                    Panel(
                        d.error_handling.value,
                        title="[cyan]Design › Error Handling[/cyan]",
                        border_style="cyan",
                    )
                )

        # ---- Quality ----
        if defaults.quality_requirements:
            any_content = True
            q = defaults.quality_requirements
            text = Text()
            for cfg_name, cfg in [
                ("linting", q.linting),
                ("type_checking", q.type_checking),
                ("testing", q.testing),
                ("security_check", q.security_check),
            ]:
                if cfg is not None:
                    status = "[green]enabled[/green]" if cfg.enabled else "[dim]disabled[/dim]"
                    tool_str = cfg.tool.value if cfg.tool else "(none)"
                    text.append(f"• {cfg_name}: {tool_str} — ")
                    text.append_text(Text.from_markup(status))
                    text.append("\n")
            console.print(
                Panel(text, title="[cyan]Quality Requirements[/cyan]", border_style="cyan")
            )

        # ---- Constraints ----
        if defaults.constraints:
            any_content = True
            text = Text()
            for c in defaults.constraints:
                text.append(f"• {c}\n")
            console.print(Panel(text, title="[cyan]Constraints[/cyan]", border_style="cyan"))

        # ---- Context ----
        if defaults.context:
            any_content = True
            text = Text()
            for k, v in sorted(defaults.context.items()):
                text.append("• ", style="bold")
                text.append(f"{k}: ", style="cyan")
                text.append(f"{v}\n")
            console.print(Panel(text, title="[cyan]Context[/cyan]", border_style="cyan"))

        if not any_content:
            console.print("[dim]defaults.yml exists but all sections are empty.[/dim]")

        console.print("")

    except (ValueError, FileNotFoundError) as e:
        error(str(e))
    except Exception as e:
        error(f"Unexpected error: {e}")


# ---------------------------------------------------------------------------
# simpletask defaults clear
# ---------------------------------------------------------------------------

_VALID_CLEAR_FIELDS = ("design", "quality", "constraints", "context")


@app.command(name="clear")
def clear_command(
    field: Annotated[
        str | None,
        typer.Option(
            "--field",
            "-f",
            help="Specific section to clear: design, quality, constraints, context. "
            "Omit to delete the entire defaults file.",
        ),
    ] = None,
) -> None:
    """Clear project defaults — entire file or a specific section.

    Examples:
        simpletask defaults clear
        simpletask defaults clear --field design
        simpletask defaults clear --field quality
        simpletask defaults clear --field constraints
        simpletask defaults clear --field context
    """
    try:
        project = ensure_project()
        defaults_path = get_defaults_path(project)

        if field is None:
            # Delete the entire file
            if not defaults_path.exists():
                console.print("[dim]No defaults file to remove.[/dim]\n")
                return
            defaults_path.unlink()
            success(f"Removed {defaults_path.name}")
            return

        # Validate field name
        if field not in _VALID_CLEAR_FIELDS:
            valid = ", ".join(_VALID_CLEAR_FIELDS)
            error(f"Invalid field '{field}'. Valid fields: {valid}")

        defaults = _load_or_empty(project)

        if field == "design":
            defaults.design = None
        elif field == "quality":
            defaults.quality_requirements = None
        elif field == "constraints":
            defaults.constraints = None
        elif field == "context":
            defaults.context = None

        save_defaults(project, defaults)
        success(f"Cleared defaults section: {field}")

    except (ValueError, FileNotFoundError) as e:
        error(str(e))
    except Exception as e:
        error(f"Unexpected error: {e}")


# ---------------------------------------------------------------------------
# simpletask defaults design set
# ---------------------------------------------------------------------------


@design_app.command(name="set")
def design_set_command(
    field: Annotated[
        str,
        typer.Argument(
            help="Field to set: pattern, reference, constraint, security, error-handling"
        ),
    ],
    value: Annotated[
        str,
        typer.Argument(help="Value to set"),
    ],
    reference_reason: Annotated[
        str | None,
        typer.Option("--reason", "-r", help="Reason for reference (required when field=reference)"),
    ] = None,
    security_category: Annotated[
        str | None,
        typer.Option(
            "--category",
            "-c",
            help="Security category (required when field=security)",
        ),
    ] = None,
) -> None:
    """Set a design field in project defaults.

    Examples:
        simpletask defaults design set pattern repository
        simpletask defaults design set constraint "Use Pydantic models with extra='forbid'"
        simpletask defaults design set reference src/module.py --reason "Follow this pattern"
        simpletask defaults design set security "Validate inputs" --category input_validation
        simpletask defaults design set error-handling exceptions
    """
    try:
        project = ensure_project()
        defaults = _load_or_empty(project)

        # Initialise design section if absent
        if defaults.design is None:
            defaults.design = Design(
                patterns=None,
                reference_implementations=None,
                architectural_constraints=None,
                security=None,
                error_handling=None,
            )

        d = defaults.design

        if field == "pattern":
            try:
                pattern = ArchitecturalPattern(value)
            except ValueError:
                valid = ", ".join(p.value for p in ArchitecturalPattern)
                error(f"Invalid pattern '{value}'. Valid: {valid}")
            if not d.patterns:
                d.patterns = []
            d.patterns.append(pattern)
            console.print(f"[green]✓[/green] Added pattern: {pattern.value}")

        elif field == "reference":
            if not reference_reason:
                error("--reason is required when adding a reference implementation")
            if not d.reference_implementations:
                d.reference_implementations = []
            ref = DesignReference(path=value, reason=reference_reason)  # type: ignore[arg-type]
            d.reference_implementations.append(ref)
            console.print(f"[green]✓[/green] Added reference: {value}")

        elif field == "constraint":
            if not d.architectural_constraints:
                d.architectural_constraints = []
            d.architectural_constraints.append(value)
            console.print("[green]✓[/green] Added design constraint")

        elif field == "security":
            if not security_category:
                error("--category is required when adding a security requirement")
            try:
                category = SecurityCategory(security_category)
            except ValueError:
                valid = ", ".join(c.value for c in SecurityCategory)
                error(f"Invalid category '{security_category}'. Valid: {valid}")
            if not d.security:
                d.security = []
            req = SecurityRequirement(category=category, description=value)  # type: ignore[arg-type]
            d.security.append(req)
            console.print(f"[green]✓[/green] Added security requirement: {category.value}")  # type: ignore[union-attr]

        elif field == "error-handling":
            try:
                strategy = ErrorHandlingStrategy(value)
            except ValueError:
                valid = ", ".join(s.value for s in ErrorHandlingStrategy)
                error(f"Invalid strategy '{value}'. Valid: {valid}")
            d.error_handling = strategy  # type: ignore[assignment]
            console.print(f"[green]✓[/green] Set error handling strategy: {strategy.value}")  # type: ignore[union-attr]

        else:
            error(
                f"Invalid field '{field}'. "
                "Use: pattern, reference, constraint, security, error-handling"
            )

        save_defaults(project, defaults)
        console.print(f"[dim]Saved to {DEFAULTS_FILENAME}[/dim]\n")

    except (ValueError, FileNotFoundError) as e:
        error(str(e))
    except typer.Exit:
        raise
    except Exception as e:
        error(f"Unexpected error: {e}")


# ---------------------------------------------------------------------------
# simpletask defaults quality set / preset
# ---------------------------------------------------------------------------


class ConfigType(str, Enum):
    """Valid quality configuration types."""

    LINTING = "linting"
    TYPE_CHECKING = "type-checking"
    TESTING = "testing"
    SECURITY = "security"


@quality_app.command(name="set")
def quality_set_command(
    config_type: Annotated[
        ConfigType,
        typer.Argument(help="Config type: linting, type-checking, testing, security"),
    ],
    tool: Annotated[
        ToolName | None,
        typer.Option("--tool", "-t", help="Tool to execute (e.g., ruff, mypy, pytest)"),
    ] = None,
    args: Annotated[
        str | None,
        typer.Option(
            "--args", "-a", help="Tool arguments as comma-separated list (e.g., 'check,.,--fix')"
        ),
    ] = None,
    enable: Annotated[bool, typer.Option("--enable", help="Enable this quality check")] = False,
    disable: Annotated[bool, typer.Option("--disable", help="Disable this quality check")] = False,
    min_coverage: Annotated[
        int | None,
        typer.Option(
            "--min-coverage",
            help="Minimum test coverage percentage (0-100, testing only)",
            min=0,
            max=100,
        ),
    ] = None,
    timeout: Annotated[
        int | None,
        typer.Option("--timeout", help="Timeout in seconds (default: 300)", min=1),
    ] = None,
) -> None:
    """Set a quality configuration in project defaults.

    Examples:
        simpletask defaults quality set linting --tool ruff --args "check,."
        simpletask defaults quality set testing --tool pytest --min-coverage 80
        simpletask defaults quality set type-checking --tool mypy --enable
    """
    try:
        if enable and disable:
            error("Cannot specify both --enable and --disable")

        project = ensure_project()
        defaults = _load_or_empty(project)

        # update_quality_requirements operates directly on QualityRequirements.

        args_list: list[str] | None = None
        if args:
            args_list = [a.strip() for a in args.split(",")]

        enabled_status: bool | None = None
        if enable:
            enabled_status = True
        elif disable:
            enabled_status = False

        # config_type may be a ConfigType enum or a plain string (when called directly in tests)
        config_type_str = config_type.value if hasattr(config_type, "value") else str(config_type)

        updated_reqs = update_quality_requirements(
            defaults.quality_requirements,
            config_type_str,  # type: ignore[arg-type]
            tool=tool,
            args=args_list,
            enabled=enabled_status,
            min_coverage=min_coverage,
            timeout=timeout,
        )
        defaults.quality_requirements = updated_reqs
        save_defaults(project, defaults)

        console.print(
            f"\n[green]✓[/green] Updated quality defaults for [bold]{config_type_str}[/bold]"
        )

        changes: list[str] = []
        if tool:
            changes.append(f"tool: {tool.value}")
        if args_list:
            changes.append(f"args: {', '.join(args_list)}")
        if enabled_status is not None:
            changes.append(f"enabled: {str(enabled_status).lower()}")
        if min_coverage is not None:
            changes.append(f"min_coverage: {min_coverage}%")
        if timeout is not None:
            changes.append(f"timeout: {timeout}s")
        if changes:
            console.print(f"[dim]Changes: {', '.join(changes)}[/dim]\n")

    except (ValueError, FileNotFoundError) as e:
        error(str(e))
    except Exception as e:
        error(f"Unexpected error: {e}")


@quality_app.command(name="preset")
def quality_preset_command(
    preset_name: Annotated[
        str | None,
        typer.Argument(help="Preset name (python, typescript, node, …). Use --list to see all."),
    ] = None,
    list_flag: Annotated[bool, typer.Option("--list", "-l", help="List available presets")] = False,
) -> None:
    """Apply a quality preset to project defaults.

    Uses fill-gaps-only strategy: only sets values not already configured.

    Examples:
        simpletask defaults quality preset --list
        simpletask defaults quality preset python
    """
    try:
        if list_flag:
            all_presets = load_all_presets()
            builtin_names = set(QUALITY_PRESETS.keys())
            custom_names = set(all_presets.keys()) - builtin_names

            console.print("\n[bold]Available Quality Presets:[/bold]\n")

            if builtin_names:
                console.print("[bold cyan]Built-in Presets:[/bold cyan]")
                for preset in sorted(builtin_names):
                    console.print(f"  • [cyan]{preset}[/cyan]")
                console.print()

            if custom_names:
                console.print("[bold green]Custom Presets:[/bold green]")
                for preset in sorted(custom_names):
                    console.print(f"  • [green]{preset}[/green]")
                console.print()

            console.print("[dim]Use 'simpletask defaults quality preset <name>' to apply[/dim]\n")
            return

        if not preset_name:
            error("Preset name required. Use --list to see available presets.")

        project = ensure_project()
        defaults = _load_or_empty(project)

        merged_reqs, applied = apply_quality_preset(defaults.quality_requirements, preset_name)  # type: ignore[arg-type]
        defaults.quality_requirements = merged_reqs
        save_defaults(project, defaults)

        console.print(f"\n[green]✓[/green] Applied [bold]{preset_name}[/bold] preset to defaults")

        applied_items = [k for k, v in applied.items() if v]
        kept_items = [k for k, v in applied.items() if not v]

        if applied_items:
            console.print("[green]Applied from preset:[/green]")
            for item in applied_items:
                console.print(f"  • {item}")

        if kept_items:
            console.print("[yellow]Kept existing configuration:[/yellow]")
            for item in kept_items:
                console.print(f"  • {item}")

        console.print("\n[dim]Use 'simpletask defaults show' to view current defaults[/dim]\n")

    except (ValueError, FileNotFoundError) as e:
        error(str(e))
    except Exception as e:
        error(f"Unexpected error: {e}")


# ---------------------------------------------------------------------------
# simpletask defaults constraint add
# ---------------------------------------------------------------------------


@constraint_app.command(name="add")
def constraint_add_command(
    value: Annotated[str, typer.Argument(help="Constraint text")],
) -> None:
    """Add a constraint to project defaults.

    Examples:
        simpletask defaults constraint add "Use Pydantic models with extra='forbid'"
        simpletask defaults constraint add "No shell=True in subprocess calls"
    """
    try:
        project = ensure_project()
        defaults = _load_or_empty(project)

        if defaults.constraints is None:
            defaults.constraints = []
        defaults.constraints.append(value)

        save_defaults(project, defaults)
        success("Added constraint to defaults")

    except (ValueError, FileNotFoundError) as e:
        error(str(e))
    except Exception as e:
        error(f"Unexpected error: {e}")


# ---------------------------------------------------------------------------
# simpletask defaults context set
# ---------------------------------------------------------------------------


@context_app.command(name="set")
def context_set_command(
    key: Annotated[str, typer.Argument(help="Context key")],
    value: Annotated[str, typer.Argument(help="Context value")],
) -> None:
    """Set a context key-value pair in project defaults.

    Examples:
        simpletask defaults context set framework django
        simpletask defaults context set database postgresql
    """
    try:
        project = ensure_project()
        defaults = _load_or_empty(project)

        if defaults.context is None:
            defaults.context = {}
        defaults.context[key] = value

        save_defaults(project, defaults)
        success(f"Set defaults context key '{key}'")

    except (ValueError, FileNotFoundError) as e:
        error(str(e))
    except Exception as e:
        error(f"Unexpected error: {e}")
