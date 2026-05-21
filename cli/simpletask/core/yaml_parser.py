"""YAML parsing for task files."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .models import SimpleTaskSpec, TaskStatus


class InvalidTaskFileError(Exception):
    """Raised when task file format is invalid or doesn't match schema."""


def parse_task_file_from_text(text: str, source_path: Path | None = None) -> SimpleTaskSpec:
    """Parse task YAML from a pre-read string without filesystem I/O.

    Args:
        text: Raw YAML content to parse.
        source_path: Optional path used only for error message context.

    Returns:
        SimpleTaskSpec instance.

    Raises:
        InvalidTaskFileError: If YAML is invalid or doesn't match schema.
    """
    path_label = str(source_path) if source_path else "<string>"

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise InvalidTaskFileError(f"Invalid YAML syntax:\n{e!s}\n\nFile: {path_label}") from e

    if not isinstance(data, dict):
        raise InvalidTaskFileError(
            f"Invalid YAML content: Expected a dictionary/object, got {type(data).__name__}.\n"
            f"File: {path_label}"
        )

    try:
        spec = SimpleTaskSpec.model_validate(data)
    except ValidationError as e:
        error_messages = []
        for error in e.errors():
            field = ".".join(str(x) for x in error["loc"])
            message = error["msg"]
            error_type = error["type"]
            error_messages.append(f"  • {field}: {message} (type: {error_type})")

        raise InvalidTaskFileError(
            "Invalid task file schema - YAML content doesn't match expected format:\n\n"
            + "\n".join(error_messages)
            + f"\n\nFile: {path_label}\n\n"
            f"See documentation for correct schema format."
        ) from e

    return spec


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

    return parse_task_file_from_text(path.read_text(encoding="utf-8"), path)


def parse_task_file_lenient(path: Path) -> dict[str, Any]:
    """Parse task YAML without Pydantic validation (for repair).

    Use this when you need to read a potentially broken task file
    to repair it. Returns raw dict without schema validation.

    Args:
        path: Path to task YAML file

    Returns:
        Raw dict from YAML

    Raises:
        FileNotFoundError: If file doesn't exist
        InvalidTaskFileError: If YAML syntax is invalid
    """
    if not path.exists():
        raise FileNotFoundError(f"Task file not found: {path}")

    content = path.read_text(encoding="utf-8")

    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise InvalidTaskFileError(f"Invalid YAML syntax:\n{e!s}\n\nFile: {path}") from e

    if not isinstance(data, dict):
        raise InvalidTaskFileError(
            f"Invalid YAML content: Expected dict, got {type(data).__name__}.\nFile: {path}"
        )

    return data


_QUALITY_CONFIG_KEYS = ("linting", "type_checking", "testing", "security_check")


def _bump_schema_version_if_canonical(data: dict[str, Any]) -> dict[str, Any]:
    """Upgrade schema_version to '1.1' when any quality section uses canonical execution.

    The model serializer already strips legacy 'args' from canonical sections;
    this function only handles the version bump that belongs to the writer layer.

    Args:
        data: Serialized task spec dict (from model_dump)

    Returns:
        Mutated dict with schema_version bumped to '1.1' when canonical execution is present
    """
    quality_reqs = data.get("quality_requirements")
    if not isinstance(quality_reqs, dict):
        return data

    has_canonical = any(
        isinstance(quality_reqs.get(key), dict) and "execution" in quality_reqs[key]
        for key in _QUALITY_CONFIG_KEYS
    )
    if has_canonical:
        data["schema_version"] = "1.1"

    return data


def serialize_task_file(spec: SimpleTaskSpec) -> str:
    """Serialize a task spec to canonical YAML string without touching the filesystem.

    Produces the same output as write_task_file() without any I/O. Used by
    fmt --check to compare in-memory canonical form against current file content.

    Args:
        spec: SimpleTaskSpec instance to serialize

    Returns:
        Canonical YAML string
    """
    data = spec.model_dump(mode="json", exclude_none=True)
    data = _bump_schema_version_if_canonical(data)
    return yaml.dump(
        data,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
        width=100,
        indent=2,
    )


def write_task_file(path: Path, spec: SimpleTaskSpec) -> None:
    """Write task YAML file.

    Revalidates the spec before writing to catch constraint violations from
    in-place mutations (e.g. removing the last acceptance criterion).

    Args:
        path: Path to task file (will be created/overwritten)
        spec: SimpleTaskSpec instance to serialize to YAML

    Raises:
        InvalidTaskFileError: If the spec fails schema validation before write
    """
    # Revalidate to catch constraint violations from in-place mutations
    try:
        SimpleTaskSpec.model_validate(spec.model_dump(mode="json", exclude_none=True))
    except ValidationError as e:
        error_messages = []
        for error in e.errors():
            field = ".".join(str(x) for x in error["loc"])
            message = error["msg"]
            error_type = error["type"]
            error_messages.append(f"  • {field}: {message} (type: {error_type})")
        raise InvalidTaskFileError(
            "Cannot write task file - schema validation failed:\n\n" + "\n".join(error_messages)
        ) from e

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Serialize and write
    path.write_text(serialize_task_file(spec), encoding="utf-8")


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

    # Write back to file
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

    # Write back to file
    write_task_file(path, spec)


# Export public API
__all__ = [
    "InvalidTaskFileError",
    "parse_task_file",
    "parse_task_file_from_text",
    "parse_task_file_lenient",
    "serialize_task_file",
    "update_criterion_status",
    "update_task_status",
    "write_task_file",
]
