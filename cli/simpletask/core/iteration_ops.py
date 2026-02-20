"""Iteration operations for CRUD on iterations in task files."""

from datetime import UTC, datetime
from pathlib import Path

from .models import Iteration, SimpleTaskSpec, Task
from .yaml_parser import parse_task_file, write_task_file


def get_next_iteration_id(iterations: list[Iteration]) -> int:
    """Generate next sequential iteration ID.

    Args:
        iterations: Existing iterations

    Returns:
        Next iteration ID as integer (e.g., 1, 2, 3)
    """
    if not iterations:
        return 1
    return max(i.id for i in iterations) + 1


def add_iteration_to_spec(
    spec: SimpleTaskSpec,
    label: str,
) -> tuple[SimpleTaskSpec, int]:
    """Add a new iteration to a task spec in memory.

    Returns a new SimpleTaskSpec without mutating the input.

    Args:
        spec: Task spec to derive from
        label: Human-readable iteration label

    Returns:
        Tuple of (new spec with iteration added, new iteration ID)
    """
    existing = list(spec.iterations or [])
    new_id = get_next_iteration_id(existing)

    new_iteration = Iteration(
        id=new_id,
        label=label,
        created=datetime.now(tz=UTC),
    )

    return spec.model_copy(update={"iterations": [*existing, new_iteration]}), new_id


def remove_iteration_from_spec(
    spec: SimpleTaskSpec,
    iteration_id: int,
) -> SimpleTaskSpec:
    """Remove an iteration and clear task references from a task spec in memory.

    Returns a new SimpleTaskSpec without mutating the input.

    Args:
        spec: Task spec to derive from
        iteration_id: Iteration ID to remove

    Returns:
        New spec with iteration removed and task references cleared

    Raises:
        ValueError: If iteration not found
    """
    existing = list(spec.iterations or [])

    if not any(it.id == iteration_id for it in existing):
        available = [i.id for i in existing]
        raise ValueError(f"Iteration {iteration_id} not found. Available: {available}")

    new_iterations = [it for it in existing if it.id != iteration_id] or None

    new_tasks = (
        [
            t.model_copy(update={"iteration": None}) if t.iteration == iteration_id else t
            for t in spec.tasks
        ]
        if spec.tasks
        else spec.tasks
    )

    return spec.model_copy(update={"iterations": new_iterations, "tasks": new_tasks})


def get_iteration_from_spec(
    spec: SimpleTaskSpec,
    iteration_id: int,
) -> Iteration:
    """Get a specific iteration by ID from a task spec.

    Args:
        spec: Task spec to search
        iteration_id: Iteration ID to retrieve

    Returns:
        The iteration with the given ID

    Raises:
        ValueError: If iteration not found
    """
    iterations = spec.iterations or []
    iteration = next((i for i in iterations if i.id == iteration_id), None)
    if iteration is None:
        available = [i.id for i in iterations]
        raise ValueError(f"Iteration {iteration_id} not found. Available: {available}")
    return iteration


# ---------------------------------------------------------------------------
# file_path-based wrappers (used by CLI commands)
# ---------------------------------------------------------------------------


def add_iteration(
    file_path: Path,
    label: str,
) -> int:
    """Add a new iteration to the task file.

    Args:
        file_path: Path to task YAML file
        label: Human-readable iteration label

    Returns:
        New iteration ID

    Raises:
        FileNotFoundError: If task file doesn't exist
        InvalidTaskFileError: If task file is malformed
    """
    spec = parse_task_file(file_path)
    spec, new_id = add_iteration_to_spec(spec, label)
    write_task_file(file_path, spec)
    return new_id


def list_iterations(
    file_path: Path,
) -> list[Iteration]:
    """List all iterations in the task file.

    Args:
        file_path: Path to task YAML file

    Returns:
        List of iterations, empty list if none

    Raises:
        FileNotFoundError: If task file doesn't exist
        InvalidTaskFileError: If task file is malformed
    """
    spec = parse_task_file(file_path)
    return spec.iterations or []


def get_iteration(
    file_path: Path,
    iteration_id: int,
) -> Iteration:
    """Get a specific iteration by ID.

    Args:
        file_path: Path to task YAML file
        iteration_id: Iteration ID to retrieve

    Returns:
        The iteration with the given ID

    Raises:
        ValueError: If iteration not found
        FileNotFoundError: If task file doesn't exist
        InvalidTaskFileError: If task file is malformed
    """
    spec = parse_task_file(file_path)
    return get_iteration_from_spec(spec, iteration_id)


def remove_iteration(
    file_path: Path,
    iteration_id: int,
) -> None:
    """Remove an iteration and clear task iteration references.

    Clears the iteration field on any tasks that referenced this iteration.

    Args:
        file_path: Path to task YAML file
        iteration_id: Iteration ID to remove

    Raises:
        ValueError: If iteration not found
        FileNotFoundError: If task file doesn't exist
        InvalidTaskFileError: If task file is malformed
    """
    spec = parse_task_file(file_path)
    spec = remove_iteration_from_spec(spec, iteration_id)
    write_task_file(file_path, spec)


def get_tasks_for_iteration(
    tasks: list[Task] | None,
    iteration_id: int,
) -> list[Task]:
    """Get all tasks assigned to a specific iteration.

    Args:
        tasks: List of all tasks
        iteration_id: Iteration ID to filter by

    Returns:
        List of tasks assigned to the iteration
    """
    if not tasks:
        return []
    return [t for t in tasks if t.iteration == iteration_id]
