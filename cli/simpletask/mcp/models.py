"""MCP response models for simpletask.

This module defines Pydantic models for MCP tool responses,
including status summaries and validation results.
"""

from pydantic import BaseModel, Field

from ..core.models import SimpleTaskSpec, TaskStatus

__all__ = [
    "SimpleTaskGetResponse",
    "StatusSummary",
    "ValidationResult",
    "compute_status_summary",
]


class StatusSummary(BaseModel):
    """Pre-computed status counts for a task file."""

    model_config = {"extra": "forbid"}

    branch: str = Field(..., description="Branch/task identifier")
    title: str = Field(..., description="Task title")
    overall_status: TaskStatus = Field(..., description="Overall task status")
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


def compute_status_summary(spec: SimpleTaskSpec) -> StatusSummary:
    """Compute status summary from a task specification.

    Args:
        spec: Task specification to analyze.

    Returns:
        StatusSummary with pre-computed counts.
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

    return StatusSummary(
        branch=spec.branch,
        title=spec.title,
        overall_status=spec.status,
        criteria_total=criteria_total,
        criteria_completed=criteria_completed,
        tasks_total=tasks_total,
        tasks_completed=tasks_completed,
        tasks_in_progress=tasks_in_progress,
        tasks_not_started=tasks_not_started,
        tasks_blocked=tasks_blocked,
    )
