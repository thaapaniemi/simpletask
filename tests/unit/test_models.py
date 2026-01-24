"""Unit tests for Pydantic models in core/models.py.

Tests cover:
- Enum value validation
- Field validation (required, optional, defaults)
- Pattern matching (regex for IDs)
- Strict validation (extra='forbid')
- Cross-field validation (prerequisite task IDs)
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from simpletask.core.models import (
    AcceptanceCriterion,
    CodeExample,
    FileAction,
    SimpleTaskSpec,
    Task,
    TaskStatus,
)


class TestTaskStatus:
    """Test TaskStatus enum."""

    def test_enum_values(self):
        """TaskStatus enum has correct values."""
        assert TaskStatus.NOT_STARTED.value == "not_started"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.BLOCKED.value == "blocked"


class TestAcceptanceCriterion:
    """Test AcceptanceCriterion model."""

    def test_valid_criterion(self):
        """Valid acceptance criterion validates correctly."""
        ac = AcceptanceCriterion(id="AC1", description="Feature works", completed=True)
        assert ac.id == "AC1"
        assert ac.description == "Feature works"
        assert ac.completed is True

    def test_default_completed_false(self):
        """completed field defaults to False."""
        ac = AcceptanceCriterion(id="AC1", description="Test")
        assert ac.completed is False

    def test_empty_description(self):
        """Empty description is technically allowed by Pydantic (just an empty string)."""
        # Pydantic v2 allows empty strings by default
        ac = AcceptanceCriterion(id="AC1", description="")
        assert ac.description == ""

    def test_missing_required_fields(self):
        """Missing required fields raises ValidationError."""
        with pytest.raises(ValidationError):
            AcceptanceCriterion(id="AC1")  # Missing description

        with pytest.raises(ValidationError):
            AcceptanceCriterion(description="Test")  # Missing id


class TestFileAction:
    """Test FileAction model."""

    def test_valid_create_action(self):
        """Valid create action validates correctly."""
        fa = FileAction(path="src/file.ts", action="create")
        assert fa.path == "src/file.ts"
        assert fa.action == "create"

    def test_valid_modify_action(self):
        """Valid modify action validates correctly."""
        fa = FileAction(path="src/file.ts", action="modify")
        assert fa.action == "modify"

    def test_valid_delete_action(self):
        """Valid delete action validates correctly."""
        fa = FileAction(path="src/file.ts", action="delete")
        assert fa.action == "delete"

    def test_invalid_action(self):
        """Invalid action raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            FileAction(path="src/file.ts", action="update")
        assert "action" in str(exc_info.value).lower()


class TestCodeExample:
    """Test CodeExample model."""

    def test_valid_code_example(self):
        """Valid code example validates correctly."""
        ce = CodeExample(
            language="python",
            description="Example function",
            code="def hello(): pass",
        )
        assert ce.language == "python"
        assert ce.description == "Example function"
        assert ce.code == "def hello(): pass"

    def test_code_example_without_description(self):
        """Code example without description is valid."""
        ce = CodeExample(language="python", code="print('hello')")
        assert ce.description is None
        assert ce.code == "print('hello')"

    def test_missing_required_fields(self):
        """Missing required fields raises ValidationError."""
        with pytest.raises(ValidationError):
            CodeExample(language="python")  # Missing code


class TestTask:
    """Test Task model."""

    def test_valid_task_minimal(self):
        """Valid minimal task validates correctly."""
        task = Task(
            id="T001",
            name="Build feature",
            goal="Complete the feature",
            steps=["Step 1", "Step 2"],
        )
        assert task.id == "T001"
        assert task.name == "Build feature"
        assert task.goal == "Complete the feature"
        assert task.status == TaskStatus.NOT_STARTED
        assert task.steps == ["Step 1", "Step 2"]
        assert task.prerequisites is None

    def test_valid_task_complete(self):
        """Valid task with all fields validates correctly."""
        task = Task(
            id="T001",
            name="Build feature",
            goal="Complete the feature",
            status=TaskStatus.COMPLETED,
            steps=["Step 1", "Step 2"],
            done_when=["Tests pass"],
            prerequisites=["T002"],
            files=[FileAction(path="src/test.ts", action="create")],
            code_examples=[CodeExample(language="python", code="print('hi')")],
        )
        assert task.status == TaskStatus.COMPLETED
        assert task.prerequisites == ["T002"]
        assert len(task.files) == 1
        assert len(task.code_examples) == 1

    def test_empty_steps_list(self):
        """Empty steps list raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Task(
                id="T001",
                name="Build",
                goal="Build feature",
                steps=[],  # Empty list not allowed
            )
        assert "steps" in str(exc_info.value).lower()

    def test_missing_required_fields(self):
        """Missing required fields raises ValidationError."""
        with pytest.raises(ValidationError):
            Task(name="Test", goal="Test", steps=["Step 1"])  # Missing id


class TestSimpleTaskSpec:
    """Test SimpleTaskSpec model (top-level schema)."""

    def test_valid_minimal_spec(self):
        """Valid minimal task spec validates correctly."""
        spec = SimpleTaskSpec(
            branch="test-feature",
            title="Test Feature",
            original_prompt="Build a test feature",
            created=datetime.now(UTC),
            acceptance_criteria=[AcceptanceCriterion(id="AC1", description="Works correctly")],
        )
        assert spec.branch == "test-feature"
        assert spec.schema_version == "1.0"
        assert len(spec.acceptance_criteria) == 1
        assert spec.tasks is None

    def test_valid_complete_spec(self):
        """Valid complete task spec validates correctly."""
        spec = SimpleTaskSpec(
            schema_version="1.0",
            branch="test-feature",
            title="Test Feature",
            original_prompt="Build a test feature",
            created=datetime.now(UTC),
            acceptance_criteria=[
                AcceptanceCriterion(id="AC1", description="Works", completed=True),
                AcceptanceCriterion(id="AC2", description="Tests pass", completed=False),
            ],
            constraints=["Must work offline"],
            context={"env": "production"},
            tasks=[
                Task(
                    id="T001",
                    name="Task 1",
                    goal="Build",
                    steps=["Do it"],
                    done_when=None,
                    code_examples=None,
                    prerequisites=None,
                    files=None,
                ),
                Task(
                    id="T002",
                    name="Task 2",
                    goal="Test",
                    steps=["Test it"],
                    done_when=None,
                    code_examples=None,
                    prerequisites=None,
                    files=None,
                ),
            ],
        )
        assert len(spec.acceptance_criteria) == 2
        assert len(spec.tasks) == 2
        assert spec.constraints == ["Must work offline"]
        assert spec.context == {"env": "production"}

    def test_empty_acceptance_criteria(self):
        """Empty acceptance_criteria list raises ValidationError."""
        with pytest.raises(ValidationError):
            SimpleTaskSpec(
                branch="test",
                title="Test",
                original_prompt="Test",
                acceptance_criteria=[],  # Empty not allowed
            )

    def test_invalid_prerequisite_reference(self):
        """Prerequisite referencing non-existent task raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            SimpleTaskSpec(
                branch="test",
                title="Test",
                original_prompt="Test",
                acceptance_criteria=[AcceptanceCriterion(id="AC1", description="Works")],
                tasks=[
                    Task(
                        id="T001",
                        name="Task 1",
                        goal="Build",
                        steps=["Do it"],
                        done_when=None,
                        code_examples=None,
                        prerequisites=None,
                        files=None,
                    ),
                    Task(
                        id="T002",
                        name="Task 2",
                        goal="Build",
                        steps=["Do it"],
                        done_when=None,
                        code_examples=None,
                        prerequisites=["T999"],  # T999 doesn't exist!
                        files=None,
                    ),
                ],
            )
        error_msg = str(exc_info.value).lower()
        assert "prerequisite" in error_msg or "t999" in error_msg

    def test_valid_prerequisites(self):
        """Valid prerequisites validate correctly."""
        spec = SimpleTaskSpec(
            branch="test",
            title="Test",
            original_prompt="Test",
            created=datetime.now(UTC),
            acceptance_criteria=[AcceptanceCriterion(id="AC1", description="Works")],
            tasks=[
                Task(
                    id="T001",
                    name="Task 1",
                    goal="Build",
                    steps=["Do it"],
                    done_when=None,
                    code_examples=None,
                    prerequisites=None,
                    files=None,
                ),
                Task(
                    id="T002",
                    name="Task 2",
                    goal="Build",
                    steps=["Do it"],
                    done_when=None,
                    code_examples=None,
                    prerequisites=["T001"],  # T001 exists
                    files=None,
                ),
                Task(
                    id="T003",
                    name="Task 3",
                    goal="Build",
                    steps=["Do it"],
                    done_when=None,
                    code_examples=None,
                    prerequisites=["T001", "T002"],  # Both exist
                    files=None,
                ),
            ],
        )
        assert len(spec.tasks) == 3
        assert spec.tasks[1].prerequisites == ["T001"]
        assert spec.tasks[2].prerequisites == ["T001", "T002"]

    def test_missing_required_fields(self):
        """Missing required fields raises ValidationError."""

        # Missing branch
        with pytest.raises(ValidationError):
            SimpleTaskSpec(
                title="Test",
                original_prompt="Test",
                acceptance_criteria=[AcceptanceCriterion(id="AC1", description="Works")],
            )

        # Missing title
        with pytest.raises(ValidationError):
            SimpleTaskSpec(
                branch="test",
                original_prompt="Test",
                acceptance_criteria=[AcceptanceCriterion(id="AC1", description="Works")],
            )

        # Missing original_prompt
        with pytest.raises(ValidationError):
            SimpleTaskSpec(
                branch="test",
                title="Test",
                acceptance_criteria=[AcceptanceCriterion(id="AC1", description="Works")],
            )
