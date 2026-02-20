"""Unit tests for criteria_ops module.

Tests cover:
- get_next_criterion_id() - ID generation
- add_acceptance_criterion() - Criterion addition
- mark_criterion_complete() - Update completion status
- remove_acceptance_criterion() - Criterion removal
- update_acceptance_criterion() - Criterion description update
"""

import pytest
from simpletask.core.criteria_ops import (
    add_acceptance_criterion,
    get_next_criterion_id,
    mark_criterion_complete,
    remove_acceptance_criterion,
    update_acceptance_criterion,
)
from simpletask.core.models import AcceptanceCriterion
from simpletask.core.yaml_parser import parse_task_file


class TestGetNextCriterionId:
    """Test get_next_criterion_id function."""

    def test_empty_list(self):
        """Return AC1 for empty criterion list."""
        assert get_next_criterion_id([]) == "AC1"

    def test_sequential_ids(self):
        """Return next sequential ID."""
        criteria = [
            AcceptanceCriterion(id="AC1", description="Test 1"),
            AcceptanceCriterion(id="AC2", description="Test 2"),
            AcceptanceCriterion(id="AC3", description="Test 3"),
        ]
        assert get_next_criterion_id(criteria) == "AC4"

    def test_non_sequential_ids(self):
        """Return max ID + 1 even if IDs are not sequential."""
        criteria = [
            AcceptanceCriterion(id="AC1", description="Test 1"),
            AcceptanceCriterion(id="AC5", description="Test 5"),
            AcceptanceCriterion(id="AC3", description="Test 3"),
        ]
        assert get_next_criterion_id(criteria) == "AC6"


class TestAddAcceptanceCriterion:
    """Test add_acceptance_criterion function."""

    def test_add_criterion_basic(self, tmp_task_file):
        """Add criterion with basic properties."""
        new_id, _ = add_acceptance_criterion(tmp_task_file, description="New criterion")
        assert new_id == "AC3"

        spec = parse_task_file(tmp_task_file)
        assert len(spec.acceptance_criteria) == 3
        assert spec.acceptance_criteria[2].id == "AC3"
        assert spec.acceptance_criteria[2].description == "New criterion"
        assert spec.acceptance_criteria[2].completed is False

    def test_add_multiple_criteria(self, tmp_task_file):
        """Add multiple criteria."""
        id1, _ = add_acceptance_criterion(tmp_task_file, description="Criterion 1")
        id2, _ = add_acceptance_criterion(tmp_task_file, description="Criterion 2")

        assert id1 == "AC3"
        assert id2 == "AC4"

        spec = parse_task_file(tmp_task_file)
        assert len(spec.acceptance_criteria) == 4


class TestMarkCriterionComplete:
    """Test mark_criterion_complete function."""

    def test_mark_complete(self, tmp_task_file):
        """Mark criterion as complete."""
        mark_criterion_complete(tmp_task_file, "AC1", completed=True)

        spec = parse_task_file(tmp_task_file)
        assert spec.acceptance_criteria[0].completed is True

    def test_mark_incomplete(self, tmp_task_file):
        """Mark criterion as incomplete."""
        # First mark complete
        mark_criterion_complete(tmp_task_file, "AC1", completed=True)
        # Then mark incomplete
        mark_criterion_complete(tmp_task_file, "AC1", completed=False)

        spec = parse_task_file(tmp_task_file)
        assert spec.acceptance_criteria[0].completed is False

    def test_default_completed_true(self, tmp_task_file):
        """Default value for completed is True."""
        mark_criterion_complete(tmp_task_file, "AC1")

        spec = parse_task_file(tmp_task_file)
        assert spec.acceptance_criteria[0].completed is True

    def test_mark_criterion_not_found(self, tmp_task_file):
        """Raise ValueError when criterion doesn't exist."""
        with pytest.raises(ValueError, match="Criterion AC999 not found"):
            mark_criterion_complete(tmp_task_file, "AC999")


class TestRemoveAcceptanceCriterion:
    """Test remove_acceptance_criterion function."""

    def test_remove_criterion(self, tmp_task_file):
        """Remove criterion successfully."""
        remove_acceptance_criterion(tmp_task_file, "AC2")

        spec = parse_task_file(tmp_task_file)
        assert len(spec.acceptance_criteria) == 1
        assert spec.acceptance_criteria[0].id == "AC1"

    def test_remove_criterion_not_found(self, tmp_task_file):
        """Raise ValueError when criterion doesn't exist."""
        with pytest.raises(ValueError, match="Criterion AC999 not found"):
            remove_acceptance_criterion(tmp_task_file, "AC999")

    def test_remove_first_criterion(self, tmp_task_file):
        """Remove first criterion from list."""
        remove_acceptance_criterion(tmp_task_file, "AC1")

        spec = parse_task_file(tmp_task_file)
        assert len(spec.acceptance_criteria) == 1
        assert spec.acceptance_criteria[0].id == "AC2"


class TestUpdateAcceptanceCriterion:
    """Test update_acceptance_criterion function."""

    def test_update_description(self, tmp_task_file):
        """Update criterion description successfully."""
        update_acceptance_criterion(tmp_task_file, "AC1", "Updated description")

        spec = parse_task_file(tmp_task_file)
        assert spec.acceptance_criteria[0].description == "Updated description"

    def test_update_preserves_completed_status(self, tmp_task_file):
        """Update preserves the criterion's completed status."""
        mark_criterion_complete(tmp_task_file, "AC1", completed=True)
        update_acceptance_criterion(tmp_task_file, "AC1", "New text")

        spec = parse_task_file(tmp_task_file)
        assert spec.acceptance_criteria[0].description == "New text"
        assert spec.acceptance_criteria[0].completed is True

    def test_update_non_first_criterion(self, tmp_task_file):
        """Update non-first criterion (AC2) to verify next() scan works."""
        original_spec = parse_task_file(tmp_task_file)
        original_ac1_desc = original_spec.acceptance_criteria[0].description

        update_acceptance_criterion(tmp_task_file, "AC2", "Updated AC2 description")

        spec = parse_task_file(tmp_task_file)
        assert spec.acceptance_criteria[1].description == "Updated AC2 description"
        # AC1 should remain unchanged
        assert spec.acceptance_criteria[0].description == original_ac1_desc

    def test_update_criterion_not_found(self, tmp_task_file):
        """Raise ValueError when criterion doesn't exist."""
        with pytest.raises(ValueError, match="Criterion AC999 not found"):
            update_acceptance_criterion(tmp_task_file, "AC999", "New text")
