"""Task operations for CRUD on implementation tasks in task files."""

from pathlib import Path
from typing import List, Optional

from .models import Task, TaskStatus
from .yaml_parser import parse_task_file, write_task_file


def get_next_task_id(tasks: List[Task]) -> str:
    """Generate next sequential task ID.

    Args:
        tasks: Existing tasks

    Returns:
        Next task ID (e.g., "T003")
    """
    if not tasks:
        return "T001"
    max_num = max(int(t.id[1:]) for t in tasks)
    return f"T{max_num + 1:03d}"


def add_implementation_task(
    file_path: Path,
    name: str,
    goal: Optional[str] = None,
    status: TaskStatus = TaskStatus.NOT_STARTED,
) -> str:
    """Add a new implementation task to the task file.

    Args:
        file_path: Path to task YAML file
        name: Task name
        goal: Optional task goal/description (defaults to name if not provided)
        status: Initial status (default: not_started)

    Returns:
        New task ID

    Raises:
        FileNotFoundError: If task file doesn't exist
    """
    # Parse existing file
    spec = parse_task_file(file_path)

    # Default goal to name if not provided
    if goal is None:
        goal = name

    # Generate new ID
    tasks = spec.tasks or []
    new_id = get_next_task_id(tasks)

    # Create new task with required fields
    new_task = Task(
        id=new_id,
        name=name,
        goal=goal,
        status=status,
        steps=["To be defined"],  # Default placeholder step
    )

    # Append task
    if spec.tasks is None:
        spec.tasks = []
    spec.tasks.append(new_task)

    # Write back (auto-updates timestamp)
    write_task_file(file_path, spec)

    return new_id


def update_implementation_task(
    file_path: Path,
    task_id: str,
    name: Optional[str] = None,
    goal: Optional[str] = None,
    status: Optional[TaskStatus] = None,
) -> None:
    """Update an existing implementation task.

    Args:
        file_path: Path to task YAML file
        task_id: Task ID to update
        name: New name (optional)
        goal: New goal (optional)
        status: New status (optional)

    Raises:
        ValueError: If task not found
        FileNotFoundError: If task file doesn't exist
    """
    # Parse existing file
    spec = parse_task_file(file_path)

    if not spec.tasks:
        raise ValueError(f"No tasks defined in {file_path}")

    # Find task
    task = next((t for t in spec.tasks if t.id == task_id), None)
    if not task:
        available = [t.id for t in spec.tasks]
        raise ValueError(f"Task {task_id} not found. Available: {available}")

    # Update fields
    if name is not None:
        task.name = name
    if goal is not None:
        task.goal = goal
    if status is not None:
        task.status = status

    # Write back (auto-updates timestamp)
    write_task_file(file_path, spec)


def remove_implementation_task(
    file_path: Path,
    task_id: str,
) -> None:
    """Remove an implementation task.

    Args:
        file_path: Path to task YAML file
        task_id: Task ID to remove

    Raises:
        ValueError: If task not found
        FileNotFoundError: If task file doesn't exist
    """
    # Parse existing file
    spec = parse_task_file(file_path)

    if not spec.tasks:
        raise ValueError(f"No tasks defined in {file_path}")

    # Find task index
    task_index = next((i for i, t in enumerate(spec.tasks) if t.id == task_id), None)
    if task_index is None:
        available = [t.id for t in spec.tasks]
        raise ValueError(f"Task {task_id} not found. Available: {available}")

    # Remove task
    removed_id = spec.tasks[task_index].id
    del spec.tasks[task_index]

    # Clean up prerequisite references to the removed task
    for task in spec.tasks:
        if task.prerequisites and removed_id in task.prerequisites:
            task.prerequisites.remove(removed_id)
            if not task.prerequisites:  # Clean up empty list
                task.prerequisites = None

    # Write back (auto-updates timestamp)
    write_task_file(file_path, spec)
