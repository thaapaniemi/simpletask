"""Design set command."""

from typing import Annotated

import typer

from simpletask.core.models import (
    ArchitecturalPattern,
    Design,
    DesignReference,
    ErrorHandlingStrategy,
    SecurityCategory,
    SecurityRequirement,
)
from simpletask.core.project import get_task_file_path
from simpletask.core.yaml_parser import parse_task_file, write_task_file
from simpletask.utils.console import console, error


def set_command(
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
    branch: Annotated[
        str | None,
        typer.Option("--branch", "-b", help="Branch name (defaults to current git branch)"),
    ] = None,
    reference_reason: Annotated[
        str | None,
        typer.Option(
            "--reason",
            "-r",
            help="Reason for reference (required when field=reference)",
        ),
    ] = None,
    security_category: Annotated[
        str | None,
        typer.Option(
            "--category",
            "-c",
            help="Security category (required when field=security): authentication, authorization, cryptography, input_validation, output_encoding, session_management, secure_communication, data_protection, audit_logging",
        ),
    ] = None,
) -> None:
    """Set design guidance fields.

    Field options:
        pattern          - Add architectural pattern (single enum value)
        reference        - Add reference implementation (requires --reason)
        constraint       - Add architectural constraint (free text)
        security         - Add security requirement (requires --category)
        error-handling   - Set error handling strategy (single enum value)

    Available architectural patterns:
        repository, service_layer, factory, strategy, adapter, observer, command,
        mvc, clean_architecture, hexagonal, dependency_injection, singleton, builder, decorator

    Available error handling strategies:
        exceptions, result_type, error_codes, callbacks, panic_recover

    Security categories:
        authentication, authorization, cryptography, input_validation, output_encoding,
        session_management, secure_communication, data_protection, audit_logging

    Examples:
        simpletask design set pattern repository
        simpletask design set pattern dependency_injection
        simpletask design set reference src/existing/module.py --reason "Similar functionality"
        simpletask design set constraint "Use clean architecture"
        simpletask design set security "Validate all user inputs" --category input_validation
        simpletask design set error-handling result_type
    """
    try:
        # Get file path
        file_path = get_task_file_path(branch)

        # Parse task file
        spec = parse_task_file(file_path)

        # Initialize design section if it doesn't exist
        if not spec.design:
            spec.design = Design(
                patterns=None,
                reference_implementations=None,
                architectural_constraints=None,
                security=None,
                error_handling=None,
            )

        # Handle different field types
        if field == "pattern":
            # Parse enum value
            try:
                pattern = ArchitecturalPattern(value)
            except ValueError:
                valid_patterns = ", ".join([p.value for p in ArchitecturalPattern])
                error(f"Invalid pattern: {value}. Valid patterns: {valid_patterns}")
                raise typer.Exit(1) from None

            if not spec.design.patterns:
                spec.design.patterns = []
            spec.design.patterns.append(pattern)
            console.print(f"[green]✓[/green] Added pattern: {pattern.value}")

        elif field == "reference":
            # Requires --reason option
            if not reference_reason:
                error("--reason is required when adding reference implementations")
                raise typer.Exit(1)

            if not spec.design.reference_implementations:
                spec.design.reference_implementations = []

            ref = DesignReference(path=value, reason=reference_reason)
            spec.design.reference_implementations.append(ref)
            console.print(f"[green]✓[/green] Added reference: {value}")

        elif field == "constraint":
            # Free text constraint
            if not spec.design.architectural_constraints:
                spec.design.architectural_constraints = []
            spec.design.architectural_constraints.append(value)
            console.print("[green]✓[/green] Added constraint")

        elif field == "security":
            # Requires --category option
            if not security_category:
                error("--category is required when adding security requirements")
                raise typer.Exit(1)

            # Parse category enum
            try:
                category = SecurityCategory(security_category)
            except ValueError:
                valid_categories = ", ".join([c.value for c in SecurityCategory])
                error(
                    f"Invalid category: {security_category}. Valid categories: {valid_categories}"
                )
                raise typer.Exit(1) from None

            if not spec.design.security:
                spec.design.security = []

            req = SecurityRequirement(category=category, description=value)
            spec.design.security.append(req)
            console.print(f"[green]✓[/green] Added security requirement: {category.value}")

        elif field == "error-handling":
            # Parse enum value
            try:
                strategy = ErrorHandlingStrategy(value)
            except ValueError:
                valid_strategies = ", ".join([s.value for s in ErrorHandlingStrategy])
                error(f"Invalid strategy: {value}. Valid strategies: {valid_strategies}")
                raise typer.Exit(1) from None

            spec.design.error_handling = strategy
            console.print(f"[green]✓[/green] Set error handling strategy: {strategy.value}")

        else:
            error(
                f"Invalid field: {field}. "
                "Use: pattern, reference, constraint, security, error-handling"
            )
            raise typer.Exit(1)

        # Write back to file
        write_task_file(file_path, spec)
        console.print(f"[dim]Updated {file_path.name}[/dim]\n")

    except FileNotFoundError as e:
        error(str(e))
    except typer.Exit:
        raise
    except Exception as e:
        error(f"Unexpected error: {e}")
