"""
Show command - Display task details."""

import typer

from ..core.models import Design, QualityRequirements, Task
from ..core.project import ensure_project, get_task_file_path
from ..core.yaml_parser import InvalidTaskFileError, parse_task_file
from ..utils.console import console, error


def _format_quality_summary(quality_reqs: QualityRequirements) -> str:
    """Format quality requirements as a compact summary line.

    Args:
        quality_reqs: Quality requirements configuration

    Returns:
        Formatted string like "✓ lint (ruff)  ✓ test (pytest, 80% cov)  ○ types  ○ security"
    """
    parts = []

    # Linting
    icon = "✓" if quality_reqs.linting.enabled else "○"
    color = "green" if quality_reqs.linting.enabled else "dim"
    tool_name = quality_reqs.linting.tool.value if quality_reqs.linting.enabled else ""
    parts.append(f"[{color}]{icon}[/{color}] lint" + (f" ({tool_name})" if tool_name else ""))

    # Testing
    icon = "✓" if quality_reqs.testing.enabled else "○"
    color = "green" if quality_reqs.testing.enabled else "dim"
    tool_name = quality_reqs.testing.tool.value if quality_reqs.testing.enabled else ""
    cov = f", {quality_reqs.testing.min_coverage}% cov" if quality_reqs.testing.min_coverage else ""
    parts.append(f"[{color}]{icon}[/{color}] test" + (f" ({tool_name}{cov})" if tool_name else ""))

    # Type checking
    if quality_reqs.type_checking:
        icon = "✓" if quality_reqs.type_checking.enabled else "○"
        color = "green" if quality_reqs.type_checking.enabled else "dim"
        tool_name = (
            quality_reqs.type_checking.tool.value if quality_reqs.type_checking.enabled else ""
        )
        parts.append(f"[{color}]{icon}[/{color}] types" + (f" ({tool_name})" if tool_name else ""))
    else:
        parts.append("[dim]○[/dim] types")

    # Security
    if quality_reqs.security_check:
        icon = "✓" if quality_reqs.security_check.enabled else "○"
        color = "green" if quality_reqs.security_check.enabled else "dim"
        tool_name = (
            quality_reqs.security_check.tool.value
            if quality_reqs.security_check.enabled and quality_reqs.security_check.tool
            else ""
        )
        parts.append(
            f"[{color}]{icon}[/{color}] security" + (f" ({tool_name})" if tool_name else "")
        )
    else:
        parts.append("[dim]○[/dim] security")

    return "  ".join(parts)


def _format_design_summary(design: Design) -> list[str]:
    """Format design section as compact summary lines.

    Args:
        design: Design configuration

    Returns:
        List of summary lines to display
    """
    lines = []

    # Patterns
    if design.patterns:
        pattern_names = ", ".join(p.value for p in design.patterns)
        lines.append(f"  Patterns: [cyan]{pattern_names}[/cyan]")

    # Counts for references, constraints, security
    counts = []
    if design.reference_implementations:
        count = len(design.reference_implementations)
        counts.append(f"{count} reference{'s' if count != 1 else ''}")
    if design.architectural_constraints:
        count = len(design.architectural_constraints)
        counts.append(f"{count} constraint{'s' if count != 1 else ''}")
    if design.security:
        count = len(design.security)
        counts.append(f"{count} security requirement{'s' if count != 1 else ''}")

    if counts:
        lines.append(f"  {', '.join(counts)}")

    # Error handling
    if design.error_handling:
        lines.append(f"  Error handling: [cyan]{design.error_handling.value}[/cyan]")

    return lines


def _truncate_text(text: str, max_length: int = 160) -> str:
    """Truncate text to max_length with ellipsis if needed.

    Args:
        text: Text to truncate
        max_length: Maximum length including ellipsis

    Returns:
        Truncated text with "..." if longer than max_length
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def _count_task_notes(tasks: list[Task] | None) -> tuple[int, int]:
    """Count total task notes and tasks with notes.

    Single-pass iteration for efficiency.

    Args:
        tasks: List of tasks to count notes from

    Returns:
        Tuple of (total_notes_count, tasks_with_notes_count)
    """
    if not tasks:
        return 0, 0

    total_notes = 0
    tasks_with_notes = 0

    for task in tasks:
        if task.notes:
            total_notes += len(task.notes)
            tasks_with_notes += 1

    return total_notes, tasks_with_notes


def show(
    branch: str | None = typer.Argument(None, help="Branch name (defaults to current git branch)"),
) -> None:
    """Show detailed information about a task.

    Displays:
    - Task file location
    - Title and branch
    - Acceptance criteria with completion status
    - Implementation tasks (if defined)
    - Constraints (if defined)
    - Quality requirements summary (if configured)
    - Design summary (if configured)
    - Original prompt (truncated to 160 chars)
    - Notes (if present): root notes with bullets, task notes as count summary

    Examples:
        simpletask show                    # Uses current git branch
        simpletask show add-dark-mode      # Explicit branch
    """
    task_file = None
    try:
        task_file = get_task_file_path(branch)
        project = ensure_project()

        # Parse task file
        spec = parse_task_file(task_file)

        # Display file location (relative to project root)
        relative_path = task_file.relative_to(project.root)
        console.print(f"\n[bold]Task File:[/bold] {relative_path}")
        console.print()

        # Display task information
        console.print(f"[bold cyan]Task:[/bold cyan] {spec.title}")
        console.print(f"[bold]Branch:[/bold] {spec.branch}")
        console.print(f"[bold]Created:[/bold] {spec.created.strftime('%Y-%m-%d %H:%M:%S UTC')}")

        # Acceptance criteria
        console.print("\n[bold magenta]Acceptance Criteria:[/bold magenta]")
        for criterion in spec.acceptance_criteria:
            status_icon = "✓" if criterion.completed else "○"
            status_color = "green" if criterion.completed else "white"
            console.print(
                f"  [{status_color}]{status_icon}[/{status_color}] {criterion.id}: {criterion.description}"
            )

        # Constraints
        if spec.constraints:
            console.print("\n[bold yellow]Constraints:[/bold yellow]")
            for constraint in spec.constraints:
                console.print(f"  • {constraint}")

        # Tasks
        if spec.tasks:
            console.print("\n[bold green]Implementation Tasks:[/bold green]")
            for task in spec.tasks:
                if task.status.value == "completed":
                    status_icon = "✓"
                    status_color = "green"
                elif task.status.value == "in_progress":
                    status_icon = "▶"
                    status_color = "yellow"
                elif task.status.value == "blocked":
                    status_icon = "✗"
                    status_color = "red"
                elif task.status.value == "paused":
                    status_icon = "⏸"
                    status_color = "blue"
                else:  # not_started
                    status_icon = "○"
                    status_color = "white"
                console.print(
                    f"  [{status_color}]{status_icon}[/{status_color}] {task.id}: {task.name} ({task.status.value})"
                )
        else:
            console.print("\n[dim]No implementation tasks defined yet[/dim]")

        # Quality Requirements Summary
        if spec.quality_requirements:
            console.print("\n[bold blue]Quality Requirements:[/bold blue]")
            console.print(f"  {_format_quality_summary(spec.quality_requirements)}")
            console.print(
                "  [dim]→ Run:[/dim] simpletask quality check [dim]| Details:[/dim] simpletask quality show"
            )

        # Design Summary
        if spec.design:
            console.print("\n[bold cyan]Design:[/bold cyan]")
            design_lines = _format_design_summary(spec.design)
            if design_lines:
                for line in design_lines:
                    console.print(line)
                console.print("  [dim]→ Details:[/dim] simpletask design show")
            else:
                console.print("  [dim]Design section exists but is empty[/dim]")

        # Original Prompt
        console.print("\n[bold yellow]Original Prompt:[/bold yellow]")
        truncated_prompt = _truncate_text(spec.original_prompt)
        console.print(f'  "{truncated_prompt}"')

        # Notes Section (Option C: Hybrid format)
        # Display root notes with bullets, task notes as summary
        # Hidden when no notes exist
        has_root_notes = bool(spec.notes)
        task_note_count, task_with_notes_count = _count_task_notes(spec.tasks)

        if has_root_notes or task_note_count > 0:
            console.print("\n[bold cyan]Notes:[/bold cyan]")

            # Display root notes with bullets
            if has_root_notes:
                console.print("  [bold]Root:[/bold]")
                if spec.notes:  # Type guard for mypy
                    for note in spec.notes:
                        truncated_note = _truncate_text(note)
                        console.print(f"    • {truncated_note}")
                console.print()

            # Display task notes summary
            if task_note_count > 0:
                note_word = "note" if task_note_count == 1 else "notes"
                task_word = "task" if task_with_notes_count == 1 else "tasks"
                console.print(
                    f"  [bold]Tasks:[/bold] {task_note_count} {note_word} across {task_with_notes_count} {task_word}"
                )
                console.print("  [dim]→ Details:[/dim] simpletask note list")

        console.print()

    except FileNotFoundError:
        error(f"Task file not found: {task_file}")
    except InvalidTaskFileError as e:
        error(f"Invalid task file: {e}")
    except ValueError as e:
        error(str(e))
    except Exception as e:
        error(f"Unexpected error: {e}")
