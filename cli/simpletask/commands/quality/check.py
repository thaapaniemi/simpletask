"""Quality check command."""

import json
from enum import Enum
from typing import Annotated

import typer
from rich.table import Table

from simpletask.core.models import QualityCheckResult
from simpletask.core.project import get_task_file_path
from simpletask.core.quality_ops import run_quality_checks
from simpletask.core.yaml_parser import parse_task_file
from simpletask.utils.console import console, error


class OutputFormat(str, Enum):
    """Output format options."""

    RICH = "rich"
    PLAIN = "plain"
    JSON = "json"


def print_plain_results(results: list[QualityCheckResult], all_passed: bool) -> None:
    """Print results in plain text format (no colors, CI/CD friendly)."""
    print("\n=== Quality Check Results ===\n")

    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.check_name}")
        print(f"  Command: {result.command}")

    if not all_passed:
        print("\n=== Failed Checks Details ===\n")
        for result in results:
            if not result.passed:
                print(f"{result.check_name}:")
                if result.stderr:
                    print(f"  Error: {result.stderr}")
                if result.stdout:
                    print(f"  Output: {result.stdout}")
                print()

    if all_passed:
        print("\n✓ All quality checks passed!\n")
    else:
        print("\n✗ Some quality checks failed. Please fix the issues and try again.\n")


def print_json_results(results: list[QualityCheckResult], all_passed: bool) -> None:
    """Print results in JSON format (machine-readable)."""
    output = {
        "all_passed": all_passed,
        "results": [
            {
                "check_name": r.check_name,
                "passed": r.passed,
                "command": r.command,
                "stdout": r.stdout,
                "stderr": r.stderr,
            }
            for r in results
        ],
    }
    print(json.dumps(output, indent=2))


def check_command(
    lint_only: Annotated[bool, typer.Option("--lint-only", help="Run only linting checks")] = False,
    test_only: Annotated[bool, typer.Option("--test-only", help="Run only test checks")] = False,
    type_only: Annotated[bool, typer.Option("--type-only", help="Run only type checking")] = False,
    security_only: Annotated[
        bool, typer.Option("--security-only", help="Run only security checks")
    ] = False,
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format (rich, plain, json)"),
    ] = OutputFormat.RICH,
    branch: Annotated[
        str | None,
        typer.Option("--branch", "-b", help="Branch name (defaults to current git branch)"),
    ] = None,
) -> None:
    """Run quality checks on the codebase.

    By default, runs all enabled quality checks. Use flags to run specific checks only.

    Examples:
        simpletask quality check
        simpletask quality check --lint-only
        simpletask quality check --test-only
        simpletask quality check --format plain  # CI/CD friendly
        simpletask quality check --format json   # Machine-readable
    """
    try:
        # Get file path
        file_path = get_task_file_path(branch)

        # Parse task file
        spec = parse_task_file(file_path)

        # Get quality requirements
        quality_reqs = spec.quality_requirements
        if quality_reqs is None:
            error("No quality_requirements configuration found in task file")
            raise typer.Exit(1)

        # Auto-detect non-terminal environment and use plain format if rich was selected
        if format == OutputFormat.RICH and not console.is_terminal:
            format = OutputFormat.PLAIN

        # Only print Rich formatted header if using rich format
        if format == OutputFormat.RICH:
            console.print(f"\n[bold]Running Quality Checks[/bold] ({file_path.name})\n")

        # Run quality checks using shared logic
        results, all_passed = run_quality_checks(
            quality_reqs,
            lint_only=lint_only,
            test_only=test_only,
            type_only=type_only,
            security_only=security_only,
        )

        if not results:
            if format == OutputFormat.RICH:
                console.print("[yellow]No quality checks enabled or selected[/yellow]")
            elif format == OutputFormat.PLAIN:
                print("No quality checks enabled or selected")
            else:  # JSON
                print(json.dumps({"all_passed": True, "results": []}))
            return

        # Display results based on format
        if format == OutputFormat.JSON:
            print_json_results(results, all_passed)
        elif format == OutputFormat.PLAIN:
            print_plain_results(results, all_passed)
        else:  # RICH
            # Display progress
            for result in results:
                console.print(f"Running {result.check_name}... ", end="")
                if result.passed:
                    console.print("[green]✓ PASS[/green]")
                else:
                    console.print("[red]✗ FAIL[/red]")

            # Display summary table
            console.print("\n[bold]Results Summary:[/bold]")
            table = Table(show_header=True, header_style="bold")
            table.add_column("Check", style="cyan")
            table.add_column("Status", justify="center")
            table.add_column("Command", style="dim")

            for result in results:
                status = "[green]✓ PASS[/green]" if result.passed else "[red]✗ FAIL[/red]"
                table.add_row(result.check_name, status, result.command)

            console.print(table)

            # Display detailed errors for failed checks
            if not all_passed:
                console.print("\n[bold red]Failed Checks Details:[/bold red]\n")
                for result in results:
                    if not result.passed:
                        console.print(f"[bold]{result.check_name}:[/bold]")
                        if result.stderr:
                            console.print(f"[red]{result.stderr}[/red]")
                        if result.stdout:
                            console.print(result.stdout)
                        console.print("")

            # Exit with appropriate code
            if all_passed:
                console.print("\n[bold green]All quality checks passed![/bold green]\n")
            else:
                console.print(
                    "\n[bold red]Some quality checks failed. Please fix the issues and try again.[/bold red]\n"
                )

        # Exit with appropriate code (for all formats)
        if all_passed:
            raise typer.Exit(0)
        else:
            raise typer.Exit(1)

    except FileNotFoundError as e:
        error(str(e))
    except ValueError as e:
        error(str(e))
        raise typer.Exit(1) from None
    except Exception as e:
        error(f"Unexpected error: {e}")
