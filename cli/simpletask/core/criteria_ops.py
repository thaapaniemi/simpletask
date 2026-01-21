"""Criteria operations for CRUD on acceptance criteria in task files."""

from pathlib import Path

from .models import AcceptanceCriterion
from .repair import repair_task_file
from .yaml_parser import InvalidTaskFileError, parse_task_file, write_task_file


def get_next_criterion_id(criteria: list[AcceptanceCriterion]) -> str:
    """Generate next sequential criterion ID.

    Args:
        criteria: Existing acceptance criteria

    Returns:
        Next criterion ID (e.g., "AC3")
    """
    if not criteria:
        return "AC1"
    max_num = max(int(c.id[2:]) for c in criteria)
    return f"AC{max_num + 1}"


def add_acceptance_criterion(
    file_path: Path,
    description: str,
) -> str:
    """Add a new acceptance criterion to the task file.

    Automatically repairs broken task files with empty criteria or unknown fields.

    Args:
        file_path: Path to task YAML file
        description: Criterion description

    Returns:
        New criterion ID

    Raises:
        FileNotFoundError: If task file doesn't exist
        InvalidTaskFileError: If task file cannot be repaired
    """
    # Parse existing file (with automatic repair if needed)
    try:
        spec = parse_task_file(file_path)
    except InvalidTaskFileError:
        # Attempt automatic repair for common issues
        spec = repair_task_file(file_path)

    # Generate new ID
    new_id = get_next_criterion_id(spec.acceptance_criteria)

    # Create new criterion
    new_criterion = AcceptanceCriterion(
        id=new_id,
        description=description,
        completed=False,
    )

    # Append criterion
    spec.acceptance_criteria.append(new_criterion)

    # Write back (auto-updates timestamp)
    write_task_file(file_path, spec)

    return new_id


def mark_criterion_complete(
    file_path: Path,
    criterion_id: str,
    completed: bool = True,
) -> None:
    """Mark an acceptance criterion as completed or not completed.

    Args:
        file_path: Path to task YAML file
        criterion_id: Criterion ID to update
        completed: Whether criterion is completed (default: True)

    Raises:
        ValueError: If criterion not found
        FileNotFoundError: If task file doesn't exist
    """
    # Parse existing file
    spec = parse_task_file(file_path)

    # Find criterion
    criterion = next((c for c in spec.acceptance_criteria if c.id == criterion_id), None)
    if not criterion:
        available = [c.id for c in spec.acceptance_criteria]
        raise ValueError(f"Criterion {criterion_id} not found. Available: {available}")

    # Update completion status
    criterion.completed = completed

    # Write back (auto-updates timestamp)
    write_task_file(file_path, spec)


def remove_acceptance_criterion(
    file_path: Path,
    criterion_id: str,
) -> None:
    """Remove an acceptance criterion.

    Args:
        file_path: Path to task YAML file
        criterion_id: Criterion ID to remove

    Raises:
        ValueError: If criterion not found
        FileNotFoundError: If task file doesn't exist
    """
    # Parse existing file
    spec = parse_task_file(file_path)

    # Find criterion index
    criterion_index = next(
        (i for i, c in enumerate(spec.acceptance_criteria) if c.id == criterion_id), None
    )
    if criterion_index is None:
        available = [c.id for c in spec.acceptance_criteria]
        raise ValueError(f"Criterion {criterion_id} not found. Available: {available}")

    # Remove criterion
    del spec.acceptance_criteria[criterion_index]

    # Write back (auto-updates timestamp)
    write_task_file(file_path, spec)
