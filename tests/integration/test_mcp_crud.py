"""Integration tests for MCP write tools - full CRUD cycles."""

import subprocess
from pathlib import Path

import pytest
from simpletask.core.models import TaskStatus
from simpletask.mcp.server import (
    simpletask_criteria,
    simpletask_get,
    simpletask_new,
    simpletask_task,
)


@pytest.fixture
def crud_project(tmp_path: Path, monkeypatch) -> Path:
    """Create a clean git repository for CRUD testing."""
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
        ["git", "checkout", "-b", "feature/crud-test"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    monkeypatch.chdir(tmp_path)
    return tmp_path


class TestTaskCRUDCycle:
    """Integration tests for full task lifecycle."""

    def test_full_task_lifecycle(self, crud_project: Path):
        """Test complete task lifecycle: create → add → update → remove."""
        # CREATE: Initialize task file
        result = simpletask_new(
            branch="feature/crud-test",
            title="CRUD Test Task",
            prompt="Test CRUD operation",
            criteria=["Must be testable"],
        )
        assert result.summary.branch == "feature/crud-test"
        assert result.summary.title == "CRUD Test Task"
        assert result.summary.criteria_total == 1
        assert result.summary.tasks_total == 0

        # ADD: Add first task
        result = simpletask_task(
            action="add",
            branch="feature/crud-test",
            name="First task",
        )
        assert result.summary.tasks_total == 1
        assert result.summary.tasks_not_started == 1
        task_t001 = next(t for t in result.spec.tasks if t.id == "T001")
        assert task_t001.name == "First task"
        assert task_t001.status == TaskStatus.NOT_STARTED

        # ADD: Add second task with goal
        result = simpletask_task(
            action="add",
            branch="feature/crud-test",
            name="Second task",
            goal="Complete this task",
        )
        assert result.summary.tasks_total == 2
        assert result.summary.tasks_not_started == 2

        # UPDATE: Mark first task as in_progress
        result = simpletask_task(
            action="update",
            branch="feature/crud-test",
            task_id="T001",
            status="in_progress",
        )
        assert result.summary.tasks_in_progress == 1
        assert result.summary.tasks_not_started == 1
        task_t001 = next(t for t in result.spec.tasks if t.id == "T001")
        assert task_t001.status == TaskStatus.IN_PROGRESS

        # UPDATE: Mark first task as completed
        result = simpletask_task(
            action="update",
            branch="feature/crud-test",
            task_id="T001",
            status="completed",
        )
        assert result.summary.tasks_completed == 1
        assert result.summary.tasks_in_progress == 0
        assert result.summary.tasks_not_started == 1
        task_t001 = next(t for t in result.spec.tasks if t.id == "T001")
        assert task_t001.status == TaskStatus.COMPLETED

        # UPDATE: Change name of second task
        result = simpletask_task(
            action="update",
            branch="feature/crud-test",
            task_id="T002",
            name="Updated second task name",
        )
        task_t002 = next(t for t in result.spec.tasks if t.id == "T002")
        assert task_t002.name == "Updated second task name"
        assert task_t002.status == TaskStatus.NOT_STARTED  # Status unchanged

        # REMOVE: Remove completed task
        result = simpletask_task(
            action="remove",
            branch="feature/crud-test",
            task_id="T001",
        )
        assert result.summary.tasks_total == 1
        assert result.summary.tasks_completed == 0
        assert result.summary.tasks_not_started == 1
        assert len(result.spec.tasks) == 1
        assert result.spec.tasks[0].id == "T002"

        # VERIFY: Final state via simpletask_get
        result = simpletask_get(branch="feature/crud-test")
        assert result.summary.tasks_total == 1
        assert len(result.spec.tasks) == 1
        assert result.spec.tasks[0].id == "T002"
        assert result.spec.tasks[0].name == "Updated second task name"


class TestCriteriaCRUDCycle:
    """Integration tests for full acceptance criteria lifecycle."""

    def test_full_criteria_lifecycle(self, crud_project: Path):
        """Test complete criteria lifecycle: create → add → complete → remove."""
        # CREATE: Initialize task file with one criterion
        result = simpletask_new(
            branch="feature/crud-test",
            title="Criteria CRUD Test",
            prompt="Test CRUD operation",
            criteria=["Initial criterion"],
        )
        assert result.summary.criteria_total == 1
        assert result.summary.criteria_completed == 0
        ac1 = result.spec.acceptance_criteria[0]
        assert ac1.id == "AC1"
        assert ac1.description == "Initial criterion"
        assert ac1.completed is False

        # ADD: Add second criterion
        result = simpletask_criteria(
            action="add",
            branch="feature/crud-test",
            description="Second criterion",
        )
        assert result.summary.criteria_total == 2
        assert result.summary.criteria_completed == 0
        ac2 = next(c for c in result.spec.acceptance_criteria if c.id == "AC2")
        assert ac2.description == "Second criterion"
        assert ac2.completed is False

        # ADD: Add third criterion
        result = simpletask_criteria(
            action="add",
            branch="feature/crud-test",
            description="Third criterion",
        )
        assert result.summary.criteria_total == 3
        ac3 = next(c for c in result.spec.acceptance_criteria if c.id == "AC3")
        assert ac3.description == "Third criterion"

        # COMPLETE: Mark first criterion as completed
        result = simpletask_criteria(
            action="complete",
            branch="feature/crud-test",
            criterion_id="AC1",
            completed=True,
        )
        assert result.summary.criteria_completed == 1
        ac1 = next(c for c in result.spec.acceptance_criteria if c.id == "AC1")
        assert ac1.completed is True

        # COMPLETE: Mark second criterion as completed
        result = simpletask_criteria(
            action="complete",
            branch="feature/crud-test",
            criterion_id="AC2",
            completed=True,
        )
        assert result.summary.criteria_completed == 2
        ac2 = next(c for c in result.spec.acceptance_criteria if c.id == "AC2")
        assert ac2.completed is True

        # COMPLETE: Mark first criterion as incomplete again
        result = simpletask_criteria(
            action="complete",
            branch="feature/crud-test",
            criterion_id="AC1",
            completed=False,
        )
        assert result.summary.criteria_completed == 1
        ac1 = next(c for c in result.spec.acceptance_criteria if c.id == "AC1")
        assert ac1.completed is False

        # REMOVE: Remove uncompleted first criterion
        result = simpletask_criteria(
            action="remove",
            branch="feature/crud-test",
            criterion_id="AC1",
        )
        assert result.summary.criteria_total == 2
        assert result.summary.criteria_completed == 1
        assert len(result.spec.acceptance_criteria) == 2
        # AC2 and AC3 should remain, IDs unchanged
        assert result.spec.acceptance_criteria[0].id == "AC2"
        assert result.spec.acceptance_criteria[1].id == "AC3"

        # REMOVE: Remove completed second criterion (now first in list)
        result = simpletask_criteria(
            action="remove",
            branch="feature/crud-test",
            criterion_id="AC2",
        )
        assert result.summary.criteria_total == 1
        assert result.summary.criteria_completed == 0
        assert len(result.spec.acceptance_criteria) == 1
        assert result.spec.acceptance_criteria[0].id == "AC3"

        # VERIFY: Last state before attempted invalid operation
        result = simpletask_get(branch="feature/crud-test")
        assert result.summary.criteria_total == 1
        assert len(result.spec.acceptance_criteria) == 1
        assert result.spec.acceptance_criteria[0].id == "AC3"
        assert result.spec.acceptance_criteria[0].description == "Third criterion"
        assert result.spec.acceptance_criteria[0].completed is False

        # VERIFY: Cannot remove last criterion (schema constraint)
        with pytest.raises(Exception):  # InvalidTaskFileError or ValidationError
            simpletask_criteria(
                action="remove",
                branch="feature/crud-test",
                criterion_id="AC3",
            )


class TestMixedCRUDOperations:
    """Integration tests for mixed task and criteria operations."""

    def test_mixed_operations_update_summary(self, crud_project: Path):
        """Test that summary updates correctly across mixed operations."""
        # CREATE: Initialize with multiple criteria
        result = simpletask_new(
            branch="feature/crud-test",
            title="Mixed Operations Test",
            prompt="Test CRUD operation",
            criteria=["Criterion 1", "Criterion 2", "Criterion 3"],
        )
        assert result.summary.criteria_total == 3
        assert result.summary.tasks_total == 0

        # Add tasks
        simpletask_task(
            action="add",
            branch="feature/crud-test",
            name="Task 1",
        )
        simpletask_task(
            action="add",
            branch="feature/crud-test",
            name="Task 2",
        )
        result = simpletask_task(
            action="add",
            branch="feature/crud-test",
            name="Task 3",
        )
        assert result.summary.tasks_total == 3
        assert result.summary.tasks_not_started == 3

        # Update task statuses to different states
        simpletask_task(
            action="update",
            branch="feature/crud-test",
            task_id="T001",
            status="in_progress",
        )
        simpletask_task(
            action="update",
            branch="feature/crud-test",
            task_id="T002",
            status="completed",
        )
        result = simpletask_task(
            action="update",
            branch="feature/crud-test",
            task_id="T003",
            status="blocked",
        )
        assert result.summary.tasks_in_progress == 1
        assert result.summary.tasks_completed == 1
        assert result.summary.tasks_blocked == 1
        assert result.summary.tasks_not_started == 0

        # Complete some criteria
        simpletask_criteria(
            action="complete",
            branch="feature/crud-test",
            criterion_id="AC1",
            completed=True,
        )
        result = simpletask_criteria(
            action="complete",
            branch="feature/crud-test",
            criterion_id="AC3",
            completed=True,
        )
        assert result.summary.criteria_completed == 2

        # VERIFY: Final comprehensive state
        result = simpletask_get(branch="feature/crud-test")
        assert result.summary.criteria_total == 3
        assert result.summary.criteria_completed == 2
        assert result.summary.tasks_total == 3
        assert result.summary.tasks_completed == 1
        assert result.summary.tasks_in_progress == 1
        assert result.summary.tasks_not_started == 0
        assert result.summary.tasks_blocked == 1
