"""Constraint operations for simpletask.

This module provides CRUD operations for implementation constraints.
"""

from .models import SimpleTaskSpec


def add_constraint(
    spec: SimpleTaskSpec,
    value: str,
) -> SimpleTaskSpec:
    """Add a constraint to the constraints list.

    Args:
        spec: The task specification to modify
        value: The constraint text to add

    Returns:
        Modified SimpleTaskSpec with the constraint added
    """
    if spec.constraints is None:
        spec.constraints = []
    spec.constraints.append(value)
    return spec


def remove_constraint(
    spec: SimpleTaskSpec,
    index: int | None = None,
    all: bool = False,
) -> SimpleTaskSpec:
    """Remove constraints from the list.

    Args:
        spec: The task specification to modify
        index: Optional index of constraint to remove (0-based)
        all: If True, removes all constraints

    Returns:
        Modified SimpleTaskSpec with constraint(s) removed

    Raises:
        ValueError: If index is invalid or if neither index nor all is provided
    """
    if all:
        spec.constraints = None
    elif index is not None:
        if spec.constraints is None or index < 0 or index >= len(spec.constraints):
            if spec.constraints is None:
                raise ValueError(f"Invalid constraint index: {index}. No constraints exist.")
            raise ValueError(
                f"Invalid constraint index: {index}. Valid range: 0-{len(spec.constraints) - 1}"
            )
        spec.constraints.pop(index)
        # Set to None if empty
        if not spec.constraints:
            spec.constraints = None
    else:
        raise ValueError("Must provide either index or all=True")

    return spec


def list_constraints(
    spec: SimpleTaskSpec,
) -> list[str] | None:
    """List all constraints.

    Args:
        spec: The task specification to read from

    Returns:
        List of constraint strings or None if no constraints exist
    """
    return spec.constraints
