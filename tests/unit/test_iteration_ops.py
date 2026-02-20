"""Unit tests for iteration_ops module.

Tests cover:
- get_next_iteration_id() - ID generation
- add_iteration() - Iteration addition
- list_iterations() - Listing all iterations
- get_iteration() - Get single iteration by ID
- remove_iteration() - Iteration removal with cascading cleanup
- get_tasks_for_iteration() - Filter tasks by iteration
"""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError
from simpletask.core.iteration_ops import (
    add_iteration,
    get_iteration,
    get_next_iteration_id,
    get_tasks_for_iteration,
    list_iterations,
    remove_iteration,
)
from simpletask.core.models import AcceptanceCriterion, Iteration, SimpleTaskSpec, Task, TaskStatus
from simpletask.core.yaml_parser import parse_task_file


class TestGetNextIterationId:
    """Test get_next_iteration_id function."""

    def test_empty_list_returns_one(self):
        """Return 1 for empty iteration list."""
        assert get_next_iteration_id([]) == 1

    def test_single_existing_iteration(self):
        """Return 2 when one iteration with ID 1 exists."""
        from datetime import UTC, datetime

        iterations = [Iteration(id=1, label="MVP", created=datetime.now(tz=UTC))]
        assert get_next_iteration_id(iterations) == 2

    def test_sequential_ids(self):
        """Return max + 1 for sequential IDs."""
        from datetime import UTC, datetime

        iterations = [
            Iteration(id=1, label="MVP", created=datetime.now(tz=UTC)),
            Iteration(id=2, label="Beta", created=datetime.now(tz=UTC)),
            Iteration(id=3, label="v1.0", created=datetime.now(tz=UTC)),
        ]
        assert get_next_iteration_id(iterations) == 4

    def test_non_sequential_ids(self):
        """Return max + 1 even with gaps in IDs."""
        from datetime import UTC, datetime

        iterations = [
            Iteration(id=1, label="MVP", created=datetime.now(tz=UTC)),
            Iteration(id=5, label="v5", created=datetime.now(tz=UTC)),
        ]
        assert get_next_iteration_id(iterations) == 6


class TestAddIteration:
    """Test add_iteration function."""

    def test_add_first_iteration(self, tmp_task_file):
        """Add first iteration to file with no iterations."""
        new_id = add_iteration(tmp_task_file, label="MVP")
        assert new_id == 1

        spec = parse_task_file(tmp_task_file)
        assert spec.iterations is not None
        assert len(spec.iterations) == 1
        assert spec.iterations[0].id == 1
        assert spec.iterations[0].label == "MVP"

    def test_add_second_iteration(self, tmp_task_file):
        """Add second iteration increments ID."""
        id1 = add_iteration(tmp_task_file, label="MVP")
        id2 = add_iteration(tmp_task_file, label="Beta")

        assert id1 == 1
        assert id2 == 2

        spec = parse_task_file(tmp_task_file)
        assert spec.iterations is not None
        assert len(spec.iterations) == 2
        assert spec.iterations[0].label == "MVP"
        assert spec.iterations[1].label == "Beta"

    def test_add_iteration_has_created_timestamp(self, tmp_task_file):
        """Iteration is created with a UTC timestamp."""
        from datetime import UTC, datetime

        before = datetime.now(tz=UTC)
        add_iteration(tmp_task_file, label="v1.0")
        after = datetime.now(tz=UTC)

        spec = parse_task_file(tmp_task_file)
        assert spec.iterations is not None
        created = spec.iterations[0].created
        # Accept naive datetimes (timezone stripped during serialization)
        if created.tzinfo is None:
            created = created.replace(tzinfo=UTC)
        assert before <= created <= after

    def test_add_iteration_file_not_found(self, tmp_path):
        """Raise FileNotFoundError for missing task file."""
        missing_file = tmp_path / "missing.yml"
        with pytest.raises(FileNotFoundError):
            add_iteration(missing_file, label="MVP")


class TestListIterations:
    """Test list_iterations function."""

    def test_list_empty(self, tmp_task_file):
        """Return empty list when no iterations exist."""
        result = list_iterations(tmp_task_file)
        assert result == []

    def test_list_with_iterations(self, tmp_task_file):
        """Return all iterations."""
        add_iteration(tmp_task_file, label="MVP")
        add_iteration(tmp_task_file, label="Beta")

        result = list_iterations(tmp_task_file)
        assert len(result) == 2
        assert result[0].label == "MVP"
        assert result[1].label == "Beta"

    def test_list_returns_in_order(self, tmp_task_file):
        """Return iterations in order added."""
        for label in ["A", "B", "C"]:
            add_iteration(tmp_task_file, label=label)

        result = list_iterations(tmp_task_file)
        assert [i.label for i in result] == ["A", "B", "C"]


class TestGetIteration:
    """Test get_iteration function."""

    def test_get_existing_iteration(self, tmp_task_file):
        """Retrieve existing iteration by ID."""
        add_iteration(tmp_task_file, label="MVP")
        add_iteration(tmp_task_file, label="Beta")

        result = get_iteration(tmp_task_file, iteration_id=2)
        assert result.id == 2
        assert result.label == "Beta"

    def test_get_iteration_not_found(self, tmp_task_file):
        """Raise ValueError when iteration doesn't exist."""
        with pytest.raises(ValueError, match="Iteration 99 not found"):
            get_iteration(tmp_task_file, iteration_id=99)

    def test_get_iteration_from_empty(self, tmp_task_file):
        """Raise ValueError when no iterations exist."""
        with pytest.raises(ValueError, match="Iteration 1 not found"):
            get_iteration(tmp_task_file, iteration_id=1)


class TestRemoveIteration:
    """Test remove_iteration function."""

    def test_remove_iteration(self, tmp_task_file):
        """Remove iteration successfully."""
        add_iteration(tmp_task_file, label="MVP")
        add_iteration(tmp_task_file, label="Beta")

        remove_iteration(tmp_task_file, iteration_id=1)

        spec = parse_task_file(tmp_task_file)
        assert spec.iterations is not None
        assert len(spec.iterations) == 1
        assert spec.iterations[0].id == 2

    def test_remove_last_iteration_clears_field(self, tmp_task_file):
        """Removing last iteration sets iterations to None."""
        add_iteration(tmp_task_file, label="MVP")

        remove_iteration(tmp_task_file, iteration_id=1)

        spec = parse_task_file(tmp_task_file)
        assert spec.iterations is None

    def test_remove_iteration_not_found(self, tmp_task_file):
        """Raise ValueError when iteration doesn't exist."""
        with pytest.raises(ValueError, match="Iteration 99 not found"):
            remove_iteration(tmp_task_file, iteration_id=99)

    def test_remove_iteration_clears_task_references(self, tmp_task_file):
        """Remove iteration clears iteration field on tasks."""
        from simpletask.core.task_ops import add_implementation_task

        add_iteration(tmp_task_file, label="MVP")
        add_implementation_task(tmp_task_file, "Task A", iteration=1)
        add_implementation_task(tmp_task_file, "Task B", iteration=1)
        add_implementation_task(tmp_task_file, "Task C")

        remove_iteration(tmp_task_file, iteration_id=1)

        spec = parse_task_file(tmp_task_file)
        assert spec.tasks is not None
        # Tasks that had iteration=1 should have iteration=None
        for task in spec.tasks:
            assert task.iteration is None

    def test_remove_iteration_only_clears_matching_tasks(self, tmp_task_file):
        """Only tasks referencing the removed iteration are cleared."""
        from simpletask.core.task_ops import add_implementation_task

        add_iteration(tmp_task_file, label="MVP")
        add_iteration(tmp_task_file, label="Beta")

        add_implementation_task(tmp_task_file, "Task A", iteration=1)
        add_implementation_task(tmp_task_file, "Task B", iteration=2)

        remove_iteration(tmp_task_file, iteration_id=1)

        spec = parse_task_file(tmp_task_file)
        assert spec.tasks is not None

        # Find tasks by name
        tasks_by_name = {t.name: t for t in spec.tasks}
        assert tasks_by_name["Task A"].iteration is None  # Cleared
        assert tasks_by_name["Task B"].iteration == 2  # Preserved


class TestGetTasksForIteration:
    """Test get_tasks_for_iteration function."""

    def test_empty_tasks(self):
        """Return empty list for None tasks."""
        assert get_tasks_for_iteration(None, iteration_id=1) == []

    def test_empty_task_list(self):
        """Return empty list for empty tasks list."""
        assert get_tasks_for_iteration([], iteration_id=1) == []

    def test_filter_tasks_by_iteration(self):
        """Return only tasks matching the iteration ID."""
        tasks = [
            Task(
                id="T001",
                name="A",
                status=TaskStatus.NOT_STARTED,
                goal="G",
                steps=["S"],
                iteration=1,
            ),
            Task(
                id="T002",
                name="B",
                status=TaskStatus.NOT_STARTED,
                goal="G",
                steps=["S"],
                iteration=2,
            ),
            Task(
                id="T003",
                name="C",
                status=TaskStatus.NOT_STARTED,
                goal="G",
                steps=["S"],
                iteration=1,
            ),
        ]
        result = get_tasks_for_iteration(tasks, iteration_id=1)
        assert len(result) == 2
        assert result[0].id == "T001"
        assert result[1].id == "T003"

    def test_no_tasks_match_iteration(self):
        """Return empty list when no tasks match."""
        tasks = [
            Task(
                id="T001",
                name="A",
                status=TaskStatus.NOT_STARTED,
                goal="G",
                steps=["S"],
                iteration=2,
            ),
        ]
        result = get_tasks_for_iteration(tasks, iteration_id=1)
        assert result == []

    def test_tasks_without_iteration_not_included(self):
        """Tasks with iteration=None are excluded."""
        tasks = [
            Task(
                id="T001",
                name="A",
                status=TaskStatus.NOT_STARTED,
                goal="G",
                steps=["S"],
                iteration=None,
            ),
            Task(
                id="T002",
                name="B",
                status=TaskStatus.NOT_STARTED,
                goal="G",
                steps=["S"],
                iteration=1,
            ),
        ]
        result = get_tasks_for_iteration(tasks, iteration_id=1)
        assert len(result) == 1
        assert result[0].id == "T002"


class TestIterationModel:
    """Test the Iteration model directly."""

    def test_iteration_model_basic(self):
        """Create a basic Iteration model."""
        from datetime import UTC, datetime

        iter_obj = Iteration(id=1, label="MVP", created=datetime.now(tz=UTC))
        assert iter_obj.id == 1
        assert iter_obj.label == "MVP"

    def test_iteration_model_forbids_extra_fields(self):
        """Pydantic forbids extra fields."""
        from datetime import UTC, datetime

        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            Iteration(id=1, label="MVP", created=datetime.now(tz=UTC), extra_field="x")  # type: ignore

    def test_iteration_model_id_must_be_positive(self):
        """Iteration ID must be >= 1."""
        from datetime import UTC, datetime

        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            Iteration(id=0, label="MVP", created=datetime.now(tz=UTC))

    def test_task_with_iteration_field(self):
        """Task model accepts optional iteration field."""
        task = Task(
            id="T001",
            name="Test",
            status=TaskStatus.NOT_STARTED,
            goal="G",
            steps=["S"],
            iteration=3,
        )
        assert task.iteration == 3

    def test_task_iteration_defaults_to_none(self):
        """Task iteration field defaults to None."""
        task = Task(
            id="T001",
            name="Test",
            status=TaskStatus.NOT_STARTED,
            goal="G",
            steps=["S"],
        )
        assert task.iteration is None

    def test_task_iteration_must_be_positive(self):
        """Task iteration must be >= 1 when set."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            Task(
                id="T001",
                name="Test",
                status=TaskStatus.NOT_STARTED,
                goal="G",
                steps=["S"],
                iteration=0,
            )


class TestIterationDuplicateLabels:
    """Tests for duplicate label behavior when adding iterations."""

    def test_duplicate_labels_are_allowed(self, tmp_task_file):
        """Adding two iterations with the same label creates two distinct iterations."""
        add_iteration(tmp_task_file, "Sprint 1")
        add_iteration(tmp_task_file, "Sprint 1")
        iterations = list_iterations(tmp_task_file)
        assert len(iterations) == 2
        assert iterations[0].label == "Sprint 1"
        assert iterations[1].label == "Sprint 1"
        assert iterations[0].id != iterations[1].id

    def test_duplicate_labels_get_sequential_ids(self, tmp_task_file):
        """Duplicate label iterations receive sequential IDs."""
        add_iteration(tmp_task_file, "Sprint 1")
        add_iteration(tmp_task_file, "Sprint 1")
        iterations = list_iterations(tmp_task_file)
        assert iterations[0].id == 1
        assert iterations[1].id == 2


class TestIterationReferenceValidation:
    """Tests for model-level validation of task iteration references."""

    def test_task_referencing_nonexistent_iteration_raises(self, tmp_task_file):
        """SimpleTaskSpec raises ValidationError if a task references a nonexistent iteration."""
        from datetime import UTC, datetime

        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="iteration"):
            SimpleTaskSpec(
                branch="test",
                title="Test",
                original_prompt="p",
                created=datetime.now(UTC),
                acceptance_criteria=[
                    AcceptanceCriterion(id="AC1", description="c", completed=False)
                ],
                tasks=[
                    Task(
                        id="T001",
                        name="Task",
                        goal="G",
                        status=TaskStatus.NOT_STARTED,
                        steps=["S"],
                        iteration=99,  # No iteration with id=99 in spec
                    )
                ],
                iterations=[],  # Empty — id 99 doesn't exist
            )

    def test_task_with_valid_iteration_reference_passes(self, tmp_task_file):
        """SimpleTaskSpec accepts a task whose iteration references an existing iteration."""
        from datetime import UTC, datetime

        SimpleTaskSpec(
            branch="test",
            title="Test",
            original_prompt="p",
            created=datetime.now(UTC),
            acceptance_criteria=[AcceptanceCriterion(id="AC1", description="c", completed=False)],
            tasks=[
                Task(
                    id="T001",
                    name="Task",
                    goal="G",
                    status=TaskStatus.NOT_STARTED,
                    steps=["S"],
                    iteration=1,
                )
            ],
            iterations=[Iteration(id=1, label="Sprint 1", created=datetime.now(UTC))],
        )  # no exception = test passes


class TestIterationEdgeCases:
    """Tests for edge cases: backward compat, invalid IDs, and duplicate IDs."""

    def test_backward_compat_yaml_without_iterations_key(self, tmp_path: Path):
        """YAML without 'iterations' key parses successfully with iterations=None."""
        yaml_content = """schema_version: '1.0'
branch: legacy-branch
title: Legacy Task
original_prompt: Old task without iterations
created: '2024-01-01T00:00:00+00:00'
acceptance_criteria:
  - id: AC1
    description: It works
    completed: false
tasks:
  - id: T001
    name: Do something
    goal: Get it done
    status: not_started
    steps:
      - Step 1
"""
        task_file = tmp_path / "legacy-branch.yml"
        task_file.write_text(yaml_content)
        spec = parse_task_file(task_file)
        assert spec.iterations is None

    def test_duplicate_iteration_ids_raise_validation_error(self):
        """SimpleTaskSpec with duplicate iteration IDs raises ValidationError."""
        from datetime import UTC, datetime

        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="Duplicate iteration ID 1"):
            SimpleTaskSpec(
                branch="dup-iter",
                title="Dup",
                original_prompt="p",
                created=datetime.now(UTC),
                acceptance_criteria=[
                    AcceptanceCriterion(id="AC1", description="c", completed=False)
                ],
                tasks=[],
                iterations=[
                    Iteration(id=1, label="Sprint 1", created=datetime.now(UTC)),
                    Iteration(id=1, label="Sprint 1 duplicate", created=datetime.now(UTC)),
                ],
            )

    def test_batch_add_with_nonexistent_iteration_raises_error(self, tmp_task_file: Path):
        """batch_tasks with iteration=99 that doesn't exist raises ValueError."""
        from simpletask.core.task_ops import batch_tasks

        with pytest.raises(ValueError, match=r"Invalid iteration '99' - iteration does not exist"):
            batch_tasks(
                tmp_task_file,
                [{"op": "add", "name": "Task with bad iter", "goal": "X", "iteration": 99}],
            )

    def test_iteration_zero_is_rejected(self):
        """Iteration model with id=0 raises ValidationError (ge=1 constraint)."""
        with pytest.raises(ValidationError):
            Iteration(id=0, label="Zero Sprint", created=datetime.now(UTC))
