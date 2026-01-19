"""Shared pytest fixtures for simpletask tests."""

from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path

import git
import pytest
from simpletask.core.models import (
    AcceptanceCriterion,
    SimpleTaskSpec,
    Task,
    TaskStatus,
)
from simpletask.core.yaml_parser import write_task_file


@pytest.fixture
def sample_spec() -> SimpleTaskSpec:
    """Create a sample SimpleTaskSpec object for testing."""
    now = datetime.now(UTC)
    return SimpleTaskSpec(
        schema_version="1.0",
        branch="test-feature",
        title="Test Feature",
        original_prompt="Implement a test feature for testing",
        status=TaskStatus.NOT_STARTED,
        created=now,
        updated=now,
        acceptance_criteria=[
            AcceptanceCriterion(id="AC1", description="Feature works correctly", completed=False),
            AcceptanceCriterion(id="AC2", description="Tests pass", completed=False),
        ],
        constraints=["Must work in all browsers"],
        context={"requirements": ["Python 3.11+"], "dependencies": ["pytest"]},
        tasks=[
            Task(
                id="T001",
                name="Setup environment",
                status=TaskStatus.NOT_STARTED,
                goal="Configure development environment",
                steps=["Install dependencies", "Setup config"],
                prerequisites=None,
            ),
            Task(
                id="T002",
                name="Implement feature",
                status=TaskStatus.NOT_STARTED,
                goal="Build the core feature",
                steps=["Write code", "Add tests"],
                prerequisites=["T001"],
            ),
        ],
    )


@pytest.fixture
def sample_yaml_content() -> str:
    """Return valid task YAML content as string."""
    return """schema_version: '1.0'
branch: test-feature
title: Test Feature
original_prompt: Implement a test feature for testing
status: not_started
created: '2026-01-13T10:00:00Z'
updated: '2026-01-13T10:00:00Z'
acceptance_criteria:
  - id: AC1
    description: Feature works correctly
    completed: false
context:
  requirements:
    - Python 3.11+
tasks:
  - id: T001
    name: Setup environment
    status: not_started
    goal: Configure development environment
    steps:
      - Install dependencies
"""


@pytest.fixture
def tmp_task_file(tmp_path: Path, sample_spec: SimpleTaskSpec) -> Path:
    """Create a temporary task YAML file with sample data.

    Args:
        tmp_path: pytest's tmp_path fixture
        sample_spec: Sample task specification

    Returns:
        Path to the created task file
    """
    task_file = tmp_path / "test-feature.yml"
    write_task_file(task_file, sample_spec, update_timestamp=False)
    return task_file


@pytest.fixture
def tmp_project(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary git repository with .tasks/ directory.

    Args:
        tmp_path: pytest's tmp_path fixture

    Yields:
        Path to the project root
    """
    project_root = tmp_path / "test-project"
    project_root.mkdir()

    # Initialize git repo
    repo = git.Repo.init(project_root)

    # Create initial commit
    (project_root / "README.md").write_text("# Test Project")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")

    # Create tasks directory
    tasks_dir = project_root / ".tasks"
    tasks_dir.mkdir()

    yield project_root

    # Cleanup handled by tmp_path fixture


@pytest.fixture
def tmp_project_with_task(
    tmp_project: Path, sample_spec: SimpleTaskSpec
) -> Generator[tuple[Path, Path], None, None]:
    """Create a temporary project with a task file.

    Args:
        tmp_project: Temporary project root
        sample_spec: Sample task specification

    Yields:
        Tuple of (project_root, task_file_path)
    """
    task_file = tmp_project / ".tasks" / "test-feature.yml"
    write_task_file(task_file, sample_spec, update_timestamp=False)

    yield tmp_project, task_file


@pytest.fixture
def tmp_git_project_with_task(
    tmp_project: Path,
) -> Generator[tuple[Path, str, Path], None, None]:
    """Create a git project with a branch containing slashes and its task file.

    This fixture specifically tests issue #4: branch names with slashes.

    Args:
        tmp_project: Temporary project root

    Yields:
        Tuple of (project_root, branch_name, task_file_path)
    """
    branch_name = "feature/mcp-server-support"
    normalized_filename = "feature-mcp-server-support.yml"

    # Create and checkout the branch
    repo = git.Repo(tmp_project)
    new_branch = repo.create_head(branch_name)
    new_branch.checkout()

    # Create a task file with the normalized filename
    task_file = tmp_project / ".tasks" / normalized_filename

    # Create task spec with the original branch name (with slash)
    now = datetime.now(UTC)
    spec = SimpleTaskSpec(
        schema_version="1.0",
        branch=branch_name,  # Original branch name with slash
        title="Test Task",
        original_prompt="Test task for branch normalization",
        status=TaskStatus.NOT_STARTED,
        created=now,
        updated=now,
        acceptance_criteria=[
            AcceptanceCriterion(id="AC1", description="Task file is found", completed=False),
        ],
        constraints=[],
        context={},
        tasks=[
            Task(
                id="T001",
                name="Test task",
                status=TaskStatus.NOT_STARTED,
                goal="Verify branch normalization works",
                steps=["Run simpletask show"],
                prerequisites=None,
            ),
        ],
    )

    write_task_file(task_file, spec, update_timestamp=False)

    yield tmp_project, branch_name, task_file


@pytest.fixture
def sample_spec_no_tasks() -> SimpleTaskSpec:
    """Task spec with no implementation tasks."""
    now = datetime.now(UTC)
    return SimpleTaskSpec(
        schema_version="1.0",
        branch="test-no-tasks",
        title="Test No Tasks",
        original_prompt="Test prompt",
        status=TaskStatus.NOT_STARTED,
        created=now,
        updated=now,
        acceptance_criteria=[
            AcceptanceCriterion(id="AC1", description="Criterion 1", completed=False),
        ],
        tasks=None,  # No tasks
    )


@pytest.fixture
def sample_spec_mixed_statuses() -> SimpleTaskSpec:
    """Task spec with all task statuses represented."""
    now = datetime.now(UTC)
    return SimpleTaskSpec(
        schema_version="1.0",
        branch="test-mixed",
        title="Test Mixed Statuses",
        original_prompt="Test prompt",
        status=TaskStatus.IN_PROGRESS,
        created=now,
        updated=now,
        acceptance_criteria=[
            AcceptanceCriterion(id="AC1", description="Done", completed=True),
            AcceptanceCriterion(id="AC2", description="Not done", completed=False),
        ],
        tasks=[
            Task(
                id="T001",
                name="Done",
                status=TaskStatus.COMPLETED,
                goal="G",
                steps=["S"],
            ),
            Task(
                id="T002",
                name="WIP",
                status=TaskStatus.IN_PROGRESS,
                goal="G",
                steps=["S"],
            ),
            Task(
                id="T003",
                name="Blocked",
                status=TaskStatus.BLOCKED,
                goal="G",
                steps=["S"],
            ),
            Task(
                id="T004",
                name="Todo",
                status=TaskStatus.NOT_STARTED,
                goal="G",
                steps=["S"],
            ),
        ],
    )


@pytest.fixture
def sample_spec_all_completed() -> SimpleTaskSpec:
    """Task spec with all criteria and tasks completed."""
    now = datetime.now(UTC)
    return SimpleTaskSpec(
        schema_version="1.0",
        branch="test-all-done",
        title="Test All Completed",
        original_prompt="Test prompt",
        status=TaskStatus.COMPLETED,
        created=now,
        updated=now,
        acceptance_criteria=[
            AcceptanceCriterion(id="AC1", description="Criterion 1", completed=True),
            AcceptanceCriterion(id="AC2", description="Criterion 2", completed=True),
        ],
        tasks=[
            Task(
                id="T001",
                name="Task 1",
                status=TaskStatus.COMPLETED,
                goal="G",
                steps=["S"],
            ),
            Task(
                id="T002",
                name="Task 2",
                status=TaskStatus.COMPLETED,
                goal="G",
                steps=["S"],
            ),
        ],
    )


@pytest.fixture
def sample_spec_minimal() -> SimpleTaskSpec:
    """Minimum valid spec."""
    now = datetime.now(UTC)
    return SimpleTaskSpec(
        schema_version="1.0",
        branch="test-minimal",
        title="Minimal",
        original_prompt="Test",
        status=TaskStatus.NOT_STARTED,
        created=now,
        updated=now,
        acceptance_criteria=[
            AcceptanceCriterion(id="AC1", description="Done", completed=False),
        ],
    )
