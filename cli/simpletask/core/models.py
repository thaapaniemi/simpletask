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


class ToolName(str, Enum):
    """Whitelisted tool names for quality checks.

    Only these tools can be executed to prevent shell injection attacks.
    """

    # Python tools
    RUFF = "ruff"
    MYPY = "mypy"
    PYTEST = "pytest"
    BLACK = "black"
    PYLINT = "pylint"
    BANDIT = "bandit"

    # TypeScript/JavaScript tools
    ESLINT = "eslint"
    TSC = "tsc"
    NPM = "npm"
    YARN = "yarn"
    JEST = "jest"

    # Go tools
    GO = "go"
    GOLANGCI_LINT = "golangci-lint"
    GOSEC = "gosec"

    # Rust tools
    CARGO = "cargo"
    CLIPPY = "clippy"

    # Java tools
    MVN = "mvn"
    GRADLE = "gradle"

    # Other tools
    MAKE = "make"


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


def validate_no_shell_metacharacters(args: list[str]) -> list[str]:
    """Shared validator for rejecting dangerous shell metacharacters.

    This prevents shell injection attacks while allowing legitimate characters
    like parentheses, brackets, and braces that are commonly used in tool arguments.

    Args:
        args: List of command-line arguments to validate

    Returns:
        The validated args list

    Raises:
        ValueError: If any argument contains dangerous shell metacharacters
    """
    # Only block actually dangerous shell metacharacters
    # Parentheses, brackets, braces are legitimate in many tool arguments
    # Example: pytest -k "(test_user or test_admin) and not slow"
    dangerous_chars = {";", "&", "|", "`", "$", ">", "<"}

    for arg in args:
        if any(char in arg for char in dangerous_chars):
            raise ValueError(
                f"Argument '{arg}' contains shell metacharacters ({', '.join(sorted(dangerous_chars))}). "
                f"Use structured arguments only, not shell commands."
            )
    return args


class LintingConfig(BaseModel):
    """Configuration for code linting checks."""

    model_config = {"extra": "forbid"}

    enabled: bool = Field(..., description="Whether linting is enabled")
    tool: ToolName = Field(..., description="Tool to run linting check")
    args: list[str] = Field(default_factory=list, description="Arguments to pass to the tool")
    timeout: int | None = Field(
        default=300, ge=1, description="Timeout in seconds for linting check (default: 300)"
    )

    @field_validator("args")
    @classmethod
    def validate_args(cls, v: list[str]) -> list[str]:
        """Validate that arguments don't contain dangerous shell metacharacters."""
        return validate_no_shell_metacharacters(v)


class TypeCheckConfig(BaseModel):
    """Configuration for type checking."""

    model_config = {"extra": "forbid"}

    enabled: bool = Field(..., description="Whether type checking is enabled")
    tool: ToolName = Field(..., description="Tool to run type check")
    args: list[str] = Field(default_factory=list, description="Arguments to pass to the tool")
    timeout: int | None = Field(
        default=300, ge=1, description="Timeout in seconds for type checking (default: 300)"
    )

    @field_validator("args")
    @classmethod
    def validate_args(cls, v: list[str]) -> list[str]:
        """Validate that arguments don't contain dangerous shell metacharacters."""
        return validate_no_shell_metacharacters(v)


class TestingConfig(BaseModel):
    """Configuration for test execution."""

    model_config = {"extra": "forbid"}

    enabled: bool = Field(..., description="Whether testing is enabled")
    tool: ToolName = Field(..., description="Tool to run tests")
    args: list[str] = Field(default_factory=list, description="Arguments to pass to the tool")
    min_coverage: int | None = Field(
        None, ge=0, le=100, description="Minimum test coverage percentage (0-100)"
    )
    timeout: int | None = Field(
        default=300, ge=1, description="Timeout in seconds for test execution (default: 300)"
    )

    @field_validator("args")
    @classmethod
    def validate_args(cls, v: list[str]) -> list[str]:
        """Validate that arguments don't contain dangerous shell metacharacters."""
        return validate_no_shell_metacharacters(v)


class SecurityCheckConfig(BaseModel):
    """Configuration for security checks."""

    model_config = {"extra": "forbid"}

    enabled: bool = Field(default=False, description="Whether security checks are enabled")
    tool: ToolName | None = Field(None, description="Tool to run security check")
    args: list[str] = Field(default_factory=list, description="Arguments to pass to the tool")
    timeout: int | None = Field(
        default=300, ge=1, description="Timeout in seconds for security check (default: 300)"
    )

    @field_validator("args")
    @classmethod
    def validate_args(cls, v: list[str]) -> list[str]:
        """Validate that arguments don't contain dangerous shell metacharacters."""
        return validate_no_shell_metacharacters(v)


class DesignReference(BaseModel):
    """A reference implementation to follow."""

    model_config = {"extra": "forbid"}

    path: str = Field(..., description="Path to the reference implementation")
    reason: str = Field(..., description="Why this reference is relevant")

    @field_validator("path")
    @classmethod
    def validate_path_safe(cls, v: str) -> str:
        """Validate that path is safe and doesn't leak sensitive information.

        Checks:
        - Path doesn't contain suspicious patterns like secrets/credentials
        - Path doesn't escape project with ../..
        - Path uses forward slashes (normalized)

        Note: We don't check if path exists because task files may be created
        before the referenced files exist during planning.
        """
        # Normalize path separators
        normalized = v.replace("\\", "/")

        # Check for path traversal attempts
        if ".." in normalized:
            raise ValueError(
                f"Path '{v}' contains '..' which may indicate path traversal. "
                f"Use relative paths from project root without '..'."
            )

        # Check for absolute paths (should be relative to project)
        if normalized.startswith("/") or (len(normalized) > 1 and normalized[1] == ":"):
            raise ValueError(
                f"Path '{v}' appears to be absolute. "
                f"Use relative paths from project root (e.g., 'src/module/file.py')."
            )

        # Check for common sensitive file patterns
        sensitive_patterns = [".env", ".key", ".pem", ".crt", "credentials", "secrets", "password"]
        path_lower = normalized.lower()
        for pattern in sensitive_patterns:
            if pattern in path_lower:
                raise ValueError(
                    f"Path '{v}' may reference sensitive files (contains '{pattern}'). "
                    f"Reference implementations should point to source code, not secrets/credentials."
                )

        return v


class ArchitecturalPattern(str, Enum):
    """Common architectural and design patterns."""

    REPOSITORY = "repository"
    SERVICE_LAYER = "service_layer"
    FACTORY = "factory"
    STRATEGY = "strategy"
    ADAPTER = "adapter"
    OBSERVER = "observer"
    COMMAND = "command"
    MVC = "mvc"
    CLEAN_ARCHITECTURE = "clean_architecture"
    HEXAGONAL = "hexagonal"
    DEPENDENCY_INJECTION = "dependency_injection"
    SINGLETON = "singleton"
    BUILDER = "builder"
    DECORATOR = "decorator"


class ErrorHandlingStrategy(str, Enum):
    """Error handling strategies."""

    EXCEPTIONS = "exceptions"
    RESULT_TYPE = "result_type"
    ERROR_CODES = "error_codes"
    CALLBACKS = "callbacks"
    PANIC_RECOVER = "panic_recover"


class SecurityCategory(str, Enum):
    """Categories of security requirements."""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    CRYPTOGRAPHY = "cryptography"
    INPUT_VALIDATION = "input_validation"
    OUTPUT_ENCODING = "output_encoding"
    SESSION_MANAGEMENT = "session_management"
    SECURE_COMMUNICATION = "secure_communication"
    DATA_PROTECTION = "data_protection"
    AUDIT_LOGGING = "audit_logging"


class SecurityRequirement(BaseModel):
    """A specific security requirement with category and description."""

    model_config = {"extra": "forbid"}

    category: SecurityCategory = Field(..., description="Security category")
    description: str = Field(..., description="Specific security requirement")


class Design(BaseModel):
    """Design guidance and architectural context for implementation."""

    model_config = {"extra": "forbid"}

    patterns: list[ArchitecturalPattern] | None = Field(
        None, description="Design patterns and architectural patterns to follow"
    )
    reference_implementations: list[DesignReference] | None = Field(
        None, description="Existing code to use as reference"
    )
    architectural_constraints: list[str] | None = Field(
        None, min_length=1, description="Architectural rules and constraints"
    )
    security: list[SecurityRequirement] | None = Field(
        None, description="Security requirements and considerations"
    )
    error_handling: ErrorHandlingStrategy | None = Field(
        None, description="Error handling strategy to use"
    )


class QualityRequirements(BaseModel):
    """Quality requirements and checks for the task."""

    model_config = {"extra": "forbid"}

    linting: LintingConfig = Field(..., description="Linting configuration")
    type_checking: TypeCheckConfig | None = Field(None, description="Type checking configuration")
    testing: TestingConfig = Field(..., description="Testing configuration")
    security_check: SecurityCheckConfig | None = Field(
        None, description="Security check configuration"
    )


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

    Current schema version: 1.0
    """

    model_config = {"extra": "forbid"}

    schema_version: str = Field(
        default="1.0", description="Schema version for compatibility tracking"
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
    quality_requirements: QualityRequirements | None = Field(
        None, description="Quality gates and checks for the task"
    )
    design: Design | None = Field(None, description="Design guidance and architectural context")
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
    "Design",
    "DesignReference",
    "FileAction",
    "LintingConfig",
    "QualityRequirements",
    "SecurityCheckConfig",
    "SimpleTaskSpec",
    "Task",
    "TaskStatus",
    "TestingConfig",
    "ToolName",
    "TypeCheckConfig",
]
