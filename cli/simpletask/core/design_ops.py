"""Shared design operations logic for CLI and MCP.

This module provides shared functions for managing design section operations
to avoid code duplication between CLI commands and MCP tools.
"""

from simpletask.core.models import SimpleTaskSpec


def remove_design_field(
    spec: SimpleTaskSpec,
    field: str,
    index: int | None = None,
    all_items: bool = False,
) -> tuple[SimpleTaskSpec, str]:
    """Remove design field or list items.

    Args:
        spec: Task specification with design section
        field: Field to remove (pattern/patterns, reference/references, constraint/constraints,
               security, error-handling, all)
        index: Index to remove from list fields (0-based), None to remove all
        all_items: If True, remove all items from list field (for MCP explicit all=True)

    Returns:
        Tuple of (updated_spec, success_message)

    Raises:
        ValueError: If field is invalid, design section missing, or index out of range
    """
    if not spec.design:
        raise ValueError("No design section found")

    # Normalize field names (CLI uses plural, MCP uses singular)
    field_normalized = field.lower()
    if field_normalized in ("pattern", "patterns"):
        field_key = "patterns"
    elif field_normalized in ("reference", "references"):
        field_key = "references"
    elif field_normalized in ("constraint", "constraints"):
        field_key = "constraints"
    elif field_normalized == "security":
        field_key = "security"
    elif field_normalized == "error-handling":
        field_key = "error-handling"
    elif field_normalized == "all":
        field_key = "all"
    else:
        raise ValueError(
            f"Invalid field: {field}. "
            "Valid options: pattern/patterns, reference/references, "
            "constraint/constraints, security, error-handling, all"
        )

    # Handle "all" - remove entire design section
    if field_key == "all":
        spec.design = None
        return spec, "Removed entire design section"

    # Handle error-handling (single value field)
    if field_key == "error-handling":
        if not spec.design.error_handling:
            raise ValueError("No error handling strategy found")
        spec.design.error_handling = None
        return spec, "Cleared error handling strategy"

    # Handle list fields
    if field_key == "patterns":
        if not spec.design.patterns:
            raise ValueError("No patterns found")

        if index is not None:
            if 0 <= index < len(spec.design.patterns):
                removed = spec.design.patterns.pop(index)
                return spec, f"Removed pattern: {removed.value}"
            else:
                raise ValueError(f"Index {index} out of range (0-{len(spec.design.patterns) - 1})")
        elif all_items or index is None:
            # For CLI: index=None means clear all
            # For MCP: all_items=True means clear all
            spec.design.patterns = None
            return spec, "Cleared all patterns"
        else:
            raise ValueError("Either 'index' or 'all_items=True' is required for pattern removal")

    elif field_key == "references":
        if not spec.design.reference_implementations:
            raise ValueError("No references found")

        if index is not None:
            if 0 <= index < len(spec.design.reference_implementations):
                removed_ref = spec.design.reference_implementations.pop(index)
                return spec, f"Removed reference: {removed_ref.path}"
            else:
                raise ValueError(
                    f"Index {index} out of range "
                    f"(0-{len(spec.design.reference_implementations) - 1})"
                )
        elif all_items or index is None:
            spec.design.reference_implementations = None
            return spec, "Cleared all references"
        else:
            raise ValueError("Either 'index' or 'all_items=True' is required for reference removal")

    elif field_key == "constraints":
        if not spec.design.architectural_constraints:
            raise ValueError("No constraints found")

        if index is not None:
            if 0 <= index < len(spec.design.architectural_constraints):
                removed_constraint = spec.design.architectural_constraints.pop(index)
                return spec, f"Removed constraint: {removed_constraint}"
            else:
                raise ValueError(
                    f"Index {index} out of range "
                    f"(0-{len(spec.design.architectural_constraints) - 1})"
                )
        elif all_items or index is None:
            spec.design.architectural_constraints = None
            return spec, "Cleared all constraints"
        else:
            raise ValueError(
                "Either 'index' or 'all_items=True' is required for constraint removal"
            )

    elif field_key == "security":
        if not spec.design.security:
            raise ValueError("No security requirements found")

        if index is not None:
            if 0 <= index < len(spec.design.security):
                removed_security = spec.design.security.pop(index)
                return spec, f"Removed security requirement: {removed_security.category.value}"
            else:
                raise ValueError(f"Index {index} out of range (0-{len(spec.design.security) - 1})")
        elif all_items or index is None:
            spec.design.security = None
            return spec, "Cleared all security requirements"
        else:
            raise ValueError("Either 'index' or 'all_items=True' is required for security removal")

    # Should never reach here due to field_key validation above
    raise ValueError(f"Unhandled field: {field_key}")
