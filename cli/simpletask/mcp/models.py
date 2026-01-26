"""MCP response models for simpletask.

This module defines Pydantic models for MCP tool responses,
including status summaries and validation results.
"""

from pydantic import BaseModel, Field

from ..core.models import (
    AcceptanceCriterion,
    Design,
    QualityRequirements,
    SimpleTaskSpec,
    Task,
    TaskStatus,
)

__all__ = [
    "QualityCheckResult",
    "SimpleTaskDesignResponse",
    "SimpleTaskGetResponse",
    "SimpleTaskItemResponse",
    "SimpleTaskQualityResponse",
    "SimpleTaskWriteResponse",
    "StatusSummary",
    "ValidationResult",
    "compute_status_summary",
]


class QualityCheckResult(BaseModel):
    """Result of a single quality check."""

    model_config = {"extra": "forbid"}

    check_name: str = Field(..., description="Name of the check (e.g., 'Linting', 'Testing')")
    passed: bool = Field(..., description="Whether the check passed")
    command: str = Field(..., description="Command that was executed")
    stdout: str = Field(default="", description="Standard output from command")
    stderr: str = Field(default="", description="Standard error from command")


class StatusSummary(BaseModel):
    """Pre-computed status counts for a task file."""

    model_config = {"extra": "forbid"}

    branch: str = Field(..., description="Branch/task identifier")
    title: str = Field(..., description="Task title")
    overall_status: TaskStatus = Field(..., description="Computed overall task status")
    criteria_total: int = Field(..., description="Total acceptance criteria")
    criteria_completed: int = Field(..., description="Completed criteria count")
    tasks_total: int = Field(0, description="Total implementation tasks")
    tasks_completed: int = Field(0, description="Completed tasks")
    tasks_in_progress: int = Field(0, description="In-progress tasks")
    tasks_not_started: int = Field(0, description="Not started tasks")
    tasks_blocked: int = Field(0, description="Blocked tasks")


class ValidationResult(BaseModel):
    """Schema validation result. Note: file_path is in parent response."""

    model_config = {"extra": "forbid"}

    valid: bool = Field(..., description="Whether file is valid")
    errors: list[str] = Field(default_factory=list, description="Validation errors")


class SimpleTaskGetResponse(BaseModel):
    """Response model for simpletask_get tool."""

    model_config = {"extra": "forbid"}

    spec: SimpleTaskSpec = Field(..., description="Complete task specification")
    file_path: str = Field(..., description="Path to task file")
    summary: StatusSummary = Field(..., description="Pre-computed status summary")
    validation: ValidationResult | None = Field(
        None, description="Validation result (only when validate=true)"
    )


class SimpleTaskWriteResponse(BaseModel):
    """Minimal response model for write operations (add/update/remove/complete).

    Returns just enough information to confirm the operation succeeded
    and provide current status, without the full task specification.
    """

    model_config = {"extra": "forbid"}

    success: bool = Field(..., description="Whether operation succeeded")
    action: str = Field(
        ..., description="Action performed (e.g., 'task_added', 'criterion_completed')"
    )
    message: str = Field(..., description="Human-readable confirmation message")
    file_path: str = Field(..., description="Path to task file")
    summary: StatusSummary = Field(..., description="Pre-computed status summary")
    new_item_id: str | None = Field(
        None, description="ID of newly created item (for add operations)"
    )


class SimpleTaskItemResponse(BaseModel):
    """Response model for retrieving a single task or criterion.

    Used by action='get' on simpletask_task and simpletask_criteria tools.
    Returns just the requested item plus status summary.
    """

    model_config = {"extra": "forbid"}

    task: Task | None = Field(None, description="The requested task (for simpletask_task)")
    criterion: AcceptanceCriterion | None = Field(
        None, description="The requested criterion (for simpletask_criteria)"
    )
    file_path: str = Field(..., description="Path to task file")
    summary: StatusSummary = Field(..., description="Pre-computed status summary")


class SimpleTaskQualityResponse(BaseModel):
    """Response model for simpletask_quality tool.

    Used for quality check and get actions.
    """

    model_config = {"extra": "forbid"}

    action: str = Field(..., description="Action performed (e.g., 'quality_check', 'quality_get')")
    quality_requirements: QualityRequirements | None = Field(
        None, description="Current quality requirements (for 'get' action)"
    )
    check_results: list[QualityCheckResult] | None = Field(
        None, description="Quality check results (for 'check' action)"
    )
    all_passed: bool | None = Field(
        None, description="Whether all checks passed (for 'check' action)"
    )
    applied_fields: dict[str, bool] | None = Field(
        None, description="Fields applied from preset (for 'preset' action)"
    )
    file_path: str = Field(..., description="Path to task file")
    summary: StatusSummary = Field(..., description="Pre-computed status summary")


class SimpleTaskDesignResponse(BaseModel):
    """Response model for simpletask_design tool.

    Used for design get action.
    """

    model_config = {"extra": "forbid"}

    action: str = Field(..., description="Action performed (e.g., 'design_get')")
    design: Design | None = Field(None, description="Current design section")
    file_path: str = Field(..., description="Path to task file")
    summary: StatusSummary = Field(..., description="Pre-computed status summary")


def compute_status_summary(spec: SimpleTaskSpec) -> StatusSummary:
    """Compute status summary from a task specification.

    Args:
        spec: Task specification to analyze.

    Returns:
        StatusSummary with pre-computed counts and overall status.
    """
    # Count acceptance criteria
    criteria_total = len(spec.acceptance_criteria)
    criteria_completed = sum(1 for ac in spec.acceptance_criteria if ac.completed)

    # Count tasks by status
    tasks_total = 0
    tasks_completed = 0
    tasks_in_progress = 0
    tasks_not_started = 0
    tasks_blocked = 0

    if spec.tasks:
        tasks_total = len(spec.tasks)
        for task in spec.tasks:
            match task.status:
                case TaskStatus.COMPLETED:
                    tasks_completed += 1
                case TaskStatus.IN_PROGRESS:
                    tasks_in_progress += 1
                case TaskStatus.NOT_STARTED:
                    tasks_not_started += 1
                case TaskStatus.BLOCKED:
                    tasks_blocked += 1

    # Derive overall status
    if tasks_blocked > 0:
        overall_status = TaskStatus.BLOCKED
    elif tasks_in_progress > 0:
        overall_status = TaskStatus.IN_PROGRESS
    elif tasks_total > 0 and tasks_completed == tasks_total:
        overall_status = TaskStatus.COMPLETED
    else:
        overall_status = TaskStatus.NOT_STARTED

    return StatusSummary(
        branch=spec.branch,
        title=spec.title,
        overall_status=overall_status,
        criteria_total=criteria_total,
        criteria_completed=criteria_completed,
        tasks_total=tasks_total,
        tasks_completed=tasks_completed,
        tasks_in_progress=tasks_in_progress,
        tasks_not_started=tasks_not_started,
        tasks_blocked=tasks_blocked,
    )
