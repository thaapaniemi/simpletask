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
        operations = [
            {"action": "add", "name": "New Task", "goal": "New goal", "steps": ["Step 1"]}
        ]

        new_ids, _ = batch_tasks(task_file, operations)

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
            {"action": "add", "name": "Task A", "goal": "Goal A"},
            {"action": "add", "name": "Task B", "goal": "Goal B"},
            {"action": "add", "name": "Task C", "goal": "Goal C"},
        ]

        new_ids, _ = batch_tasks(task_file, operations)

        assert len(new_ids) == 3
        assert new_ids == ["T004", "T005", "T006"]

        spec = parse_task_file(task_file)
        assert len(spec.tasks) == 6

    def test_batch_add_without_goal_defaults_to_name(self, task_file: Path):
        """Test that goal defaults to name when not provided."""
        operations = [{"action": "add", "name": "Task Name Only"}]

        new_ids, _ = batch_tasks(task_file, operations)

        assert len(new_ids) == 1
        spec = parse_task_file(task_file)
        new_task = spec.tasks[-1]
        assert new_task.goal == "Task Name Only"

    def test_batch_add_without_steps_adds_placeholder(self, task_file: Path):
        """Test that steps defaults to placeholder when not provided."""
        operations = [{"action": "add", "name": "Task Without Steps", "goal": "Goal"}]

        batch_tasks(task_file, operations)

        spec = parse_task_file(task_file)
        new_task = spec.tasks[-1]
        assert new_task.steps == ["To be defined"]


class TestBatchRemoveOperations:
    """Tests for batch remove operations."""

    def test_batch_remove_single_task(self, task_file: Path):
        """Test removing a single task via batch."""
        operations = [{"action": "remove", "task_id": "T002"}]

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
            {"action": "remove", "task_id": "T001"},
            {"action": "remove", "task_id": "T002"},
        ]

        batch_tasks(task_file, operations)

        spec = parse_task_file(task_file)
        assert len(spec.tasks) == 1
        assert spec.tasks[0].id == "T003"

    def test_batch_remove_cleans_prerequisites(self, task_file: Path):
        """Test that removing a task cleans up prerequisite references."""
        # T003 has T001 as prerequisite
        operations = [{"action": "remove", "task_id": "T001"}]

        batch_tasks(task_file, operations)

        spec = parse_task_file(task_file)
        task3 = next(t for t in spec.tasks if t.id == "T003")
        assert task3.prerequisites is None or "T001" not in task3.prerequisites


class TestBatchUpdateOperations:
    """Tests for batch update operations."""

    def test_batch_update_task_status(self, task_file: Path):
        """Test updating task status via batch."""
        operations = [{"action": "update", "task_id": "T001", "status": "completed"}]

        batch_tasks(task_file, operations)

        spec = parse_task_file(task_file)
        task1 = next(t for t in spec.tasks if t.id == "T001")
        assert task1.status == TaskStatus.COMPLETED

    def test_batch_update_task_name_and_goal(self, task_file: Path):
        """Test updating task name and goal via batch."""
        operations = [
            {"action": "update", "task_id": "T002", "name": "Updated Name", "goal": "Updated Goal"}
        ]

        batch_tasks(task_file, operations)

        spec = parse_task_file(task_file)
        task2 = next(t for t in spec.tasks if t.id == "T002")
        assert task2.name == "Updated Name"
        assert task2.goal == "Updated Goal"

    def test_batch_update_multiple_tasks(self, task_file: Path):
        """Test updating multiple tasks in one batch."""
        operations = [
            {"action": "update", "task_id": "T001", "status": "completed"},
            {"action": "update", "task_id": "T002", "status": "in_progress"},
            {"action": "update", "task_id": "T003", "status": "blocked"},
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
            {"action": "remove", "task_id": "T002"},
            {"action": "update", "task_id": "T001", "status": "completed"},
            {
                "action": "add",
                "name": "New Task",
                "goal": "Added after remove",
                "steps": ["Step 1"],
            },
        ]

        new_ids, _ = batch_tasks(task_file, operations)

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
            {"action": "update", "task_id": "T001", "status": "completed"},
            {"action": "remove", "task_id": "T999"},  # Invalid - doesn't exist
            {"action": "add", "name": "New Task"},
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
        operations = [{"action": "remove"}]

        with pytest.raises(ValueError, match="task_id is required for remove"):
            batch_tasks(task_file, operations)

    def test_batch_missing_name_for_add(self, task_file: Path):
        """Test that add without name raises error."""
        operations = [{"action": "add", "goal": "Goal without name"}]

        with pytest.raises(ValueError, match="name is required for add"):
            batch_tasks(task_file, operations)

    def test_batch_invalid_task_id_for_update(self, task_file: Path):
        """Test that update with non-existent task_id raises error."""
        operations = [{"action": "update", "task_id": "T999", "status": "completed"}]

        with pytest.raises(ValueError, match="task T999 not found"):
            batch_tasks(task_file, operations)

    def test_batch_remove_update_conflict(self, task_file: Path):
        """Test that batch with remove+update on same task_id raises error."""
        operations = [
            {"action": "remove", "task_id": "T001"},
            {"action": "update", "task_id": "T001", "status": "completed"},
        ]

        with pytest.raises(
            ValueError, match=r"Cannot update task T001.*being removed in the same batch"
        ):
            batch_tasks(task_file, operations)

        # Verify atomicity - no changes made
        spec = parse_task_file(task_file)
        assert len(spec.tasks) == 3
        assert any(t.id == "T001" for t in spec.tasks)  # T001 still exists

    def test_batch_invalid_status_value(self, task_file: Path):
        """Test that invalid status value raises error during validation."""
        operations = [{"action": "update", "task_id": "T001", "status": "invalid_status"}]

        with pytest.raises(ValueError, match="Invalid status 'invalid_status'"):
            batch_tasks(task_file, operations)

        # Verify atomicity - no changes made
        spec = parse_task_file(task_file)
        assert spec.tasks[0].status == TaskStatus.NOT_STARTED  # Unchanged

    def test_batch_unknown_action_key_raises_value_error(self, task_file: Path):
        """Test that an unknown action key raises ValueError, not a silent no-op.

        Regression test for AC6: passing the old 'op' key (or any unknown key)
        must raise ValueError — not silently skip the operation.
        """
        operations = [{"op": "remove", "task_id": "T001"}]

        with pytest.raises(ValueError):
            batch_tasks(task_file, operations)

        # Verify no changes were made (atomicity preserved)
        spec = parse_task_file(task_file)
        assert len(spec.tasks) == 3
        assert any(t.id == "T001" for t in spec.tasks)

    def test_batch_none_action_raises_value_error(self, task_file: Path):
        """Test that a None/missing action value raises ValueError."""
        operations = [{"task_id": "T001"}]

        with pytest.raises(ValueError):
            batch_tasks(task_file, operations)


class TestBatchForwardPrerequisites:
    """Tests for intra-batch forward prerequisite reference resolution (AC7)."""

    def test_batch_forward_prereq_reference_succeeds(self, task_file: Path):
        """An add op can reference a task ID created by a later add op in the same batch.

        Previously, prerequisite validation only saw IDs already added in the batch,
        so forward references silently failed. Now IDs are pre-allocated before validation.
        """
        # T004 references T005 which is added later in the same batch
        operations = [
            {"action": "add", "name": "Task A", "goal": "First", "prerequisites": ["T005"]},
            {"action": "add", "name": "Task B", "goal": "Second"},
        ]

        new_ids, _ = batch_tasks(task_file, operations)

        assert len(new_ids) == 2
        assert new_ids[0] == "T004"
        assert new_ids[1] == "T005"

        spec = parse_task_file(task_file)
        task_a = next(t for t in spec.tasks if t.name == "Task A")
        assert task_a.prerequisites == ["T005"]

    def test_batch_invalid_prereq_still_raises(self, task_file: Path):
        """An add op with a prerequisite for a nonexistent task still raises."""
        operations = [
            {"action": "add", "name": "Task X", "prerequisites": ["T999"]},
        ]

        with pytest.raises(ValueError, match="Invalid prerequisite 'T999'"):
            batch_tasks(task_file, operations)


class TestGetNextTaskId:
    """Unit tests for get_next_task_id() — explicit contract for ID generation behavior."""

    def test_empty_list_returns_t001(self):
        """Given no tasks, get_next_task_id returns T001."""
        from simpletask.core.task_ops import get_next_task_id

        result = get_next_task_id([])
        assert result == "T001"

    def test_sequential_tasks_returns_next(self):
        """Given T001 and T002, returns T003."""
        from simpletask.core.task_ops import get_next_task_id

        tasks = [
            Task(id="T001", name="T1", goal="g", steps=["s"], status=TaskStatus.NOT_STARTED),
            Task(id="T002", name="T2", goal="g", steps=["s"], status=TaskStatus.NOT_STARTED),
        ]
        assert get_next_task_id(tasks) == "T003"

    def test_after_removals_continues_from_max_no_recycling(self, task_file: Path):
        """After removing T001 and T002, next ID is T004 (max+1), not T001 (no recycling)."""
        from simpletask.core.task_ops import get_next_task_id

        # Remove T001 and T002 — only T003 remains
        batch_tasks(
            task_file,
            [
                {"action": "remove", "task_id": "T001"},
                {"action": "remove", "task_id": "T002"},
            ],
        )

        from simpletask.core.yaml_parser import parse_task_file as _parse

        spec = _parse(task_file)
        assert len(spec.tasks) == 1
        assert spec.tasks[0].id == "T003"

        # Next ID must be T004, not T001 (no ID recycling)
        next_id = get_next_task_id(spec.tasks)
        assert next_id == "T004"

    """Tests for iteration field handling in batch_tasks."""

    @pytest.fixture
    def spec_with_iteration(self) -> SimpleTaskSpec:
        """Create a sample spec that includes an iteration."""
        from datetime import UTC, datetime

        from simpletask.core.models import Iteration

        return SimpleTaskSpec(
            branch="test-batch-iter",
            title="Test Batch Iteration",
            original_prompt="Test batch with iterations",
            created=datetime.now(UTC),
            acceptance_criteria=[
                AcceptanceCriterion(id="AC1", description="Criterion", completed=False)
            ],
            tasks=[
                Task(
                    id="T001",
                    name="Task 1",
                    goal="First task",
                    status=TaskStatus.NOT_STARTED,
                    steps=["Step 1"],
                ),
            ],
            iterations=[
                Iteration(id=1, label="Sprint 1", created=datetime.now(UTC)),
            ],
        )

    @pytest.fixture
    def iter_task_file(self, tmp_path: Path, spec_with_iteration: SimpleTaskSpec) -> Path:
        """Write spec_with_iteration to a temp file."""
        task_file = tmp_path / "test-batch-iter.yml"
        write_task_file(task_file, spec_with_iteration)
        return task_file

    def test_batch_add_with_iteration_assigns_field(self, iter_task_file: Path) -> None:
        """Batch add operation sets iteration field on new task."""
        operations = [
            {"action": "add", "name": "New Task", "goal": "Goal", "steps": ["S"], "iteration": 1},
        ]
        batch_tasks(iter_task_file, operations)
        spec = parse_task_file(iter_task_file)
        new_task = next(t for t in spec.tasks if t.name == "New Task")
        assert new_task.iteration == 1

    def test_batch_update_assigns_iteration(self, iter_task_file: Path) -> None:
        """Batch update operation assigns a task to an iteration."""
        operations = [{"action": "update", "task_id": "T001", "iteration": 1}]
        batch_tasks(iter_task_file, operations)
        spec = parse_task_file(iter_task_file)
        t001 = next(t for t in spec.tasks if t.id == "T001")
        assert t001.iteration == 1

    def test_batch_update_unassigns_iteration(self, iter_task_file: Path) -> None:
        """Batch update with iteration=None unassigns a task from its iteration."""
        # First assign
        batch_tasks(iter_task_file, [{"action": "update", "task_id": "T001", "iteration": 1}])
        # Then unassign
        batch_tasks(iter_task_file, [{"action": "update", "task_id": "T001", "iteration": None}])
        spec = parse_task_file(iter_task_file)
        t001 = next(t for t in spec.tasks if t.id == "T001")
        assert t001.iteration is None

    def test_batch_update_without_iteration_key_leaves_assignment_unchanged(
        self, iter_task_file: Path
    ) -> None:
        """Batch update that omits the iteration key does not change the iteration assignment."""
        # Assign iteration first
        batch_tasks(iter_task_file, [{"action": "update", "task_id": "T001", "iteration": 1}])
        # Update something else without touching iteration
        batch_tasks(
            iter_task_file, [{"action": "update", "task_id": "T001", "status": "completed"}]
        )
        spec = parse_task_file(iter_task_file)
        t001 = next(t for t in spec.tasks if t.id == "T001")
        assert t001.iteration == 1  # Unchanged
