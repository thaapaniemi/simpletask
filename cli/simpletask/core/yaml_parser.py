"""YAML parsing for task files with auto-timestamp management."""

from datetime import datetime, timezone
from pathlib import Path

import yaml
from pydantic import ValidationError

from .models import SimpleTaskSpec, TaskStatus


class InvalidTaskFileError(Exception):
    """Raised when task file format is invalid or doesn't match schema."""

    pass


def parse_task_file(path: Path) -> SimpleTaskSpec:
    """Parse task YAML file.

    Args:
        path: Path to task YAML file

    Returns:
        SimpleTaskSpec instance

    Raises:
        FileNotFoundError: If file doesn't exist
        InvalidTaskFileError: If YAML is invalid or doesn't match schema
    """
    if not path.exists():
        raise FileNotFoundError(f"Task file not found: {path}")

    content = path.read_text(encoding="utf-8")

    # Parse YAML
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise InvalidTaskFileError(f"Invalid YAML syntax:\n{str(e)}\n\nFile: {path}") from e

    # Validate that YAML parsed to a dict
    if not isinstance(data, dict):
        raise InvalidTaskFileError(
            f"Invalid YAML content: Expected a dictionary/object, got {type(data).__name__}.\n"
            f"File: {path}"
        )

    # Validate against Pydantic schema
    try:
        spec = SimpleTaskSpec.model_validate(data)
    except ValidationError as e:
        # Format validation errors nicely
        error_messages = []
        for error in e.errors():
            field = ".".join(str(x) for x in error["loc"])
            message = error["msg"]
            error_type = error["type"]
            error_messages.append(f"  • {field}: {message} (type: {error_type})")

        raise InvalidTaskFileError(
            "Invalid task file schema - YAML content doesn't match expected format:\n\n"
            + "\n".join(error_messages)
            + f"\n\nFile: {path}\n\n"
            f"See documentation for correct schema format."
        ) from e

    return spec


def write_task_file(path: Path, spec: SimpleTaskSpec, update_timestamp: bool = True) -> None:
    """Write task YAML file with auto-timestamp management.

    Args:
        path: Path to task file (will be created/overwritten)
        spec: SimpleTaskSpec instance to serialize to YAML
        update_timestamp: Whether to update the 'updated' timestamp (default: True)
    """
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Update timestamp if requested
    if update_timestamp:
        spec.updated = datetime.now(timezone.utc)

    # Convert spec to dict (mode='json' for datetime serialization)
    data = spec.model_dump(mode="json", exclude_none=True)

    # Generate YAML with nice formatting
    yaml_content = yaml.dump(
        data,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
        width=100,  # Wrap long lines at 100 chars
        indent=2,
    )

    # Write to file
    path.write_text(yaml_content, encoding="utf-8")


def update_task_status(path: Path, task_id: str, new_status: TaskStatus) -> None:
    """Update a specific task's status in task file.

    Args:
        path: Path to task file
        task_id: Task ID to update (e.g., "T001")
        new_status: New status

    Raises:
        FileNotFoundError: If file doesn't exist
        InvalidTaskFileError: If file format is invalid
        ValueError: If task_id not found
    """
    # Parse file
    spec = parse_task_file(path)

    if not spec.tasks:
        raise ValueError("No tasks defined in task file")

    # Find and update task
    task_found = False
    for task in spec.tasks:
        if task.id == task_id:
            task_found = True
            task.status = new_status
            break

    if not task_found:
        task_ids = [t.id for t in spec.tasks]
        raise ValueError(f"Task '{task_id}' not found. Available tasks: {task_ids}")

    # Write back to file (with auto-timestamp update)
    write_task_file(path, spec)


def update_criterion_status(path: Path, criterion_id: str, completed: bool) -> None:
    """Update acceptance criterion completion status.

    Args:
        path: Path to task file
        criterion_id: Criterion ID to update (e.g., "AC1")
        completed: New completion status

    Raises:
        FileNotFoundError: If file doesn't exist
        InvalidTaskFileError: If file format is invalid
        ValueError: If criterion_id not found
    """
    # Parse file
    spec = parse_task_file(path)

    # Find and update criterion
    criterion_found = False
    for criterion in spec.acceptance_criteria:
        if criterion.id == criterion_id:
            criterion_found = True
            criterion.completed = completed
            break

    if not criterion_found:
        criterion_ids = [c.id for c in spec.acceptance_criteria]
        raise ValueError(f"Criterion '{criterion_id}' not found. Available: {criterion_ids}")

    # Write back to file (with auto-timestamp update)
    write_task_file(path, spec)


# Export public API
__all__ = [
    "InvalidTaskFileError",
    "parse_task_file",
    "write_task_file",
    "update_task_status",
    "update_criterion_status",
]
