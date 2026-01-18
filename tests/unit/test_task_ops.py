"""Unit tests for task_ops module.

Tests cover:
- get_next_task_id() - ID generation with edge cases
- add_implementation_task() - Task addition with validation
- update_implementation_task() - Task property updates
- remove_implementation_task() - Task removal
"""

import pytest
from pathlib import Path
from datetime import datetime

from simpletask.core.task_ops import (
    get_next_task_id,
    add_implementation_task,
    update_implementation_task,
    remove_implementation_task,
)
from simpletask.core.yaml_parser import parse_task_file
from simpletask.core.models import TaskStatus, Task


class TestGetNextTaskId:
    """Test get_next_task_id function."""

    def test_empty_list(self):
        """Return T001 for empty task list."""
        assert get_next_task_id([]) == "T001"

    def test_sequential_ids(self):
        """Return next sequential ID."""
        tasks = [
            Task(id="T001", name="Task 1", goal="G1", steps=["S1"]),
            Task(id="T002", name="Task 2", goal="G2", steps=["S2"]),
            Task(id="T003", name="Task 3", goal="G3", steps=["S3"]),
        ]
        assert get_next_task_id(tasks) == "T004"

    def test_non_sequential_ids(self):
        """Return max ID + 1 even if IDs are not sequential."""
        tasks = [
            Task(id="T001", name="Task 1", goal="G1", steps=["S1"]),
            Task(id="T005", name="Task 5", goal="G5", steps=["S5"]),
            Task(id="T003", name="Task 3", goal="G3", steps=["S3"]),
        ]
        assert get_next_task_id(tasks) == "T006"

    def test_high_numbers(self):
        """Handle high task numbers correctly."""
        tasks = [
            Task(id="T099", name="Task 99", goal="G99", steps=["S99"]),
        ]
        assert get_next_task_id(tasks) == "T100"


class TestAddImplementationTask:
    """Test add_implementation_task function."""

    def test_add_task_basic(self, tmp_task_file):
        """Add task with basic properties."""
        new_id = add_implementation_task(tmp_task_file, name="New task", goal="Complete new task")
        assert new_id == "T003"

        spec = parse_task_file(tmp_task_file)
        assert len(spec.tasks) == 3
        assert spec.tasks[2].id == "T003"
        assert spec.tasks[2].name == "New task"
        assert spec.tasks[2].goal == "Complete new task"
        assert spec.tasks[2].status == TaskStatus.NOT_STARTED
        assert spec.tasks[2].steps == ["To be defined"]

    def test_add_task_default_goal(self, tmp_task_file):
        """Add task with default goal (uses name)."""
        new_id = add_implementation_task(tmp_task_file, name="New task")
        assert new_id == "T003"

        spec = parse_task_file(tmp_task_file)
        assert spec.tasks[2].goal == "New task"  # Goal defaults to name

    def test_add_task_with_status(self, tmp_task_file):
        """Add task with custom status."""
        new_id = add_implementation_task(tmp_task_file, name="Task", status=TaskStatus.IN_PROGRESS)

        spec = parse_task_file(tmp_task_file)
        assert spec.tasks[2].status == TaskStatus.IN_PROGRESS

    def test_add_task_updates_timestamp(self, tmp_task_file):
        """Verify updated timestamp is modified."""
        spec_before = parse_task_file(tmp_task_file)
        updated_before = spec_before.updated

        add_implementation_task(tmp_task_file, name="New task")

        spec_after = parse_task_file(tmp_task_file)
        assert spec_after.updated > updated_before

    def test_add_task_to_empty_tasks_list(self, tmp_path, sample_spec):
        """Add task when tasks list is None."""
        # Create spec with no tasks
        sample_spec.tasks = None
        task_file = tmp_path / "test.yml"
        from simpletask.core.yaml_parser import write_task_file

        write_task_file(task_file, sample_spec, update_timestamp=False)

        # Add first task
        new_id = add_implementation_task(task_file, name="First task")
        assert new_id == "T001"

        spec = parse_task_file(task_file)
        assert len(spec.tasks) == 1
        assert spec.tasks[0].id == "T001"


class TestUpdateImplementationTask:
    """Test update_implementation_task function."""

    def test_update_status(self, tmp_task_file):
        """Update task status."""
        update_implementation_task(tmp_task_file, "T001", status=TaskStatus.COMPLETED)

        spec = parse_task_file(tmp_task_file)
        assert spec.tasks[0].status == TaskStatus.COMPLETED

    def test_update_name(self, tmp_task_file):
        """Update task name."""
        update_implementation_task(tmp_task_file, "T001", name="Updated name")

        spec = parse_task_file(tmp_task_file)
        assert spec.tasks[0].name == "Updated name"

    def test_update_goal(self, tmp_task_file):
        """Update task goal."""
        update_implementation_task(tmp_task_file, "T001", goal="Updated goal")

        spec = parse_task_file(tmp_task_file)
        assert spec.tasks[0].goal == "Updated goal"

    def test_update_multiple_fields(self, tmp_task_file):
        """Update multiple fields at once."""
        update_implementation_task(
            tmp_task_file,
            "T001",
            name="New name",
            goal="New goal",
            status=TaskStatus.IN_PROGRESS,
        )

        spec = parse_task_file(tmp_task_file)
        assert spec.tasks[0].name == "New name"
        assert spec.tasks[0].goal == "New goal"
        assert spec.tasks[0].status == TaskStatus.IN_PROGRESS

    def test_update_task_not_found(self, tmp_task_file):
        """Raise ValueError when task doesn't exist."""
        with pytest.raises(ValueError, match="Task T999 not found"):
            update_implementation_task(tmp_task_file, "T999", status=TaskStatus.COMPLETED)

    def test_update_no_tasks(self, tmp_path, sample_spec):
        """Raise ValueError when no tasks defined."""
        sample_spec.tasks = None
        task_file = tmp_path / "test.yml"
        from simpletask.core.yaml_parser import write_task_file

        write_task_file(task_file, sample_spec, update_timestamp=False)

        with pytest.raises(ValueError, match="No tasks defined"):
            update_implementation_task(task_file, "T001", name="Test")


class TestRemoveImplementationTask:
    """Test remove_implementation_task function."""

    def test_remove_task(self, tmp_task_file):
        """Remove task successfully."""
        remove_implementation_task(tmp_task_file, "T002")

        spec = parse_task_file(tmp_task_file)
        assert len(spec.tasks) == 1
        assert spec.tasks[0].id == "T001"

    def test_remove_task_not_found(self, tmp_task_file):
        """Raise ValueError when task doesn't exist."""
        with pytest.raises(ValueError, match="Task T999 not found"):
            remove_implementation_task(tmp_task_file, "T999")

    def test_remove_no_tasks(self, tmp_path, sample_spec):
        """Raise ValueError when no tasks defined."""
        sample_spec.tasks = None
        task_file = tmp_path / "test.yml"
        from simpletask.core.yaml_parser import write_task_file

        write_task_file(task_file, sample_spec, update_timestamp=False)

        with pytest.raises(ValueError, match="No tasks defined"):
            remove_implementation_task(task_file, "T001")

    def test_remove_first_task(self, tmp_task_file):
        """Remove first task from list."""
        remove_implementation_task(tmp_task_file, "T001")

        spec = parse_task_file(tmp_task_file)
        assert len(spec.tasks) == 1
        assert spec.tasks[0].id == "T002"

    def test_remove_updates_timestamp(self, tmp_task_file):
        """Verify updated timestamp is modified."""
        spec_before = parse_task_file(tmp_task_file)
        updated_before = spec_before.updated

        remove_implementation_task(tmp_task_file, "T001")

        spec_after = parse_task_file(tmp_task_file)
        assert spec_after.updated > updated_before
