"""JSON schema validation for task files."""

import json
from importlib import resources
from pathlib import Path

import jsonschema
import yaml


def get_bundled_schema() -> dict:
    """Load the bundled JSON schema.

    Returns:
        Schema dictionary
    """
    # Load schema from package
    try:
        # Python 3.11+ importlib.resources API
        schema_text = (
            resources.files("simpletask.schema").joinpath("simpletask.schema.json").read_text()
        )
    except (AttributeError, TypeError):
        # Fallback for older Python versions
        import importlib.resources as pkg_resources

        schema_text = pkg_resources.read_text("simpletask.schema", "simpletask.schema.json")

    return json.loads(schema_text)


def validate_task_file(path: Path) -> list[str]:
    """Validate task YAML file against JSON schema.

    This provides explicit schema validation beyond Pydantic's runtime checks.
    Returns a list of validation errors (empty list if valid).

    Args:
        path: Path to task YAML file

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    # Check file exists
    if not path.exists():
        errors.append(f"File not found: {path}")
        return errors

    # Load YAML
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        errors.append(f"Invalid YAML syntax: {e}")
        return errors
    except Exception as e:
        errors.append(f"Error reading file: {e}")
        return errors

    # Load schema
    try:
        schema = get_bundled_schema()
    except Exception as e:
        errors.append(f"Error loading schema: {e}")
        return errors

    # Validate against schema
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        # Format the error message
        error_path = ".".join(str(p) for p in e.path) if e.path else "root"
        errors.append(f"Validation error at '{error_path}': {e.message}")
    except jsonschema.SchemaError as e:
        errors.append(f"Schema error: {e.message}")
    except Exception as e:
        errors.append(f"Validation error: {e}")

    return errors


# Export public API
__all__ = [
    "get_bundled_schema",
    "validate_task_file",
]
