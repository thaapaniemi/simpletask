"""Context operations for simpletask.

This module provides CRUD operations for context key-value pairs.
"""

from typing import Any

from .models import SimpleTaskSpec


def set_context(
    spec: SimpleTaskSpec,
    key: str,
    value: Any,
) -> SimpleTaskSpec:
    """Set a context key-value pair.

    Args:
        spec: The task specification to modify
        key: The context key to set
        value: The value to associate with the key

    Returns:
        Modified SimpleTaskSpec with the context value set
    """
    if spec.context is None:
        spec.context = {}
    spec.context[key] = value
    return spec


def remove_context(
    spec: SimpleTaskSpec,
    key: str | None = None,
    all: bool = False,
) -> SimpleTaskSpec:
    """Remove context key-value pairs.

    Args:
        spec: The task specification to modify
        key: Optional key to remove
        all: If True, removes all context entries

    Returns:
        Modified SimpleTaskSpec with context entry/entries removed

    Raises:
        ValueError: If key is invalid or if neither key nor all is provided
    """
    if all:
        spec.context = None
    elif key is not None:
        if spec.context is None:
            raise ValueError(f"Context key '{key}' not found. No context exists.")
        if key not in spec.context:
            raise ValueError(f"Context key '{key}' not found")
        del spec.context[key]
        # Set to None if empty
        if not spec.context:
            spec.context = None
    else:
        raise ValueError("Must provide either key or all=True")

    return spec


def show_context(
    spec: SimpleTaskSpec,
) -> dict[str, Any] | None:
    """Show all context key-value pairs.

    Args:
        spec: The task specification to read from

    Returns:
        Dictionary of context key-value pairs or None if no context exists
    """
    return spec.context
