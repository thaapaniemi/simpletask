"""Integration tests for MCP write tools - full CRUD cycles."""

import subprocess
from pathlib import Path

import pytest
from simpletask.core.models import TaskStatus
from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.mcp.server import (
    criteria,
    get,
    new,
    task,
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
        result = new(
            branch="feature/crud-test",
            title="CRUD Test Task",
            prompt="Test CRUD operation",
            criteria=["Must be testable"],
        )
        assert result.summary.branch == "feature/crud-test"
        assert result.summary.title == "CRUD Test Task"
        assert result.summary.overall_status == TaskStatus.NOT_STARTED

        # ADD: Add first task
        result = task(
            action="add",
            name="First task",
        )
        assert result.summary.overall_status == TaskStatus.NOT_STARTED
        # Get task details using action='get'
        task_result = task(
            action="get",
            task_id="T001",
        )
        task_t001 = task_result.task
        assert task_t001.name == "First task"
        assert task_t001.status == TaskStatus.NOT_STARTED

        # ADD: Add second task with goal
        result = task(
            action="add",
            name="Second task",
            goal="Complete this task",
        )
        assert result.summary.overall_status == TaskStatus.NOT_STARTED

        # UPDATE: Mark first task as in_progress
        result = task(
            action="update",
            task_id="T001",
            status="in_progress",
        )
        assert result.summary.overall_status == TaskStatus.IN_PROGRESS
        # Get task details using action='get'
        task_result = task(
            action="get",
            task_id="T001",
        )
        assert task_result.task.status == TaskStatus.IN_PROGRESS

        # UPDATE: Mark first task as completed
        result = task(
            action="update",
            task_id="T001",
            status="completed",
        )
        assert result.summary.overall_status == TaskStatus.NOT_STARTED
        # Get task details using action='get'
        task_result = task(
            action="get",
            task_id="T001",
        )
        assert task_result.task.status == TaskStatus.COMPLETED

        # UPDATE: Change name of second task
        result = task(
            action="update",
            task_id="T002",
            name="Updated second task name",
        )
        # Get task details using action='get'
        task_result = task(
            action="get",
            task_id="T002",
        )
        task_t002 = task_result.task
        assert task_t002.name == "Updated second task name"
        assert task_t002.status == TaskStatus.NOT_STARTED  # Status unchanged

        # REMOVE: Remove completed task
        result = task(
            action="remove",
            task_id="T001",
        )
        assert result.summary.overall_status == TaskStatus.NOT_STARTED
        # Verify using get to check task list
        get_result = get()
        assert len(get_result.spec.tasks) == 1
        assert get_result.spec.tasks[0].id == "T002"

        # VERIFY: Final state via get
        result = get()
        assert result.summary.tasks_total == 1
        assert len(result.spec.tasks) == 1
        assert result.spec.tasks[0].id == "T002"
        assert result.spec.tasks[0].name == "Updated second task name"


class TestCriteriaCRUDCycle:
    """Integration tests for full acceptance criteria lifecycle."""

    def test_full_criteria_lifecycle(self, crud_project: Path):
        """Test complete criteria lifecycle: create → add → complete → remove."""
        # CREATE: Initialize task file with one criterion
        result = new(
            branch="feature/crud-test",
            title="Criteria CRUD Test",
            prompt="Test CRUD operation",
            criteria=["Initial criterion"],
        )
        assert result.summary.overall_status == TaskStatus.NOT_STARTED
        # Get criterion details using action='get'
        criterion_result = criteria(
            action="get",
            criterion_id="AC1",
        )
        ac1 = criterion_result.criterion
        assert ac1.id == "AC1"
        assert ac1.description == "Initial criterion"
        assert ac1.completed is False

        # ADD: Add second criterion
        result = criteria(
            action="add",
            description="Second criterion",
        )
        assert result.summary.overall_status == TaskStatus.NOT_STARTED
        # Get criterion details using action='get'
        criterion_result = criteria(
            action="get",
            criterion_id="AC2",
        )
        ac2 = criterion_result.criterion
        assert ac2.description == "Second criterion"
        assert ac2.completed is False

        # ADD: Add third criterion
        result = criteria(
            action="add",
            description="Third criterion",
        )
        assert result.summary.overall_status == TaskStatus.NOT_STARTED
        # Get criterion details using action='get'
        criterion_result = criteria(
            action="get",
            criterion_id="AC3",
        )
        assert criterion_result.criterion.description == "Third criterion"

        # COMPLETE: Mark first criterion as completed
        result = criteria(
            action="complete",
            criterion_id="AC1",
            completed=True,
        )
        assert result.summary.overall_status == TaskStatus.NOT_STARTED
        # Get criterion details using action='get'
        criterion_result = criteria(
            action="get",
            criterion_id="AC1",
        )
        assert criterion_result.criterion.completed is True

        # COMPLETE: Mark second criterion as completed
        result = criteria(
            action="complete",
            criterion_id="AC2",
            completed=True,
        )
        assert result.summary.overall_status == TaskStatus.NOT_STARTED
        # Get criterion details using action='get'
        criterion_result = criteria(
            action="get",
            criterion_id="AC2",
        )
        assert criterion_result.criterion.completed is True

        # COMPLETE: Mark first criterion as incomplete again
        result = criteria(
            action="complete",
            criterion_id="AC1",
            completed=False,
        )
        assert result.summary.overall_status == TaskStatus.NOT_STARTED
        # Get criterion details using action='get'
        criterion_result = criteria(
            action="get",
            criterion_id="AC1",
        )
        assert criterion_result.criterion.completed is False

        # REMOVE: Remove uncompleted first criterion
        result = criteria(
            action="remove",
            criterion_id="AC1",
        )
        assert result.summary.overall_status == TaskStatus.NOT_STARTED
        # Verify using get to check criteria list
        get_result = get()
        assert len(get_result.spec.acceptance_criteria) == 2
        # AC2 and AC3 should remain, IDs unchanged
        assert get_result.spec.acceptance_criteria[0].id == "AC2"
        assert get_result.spec.acceptance_criteria[1].id == "AC3"

        # REMOVE: Remove completed second criterion (now first in list)
        result = criteria(
            action="remove",
            criterion_id="AC2",
        )
        assert result.summary.overall_status == TaskStatus.NOT_STARTED
        # Verify using get to check criteria list
        get_result = get()
        assert len(get_result.spec.acceptance_criteria) == 1
        assert get_result.spec.acceptance_criteria[0].id == "AC3"

        # VERIFY: Last state before attempted invalid operation
        result = get()
        assert result.summary.criteria_total == 1
        assert len(result.spec.acceptance_criteria) == 1
        assert result.spec.acceptance_criteria[0].id == "AC3"
        assert result.spec.acceptance_criteria[0].description == "Third criterion"
        assert result.spec.acceptance_criteria[0].completed is False

        # VERIFY: Cannot remove last criterion (schema constraint)
        with pytest.raises(InvalidTaskFileError):
            criteria(
                action="remove",
                criterion_id="AC3",
            )


class TestMixedCRUDOperations:
    """Integration tests for mixed task and criteria operations."""

    def test_mixed_operations_update_summary(self, crud_project: Path):
        """Test that summary updates correctly across mixed operations."""
        # CREATE: Initialize with multiple criteria
        result = new(
            branch="feature/crud-test",
            title="Mixed Operations Test",
            prompt="Test CRUD operation",
            criteria=["Criterion 1", "Criterion 2", "Criterion 3"],
        )
        assert result.summary.overall_status == TaskStatus.NOT_STARTED

        # Add tasks
        task(
            action="add",
            name="Task 1",
        )
        task(
            action="add",
            name="Task 2",
        )
        result = task(
            action="add",
            name="Task 3",
        )
        assert result.summary.overall_status == TaskStatus.NOT_STARTED

        # Update task statuses to different states
        task(
            action="update",
            task_id="T001",
            status="in_progress",
        )
        task(
            action="update",
            task_id="T002",
            status="completed",
        )
        result = task(
            action="update",
            task_id="T003",
            status="blocked",
        )
        assert result.summary.overall_status == TaskStatus.BLOCKED

        # Complete some criteria
        criteria(
            action="complete",
            criterion_id="AC1",
            completed=True,
        )
        result = criteria(
            action="complete",
            criterion_id="AC3",
            completed=True,
        )
        assert result.summary.overall_status == TaskStatus.BLOCKED

        # VERIFY: Final comprehensive state
        result = get()
        assert result.summary.criteria_total == 3
        assert result.summary.criteria_completed == 2
        assert result.summary.tasks_total == 3
        assert result.summary.tasks_completed == 1
        assert result.summary.tasks_in_progress == 1
        assert result.summary.tasks_not_started == 0
        assert result.summary.tasks_blocked == 1
