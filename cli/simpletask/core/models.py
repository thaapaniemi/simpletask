"""Pydantic models for simpletask schema.

This module defines the data models matching simpletask.schema.json.
All models use Pydantic v2 for validation.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class TaskStatus(str, Enum):
    """Task execution status."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class AcceptanceCriterion(BaseModel):
    """A single acceptance criterion that must be met."""

    model_config = {"extra": "forbid"}

    id: str = Field(..., description="Unique identifier (e.g., AC1, AC2)")
    description: str = Field(..., description="What needs to be true")
    completed: bool = Field(default=False, description="Whether criterion is satisfied")


class FileAction(BaseModel):
    """A file to be created, modified, or deleted."""

    model_config = {"extra": "forbid"}

    path: str = Field(..., description="Path to the file")
    action: str = Field(..., pattern=r"^(create|modify|delete)$", description="Action to perform")


class CodeExample(BaseModel):
    """A code example to guide implementation."""

    model_config = {"extra": "forbid"}

    language: str = Field(..., description="Programming language")
    description: str | None = Field(None, description="What this code demonstrates")
    code: str = Field(..., description="The actual code")


class Task(BaseModel):
    """A single implementation task."""

    model_config = {"extra": "forbid"}

    id: str = Field(..., description="Unique task identifier (e.g., T001)")
    name: str = Field(..., description="Short descriptive name")
    status: TaskStatus = Field(default=TaskStatus.NOT_STARTED, description="Current status")
    goal: str = Field(..., description="What this task aims to achieve")
    steps: list[str] = Field(..., min_length=1, description="Ordered implementation steps")
    done_when: list[str] | None = Field(None, description="Conditions that indicate completion")
    code_examples: list[CodeExample] | None = Field(
        None, description="Code examples to guide implementation"
    )
    prerequisites: list[str] | None = Field(
        None, description="Task IDs that must complete before this task"
    )
    files: list[FileAction] | None = Field(None, description="Files to create or modify")


class SimpleTaskSpec(BaseModel):
    """Top-level model for task YAML files.

    This represents the complete structure of a task definition file
    stored in ./.tasks/<branch>.yml
    """

    model_config = {"extra": "forbid"}

    schema_version: str = Field(
        default="1.1", description="Schema version for compatibility tracking"
    )
    branch: str = Field(
        ..., description="Branch name / unique task identifier (also git branch name)"
    )
    title: str = Field(..., description="Human-readable task title")
    original_prompt: str = Field(..., description="Verbatim user request that initiated this task")
    created: datetime = Field(..., description="Timestamp when the task was created")
    acceptance_criteria: list[AcceptanceCriterion] = Field(
        ..., min_length=1, description="Criteria that define task completion"
    )
    constraints: list[str] | None = Field(
        None, description="Boundaries and rules the agent must follow"
    )
    context: dict[str, Any] | None = Field(
        None, description="Flexible context for requirements, dependencies, etc."
    )
    tasks: list[Task] | None = Field(None, description="List of implementation tasks")

    @field_validator("tasks")
    @classmethod
    def validate_prerequisites_exist(cls, v: list[Task] | None) -> list[Task] | None:
        """Ensure all prerequisite task IDs reference existing tasks."""
        if not v:
            return v

        task_ids = {task.id for task in v}

        for task in v:
            if task.prerequisites:
                for prereq in task.prerequisites:
                    if prereq not in task_ids:
                        raise ValueError(
                            f"Task {task.id} has invalid prerequisite '{prereq}' "
                            f"(task does not exist in task list)"
                        )
        return v


# Export all models
__all__ = [
    "AcceptanceCriterion",
    "CodeExample",
    "FileAction",
    "SimpleTaskSpec",
    "Task",
    "TaskStatus",
]
