"""Unit tests for constraint_ops module.

Tests cover:
- add_constraint() - Add constraints to the constraints list
- remove_constraint() - Remove constraints by index or all
- list_constraints() - List all constraints
"""

import pytest
from simpletask.core.constraint_ops import add_constraint, list_constraints, remove_constraint
from simpletask.core.yaml_parser import parse_task_file


class TestAddConstraint:
    """Test add_constraint function."""

    def test_add_constraint_to_empty(self, tmp_task_file):
        """Add constraint when constraints field is None."""
        spec = parse_task_file(tmp_task_file)
        spec.constraints = None  # Ensure empty for this test

        spec = add_constraint(spec, value="Use Pydantic models")
        assert spec.constraints == ["Use Pydantic models"]

    def test_add_constraint_to_existing(self, tmp_task_file):
        """Add constraint to existing constraints."""
        spec = parse_task_file(tmp_task_file)
        spec.constraints = ["Existing constraint"]

        spec = add_constraint(spec, value="New constraint")
        assert spec.constraints == ["Existing constraint", "New constraint"]

    def test_add_multiple_constraints(self, tmp_task_file):
        """Add multiple constraints sequentially."""
        spec = parse_task_file(tmp_task_file)
        spec.constraints = None  # Ensure empty for this test

        spec = add_constraint(spec, value="Constraint 1")
        spec = add_constraint(spec, value="Constraint 2")
        spec = add_constraint(spec, value="Constraint 3")

        assert spec.constraints == ["Constraint 1", "Constraint 2", "Constraint 3"]


class TestRemoveConstraint:
    """Test remove_constraint function."""

    def test_remove_constraint_by_index(self, tmp_task_file):
        """Remove constraint by index."""
        spec = parse_task_file(tmp_task_file)
        spec.constraints = ["Constraint 1", "Constraint 2", "Constraint 3"]

        spec = remove_constraint(spec, index=1)
        assert spec.constraints == ["Constraint 1", "Constraint 3"]

    def test_remove_constraint_all(self, tmp_task_file):
        """Remove all constraints."""
        spec = parse_task_file(tmp_task_file)
        spec.constraints = ["Constraint 1", "Constraint 2"]

        spec = remove_constraint(spec, all=True)
        assert spec.constraints is None

    def test_remove_constraint_last_one(self, tmp_task_file):
        """Set constraints to None when removing last constraint."""
        spec = parse_task_file(tmp_task_file)
        spec.constraints = ["Only constraint"]

        spec = remove_constraint(spec, index=0)
        assert spec.constraints is None

    def test_remove_constraint_first(self, tmp_task_file):
        """Remove first constraint."""
        spec = parse_task_file(tmp_task_file)
        spec.constraints = ["First", "Second", "Third"]

        spec = remove_constraint(spec, index=0)
        assert spec.constraints == ["Second", "Third"]

    def test_remove_constraint_invalid_index_negative(self, tmp_task_file):
        """Raise error for negative index."""
        spec = parse_task_file(tmp_task_file)
        spec.constraints = ["Constraint 1"]

        with pytest.raises(ValueError, match="Invalid constraint index: -1"):
            remove_constraint(spec, index=-1)

    def test_remove_constraint_invalid_index_out_of_range(self, tmp_task_file):
        """Raise error for index out of range."""
        spec = parse_task_file(tmp_task_file)
        spec.constraints = ["Constraint 1", "Constraint 2"]

        with pytest.raises(ValueError, match=r"Invalid constraint index: 5.*Valid range: 0-1"):
            remove_constraint(spec, index=5)

    def test_remove_constraint_none_list(self, tmp_task_file):
        """Raise error when constraints is None."""
        spec = parse_task_file(tmp_task_file)
        spec.constraints = None

        with pytest.raises(ValueError, match=r"Invalid constraint index: 0.*No constraints exist"):
            remove_constraint(spec, index=0)

    def test_remove_constraint_requires_index_or_all(self, tmp_task_file):
        """Raise error when neither index nor all is provided."""
        spec = parse_task_file(tmp_task_file)
        spec.constraints = ["Constraint 1"]

        with pytest.raises(ValueError, match="Must provide either index or all=True"):
            remove_constraint(spec)


class TestListConstraints:
    """Test list_constraints function."""

    def test_list_constraints_empty(self, tmp_task_file):
        """List constraints when None."""
        spec = parse_task_file(tmp_task_file)
        spec.constraints = None

        constraints = list_constraints(spec)
        assert constraints is None

    def test_list_constraints_with_constraints(self, tmp_task_file):
        """List constraints with existing constraints."""
        spec = parse_task_file(tmp_task_file)
        spec.constraints = ["Constraint 1", "Constraint 2", "Constraint 3"]

        constraints = list_constraints(spec)
        assert constraints == ["Constraint 1", "Constraint 2", "Constraint 3"]

    def test_list_constraints_single(self, tmp_task_file):
        """List single constraint."""
        spec = parse_task_file(tmp_task_file)
        spec.constraints = ["Only constraint"]

        constraints = list_constraints(spec)
        assert constraints == ["Only constraint"]
