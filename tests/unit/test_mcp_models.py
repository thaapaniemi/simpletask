"""Unit tests for MCP models and helpers."""

import pytest
from pydantic import ValidationError
from simpletask.core.models import SimpleTaskSpec
from simpletask.mcp.models import (
    BatchTaskOperation,
    SimpleTaskGetResponse,
    ValidationResult,
    compute_status_summary,
)


class TestComputeStatusSummary:
    """Tests for compute_status_summary function."""

    def test_basic_counts(self, sample_spec: SimpleTaskSpec):
        """Verify counts from sample_spec fixture."""
        summary = compute_status_summary(sample_spec)

        assert summary.branch == "test-feature"
        assert summary.title == "Test Feature"
        assert summary.criteria_total == 2
        assert summary.criteria_completed == 0
        assert summary.tasks_total == 2
        assert summary.tasks_completed == 0
        assert summary.tasks_in_progress == 0
        assert summary.tasks_not_started == 2
        assert summary.tasks_blocked == 0

    def test_no_tasks(self, sample_spec_no_tasks: SimpleTaskSpec):
        """Verify when spec.tasks is None."""
        summary = compute_status_summary(sample_spec_no_tasks)

        assert summary.tasks_total == 0
        assert summary.tasks_completed == 0
        assert summary.tasks_in_progress == 0
        assert summary.tasks_not_started == 0
        assert summary.tasks_blocked == 0

    def test_mixed_task_statuses(self, sample_spec_mixed_statuses: SimpleTaskSpec):
        """Verify COMPLETED, IN_PROGRESS, BLOCKED, NOT_STARTED, PAUSED counting."""
        summary = compute_status_summary(sample_spec_mixed_statuses)

        assert summary.tasks_total == 5
        assert summary.tasks_completed == 1
        assert summary.tasks_in_progress == 1
        assert summary.tasks_not_started == 1
        assert summary.tasks_blocked == 1
        assert summary.tasks_paused == 1

    def test_overall_status_paused_priority(self, sample_spec_mixed_statuses: SimpleTaskSpec):
        """Verify overall status priority: blocked > paused > in_progress > completed > not_started."""
        summary = compute_status_summary(sample_spec_mixed_statuses)
        # With blocked task present, overall should be blocked
        assert summary.overall_status.value == "blocked"

    def test_overall_status_blocked_trumps_all(
        self, sample_spec_blocked_paused_in_progress: SimpleTaskSpec
    ):
        """Verify blocked has highest priority even with paused and in_progress tasks."""
        summary = compute_status_summary(sample_spec_blocked_paused_in_progress)
        assert summary.overall_status.value == "blocked"
        assert summary.tasks_blocked == 1
        assert summary.tasks_paused == 1
        assert summary.tasks_in_progress == 1

    def test_overall_status_paused_trumps_in_progress(
        self, sample_spec_paused_and_in_progress: SimpleTaskSpec
    ):
        """Verify paused takes priority over in_progress when no blocked tasks."""
        summary = compute_status_summary(sample_spec_paused_and_in_progress)
        assert summary.overall_status.value == "paused"
        assert summary.tasks_blocked == 0
        assert summary.tasks_paused == 1
        assert summary.tasks_in_progress == 1
        assert summary.tasks_completed == 1

    def test_overall_status_only_paused(self, sample_spec_only_paused: SimpleTaskSpec):
        """Verify overall status is PAUSED when only paused tasks exist."""
        summary = compute_status_summary(sample_spec_only_paused)
        assert summary.overall_status.value == "paused"
        assert summary.tasks_paused == 2
        assert summary.tasks_blocked == 0
        assert summary.tasks_in_progress == 0

    def test_completed_criteria(self, sample_spec_mixed_statuses: SimpleTaskSpec):
        """Verify criteria_completed count."""
        summary = compute_status_summary(sample_spec_mixed_statuses)

        assert summary.criteria_total == 2
        assert summary.criteria_completed == 1

    def test_all_tasks_completed(self, sample_spec_all_completed: SimpleTaskSpec):
        """Verify edge case when all tasks are completed."""
        summary = compute_status_summary(sample_spec_all_completed)

        assert summary.tasks_total == 2
        assert summary.tasks_completed == 2
        assert summary.tasks_in_progress == 0
        assert summary.tasks_not_started == 0
        assert summary.tasks_blocked == 0
        assert summary.criteria_total == 2
        assert summary.criteria_completed == 2


class TestValidationResult:
    """Tests for ValidationResult model."""

    def test_valid_result(self):
        """Test valid result with no errors."""
        result = ValidationResult(valid=True, errors=[])
        assert result.valid is True
        assert result.errors == []

    def test_invalid_result(self):
        """Test invalid result with errors."""
        result = ValidationResult(valid=False, errors=["error1", "error2"])
        assert result.valid is False
        assert len(result.errors) == 2

    def test_no_file_path_field(self):
        """Verify ValidationResult has no file_path attribute."""
        result = ValidationResult(valid=True)
        assert not hasattr(result, "file_path")


class TestSimpleTaskGetResponse:
    """Tests for SimpleTaskGetResponse model."""

    def test_response_structure(self, sample_spec: SimpleTaskSpec):
        """Verify all fields present in response."""
        summary = compute_status_summary(sample_spec)
        validation = ValidationResult(valid=True, errors=[])

        response = SimpleTaskGetResponse(
            spec=sample_spec,
            file_path="/path/to/task.yml",
            summary=summary,
            validation=validation,
        )

        assert response.spec == sample_spec
        assert response.file_path == "/path/to/task.yml"
        assert response.summary == summary
        assert response.validation == validation

    def test_validation_optional(self, sample_spec: SimpleTaskSpec):
        """Verify validation can be None."""
        summary = compute_status_summary(sample_spec)

        response = SimpleTaskGetResponse(
            spec=sample_spec,
            file_path="/path/to/task.yml",
            summary=summary,
            validation=None,
        )

        assert response.validation is None


class TestBatchTaskOperation:
    """Tests for BatchTaskOperation model validation."""

    def test_add_operation_valid(self):
        """Test valid add operation with required name field."""
        op = BatchTaskOperation(
            op="add",
            name="New task",
            goal="Task goal",
            steps=["Step 1", "Step 2"],
        )
        assert op.op == "add"
        assert op.name == "New task"
        assert op.goal == "Task goal"
        assert op.steps == ["Step 1", "Step 2"]
        assert op.task_id is None

    def test_add_operation_missing_name_raises(self):
        """Test add operation without name raises ValidationError."""
        with pytest.raises(ValidationError, match="name is required for add operation"):
            BatchTaskOperation(
                op="add",
                goal="Task goal",
            )

    def test_remove_operation_valid(self):
        """Test valid remove operation with required task_id."""
        op = BatchTaskOperation(
            op="remove",
            task_id="T001",
        )
        assert op.op == "remove"
        assert op.task_id == "T001"
        assert op.name is None

    def test_remove_operation_missing_task_id_raises(self):
        """Test remove operation without task_id raises ValidationError."""
        with pytest.raises(ValidationError, match="task_id is required for remove operation"):
            BatchTaskOperation(op="remove")

    def test_update_operation_valid(self):
        """Test valid update operation with required task_id."""
        op = BatchTaskOperation(
            op="update",
            task_id="T002",
            status="completed",
            name="Updated name",
        )
        assert op.op == "update"
        assert op.task_id == "T002"
        assert op.status == "completed"
        assert op.name == "Updated name"

    def test_update_operation_missing_task_id_raises(self):
        """Test update operation without task_id raises ValidationError."""
        with pytest.raises(ValidationError, match="task_id is required for update operation"):
            BatchTaskOperation(
                op="update",
                status="completed",
            )

    def test_extra_fields_forbidden(self):
        """Test that extra fields are rejected."""
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            BatchTaskOperation(
                op="add",
                name="Task",
                invalid_field="value",
            )

    def test_iteration_string_coerced_to_int(self):
        """Test that string integers are coerced to int for Qwen CLI compatibility."""
        op = BatchTaskOperation(op="update", task_id="T001", iteration="3")
        assert op.iteration == 3
        assert isinstance(op.iteration, int)

    def test_iteration_int_unchanged(self):
        """Test that integer iterations pass through unchanged."""
        op = BatchTaskOperation(op="update", task_id="T001", iteration=3)
        assert op.iteration == 3
        assert isinstance(op.iteration, int)

    def test_iteration_none_unchanged(self):
        """Test that None iterations pass through unchanged."""
        op = BatchTaskOperation(op="update", task_id="T001", iteration=None)
        assert op.iteration is None

    def test_iteration_invalid_string_raises(self):
        """Test that non-numeric strings raise ValidationError."""
        with pytest.raises(ValidationError):
            BatchTaskOperation(op="update", task_id="T001", iteration="not-a-number")
