"""Unit tests for MCP write tools (simpletask_new, simpletask_task, simpletask_criteria)."""

import subprocess
from pathlib import Path

import pytest
from simpletask.core.models import TaskStatus
from simpletask.mcp.models import SimpleTaskGetResponse
from simpletask.mcp.server import simpletask_criteria, simpletask_new, simpletask_task


@pytest.fixture
def temp_project(tmp_path, monkeypatch):
    """Create temporary git project for testing."""
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def task_project(temp_project):
    """Create project with existing task file."""
    simpletask_new(branch="test", title="Test", prompt="Test")
    return temp_project


class TestSimpletaskNew:
    """Tests for simpletask_new MCP tool."""

    def test_creates_task_file(self, temp_project):
        """Test that simpletask_new creates a task file with correct structure."""
        result = simpletask_new(
            branch="test/branch",
            title="Test Task",
            prompt="Test prompt",
        )
        assert isinstance(result, SimpleTaskGetResponse)
        assert result.spec.branch == "test/branch"
        assert Path(result.file_path).exists()
        assert result.summary.branch == "test/branch"
        assert result.summary.title == "Test Task"

    def test_already_exists_raises(self, temp_project):
        """Test that creating duplicate task raises ValueError."""
        simpletask_new(branch="test", title="T", prompt="P")
        with pytest.raises(ValueError, match="already exists"):
            simpletask_new(branch="test", title="T", prompt="P")

    def test_criteria_none_adds_placeholder(self, temp_project):
        """Test that criteria=None adds a placeholder criterion."""
        result = simpletask_new(branch="t", title="T", prompt="P", criteria=None)
        assert len(result.spec.acceptance_criteria) == 1
        assert result.spec.acceptance_criteria[0].id == "AC1"
        assert "to be filled" in result.spec.acceptance_criteria[0].description

    def test_criteria_empty_list_raises(self, temp_project):
        """Test that criteria=[] raises ValidationError (min_length=1)."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            simpletask_new(branch="t", title="T", prompt="P", criteria=[])

    def test_criteria_list_creates_criteria(self, temp_project):
        """Test that criteria list creates criteria with correct IDs."""
        result = simpletask_new(branch="t", title="T", prompt="P", criteria=["First", "Second"])
        assert len(result.spec.acceptance_criteria) == 2
        assert result.spec.acceptance_criteria[0].id == "AC1"
        assert result.spec.acceptance_criteria[0].description == "First"
        assert result.spec.acceptance_criteria[1].id == "AC2"
        assert result.spec.acceptance_criteria[1].description == "Second"

    def test_returns_correct_summary(self, temp_project):
        """Test that returned summary has correct counts."""
        result = simpletask_new(branch="t", title="T", prompt="P", criteria=["A", "B", "C"])
        assert result.summary.criteria_total == 3
        assert result.summary.criteria_completed == 0
        assert result.summary.tasks_total == 0


class TestSimpletaskTask:
    """Tests for simpletask_task MCP tool."""

    def test_add_success(self, task_project):
        """Test adding a task successfully."""
        result = simpletask_task(action="add", branch="test", name="Task 1", goal="Do something")
        assert result.summary.tasks_total == 1
        assert result.spec.tasks[0].name == "Task 1"
        assert result.spec.tasks[0].id == "T001"
        assert result.spec.tasks[0].goal == "Do something"

    def test_add_missing_name_raises(self, task_project):
        """Test that add without name raises ValueError."""
        with pytest.raises(ValueError, match="'name' is required"):
            simpletask_task(action="add", branch="test")

    def test_add_ignores_status_param(self, task_project):
        """Test that add action ignores status parameter."""
        result = simpletask_task(action="add", branch="test", name="Task", status="completed")
        # Status should be not_started despite passing "completed"
        assert result.spec.tasks[0].status == TaskStatus.NOT_STARTED

    def test_update_status_success(self, task_project):
        """Test updating task status."""
        simpletask_task(action="add", branch="test", name="Task")
        result = simpletask_task(
            action="update", branch="test", task_id="T001", status="in_progress"
        )
        assert result.spec.tasks[0].status == TaskStatus.IN_PROGRESS

    def test_update_name_and_goal(self, task_project):
        """Test updating task name and goal."""
        simpletask_task(action="add", branch="test", name="Old Name", goal="Old Goal")
        result = simpletask_task(
            action="update", branch="test", task_id="T001", name="New Name", goal="New Goal"
        )
        assert result.spec.tasks[0].name == "New Name"
        assert result.spec.tasks[0].goal == "New Goal"

    def test_update_missing_task_id_raises(self, task_project):
        """Test that update without task_id raises ValueError."""
        with pytest.raises(ValueError, match="'task_id' is required"):
            simpletask_task(action="update", branch="test", status="completed")

    def test_update_invalid_status_raises(self, task_project):
        """Test that invalid status raises ValueError."""
        simpletask_task(action="add", branch="test", name="Task")
        with pytest.raises(ValueError, match=r"Invalid status.*Valid:"):
            simpletask_task(action="update", branch="test", task_id="T001", status="invalid")

    def test_update_task_not_found_raises(self, task_project):
        """Test that updating non-existent task raises ValueError."""
        # First add a task so we have tasks defined
        simpletask_task(action="add", branch="test", name="Task")
        with pytest.raises(ValueError, match="not found"):
            simpletask_task(action="update", branch="test", task_id="T999", status="completed")

    def test_remove_success(self, task_project):
        """Test removing a task successfully."""
        simpletask_task(action="add", branch="test", name="Task")
        result = simpletask_task(action="remove", branch="test", task_id="T001")
        assert result.summary.tasks_total == 0

    def test_remove_missing_task_id_raises(self, task_project):
        """Test that remove without task_id raises ValueError."""
        with pytest.raises(ValueError, match="'task_id' is required"):
            simpletask_task(action="remove", branch="test")

    def test_remove_task_not_found_raises(self, task_project):
        """Test that removing non-existent task raises ValueError."""
        # First add a task so we have tasks defined
        simpletask_task(action="add", branch="test", name="Task")
        with pytest.raises(ValueError, match="not found"):
            simpletask_task(action="remove", branch="test", task_id="T999")


class TestSimpletaskCriteria:
    """Tests for simpletask_criteria MCP tool."""

    def test_add_success(self, task_project):
        """Test adding a criterion successfully."""
        result = simpletask_criteria(action="add", branch="test", description="New criterion")
        # Started with 1 placeholder, now have 2
        assert result.summary.criteria_total == 2
        assert result.spec.acceptance_criteria[-1].description == "New criterion"
        assert result.spec.acceptance_criteria[-1].id == "AC2"

    def test_add_missing_description_raises(self, task_project):
        """Test that add without description raises ValueError."""
        with pytest.raises(ValueError, match="'description' is required"):
            simpletask_criteria(action="add", branch="test")

    def test_complete_success(self, task_project):
        """Test marking criterion as completed."""
        result = simpletask_criteria(action="complete", branch="test", criterion_id="AC1")
        assert result.spec.acceptance_criteria[0].completed is True
        assert result.summary.criteria_completed == 1

    def test_complete_false_marks_incomplete(self, task_project):
        """Test marking criterion as incomplete."""
        simpletask_criteria(action="complete", branch="test", criterion_id="AC1")
        result = simpletask_criteria(
            action="complete", branch="test", criterion_id="AC1", completed=False
        )
        assert result.spec.acceptance_criteria[0].completed is False
        assert result.summary.criteria_completed == 0

    def test_complete_missing_criterion_id_raises(self, task_project):
        """Test that complete without criterion_id raises ValueError."""
        with pytest.raises(ValueError, match="'criterion_id' is required"):
            simpletask_criteria(action="complete", branch="test")

    def test_complete_criterion_not_found_raises(self, task_project):
        """Test that completing non-existent criterion raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            simpletask_criteria(action="complete", branch="test", criterion_id="AC999")

    def test_remove_success(self, task_project):
        """Test removing a criterion successfully."""
        # Add a second criterion first so we don't hit min_length=1
        simpletask_criteria(action="add", branch="test", description="Second")
        result = simpletask_criteria(action="remove", branch="test", criterion_id="AC2")
        assert result.summary.criteria_total == 1

    def test_remove_missing_criterion_id_raises(self, task_project):
        """Test that remove without criterion_id raises ValueError."""
        with pytest.raises(ValueError, match="'criterion_id' is required"):
            simpletask_criteria(action="remove", branch="test")

    def test_remove_criterion_not_found_raises(self, task_project):
        """Test that removing non-existent criterion raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            simpletask_criteria(action="remove", branch="test", criterion_id="AC999")

    def test_remove_last_criterion_fails(self, task_project):
        """Test that removing the last criterion fails due to schema validation."""
        # Task starts with 1 placeholder criterion due to criteria=None default
        # Removing it should fail due to min_length=1
        with pytest.raises(Exception):  # Could be ValidationError or ValueError
            simpletask_criteria(action="remove", branch="test", criterion_id="AC1")
