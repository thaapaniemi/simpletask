"""MCP response models for simpletask.

This module defines Pydantic models for MCP tool responses,
including status summaries and validation results.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from ..core.models import (
    AcceptanceCriterion,
    Design,
    Iteration,
    QualityRequirements,
    SimpleTaskSpec,
    Task,
    TaskStatus,
)

__all__ = [
    "BatchTaskOperation",
    "IterationSummary",
    "QualityCheckResult",
    "SimpleTaskBatchResponse",
    "SimpleTaskConstraintResponse",
    "SimpleTaskContextResponse",
    "SimpleTaskDesignResponse",
    "SimpleTaskGetResponse",
    "SimpleTaskItemResponse",
    "SimpleTaskIterationResponse",
    "SimpleTaskNoteResponse",
    "SimpleTaskQualityResponse",
    "SimpleTaskWriteResponse",
    "StatusSummary",
    "ValidationResult",
    "compute_status_summary",
]


class BatchTaskOperation(BaseModel):
    """A single operation in a batch task modification request.

    Used by simpletask_task tool with action='batch' to perform multiple
    task operations (add, remove, update) atomically.
    """

    model_config = {"extra": "forbid"}

    op: Literal["add", "remove", "update"] = Field(
        ..., description="Operation type: 'add', 'remove', or 'update'"
    )
    task_id: str | None = Field(None, description="Task ID (required for remove/update)")
    name: str | None = Field(None, description="Task name (required for add)")
    goal: str | None = Field(None, description="Task goal/description")
    status: str | None = Field(None, description="Task status (for update)")
    steps: list[str] | None = Field(None, description="Task steps (for add)")
    done_when: list[str] | None = Field(None, description="Completion conditions")
    prerequisites: list[str] | None = Field(None, description="Task IDs that must complete first")
    files: list[dict] | None = Field(None, description="Files to create/modify/delete")
    code_examples: list[dict] | None = Field(None, description="Code patterns to follow")
    iteration: int | None = Field(
        None, description="Iteration ID to assign task to (for add/update)"
    )

    @model_validator(mode="after")
    def validate_required_fields(self) -> "BatchTaskOperation":
        """Validate that required fields are present based on operation type."""
        if self.op in ("remove", "update") and not self.task_id:
            raise ValueError(f"task_id is required for {self.op} operation")
        if self.op == "add" and not self.name:
            raise ValueError("name is required for add operation")
        return self


class IterationSummary(BaseModel):
    """Per-iteration task status counts."""

    model_config = {"extra": "forbid"}

    id: int = Field(..., description="Iteration identifier")
    label: str = Field(..., description="Iteration label/name")
    tasks_total: int = Field(0, description="Total tasks in this iteration")
    tasks_completed: int = Field(0, description="Completed tasks in this iteration")
    tasks_in_progress: int = Field(0, description="In-progress tasks in this iteration")
    tasks_not_started: int = Field(0, description="Not started tasks in this iteration")
    tasks_blocked: int = Field(0, description="Blocked tasks in this iteration")
    tasks_paused: int = Field(0, description="Paused tasks in this iteration")


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
    tasks_paused: int = Field(0, description="Paused tasks")
    notes_total: int = Field(0, description="Total notes (root + task-level)")
    iteration_summaries: list["IterationSummary"] | None = Field(
        None, description="Per-iteration task counts (None if no iterations defined)"
    )


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
    new_item_ids: list[str] = Field(
        default_factory=list, description="IDs of newly created items (for add operations)"
    )


class SimpleTaskBatchResponse(SimpleTaskWriteResponse):
    """Response model for batch task operations.

    Extends SimpleTaskWriteResponse with new_item_ids for tracking multiple
    created items from batch add operations.
    """


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


class SimpleTaskNoteResponse(BaseModel):
    """Response model for simpletask_note tool with action='list'.

    Returns notes from root-level and/or task-level.
    The task_notes dict is sparse - only tasks with notes are included.
    """

    model_config = {"extra": "forbid"}

    action: str = Field(..., description="Action performed (e.g., 'note_list')")
    root_notes: list[str] | None = Field(None, description="Root-level notes")
    task_notes: dict[str, list[str]] = Field(
        default_factory=dict, description="Task notes (sparse dict: task_id -> notes)"
    )
    total_count: int = Field(..., description="Total number of notes (root + task)")
    file_path: str = Field(..., description="Path to task file")
    summary: StatusSummary = Field(..., description="Pre-computed status summary")


class SimpleTaskConstraintResponse(BaseModel):
    """Response model for simpletask_constraint tool with action='list'.

    Returns all implementation constraints.
    """

    model_config = {"extra": "forbid"}

    action: str = Field(..., description="Action performed (e.g., 'constraint_list')")
    constraints: list[str] | None = Field(None, description="List of constraints")
    file_path: str = Field(..., description="Path to task file")
    summary: StatusSummary = Field(..., description="Pre-computed status summary")


class SimpleTaskContextResponse(BaseModel):
    """Response model for simpletask_context tool with action='show'.

    Returns all context key-value pairs.
    """

    model_config = {"extra": "forbid"}

    action: str = Field(..., description="Action performed (e.g., 'context_show')")
    context: dict[str, Any] | None = Field(None, description="Context key-value pairs")
    file_path: str = Field(..., description="Path to task file")
    summary: StatusSummary = Field(..., description="Pre-computed status summary")


class SimpleTaskIterationResponse(BaseModel):
    """Response model for simpletask_iteration tool.

    Used for iteration add/list/get/remove actions.
    """

    model_config = {"extra": "forbid"}

    action: str = Field(
        ..., description="Action performed (e.g., 'iteration_added', 'iteration_list')"
    )
    iterations: list[Iteration] | None = Field(
        None, description="List of iterations (for list/get actions)"
    )
    file_path: str = Field(..., description="Path to task file")
    summary: StatusSummary = Field(..., description="Pre-computed status summary")


def _increment_status_counts(counts: dict[str, int], status: TaskStatus) -> None:
    """Increment the appropriate status counter in a counts dict.

    Args:
        counts: Dict with task status count keys (tasks_completed, tasks_in_progress, etc.)
        status: The task status to increment.
    """
    match status:
        case TaskStatus.COMPLETED:
            counts["tasks_completed"] += 1
        case TaskStatus.IN_PROGRESS:
            counts["tasks_in_progress"] += 1
        case TaskStatus.NOT_STARTED:
            counts["tasks_not_started"] += 1
        case TaskStatus.BLOCKED:
            counts["tasks_blocked"] += 1
        case TaskStatus.PAUSED:
            counts["tasks_paused"] += 1


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
    global_counts: dict[str, int] = {
        "tasks_completed": 0,
        "tasks_in_progress": 0,
        "tasks_not_started": 0,
        "tasks_blocked": 0,
        "tasks_paused": 0,
    }
    tasks_total = 0

    if spec.tasks:
        tasks_total = len(spec.tasks)
        for task in spec.tasks:
            _increment_status_counts(global_counts, task.status)

    # Derive overall status
    # Priority: blocked > paused > in_progress > completed > not_started
    if global_counts["tasks_blocked"] > 0:
        overall_status = TaskStatus.BLOCKED
    elif global_counts["tasks_paused"] > 0:
        overall_status = TaskStatus.PAUSED
    elif global_counts["tasks_in_progress"] > 0:
        overall_status = TaskStatus.IN_PROGRESS
    elif tasks_total > 0 and global_counts["tasks_completed"] == tasks_total:
        overall_status = TaskStatus.COMPLETED
    else:
        overall_status = TaskStatus.NOT_STARTED

    # Count total notes (root + task-level)
    notes_total = 0
    if spec.notes:
        notes_total += len(spec.notes)
    if spec.tasks:
        for task in spec.tasks:
            if task.notes:
                notes_total += len(task.notes)

    # Build per-iteration summaries
    iteration_summaries: list[IterationSummary] | None = None
    if spec.iterations:
        # Accumulate counts in plain dicts to avoid mutating Pydantic model instances
        iter_counts: dict[int, dict[str, int]] = {
            it.id: {
                "tasks_total": 0,
                "tasks_completed": 0,
                "tasks_in_progress": 0,
                "tasks_not_started": 0,
                "tasks_blocked": 0,
                "tasks_paused": 0,
            }
            for it in spec.iterations
        }
        if spec.tasks:
            for task in spec.tasks:
                if task.iteration is not None and task.iteration in iter_counts:
                    counts = iter_counts[task.iteration]
                    counts["tasks_total"] += 1
                    _increment_status_counts(counts, task.status)
        # iter_counts keys are exactly spec.iterations IDs — no guard needed
        iteration_summaries = [
            IterationSummary(id=it.id, label=it.label, **iter_counts[it.id])
            for it in spec.iterations
        ]

    return StatusSummary(
        branch=spec.branch,
        title=spec.title,
        overall_status=overall_status,
        criteria_total=criteria_total,
        criteria_completed=criteria_completed,
        tasks_total=tasks_total,
        notes_total=notes_total,
        iteration_summaries=iteration_summaries,
        **global_counts,
    )
