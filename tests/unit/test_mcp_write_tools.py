"""Unit tests for MCP write tools (new, task, criteria)."""

import subprocess
from pathlib import Path

import pytest
import yaml
from simpletask.core.models import TaskStatus
from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.mcp.models import SimpleTaskItemResponse, SimpleTaskWriteResponse
from simpletask.mcp.server import criteria, new, task


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
    new(branch="test", title="Test", prompt="Test")
    # Checkout the test branch so MCP tools can auto-detect it
    subprocess.run(["git", "checkout", "-b", "test"], cwd=temp_project, check=True)
    return temp_project


class TestSimpletaskNew:
    """Tests for new MCP tool."""

    def test_creates_task_file(self, temp_project):
        """Test that new creates a task file with correct structure."""
        result = new(
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
        new(branch="test", title="T", prompt="P")
        with pytest.raises(ValueError, match="already exists"):
            new(branch="test", title="T", prompt="P")

    def test_criteria_none_adds_placeholder(self, temp_project):
        """Test that criteria=None adds a placeholder criterion."""
        result = new(branch="t", title="T", prompt="P", criteria=None)
        assert result.summary.criteria_total == 1
        assert "1 criteria" in result.message

    def test_criteria_empty_list_creates_placeholder(self, temp_project):
        """Test that criteria=[] creates a placeholder criterion."""
        from simpletask.core.project import get_task_file_path
        from simpletask.core.yaml_parser import parse_task_file

        result = new(branch="t", title="T", prompt="P", criteria=[])

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
        result = new(branch="t", title="T", prompt="P", criteria=["First", "Second"])
        assert result.summary.criteria_total == 2

    def test_returns_correct_summary(self, temp_project):
        """Test that returned summary has correct counts."""
        result = new(branch="t", title="T", prompt="P", criteria=["A", "B", "C"])
        assert result.summary.criteria_total == 3
        assert result.summary.criteria_completed == 0
        assert result.summary.tasks_total == 0


class TestSimpletaskTask:
    """Tests for task MCP tool."""

    def test_add_success(self, task_project):
        """Test adding a task successfully."""
        result = task(action="add", name="Task 1", goal="Do something")
        assert isinstance(result, SimpleTaskWriteResponse)
        assert result.success is True
        assert result.action == "task_added"
        assert result.summary.tasks_total == 1
        assert "Task 1" in result.message

    def test_add_missing_name_raises(self, task_project):
        """Test that add without name raises ValueError."""
        with pytest.raises(ValueError, match="'name' is required"):
            task(action="add")

    def test_add_ignores_status_param(self, task_project):
        """Test that add action ignores status parameter."""
        task(action="add", name="Task", status="completed")
        # Verify task was added as not_started - we need to fetch it to check
        get_result = task(action="get", task_id="T001")
        assert get_result.task.status == TaskStatus.NOT_STARTED

    def test_update_status_success(self, task_project):
        """Test updating task status."""
        task(action="add", name="Task")
        result = task(action="update", task_id="T001", status="in_progress")
        assert isinstance(result, SimpleTaskWriteResponse)
        assert result.success is True
        assert result.action == "task_updated"
        # Verify status was updated by getting the task
        get_result = task(action="get", task_id="T001")
        assert get_result.task.status == TaskStatus.IN_PROGRESS

    def test_update_name_and_goal(self, task_project):
        """Test updating task name and goal."""
        task(action="add", name="Old Name", goal="Old Goal")
        result = task(action="update", task_id="T001", name="New Name", goal="New Goal")
        assert result.success is True
        # Verify name and goal were updated by getting the task
        get_result = task(action="get", task_id="T001")
        assert get_result.task.name == "New Name"
        assert get_result.task.goal == "New Goal"

    def test_update_missing_task_id_raises(self, task_project):
        """Test that update without task_id raises ValueError."""
        with pytest.raises(ValueError, match="'task_id' is required"):
            task(action="update", status="completed")

    def test_update_invalid_status_raises(self, task_project):
        """Test that invalid status raises ValueError."""
        task(action="add", name="Task")
        with pytest.raises(ValueError, match=r"Invalid status.*Valid:"):
            task(action="update", task_id="T001", status="invalid")

    def test_update_task_not_found_raises(self, task_project):
        """Test that updating non-existent task raises ValueError."""
        # First add a task so we have tasks defined
        task(action="add", name="Task")
        with pytest.raises(ValueError, match="not found"):
            task(action="update", task_id="T999", status="completed")

    def test_remove_success(self, task_project):
        """Test removing a task successfully."""
        task(action="add", name="Task")
        result = task(action="remove", task_id="T001")
        assert result.summary.tasks_total == 0

    def test_remove_missing_task_id_raises(self, task_project):
        """Test that remove without task_id raises ValueError."""
        with pytest.raises(ValueError, match="'task_id' is required"):
            task(action="remove")

    def test_remove_task_not_found_raises(self, task_project):
        """Test that removing non-existent task raises ValueError."""
        # First add a task so we have tasks defined
        task(action="add", name="Task")
        with pytest.raises(ValueError, match="not found"):
            task(action="remove", task_id="T999")

    def test_get_success(self, task_project):
        """Test getting a task by ID."""
        task(action="add", name="Test Task", goal="Test Goal")
        result = task(action="get", task_id="T001")
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
            task(action="get")

    def test_get_task_not_found_raises(self, task_project):
        """Test that getting non-existent task raises ValueError."""
        # First add a task so we have tasks defined
        task(action="add", name="Task")
        with pytest.raises(ValueError, match="not found"):
            task(action="get", task_id="T999")


class TestSimpletaskCriteria:
    """Tests for criteria MCP tool."""

    def test_add_success(self, task_project):
        """Test adding a criterion successfully."""
        result = criteria(action="add", description="New criterion")
        assert isinstance(result, SimpleTaskWriteResponse)
        assert result.success is True
        assert result.action == "criterion_added"
        # Started with 1 placeholder, now have 2
        assert result.summary.criteria_total == 2
        assert "New criterion" in result.message

    def test_add_missing_description_raises(self, task_project):
        """Test that add without description raises ValueError."""
        with pytest.raises(ValueError, match="'description' is required"):
            criteria(action="add")

    def test_complete_success(self, task_project):
        """Test marking criterion as completed."""
        result = criteria(action="complete", criterion_id="AC1")
        assert isinstance(result, SimpleTaskWriteResponse)
        assert result.success is True
        assert result.action == "criterion_completed"
        assert result.summary.criteria_completed == 1
        # Verify it was actually completed by getting it
        get_result = criteria(action="get", criterion_id="AC1")
        assert get_result.criterion.completed is True

    def test_complete_false_marks_incomplete(self, task_project):
        """Test marking criterion as incomplete."""
        criteria(action="complete", criterion_id="AC1")
        result = criteria(action="complete", criterion_id="AC1", completed=False)
        assert result.action == "criterion_uncompleted"
        assert result.summary.criteria_completed == 0
        # Verify it was actually marked incomplete by getting it
        get_result = criteria(action="get", criterion_id="AC1")
        assert get_result.criterion.completed is False

    def test_complete_missing_criterion_id_raises(self, task_project):
        """Test that complete without criterion_id raises ValueError."""
        with pytest.raises(ValueError, match="'criterion_id' is required"):
            criteria(action="complete")

    def test_complete_criterion_not_found_raises(self, task_project):
        """Test that completing non-existent criterion raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            criteria(action="complete", criterion_id="AC999")

    def test_remove_success(self, task_project):
        """Test removing a criterion successfully."""
        # Add a second criterion first so we don't hit min_length=1
        criteria(action="add", description="Second")
        result = criteria(action="remove", criterion_id="AC2")
        assert isinstance(result, SimpleTaskWriteResponse)
        assert result.success is True
        assert result.action == "criterion_removed"
        assert result.summary.criteria_total == 1

    def test_remove_missing_criterion_id_raises(self, task_project):
        """Test that remove without criterion_id raises ValueError."""
        with pytest.raises(ValueError, match="'criterion_id' is required"):
            criteria(action="remove")

    def test_remove_criterion_not_found_raises(self, task_project):
        """Test that removing non-existent criterion raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            criteria(action="remove", criterion_id="AC999")

    def test_remove_last_criterion_fails(self, task_project):
        """Test that removing the last criterion fails due to schema validation."""
        # Task starts with 1 placeholder criterion due to criteria=None default
        # Removing it should fail due to min_length=1
        with pytest.raises(InvalidTaskFileError):
            criteria(action="remove", criterion_id="AC1")

    def test_get_success(self, task_project):
        """Test getting a criterion by ID."""
        criteria(action="add", description="Test Criterion")
        result = criteria(action="get", criterion_id="AC2")
        assert isinstance(result, SimpleTaskItemResponse)
        assert result.criterion is not None
        assert result.task is None
        assert result.criterion.id == "AC2"
        assert result.criterion.description == "Test Criterion"
        assert result.criterion.completed is False

    def test_get_missing_criterion_id_raises(self, task_project):
        """Test that get without criterion_id raises ValueError."""
        with pytest.raises(ValueError, match="'criterion_id' is required"):
            criteria(action="get")

    def test_get_criterion_not_found_raises(self, task_project):
        """Test that getting non-existent criterion raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            criteria(action="get", criterion_id="AC999")


class TestCriteriaRepair:
    """Tests for automatic repair of broken task files."""

    def test_repair_empty_criteria(self, temp_project):
        """Test that empty acceptance_criteria is automatically repaired."""
        import subprocess

        import yaml
        from simpletask.core.project import get_task_file_path
        from simpletask.core.yaml_parser import parse_task_file

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

        # Checkout the repair-test branch so MCP tools can find it
        subprocess.run(["git", "checkout", "-b", "repair-test"], cwd=temp_project, check=True)

        # This should trigger repair and succeed
        result = criteria(action="add", description="New criterion")

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
        import subprocess

        import yaml
        from simpletask.core.project import get_task_file_path
        from simpletask.core.yaml_parser import parse_task_file

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

        # Checkout the repair-test2 branch so MCP tools can find it
        subprocess.run(["git", "checkout", "-b", "repair-test2"], cwd=temp_project, check=True)

        # This should trigger repair and succeed
        result = criteria(action="add", description="New criterion")

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
        import subprocess

        import yaml
        from simpletask.core.project import get_task_file_path
        from simpletask.core.yaml_parser import parse_task_file

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

        # Checkout the repair-test3 branch so MCP tools can find it
        subprocess.run(["git", "checkout", "-b", "repair-test3"], cwd=temp_project, check=True)

        # This should repair both issues and succeed
        result = criteria(action="add", description="New criterion")

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
    """Tests for steps parameter in task."""

    def test_task_add_steps_none(self, temp_project):
        """Test that steps=None creates placeholder."""
        import subprocess

        from simpletask.core.project import get_task_file_path
        from simpletask.core.yaml_parser import parse_task_file

        # Create task file first
        new(branch="steps-test", title="Test", prompt="Test", criteria=["AC1"])

        # Checkout the steps-test branch so MCP tools can find it
        subprocess.run(["git", "checkout", "-b", "steps-test"], cwd=temp_project, check=True)

        # Add task with steps=None (default)
        result = task(
            action="add",
            name="Test Task",
            goal="Test goal",
            # steps not provided = None
        )

        assert result.success is True

        # Verify placeholder was created by reading the file
        task_path = get_task_file_path("steps-test")
        spec = parse_task_file(task_path)
        assert spec.tasks is not None
        task_obj = spec.tasks[0]
        assert task_obj.steps == ["To be defined"]

    def test_task_add_steps_empty(self, temp_project):
        """Test that steps=[] creates placeholder."""
        import subprocess

        from simpletask.core.project import get_task_file_path
        from simpletask.core.yaml_parser import parse_task_file

        new(branch="steps-test2", title="Test", prompt="Test", criteria=["AC1"])

        # Checkout the steps-test2 branch so MCP tools can find it
        subprocess.run(["git", "checkout", "-b", "steps-test2"], cwd=temp_project, check=True)

        result = task(
            action="add",
            name="Test Task",
            goal="Test goal",
            steps=[],  # Explicit empty list
        )

        assert result.success is True

        # Verify placeholder was created by reading the file
        task_path = get_task_file_path("steps-test2")
        spec = parse_task_file(task_path)
        assert spec.tasks is not None
        task_obj = spec.tasks[0]
        assert task_obj.steps == ["To be defined"]

    def test_task_add_steps_provided(self, temp_project):
        """Test that provided steps are used."""
        import subprocess

        from simpletask.core.project import get_task_file_path
        from simpletask.core.yaml_parser import parse_task_file

        new(branch="steps-test3", title="Test", prompt="Test", criteria=["AC1"])

        # Checkout the steps-test3 branch so MCP tools can find it
        subprocess.run(["git", "checkout", "-b", "steps-test3"], cwd=temp_project, check=True)

        custom_steps = ["Step 1", "Step 2", "Step 3"]
        result = task(
            action="add",
            name="Test Task",
            goal="Test goal",
            steps=custom_steps,
        )

        assert result.success is True

        # Verify custom steps were used by reading the file
        task_path = get_task_file_path("steps-test3")
        spec = parse_task_file(task_path)
        assert spec.tasks is not None
        task_obj = spec.tasks[0]
        assert task_obj.steps == custom_steps
        assert len(task_obj.steps) == 3

    def test_task_add_steps_in_yaml(self, temp_project):
        """Test that steps are properly serialized in YAML."""
        from simpletask.core.project import get_task_file_path

        new(branch="steps-test4", title="Test", prompt="Test", criteria=["AC1"])

        # Checkout the steps-test4 branch so MCP tools can find it
        subprocess.run(["git", "checkout", "-b", "steps-test4"], cwd=temp_project, check=True)

        task(
            action="add",
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


class TestTaskNewFields:
    """Tests for new Task model fields (done_when, prerequisites, files, code_examples)."""

    def test_task_add_with_done_when(self, temp_project):
        """Test task add with done_when parameter."""
        import subprocess

        from simpletask.core.project import get_task_file_path
        from simpletask.core.yaml_parser import parse_task_file

        new(branch="done-when-test", title="Test", prompt="Test", criteria=["AC1"])

        subprocess.run(["git", "checkout", "-b", "done-when-test"], cwd=temp_project, check=True)

        result = task(
            action="add",
            name="Test Task",
            goal="Test goal",
            done_when=["pytest passes", "No lint errors"],
        )

        assert result.success is True

        # Verify done_when was saved
        task_path = get_task_file_path("done-when-test")
        spec = parse_task_file(task_path)
        assert spec.tasks is not None
        task_obj = spec.tasks[0]
        assert task_obj.done_when == ["pytest passes", "No lint errors"]

    def test_task_add_with_prerequisites(self, temp_project):
        """Test task add with prerequisites parameter."""
        import subprocess

        from simpletask.core.project import get_task_file_path
        from simpletask.core.yaml_parser import parse_task_file

        new(branch="prereq-test", title="Test", prompt="Test", criteria=["AC1"])

        subprocess.run(["git", "checkout", "-b", "prereq-test"], cwd=temp_project, check=True)

        # Add first task
        task(action="add", name="First Task", goal="First")

        # Add second task with prerequisite
        result = task(
            action="add",
            name="Second Task",
            goal="Second",
            prerequisites=["T001"],
        )

        assert result.success is True

        # Verify prerequisites was saved
        task_path = get_task_file_path("prereq-test")
        spec = parse_task_file(task_path)
        assert spec.tasks is not None
        assert len(spec.tasks) == 2
        second_task = spec.tasks[1]
        assert second_task.prerequisites == ["T001"]

    def test_task_add_with_files(self, temp_project):
        """Test task add with files parameter."""
        import subprocess

        from simpletask.core.project import get_task_file_path
        from simpletask.core.yaml_parser import parse_task_file

        new(branch="files-test", title="Test", prompt="Test", criteria=["AC1"])

        subprocess.run(["git", "checkout", "-b", "files-test"], cwd=temp_project, check=True)

        result = task(
            action="add",
            name="Test Task",
            goal="Test goal",
            files=[
                {"path": "src/models.py", "action": "create"},
                {"path": "src/views.py", "action": "modify"},
            ],
        )

        assert result.success is True

        # Verify files was saved
        task_path = get_task_file_path("files-test")
        spec = parse_task_file(task_path)
        assert spec.tasks is not None
        task_obj = spec.tasks[0]
        assert task_obj.files is not None
        assert len(task_obj.files) == 2
        assert task_obj.files[0].path == "src/models.py"
        assert task_obj.files[0].action == "create"
        assert task_obj.files[1].path == "src/views.py"
        assert task_obj.files[1].action == "modify"

    def test_task_add_with_code_examples(self, temp_project):
        """Test task add with code_examples parameter."""
        import subprocess

        from simpletask.core.project import get_task_file_path
        from simpletask.core.yaml_parser import parse_task_file

        new(branch="code-examples-test", title="Test", prompt="Test", criteria=["AC1"])

        subprocess.run(
            ["git", "checkout", "-b", "code-examples-test"], cwd=temp_project, check=True
        )

        result = task(
            action="add",
            name="Test Task",
            goal="Test goal",
            code_examples=[
                {
                    "language": "python",
                    "description": "Example pattern",
                    "code": "def example(): pass",
                },
            ],
        )

        assert result.success is True

        # Verify code_examples was saved
        task_path = get_task_file_path("code-examples-test")
        spec = parse_task_file(task_path)
        assert spec.tasks is not None
        task_obj = spec.tasks[0]
        assert task_obj.code_examples is not None
        assert len(task_obj.code_examples) == 1
        assert task_obj.code_examples[0].language == "python"
        assert task_obj.code_examples[0].description == "Example pattern"
        assert task_obj.code_examples[0].code == "def example(): pass"

    def test_task_add_with_all_fields(self, temp_project):
        """Test task add with all new parameters combined."""
        import subprocess

        from simpletask.core.project import get_task_file_path
        from simpletask.core.yaml_parser import parse_task_file

        new(branch="all-fields-test", title="Test", prompt="Test", criteria=["AC1"])

        subprocess.run(["git", "checkout", "-b", "all-fields-test"], cwd=temp_project, check=True)

        # Add first task to use as prerequisite
        task(action="add", name="First Task", goal="First")

        # Add second task with all fields
        result = task(
            action="add",
            name="Full Task",
            goal="Task with all fields",
            steps=["Step 1", "Step 2"],
            done_when=["All tests pass", "No errors"],
            prerequisites=["T001"],
            files=[
                {"path": "src/module.py", "action": "create"},
            ],
            code_examples=[
                {
                    "language": "python",
                    "description": "Pattern to follow",
                    "code": "class Example: pass",
                },
            ],
        )

        assert result.success is True

        # Verify all fields were saved correctly
        task_path = get_task_file_path("all-fields-test")
        spec = parse_task_file(task_path)
        assert spec.tasks is not None
        assert len(spec.tasks) == 2
        full_task = spec.tasks[1]

        assert full_task.name == "Full Task"
        assert full_task.goal == "Task with all fields"
        assert full_task.steps == ["Step 1", "Step 2"]
        assert full_task.done_when == ["All tests pass", "No errors"]
        assert full_task.prerequisites == ["T001"]
        assert full_task.files is not None
        assert len(full_task.files) == 1
        assert full_task.files[0].path == "src/module.py"
        assert full_task.files[0].action == "create"
        assert full_task.code_examples is not None
        assert len(full_task.code_examples) == 1
        assert full_task.code_examples[0].language == "python"
        assert full_task.code_examples[0].code == "class Example: pass"

    def test_task_update_steps(self, temp_project):
        """Test task update can modify steps."""
        import subprocess

        from simpletask.core.project import get_task_file_path
        from simpletask.core.yaml_parser import parse_task_file

        new(branch="update-steps-test", title="Test", prompt="Test", criteria=["AC1"])

        subprocess.run(["git", "checkout", "-b", "update-steps-test"], cwd=temp_project, check=True)

        # Add task with initial steps
        task(action="add", name="Test Task", steps=["Initial step"])

        # Update steps
        result = task(
            action="update",
            task_id="T001",
            steps=["Updated step 1", "Updated step 2"],
        )

        assert result.success is True

        # Verify steps were updated
        task_path = get_task_file_path("update-steps-test")
        spec = parse_task_file(task_path)
        assert spec.tasks is not None
        task_obj = spec.tasks[0]
        assert task_obj.steps == ["Updated step 1", "Updated step 2"]

    def test_task_update_done_when_and_files(self, temp_project):
        """Test task update can modify done_when and files."""
        import subprocess

        from simpletask.core.project import get_task_file_path
        from simpletask.core.yaml_parser import parse_task_file

        new(branch="update-fields-test", title="Test", prompt="Test", criteria=["AC1"])

        subprocess.run(
            ["git", "checkout", "-b", "update-fields-test"], cwd=temp_project, check=True
        )

        # Add task
        task(action="add", name="Test Task")

        # Update done_when and files
        result = task(
            action="update",
            task_id="T001",
            done_when=["Tests pass"],
            files=[{"path": "src/new.py", "action": "create"}],
        )

        assert result.success is True

        # Verify fields were updated
        task_path = get_task_file_path("update-fields-test")
        spec = parse_task_file(task_path)
        assert spec.tasks is not None
        task_obj = spec.tasks[0]
        assert task_obj.done_when == ["Tests pass"]
        assert task_obj.files is not None
        assert len(task_obj.files) == 1
        assert task_obj.files[0].path == "src/new.py"

    def test_batch_add_with_full_fields(self, temp_project):
        """Test batch operation with all Task model fields."""
        import subprocess

        from simpletask.core.project import get_task_file_path
        from simpletask.core.yaml_parser import parse_task_file

        new(branch="batch-full-test", title="Test", prompt="Test", criteria=["AC1"])

        subprocess.run(["git", "checkout", "-b", "batch-full-test"], cwd=temp_project, check=True)

        # Use batch operation to add task with all fields
        result = task(
            action="batch",
            operations=[
                {
                    "op": "add",
                    "name": "Full Batch Task",
                    "goal": "Task with all fields in batch",
                    "steps": ["Batch step 1", "Batch step 2"],
                    "done_when": ["Batch condition met"],
                    "prerequisites": [],
                    "files": [{"path": "src/batch.py", "action": "create"}],
                    "code_examples": [
                        {
                            "language": "python",
                            "description": "Batch example",
                            "code": "def batch_example(): pass",
                        }
                    ],
                },
            ],
        )

        assert result.success is True
        assert len(result.new_item_ids) == 1

        # Verify all fields were saved
        task_path = get_task_file_path("batch-full-test")
        spec = parse_task_file(task_path)
        assert spec.tasks is not None
        assert len(spec.tasks) == 1
        batch_task = spec.tasks[0]

        assert batch_task.name == "Full Batch Task"
        assert batch_task.goal == "Task with all fields in batch"
        assert batch_task.steps == ["Batch step 1", "Batch step 2"]
        assert batch_task.done_when == ["Batch condition met"]
        assert batch_task.prerequisites == []
        assert batch_task.files is not None
        assert len(batch_task.files) == 1
        assert batch_task.files[0].path == "src/batch.py"
        assert batch_task.code_examples is not None
        assert len(batch_task.code_examples) == 1
        assert batch_task.code_examples[0].language == "python"

    def test_batch_update_new_fields(self, temp_project):
        """Test batch update operation modifies done_when, files, and code_examples."""
        import subprocess

        from simpletask.core.project import get_task_file_path
        from simpletask.core.yaml_parser import parse_task_file

        new(branch="batch-update-test", title="Test", prompt="Test", criteria=["AC1"])

        subprocess.run(["git", "checkout", "-b", "batch-update-test"], cwd=temp_project, check=True)

        # Add initial task with basic fields
        task(action="add", name="Initial Task", goal="Initial goal")

        # Use batch operation to update task with new fields
        result = task(
            action="batch",
            operations=[
                {
                    "op": "update",
                    "task_id": "T001",
                    "done_when": ["Updated condition 1", "Updated condition 2"],
                    "files": [
                        {"path": "src/updated.py", "action": "modify"},
                        {"path": "tests/test_updated.py", "action": "create"},
                    ],
                    "code_examples": [
                        {
                            "language": "python",
                            "description": "Updated pattern",
                            "code": "def updated_example(): return True",
                        }
                    ],
                },
            ],
        )

        assert result.success is True

        # Verify all fields were updated correctly
        task_path = get_task_file_path("batch-update-test")
        spec = parse_task_file(task_path)
        assert spec.tasks is not None
        assert len(spec.tasks) == 1
        updated_task = spec.tasks[0]

        assert updated_task.name == "Initial Task"
        assert updated_task.goal == "Initial goal"
        assert updated_task.done_when == ["Updated condition 1", "Updated condition 2"]
        assert updated_task.files is not None
        assert len(updated_task.files) == 2
        assert updated_task.files[0].path == "src/updated.py"
        assert updated_task.files[0].action == "modify"
        assert updated_task.files[1].path == "tests/test_updated.py"
        assert updated_task.files[1].action == "create"
        assert updated_task.code_examples is not None
        assert len(updated_task.code_examples) == 1
        assert updated_task.code_examples[0].language == "python"
        assert updated_task.code_examples[0].description == "Updated pattern"
        assert updated_task.code_examples[0].code == "def updated_example(): return True"

    def test_batch_invalid_prerequisite_atomicity(self, temp_project):
        """Test batch operations with invalid prerequisites fail atomically without partial changes."""
        import subprocess

        import pytest
        from simpletask.core.project import get_task_file_path
        from simpletask.core.yaml_parser import parse_task_file

        new(branch="batch-atomic-test", title="Test", prompt="Test", criteria=["AC1"])

        subprocess.run(["git", "checkout", "-b", "batch-atomic-test"], cwd=temp_project, check=True)

        # Add initial task
        task(action="add", name="Initial Task", goal="Initial")

        # Record initial state
        task_path = get_task_file_path("batch-atomic-test")
        spec_before = parse_task_file(task_path)
        assert spec_before.tasks is not None
        initial_task_count = len(spec_before.tasks)
        initial_task_name = spec_before.tasks[0].name

        # Try batch with mix of valid and invalid operations
        # Should fail atomically without applying any changes
        with pytest.raises(ValueError) as exc_info:
            task(
                action="batch",
                operations=[
                    {"op": "add", "name": "Valid Add", "goal": "This should not be added"},
                    {
                        "op": "add",
                        "name": "Invalid Prereq",
                        "prerequisites": ["T999"],  # Non-existent prerequisite
                    },
                    {"op": "update", "task_id": "T001", "name": "Updated Name"},
                ],
            )

        # Verify error message mentions prerequisite
        error_msg = str(exc_info.value)
        assert "T999" in error_msg
        assert "prerequisite" in error_msg.lower()

        # Verify task spec unchanged (no partial operations applied)
        spec_after = parse_task_file(task_path)
        assert spec_after.tasks is not None
        assert len(spec_after.tasks) == initial_task_count
        assert spec_after.tasks[0].name == initial_task_name
        # Verify no new tasks were added
        assert all(t.name != "Valid Add" for t in spec_after.tasks)
        assert all(t.name != "Invalid Prereq" for t in spec_after.tasks)

    def test_invalid_prerequisites_error(self, temp_project):
        """Test that invalid prerequisites raise clear error."""
        import subprocess

        import pytest
        from simpletask.core.yaml_parser import InvalidTaskFileError

        new(branch="invalid-prereq-test", title="Test", prompt="Test", criteria=["AC1"])

        subprocess.run(
            ["git", "checkout", "-b", "invalid-prereq-test"], cwd=temp_project, check=True
        )

        # Try to add task with non-existent prerequisite - should fail validation
        with pytest.raises(InvalidTaskFileError) as exc_info:
            task(
                action="add",
                name="Test Task",
                prerequisites=["T999"],  # Non-existent task
            )

        error_msg = str(exc_info.value)
        assert "T999" in error_msg
        assert "prerequisite" in error_msg.lower()

    def test_invalid_file_action_error(self, temp_project):
        """Test that invalid file action values raise clear error."""
        import subprocess

        import pytest
        from pydantic import ValidationError

        new(branch="invalid-file-test", title="Test", prompt="Test", criteria=["AC1"])

        subprocess.run(["git", "checkout", "-b", "invalid-file-test"], cwd=temp_project, check=True)

        # Try to add task with invalid file action
        with pytest.raises(ValidationError) as exc_info:
            task(
                action="add",
                name="Test Task",
                files=[{"path": "src/test.py", "action": "invalid_action"}],
            )

        error_msg = str(exc_info.value)
        assert "invalid_action" in error_msg or "action" in error_msg.lower()
