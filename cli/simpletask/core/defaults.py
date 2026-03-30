"""Project-level defaults management for simpletask.

Provides load/save/merge operations for .tasks/defaults.yml — the file that
stores project-level defaults automatically injected into new task files.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .models import ProjectDefaults, SimpleTaskSpec
from .project import Project
from .yaml_parser import InvalidTaskFileError

# The filename for project-level defaults within the .tasks/ directory
DEFAULTS_FILENAME = "defaults.yml"


def get_defaults_path(project: Project) -> Path:
    """Return the path to the project defaults file.

    Args:
        project: Project instance

    Returns:
        Path to .tasks/defaults.yml
    """
    return project.tasks_dir / DEFAULTS_FILENAME


def load_defaults(project: Project) -> ProjectDefaults | None:
    """Load project defaults from .tasks/defaults.yml.

    Args:
        project: Project instance

    Returns:
        ProjectDefaults if file exists and is valid, None if file doesn't exist.

    Raises:
        InvalidTaskFileError: If the file exists but is malformed YAML or fails
                              Pydantic validation.
    """
    path = get_defaults_path(project)

    if not path.exists():
        return None

    content = path.read_text(encoding="utf-8")

    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise InvalidTaskFileError(
            f"Invalid YAML syntax in defaults file:\n{e!s}\n\nFile: {path}"
        ) from e

    # Empty file or null YAML produces None — treat as empty defaults
    if data is None:
        return ProjectDefaults()

    if not isinstance(data, dict):
        raise InvalidTaskFileError(
            f"Invalid defaults file: expected a dictionary, got {type(data).__name__}.\n"
            f"File: {path}"
        )

    try:
        return ProjectDefaults.model_validate(data)
    except ValidationError as e:
        error_messages = []
        for error in e.errors():
            field = ".".join(str(x) for x in error["loc"])
            message = error["msg"]
            error_type = error["type"]
            error_messages.append(f"  • {field}: {message} (type: {error_type})")

        raise InvalidTaskFileError(
            "Invalid defaults file — content doesn't match expected schema:\n\n"
            + "\n".join(error_messages)
            + f"\n\nFile: {path}"
        ) from e


def save_defaults(project: Project, defaults: ProjectDefaults) -> Path:
    """Save project defaults to .tasks/defaults.yml.

    Args:
        project: Project instance
        defaults: ProjectDefaults to save

    Returns:
        Path to the written file.
    """
    project.ensure_tasks_dir()
    path = get_defaults_path(project)

    # Serialize — exclude_none omits unpopulated optional fields for clean output
    data: dict[str, Any] = defaults.model_dump(mode="json", exclude_none=True)

    yaml_content = yaml.dump(
        data,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
        width=100,
        indent=2,
    )

    path.write_text(yaml_content, encoding="utf-8")
    return path


def merge_defaults_into_spec(spec: SimpleTaskSpec, defaults: ProjectDefaults) -> SimpleTaskSpec:
    """Merge project defaults into a task spec using fill-gaps-only strategy.

    Only populates fields that are currently None in *spec*. Existing values in
    *spec* are never overwritten. This is a one-time merge at task file creation
    time; once written, the task file is fully independent of defaults.yml.

    Args:
        spec: Task specification to enrich.
        defaults: Project defaults to merge from.

    Returns:
        The same *spec* object (mutated in-place) with gaps filled from defaults.
    """
    if spec.design is None and defaults.design is not None:
        spec.design = defaults.design

    if spec.quality_requirements is None and defaults.quality_requirements is not None:
        spec.quality_requirements = defaults.quality_requirements

    if spec.constraints is None and defaults.constraints is not None:
        spec.constraints = defaults.constraints

    if spec.context is None and defaults.context is not None:
        spec.context = defaults.context

    return spec


__all__ = [
    "DEFAULTS_FILENAME",
    "get_defaults_path",
    "load_defaults",
    "merge_defaults_into_spec",
    "save_defaults",
]
