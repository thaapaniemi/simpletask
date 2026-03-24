"""Shared design operations logic for CLI and MCP.

This module provides shared functions for managing design section operations
to avoid code duplication between CLI commands and MCP tools.
"""

from simpletask.core.models import Design, SimpleTaskSpec


def remove_from_design(
    design: Design | None,
    field: str,
    index: int | None = None,
    all_items: bool = False,
) -> tuple[Design | None, str]:
    """Remove a field or list item from a Design object.

    Operates directly on a Design instance without requiring a SimpleTaskSpec
    wrapper. Suitable for both branch task files and project defaults.

    Args:
        design: Design object to modify (may be None)
        field: Field to remove (pattern/patterns, reference/references,
               constraint/constraints, security, error-handling, all)
        index: Index to remove from list fields (0-based), None to remove all
        all_items: If True, remove all items from list field

    Returns:
        Tuple of (updated_design, success_message). updated_design is None
        when field='all' or the entire section is cleared.

    Raises:
        ValueError: If field is invalid, design section missing, or index out of range
    """
    if not design:
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
        return None, "Removed entire design section"

    # Handle error-handling (single value field)
    if field_key == "error-handling":
        if not design.error_handling:
            raise ValueError("No error handling strategy found")
        design.error_handling = None
        return design, "Cleared error handling strategy"

    # Handle list fields
    if field_key == "patterns":
        if not design.patterns:
            raise ValueError("No patterns found")

        if index is not None:
            if 0 <= index < len(design.patterns):
                removed = design.patterns.pop(index)
                return design, f"Removed pattern: {removed.value}"
            else:
                raise ValueError(f"Index {index} out of range (0-{len(design.patterns) - 1})")
        elif all_items or index is None:
            design.patterns = None
            return design, "Cleared all patterns"
        else:
            raise ValueError("Either 'index' or 'all_items=True' is required for pattern removal")

    elif field_key == "references":
        if not design.reference_implementations:
            raise ValueError("No references found")

        if index is not None:
            if 0 <= index < len(design.reference_implementations):
                removed_ref = design.reference_implementations.pop(index)
                return design, f"Removed reference: {removed_ref.path}"
            else:
                raise ValueError(
                    f"Index {index} out of range (0-{len(design.reference_implementations) - 1})"
                )
        elif all_items or index is None:
            design.reference_implementations = None
            return design, "Cleared all references"
        else:
            raise ValueError("Either 'index' or 'all_items=True' is required for reference removal")

    elif field_key == "constraints":
        if not design.architectural_constraints:
            raise ValueError("No constraints found")

        if index is not None:
            if 0 <= index < len(design.architectural_constraints):
                removed_constraint = design.architectural_constraints.pop(index)
                return design, f"Removed constraint: {removed_constraint}"
            else:
                raise ValueError(
                    f"Index {index} out of range (0-{len(design.architectural_constraints) - 1})"
                )
        elif all_items or index is None:
            design.architectural_constraints = None
            return design, "Cleared all constraints"
        else:
            raise ValueError(
                "Either 'index' or 'all_items=True' is required for constraint removal"
            )

    elif field_key == "security":
        if not design.security:
            raise ValueError("No security requirements found")

        if index is not None:
            if 0 <= index < len(design.security):
                removed_security = design.security.pop(index)
                return design, f"Removed security requirement: {removed_security.category.value}"
            else:
                raise ValueError(f"Index {index} out of range (0-{len(design.security) - 1})")
        elif all_items or index is None:
            design.security = None
            return design, "Cleared all security requirements"
        else:
            raise ValueError("Either 'index' or 'all_items=True' is required for security removal")

    # Should never reach here due to field_key validation above
    raise ValueError(f"Unhandled field: {field_key}")


def remove_design_field(
    spec: SimpleTaskSpec,
    field: str,
    index: int | None = None,
    all_items: bool = False,
) -> tuple[SimpleTaskSpec, str]:
    """Remove design field or list items.

    Delegates to remove_from_design, which operates directly on the Design
    object. This wrapper preserves the SimpleTaskSpec-based interface used by
    branch task file operations and CLI commands.

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
    updated_design, message = remove_from_design(
        spec.design, field, index=index, all_items=all_items
    )
    spec.design = updated_design
    return spec, message
