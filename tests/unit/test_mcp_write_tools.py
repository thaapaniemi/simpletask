"""Unit tests for MCP write tools (simpletask_new, simpletask_task, simpletask_criteria)."""

import subprocess
from pathlib import Path

import pytest
from simpletask.core.models import TaskStatus
from simpletask.mcp.models import SimpleTaskItemResponse, SimpleTaskWriteResponse
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
        assert isinstance(result, SimpleTaskWriteResponse)
        assert result.success is True
        assert result.action == "task_file_created"
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
        assert result.summary.criteria_total == 1
        assert "1 criteria" in result.message

    def test_criteria_empty_list_creates_placeholder(self, temp_project):
        """Test that criteria=[] creates a placeholder criterion."""
        from simpletask.core.project import get_task_file_path
        from simpletask.core.yaml_parser import parse_task_file

        result = simpletask_new(branch="t", title="T", prompt="P", criteria=[])

        # Should succeed and create placeholder
        assert result.success is True
        assert result.summary.criteria_total == 1

        # Verify placeholder criterion by reading the file
        task_path = get_task_file_path("t")
        spec = parse_task_file(task_path)
        assert len(spec.acceptance_criteria) == 1
        assert spec.acceptance_criteria[0].id == "AC1"
        assert "to be filled" in spec.acceptance_criteria[0].description.lower()

    def test_criteria_list_creates_criteria(self, temp_project):
        """Test that criteria list creates criteria with correct IDs."""
        result = simpletask_new(branch="t", title="T", prompt="P", criteria=["First", "Second"])
        assert result.summary.criteria_total == 2

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
        assert isinstance(result, SimpleTaskWriteResponse)
        assert result.success is True
        assert result.action == "task_added"
        assert result.summary.tasks_total == 1
        assert "Task 1" in result.message

    def test_add_missing_name_raises(self, task_project):
        """Test that add without name raises ValueError."""
        with pytest.raises(ValueError, match="'name' is required"):
            simpletask_task(action="add", branch="test")

    def test_add_ignores_status_param(self, task_project):
        """Test that add action ignores status parameter."""
        result = simpletask_task(action="add", branch="test", name="Task", status="completed")
        # Verify task was added as not_started - we need to fetch it to check
        get_result = simpletask_task(action="get", branch="test", task_id="T001")
        assert get_result.task.status == TaskStatus.NOT_STARTED

    def test_update_status_success(self, task_project):
        """Test updating task status."""
        simpletask_task(action="add", branch="test", name="Task")
        result = simpletask_task(
            action="update", branch="test", task_id="T001", status="in_progress"
        )
        assert isinstance(result, SimpleTaskWriteResponse)
        assert result.success is True
        assert result.action == "task_updated"
        # Verify status was updated by getting the task
        get_result = simpletask_task(action="get", branch="test", task_id="T001")
        assert get_result.task.status == TaskStatus.IN_PROGRESS

    def test_update_name_and_goal(self, task_project):
        """Test updating task name and goal."""
        simpletask_task(action="add", branch="test", name="Old Name", goal="Old Goal")
        result = simpletask_task(
            action="update", branch="test", task_id="T001", name="New Name", goal="New Goal"
        )
        assert result.success is True
        # Verify name and goal were updated by getting the task
        get_result = simpletask_task(action="get", branch="test", task_id="T001")
        assert get_result.task.name == "New Name"
        assert get_result.task.goal == "New Goal"

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

    def test_get_success(self, task_project):
        """Test getting a task by ID."""
        simpletask_task(action="add", branch="test", name="Test Task", goal="Test Goal")
        result = simpletask_task(action="get", branch="test", task_id="T001")
        assert isinstance(result, SimpleTaskItemResponse)
        assert result.task is not None
        assert result.criterion is None
        assert result.task.id == "T001"
        assert result.task.name == "Test Task"
        assert result.task.goal == "Test Goal"
        assert result.task.status == TaskStatus.NOT_STARTED

    def test_get_missing_task_id_raises(self, task_project):
        """Test that get without task_id raises ValueError."""
        with pytest.raises(ValueError, match="'task_id' is required"):
            simpletask_task(action="get", branch="test")

    def test_get_task_not_found_raises(self, task_project):
        """Test that getting non-existent task raises ValueError."""
        # First add a task so we have tasks defined
        simpletask_task(action="add", branch="test", name="Task")
        with pytest.raises(ValueError, match="not found"):
            simpletask_task(action="get", branch="test", task_id="T999")


class TestSimpletaskCriteria:
    """Tests for simpletask_criteria MCP tool."""

    def test_add_success(self, task_project):
        """Test adding a criterion successfully."""
        result = simpletask_criteria(action="add", branch="test", description="New criterion")
        assert isinstance(result, SimpleTaskWriteResponse)
        assert result.success is True
        assert result.action == "criterion_added"
        # Started with 1 placeholder, now have 2
        assert result.summary.criteria_total == 2
        assert "New criterion" in result.message

    def test_add_missing_description_raises(self, task_project):
        """Test that add without description raises ValueError."""
        with pytest.raises(ValueError, match="'description' is required"):
            simpletask_criteria(action="add", branch="test")

    def test_complete_success(self, task_project):
        """Test marking criterion as completed."""
        result = simpletask_criteria(action="complete", branch="test", criterion_id="AC1")
        assert isinstance(result, SimpleTaskWriteResponse)
        assert result.success is True
        assert result.action == "criterion_completed"
        assert result.summary.criteria_completed == 1
        # Verify it was actually completed by getting it
        get_result = simpletask_criteria(action="get", branch="test", criterion_id="AC1")
        assert get_result.criterion.completed is True

    def test_complete_false_marks_incomplete(self, task_project):
        """Test marking criterion as incomplete."""
        simpletask_criteria(action="complete", branch="test", criterion_id="AC1")
        result = simpletask_criteria(
            action="complete", branch="test", criterion_id="AC1", completed=False
        )
        assert result.action == "criterion_uncompleted"
        assert result.summary.criteria_completed == 0
        # Verify it was actually marked incomplete by getting it
        get_result = simpletask_criteria(action="get", branch="test", criterion_id="AC1")
        assert get_result.criterion.completed is False

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
        assert isinstance(result, SimpleTaskWriteResponse)
        assert result.success is True
        assert result.action == "criterion_removed"
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

    def test_get_success(self, task_project):
        """Test getting a criterion by ID."""
        simpletask_criteria(action="add", branch="test", description="Test Criterion")
        result = simpletask_criteria(action="get", branch="test", criterion_id="AC2")
        assert isinstance(result, SimpleTaskItemResponse)
        assert result.criterion is not None
        assert result.task is None
        assert result.criterion.id == "AC2"
        assert result.criterion.description == "Test Criterion"
        assert result.criterion.completed is False

    def test_get_missing_criterion_id_raises(self, task_project):
        """Test that get without criterion_id raises ValueError."""
        with pytest.raises(ValueError, match="'criterion_id' is required"):
            simpletask_criteria(action="get", branch="test")

    def test_get_criterion_not_found_raises(self, task_project):
        """Test that getting non-existent criterion raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            simpletask_criteria(action="get", branch="test", criterion_id="AC999")


class TestCriteriaRepair:
    """Tests for automatic repair of broken task files."""

    def test_repair_empty_criteria(self, temp_project):
        """Test that empty acceptance_criteria is automatically repaired."""
        from simpletask.core.project import get_task_file_path
        from simpletask.core.yaml_parser import parse_task_file
        import yaml

        # Create task with empty criteria manually
        task_path = get_task_file_path("repair-test")
        task_path.parent.mkdir(parents=True, exist_ok=True)

        broken_data = {
            "schema_version": "1.0",
            "branch": "repair-test",
            "title": "Test Repair",
            "original_prompt": "Test",
            "created": "2024-01-01T00:00:00Z",
            "acceptance_criteria": [],  # EMPTY - violates min_length=1
        }

        task_path.write_text(yaml.dump(broken_data))

        # This should trigger repair and succeed
        result = simpletask_criteria(
            action="add", branch="repair-test", description="New criterion"
        )

        assert result.success is True
        # Should have placeholder AC1 + new AC2
        assert result.summary.criteria_total == 2

        # Verify repair happened (placeholder was added) by reading file
        spec = parse_task_file(task_path)
        assert spec.acceptance_criteria[0].id == "AC1"
        assert "to be filled" in spec.acceptance_criteria[0].description.lower()
        assert spec.acceptance_criteria[1].id == "AC2"
        assert spec.acceptance_criteria[1].description == "New criterion"

    def test_repair_unknown_fields(self, temp_project):
        """Test that unknown root fields are automatically stripped."""
        from simpletask.core.project import get_task_file_path
        from simpletask.core.yaml_parser import parse_task_file
        import yaml

        # Create task with invalid root fields
        task_path = get_task_file_path("repair-test2")
        task_path.parent.mkdir(parents=True, exist_ok=True)

        broken_data = {
            "schema_version": "1.0",
            "branch": "repair-test2",
            "title": "Test Repair",
            "original_prompt": "Test",
            "created": "2024-01-01T00:00:00Z",
            "status": "in_progress",  # INVALID at root level
            "updated": "2024-01-02T00:00:00Z",  # INVALID at root level
            "acceptance_criteria": [{"id": "AC1", "description": "Test", "completed": False}],
        }

        task_path.write_text(yaml.dump(broken_data))

        # This should trigger repair and succeed
        result = simpletask_criteria(
            action="add", branch="repair-test2", description="New criterion"
        )

        assert result.success is True

        # Verify unknown fields were stripped
        spec = parse_task_file(task_path)
        assert not hasattr(spec, "status")
        assert not hasattr(spec, "updated")

        # Re-read raw YAML to verify fields are gone
        raw_data = yaml.safe_load(task_path.read_text())
        assert "status" not in raw_data
        assert "updated" not in raw_data

    def test_repair_combined(self, temp_project):
        """Test repair of both empty criteria and unknown fields."""
        from simpletask.core.project import get_task_file_path
        from simpletask.core.yaml_parser import parse_task_file
        import yaml

        # Create task with BOTH issues
        task_path = get_task_file_path("repair-test3")
        task_path.parent.mkdir(parents=True, exist_ok=True)

        broken_data = {
            "schema_version": "1.0",
            "branch": "repair-test3",
            "title": "Test Repair Combined",
            "original_prompt": "Test",
            "created": "2024-01-01T00:00:00Z",
            "status": "in_progress",  # INVALID
            "updated": "2024-01-02T00:00:00Z",  # INVALID
            "acceptance_criteria": [],  # EMPTY - violates constraint
        }

        task_path.write_text(yaml.dump(broken_data))

        # This should repair both issues and succeed
        result = simpletask_criteria(
            action="add", branch="repair-test3", description="New criterion"
        )

        assert result.success is True
        assert result.summary.criteria_total == 2  # Placeholder + new

        # Verify full repair
        spec = parse_task_file(task_path)
        assert not hasattr(spec, "status")
        assert not hasattr(spec, "updated")
        assert len(spec.acceptance_criteria) == 2
        assert spec.acceptance_criteria[0].id == "AC1"
        assert "to be filled" in spec.acceptance_criteria[0].description.lower()


class TestTaskStepsParameter:
    """Tests for steps parameter in simpletask_task."""

    def test_task_add_steps_none(self, temp_project):
        """Test that steps=None creates placeholder."""
        from simpletask.core.yaml_parser import parse_task_file
        from simpletask.core.project import get_task_file_path

        # Create task file first
        simpletask_new(branch="steps-test", title="Test", prompt="Test", criteria=["AC1"])

        # Add task with steps=None (default)
        result = simpletask_task(
            action="add",
            branch="steps-test",
            name="Test Task",
            goal="Test goal",
            # steps not provided = None
        )

        assert result.success is True

        # Verify placeholder was created by reading the file
        task_path = get_task_file_path("steps-test")
        spec = parse_task_file(task_path)
        task = spec.tasks[0]
        assert task.steps == ["To be defined"]

    def test_task_add_steps_empty(self, temp_project):
        """Test that steps=[] creates placeholder."""
        from simpletask.core.yaml_parser import parse_task_file
        from simpletask.core.project import get_task_file_path

        simpletask_new(branch="steps-test2", title="Test", prompt="Test", criteria=["AC1"])

        result = simpletask_task(
            action="add",
            branch="steps-test2",
            name="Test Task",
            goal="Test goal",
            steps=[],  # Explicit empty list
        )

        assert result.success is True

        # Verify placeholder was created by reading the file
        task_path = get_task_file_path("steps-test2")
        spec = parse_task_file(task_path)
        task = spec.tasks[0]
        assert task.steps == ["To be defined"]

    def test_task_add_steps_provided(self, temp_project):
        """Test that provided steps are used."""
        from simpletask.core.yaml_parser import parse_task_file
        from simpletask.core.project import get_task_file_path

        simpletask_new(branch="steps-test3", title="Test", prompt="Test", criteria=["AC1"])

        custom_steps = ["Step 1", "Step 2", "Step 3"]
        result = simpletask_task(
            action="add",
            branch="steps-test3",
            name="Test Task",
            goal="Test goal",
            steps=custom_steps,
        )

        assert result.success is True

        # Verify custom steps were used by reading the file
        task_path = get_task_file_path("steps-test3")
        spec = parse_task_file(task_path)
        task = spec.tasks[0]
        assert task.steps == custom_steps
        assert len(task.steps) == 3

    def test_task_add_steps_in_yaml(self, temp_project):
        """Test that steps are properly serialized in YAML."""
        from simpletask.core.project import get_task_file_path
        import yaml

        simpletask_new(branch="steps-test4", title="Test", prompt="Test", criteria=["AC1"])

        simpletask_task(
            action="add",
            branch="steps-test4",
            name="Test Task",
            steps=["First step", "Second step"],
        )

        # Read raw YAML to verify serialization
        task_path = get_task_file_path("steps-test4")
        raw_data = yaml.safe_load(task_path.read_text())

        assert "tasks" in raw_data
        assert len(raw_data["tasks"]) == 1
        assert "steps" in raw_data["tasks"][0]
        assert raw_data["tasks"][0]["steps"] == ["First step", "Second step"]
