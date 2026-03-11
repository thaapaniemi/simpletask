"""Integration tests for MCP batch operations."""

import subprocess
from pathlib import Path

import pytest
from simpletask.core.models import TaskStatus
from simpletask.mcp.server import get, new, task


@pytest.fixture
def batch_project(tmp_path: Path, monkeypatch) -> Path:
    """Create a clean git repository for batch testing."""
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "checkout", "-b", "feature/batch-test"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    monkeypatch.chdir(tmp_path)
    return tmp_path


class TestMCPBatchValidOperations:
    """Test MCP batch endpoint with valid operations."""

    def test_batch_add_multiple_tasks(self, batch_project: Path):
        """Test batch adding multiple tasks."""
        # Create task file
        new(
            branch="feature/batch-test",
            title="Batch Test",
            prompt="Test batch operations",
            criteria=["Batch operations work"],
        )

        # Batch add 3 tasks
        result = task(
            action="batch",
            operations=[
                {"op": "add", "name": "Task 1", "goal": "First task"},
                {"op": "add", "name": "Task 2", "goal": "Second task"},
                {"op": "add", "name": "Task 3", "goal": "Third task"},
            ],
        )

        assert result.success is True
        assert result.action == "batch_tasks_applied"
        assert result.new_item_ids == ["T001", "T002", "T003"]
        assert result.summary.overall_status == TaskStatus.NOT_STARTED

        state = get()
        assert state.summary.tasks_total == 3
        assert state.summary.tasks_not_started == 3

    def test_batch_remove_multiple_tasks(self, batch_project: Path):
        """Test batch removing multiple tasks."""
        # Create task file with tasks
        new(
            branch="feature/batch-test",
            title="Batch Test",
            prompt="Test batch operations",
            criteria=["Batch operations work"],
        )
        task(action="add", name="Task 1")
        task(action="add", name="Task 2")
        task(action="add", name="Task 3")

        # Batch remove 2 tasks
        result = task(
            action="batch",
            operations=[
                {"op": "remove", "task_id": "T001"},
                {"op": "remove", "task_id": "T002"},
            ],
        )

        assert result.success is True
        assert result.summary.overall_status == TaskStatus.NOT_STARTED
        assert result.new_item_ids == []

        state = get()
        assert state.summary.tasks_total == 1

    def test_batch_update_multiple_tasks(self, batch_project: Path):
        """Test batch updating multiple tasks."""
        # Create task file with tasks
        new(
            branch="feature/batch-test",
            title="Batch Test",
            prompt="Test batch operations",
            criteria=["Batch operations work"],
        )
        task(action="add", name="Task 1")
        task(action="add", name="Task 2")

        # Batch update both tasks
        result = task(
            action="batch",
            operations=[
                {"op": "update", "task_id": "T001", "status": "in_progress"},
                {"op": "update", "task_id": "T002", "status": "completed"},
            ],
        )

        assert result.success is True
        assert result.summary.overall_status == TaskStatus.IN_PROGRESS
        assert result.new_item_ids == []

        state = get()
        assert state.summary.tasks_in_progress == 1
        assert state.summary.tasks_completed == 1

    def test_batch_mixed_operations(self, batch_project: Path):
        """Test batch with mixed operations (remove, add, update)."""
        # Create task file with tasks
        new(
            branch="feature/batch-test",
            title="Batch Test",
            prompt="Test batch operations",
            criteria=["Batch operations work"],
        )
        task(action="add", name="Task 1")
        task(action="add", name="Task 2")
        task(action="add", name="Task 3")

        # Batch: remove T001, update T002, add two new tasks
        result = task(
            action="batch",
            operations=[
                {"op": "remove", "task_id": "T001"},
                {"op": "update", "task_id": "T002", "status": "completed"},
                {"op": "add", "name": "New Task 1", "goal": "Added in batch"},
                {"op": "add", "name": "New Task 2", "goal": "Also added in batch"},
            ],
        )

        assert result.success is True
        assert result.new_item_ids == ["T004", "T005"]
        assert result.summary.overall_status == TaskStatus.NOT_STARTED

        state = get()
        assert state.summary.tasks_total == 4  # 3 - 1 + 2 = 4
        assert state.summary.tasks_completed == 1
        assert state.summary.tasks_not_started == 3


class TestMCPBatchInvalidOperations:
    """Test MCP batch endpoint with invalid operations (ValidationError handling)."""

    def test_batch_missing_task_id_for_remove(self, batch_project: Path):
        """Test batch fails with ValidationError when task_id missing for remove."""
        # Create task file
        new(
            branch="feature/batch-test",
            title="Batch Test",
            prompt="Test batch operations",
            criteria=["Batch operations work"],
        )

        # Batch with missing task_id for remove
        with pytest.raises(ValueError, match="task_id required for remove"):
            task(
                action="batch",
                operations=[
                    {"op": "remove"},  # Missing task_id
                ],
            )

    def test_batch_missing_name_for_add(self, batch_project: Path):
        """Test batch fails with ValidationError when name missing for add."""
        # Create task file
        new(
            branch="feature/batch-test",
            title="Batch Test",
            prompt="Test batch operations",
            criteria=["Batch operations work"],
        )

        # Batch with missing name for add
        with pytest.raises(ValueError, match="name required for add operation"):
            task(
                action="batch",
                operations=[
                    {"op": "add", "goal": "Missing name"},  # Missing name
                ],
            )

    def test_batch_invalid_task_id(self, batch_project: Path):
        """Test batch fails atomically when any task_id is invalid."""
        # Create task file with one task
        new(
            branch="feature/batch-test",
            title="Batch Test",
            prompt="Test batch operations",
            criteria=["Batch operations work"],
        )
        task(action="add", name="Task 1")

        # Batch with invalid task_id
        with pytest.raises(ValueError, match="task T999 not found"):
            task(
                action="batch",
                operations=[
                    {"op": "update", "task_id": "T999", "status": "completed"},
                ],
            )

        # Verify no changes applied
        result = get()
        assert result.summary.tasks_total == 1
        assert result.summary.tasks_not_started == 1


class TestMCPBatchAtomicity:
    """Test MCP batch endpoint atomicity guarantees."""

    def test_batch_atomicity_all_or_nothing(self, batch_project: Path):
        """Test batch operations are atomic - all succeed or all fail."""
        # Create task file with tasks
        new(
            branch="feature/batch-test",
            title="Batch Test",
            prompt="Test batch operations",
            criteria=["Batch operations work"],
        )
        task(action="add", name="Task 1")
        task(action="add", name="Task 2")

        # Batch with one valid and one invalid operation
        with pytest.raises(ValueError, match="task T999 not found"):
            task(
                action="batch",
                operations=[
                    {"op": "update", "task_id": "T001", "status": "completed"},
                    {"op": "update", "task_id": "T999", "status": "completed"},
                ],
            )

        # Verify neither operation applied
        result = get()
        assert result.summary.tasks_total == 2
        assert result.summary.tasks_not_started == 2
        assert result.summary.tasks_completed == 0

        # Verify T001 is still not_started
        task_result = task(action="get", task_id="T001")
        assert task_result.task.status == TaskStatus.NOT_STARTED


class TestMCPBatchResponseStructure:
    """Test MCP batch response structure."""

    def test_batch_response_structure(self, batch_project: Path):
        """Test batch response has correct structure."""
        # Create task file
        new(
            branch="feature/batch-test",
            title="Batch Test",
            prompt="Test batch operations",
            criteria=["Batch operations work"],
        )

        # Batch operation
        result = task(
            action="batch",
            operations=[
                {"op": "add", "name": "Task 1"},
                {"op": "add", "name": "Task 2"},
            ],
        )

        # Verify response structure
        assert hasattr(result, "success")
        assert hasattr(result, "action")
        assert hasattr(result, "message")
        assert hasattr(result, "file_path")
        assert hasattr(result, "summary")
        assert hasattr(result, "new_item_ids")

        assert isinstance(result.new_item_ids, list)
        assert result.action == "batch_tasks_applied"
        assert result.message == "Applied 2 batch operations"

    def test_batch_response_new_item_ids_only_for_adds(self, batch_project: Path):
        """Test new_item_ids only contains IDs for add operations."""
        # Create task file with tasks
        new(
            branch="feature/batch-test",
            title="Batch Test",
            prompt="Test batch operations",
            criteria=["Batch operations work"],
        )
        task(action="add", name="Task 1")

        # Batch with remove, update, and add
        result = task(
            action="batch",
            operations=[
                {"op": "remove", "task_id": "T001"},
                {"op": "add", "name": "New Task 1"},
                {"op": "add", "name": "New Task 2"},
            ],
        )

        # Only the two add operations should have IDs
        # Note: After removing T001, new tasks use T001 and T002 (IDs are recycled)
        assert len(result.new_item_ids) == 2
        assert result.new_item_ids == ["T001", "T002"]
