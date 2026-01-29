"""Unit tests for MCP models and helpers."""

from simpletask.core.models import SimpleTaskSpec
from simpletask.mcp.models import (
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
