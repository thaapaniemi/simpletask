"""Repair operations for broken task files.

This module provides functionality to automatically repair task files
that have schema violations or invalid fields.
"""

from pathlib import Path

from .models import SimpleTaskSpec
from .task_file_ops import DEFAULT_CRITERION_DESCRIPTION
from .yaml_parser import parse_task_file_lenient


def repair_task_file(file_path: Path) -> SimpleTaskSpec:
    """Repair a broken task file by fixing schema violations.

    This function:
    1. Strips unknown root-level fields (e.g., status, updated)
    2. Fixes empty acceptance_criteria arrays by adding default criterion
    3. Returns the repaired spec (does NOT write to disk)

    The calling function is responsible for writing the repaired spec
    after making its own modifications, avoiding double-write.

    Used automatically by MCP operations when validation errors are detected.

    Args:
        file_path: Path to task YAML file

    Returns:
        Validated and repaired SimpleTaskSpec (not yet written to disk)

    Raises:
        FileNotFoundError: If file doesn't exist
        InvalidTaskFileError: If YAML syntax is invalid (not fixable)
    """
    # Load raw YAML without validation
    data = parse_task_file_lenient(file_path)

    # Get valid field names from SimpleTaskSpec model
    valid_fields = set(SimpleTaskSpec.model_fields.keys())

    # Strip unknown root-level fields
    cleaned_data = {k: v for k, v in data.items() if k in valid_fields}

    # Fix empty acceptance_criteria
    # Handle three cases explicitly:
    # 1. Missing field (key not in dict)
    # 2. Explicit null/None value
    # 3. Empty array []
    criteria = cleaned_data.get("acceptance_criteria")
    if criteria is None or (isinstance(criteria, list) and len(criteria) == 0):
        cleaned_data["acceptance_criteria"] = [
            {
                "id": "AC1",
                "description": DEFAULT_CRITERION_DESCRIPTION,
                "completed": False,
            }
        ]

    # Validate cleaned data and return (caller will write)
    spec = SimpleTaskSpec.model_validate(cleaned_data)

    return spec
