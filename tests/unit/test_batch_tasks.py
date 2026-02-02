"""Unit tests for batch_tasks function."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from simpletask.core.models import (
    AcceptanceCriterion,
    SimpleTaskSpec,
    Task,
    TaskStatus,
)
from simpletask.core.task_ops import batch_tasks
from simpletask.core.yaml_parser import parse_task_file, write_task_file


@pytest.fixture
def sample_spec_with_tasks() -> SimpleTaskSpec:
    """Create a sample spec with multiple tasks for testing."""
    return SimpleTaskSpec(
        branch="test-batch",
        title="Test Batch Operations",
        original_prompt="Test batch task operations",
        created=datetime.now(UTC),
        acceptance_criteria=[
            AcceptanceCriterion(id="AC1", description="Test criterion", completed=False)
        ],
        tasks=[
            Task(
                id="T001",
                name="Task 1",
                goal="First task",
                status=TaskStatus.NOT_STARTED,
                steps=["Step 1"],
            ),
            Task(
                id="T002",
                name="Task 2",
                goal="Second task",
                status=TaskStatus.NOT_STARTED,
                steps=["Step 1"],
            ),
            Task(
                id="T003",
                name="Task 3",
                goal="Third task",
                status=TaskStatus.NOT_STARTED,
                steps=["Step 1"],
                prerequisites=["T001"],
            ),
        ],
    )


@pytest.fixture
def task_file(tmp_path: Path, sample_spec_with_tasks: SimpleTaskSpec) -> Path:
    """Create a temporary task file for testing."""
    file_path = tmp_path / "test-batch.yml"
    write_task_file(file_path, sample_spec_with_tasks)
    return file_path


class TestBatchAddOperations:
    """Tests for batch add operations."""

    def test_batch_add_single_task(self, task_file: Path):
        """Test adding a single task via batch."""
        operations = [{"op": "add", "name": "New Task", "goal": "New goal", "steps": ["Step 1"]}]

        new_ids = batch_tasks(task_file, operations)

        assert len(new_ids) == 1
        assert new_ids[0] == "T004"

        spec = parse_task_file(task_file)
        assert len(spec.tasks) == 4
        new_task = spec.tasks[-1]
        assert new_task.id == "T004"
        assert new_task.name == "New Task"
        assert new_task.goal == "New goal"
        assert new_task.status == TaskStatus.NOT_STARTED
        assert new_task.steps == ["Step 1"]

    def test_batch_add_multiple_tasks(self, task_file: Path):
        """Test adding multiple tasks in one batch."""
        operations = [
            {"op": "add", "name": "Task A", "goal": "Goal A"},
            {"op": "add", "name": "Task B", "goal": "Goal B"},
            {"op": "add", "name": "Task C", "goal": "Goal C"},
        ]

        new_ids = batch_tasks(task_file, operations)

        assert len(new_ids) == 3
        assert new_ids == ["T004", "T005", "T006"]

        spec = parse_task_file(task_file)
        assert len(spec.tasks) == 6

    def test_batch_add_without_goal_defaults_to_name(self, task_file: Path):
        """Test that goal defaults to name when not provided."""
        operations = [{"op": "add", "name": "Task Name Only"}]

        _new_ids = batch_tasks(task_file, operations)

        spec = parse_task_file(task_file)
        new_task = spec.tasks[-1]
        assert new_task.goal == "Task Name Only"

    def test_batch_add_without_steps_adds_placeholder(self, task_file: Path):
        """Test that steps defaults to placeholder when not provided."""
        operations = [{"op": "add", "name": "Task Without Steps", "goal": "Goal"}]

        batch_tasks(task_file, operations)

        spec = parse_task_file(task_file)
        new_task = spec.tasks[-1]
        assert new_task.steps == ["To be defined"]


class TestBatchRemoveOperations:
    """Tests for batch remove operations."""

    def test_batch_remove_single_task(self, task_file: Path):
        """Test removing a single task via batch."""
        operations = [{"op": "remove", "task_id": "T002"}]

        batch_tasks(task_file, operations)

        spec = parse_task_file(task_file)
        assert len(spec.tasks) == 2
        task_ids = [t.id for t in spec.tasks]
        assert "T002" not in task_ids
        assert "T001" in task_ids
        assert "T003" in task_ids

    def test_batch_remove_multiple_tasks(self, task_file: Path):
        """Test removing multiple tasks in one batch."""
        operations = [
            {"op": "remove", "task_id": "T001"},
            {"op": "remove", "task_id": "T002"},
        ]

        batch_tasks(task_file, operations)

        spec = parse_task_file(task_file)
        assert len(spec.tasks) == 1
        assert spec.tasks[0].id == "T003"

    def test_batch_remove_cleans_prerequisites(self, task_file: Path):
        """Test that removing a task cleans up prerequisite references."""
        # T003 has T001 as prerequisite
        operations = [{"op": "remove", "task_id": "T001"}]

        batch_tasks(task_file, operations)

        spec = parse_task_file(task_file)
        task3 = next(t for t in spec.tasks if t.id == "T003")
        assert task3.prerequisites is None or "T001" not in task3.prerequisites


class TestBatchUpdateOperations:
    """Tests for batch update operations."""

    def test_batch_update_task_status(self, task_file: Path):
        """Test updating task status via batch."""
        operations = [{"op": "update", "task_id": "T001", "status": "completed"}]

        batch_tasks(task_file, operations)

        spec = parse_task_file(task_file)
        task1 = next(t for t in spec.tasks if t.id == "T001")
        assert task1.status == TaskStatus.COMPLETED

    def test_batch_update_task_name_and_goal(self, task_file: Path):
        """Test updating task name and goal via batch."""
        operations = [
            {"op": "update", "task_id": "T002", "name": "Updated Name", "goal": "Updated Goal"}
        ]

        batch_tasks(task_file, operations)

        spec = parse_task_file(task_file)
        task2 = next(t for t in spec.tasks if t.id == "T002")
        assert task2.name == "Updated Name"
        assert task2.goal == "Updated Goal"

    def test_batch_update_multiple_tasks(self, task_file: Path):
        """Test updating multiple tasks in one batch."""
        operations = [
            {"op": "update", "task_id": "T001", "status": "completed"},
            {"op": "update", "task_id": "T002", "status": "in_progress"},
            {"op": "update", "task_id": "T003", "status": "blocked"},
        ]

        batch_tasks(task_file, operations)

        spec = parse_task_file(task_file)
        assert spec.tasks[0].status == TaskStatus.COMPLETED
        assert spec.tasks[1].status == TaskStatus.IN_PROGRESS
        assert spec.tasks[2].status == TaskStatus.BLOCKED


class TestBatchMixedOperations:
    """Tests for mixed batch operations (add+remove+update)."""

    def test_batch_mixed_operations(self, task_file: Path):
        """Test a batch with add, remove, and update operations."""
        operations = [
            {"op": "remove", "task_id": "T002"},
            {"op": "update", "task_id": "T001", "status": "completed"},
            {"op": "add", "name": "New Task", "goal": "Added after remove", "steps": ["Step 1"]},
        ]

        new_ids = batch_tasks(task_file, operations)

        assert len(new_ids) == 1
        assert new_ids[0] == "T004"

        spec = parse_task_file(task_file)
        assert len(spec.tasks) == 3  # Original 3 - 1 removed + 1 added

        # Check remove worked
        task_ids = [t.id for t in spec.tasks]
        assert "T002" not in task_ids

        # Check update worked
        task1 = next(t for t in spec.tasks if t.id == "T001")
        assert task1.status == TaskStatus.COMPLETED

        # Check add worked
        new_task = next(t for t in spec.tasks if t.id == "T004")
        assert new_task.name == "New Task"


class TestBatchAtomicity:
    """Tests for atomicity guarantees."""

    def test_batch_atomicity_invalid_task_id_fails_all(self, task_file: Path):
        """Test that invalid task_id causes entire batch to fail."""
        original_spec = parse_task_file(task_file)
        original_task_count = len(original_spec.tasks)

        operations = [
            {"op": "update", "task_id": "T001", "status": "completed"},
            {"op": "remove", "task_id": "T999"},  # Invalid - doesn't exist
            {"op": "add", "name": "New Task"},
        ]

        with pytest.raises(ValueError, match="task T999 not found"):
            batch_tasks(task_file, operations)

        # Verify no changes were made
        spec = parse_task_file(task_file)
        assert len(spec.tasks) == original_task_count
        assert spec.tasks[0].status == TaskStatus.NOT_STARTED  # T001 not updated
        # No new tasks added
        assert all(t.id in ["T001", "T002", "T003"] for t in spec.tasks)


class TestBatchValidation:
    """Tests for validation error cases."""

    def test_batch_missing_task_id_for_remove(self, task_file: Path):
        """Test that remove without task_id raises error."""
        operations = [{"op": "remove"}]

        with pytest.raises(ValueError, match="task_id required for remove"):
            batch_tasks(task_file, operations)

    def test_batch_missing_name_for_add(self, task_file: Path):
        """Test that add without name raises error."""
        operations = [{"op": "add", "goal": "Goal without name"}]

        with pytest.raises(ValueError, match="name required for add"):
            batch_tasks(task_file, operations)

    def test_batch_invalid_task_id_for_update(self, task_file: Path):
        """Test that update with non-existent task_id raises error."""
        operations = [{"op": "update", "task_id": "T999", "status": "completed"}]

        with pytest.raises(ValueError, match="task T999 not found"):
            batch_tasks(task_file, operations)

    def test_batch_remove_update_conflict(self, task_file: Path):
        """Test that batch with remove+update on same task_id raises error."""
        operations = [
            {"op": "remove", "task_id": "T001"},
            {"op": "update", "task_id": "T001", "status": "completed"},
        ]

        with pytest.raises(
            ValueError, match="Cannot update task T001.*being removed in the same batch"
        ):
            batch_tasks(task_file, operations)

        # Verify atomicity - no changes made
        spec = parse_task_file(task_file)
        assert len(spec.tasks) == 3
        assert any(t.id == "T001" for t in spec.tasks)  # T001 still exists

    def test_batch_invalid_status_value(self, task_file: Path):
        """Test that invalid status value raises error during validation."""
        operations = [{"op": "update", "task_id": "T001", "status": "invalid_status"}]

        with pytest.raises(ValueError, match="Invalid status 'invalid_status'"):
            batch_tasks(task_file, operations)

        # Verify atomicity - no changes made
        spec = parse_task_file(task_file)
        assert spec.tasks[0].status == TaskStatus.NOT_STARTED  # Unchanged
