"""Shared pytest fixtures for simpletask tests."""

import pytest
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

import git

from simpletask.core.models import (
    SimpleTaskSpec,
    TaskStatus,
    AcceptanceCriterion,
    Task,
)
from simpletask.core.yaml_parser import write_task_file


@pytest.fixture
def sample_spec() -> SimpleTaskSpec:
    """Create a sample SimpleTaskSpec object for testing."""
    now = datetime.now(timezone.utc)
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
    """Create a temporary git repository with tasks/ directory.

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
    tasks_dir = project_root / "tasks"
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
    task_file = tmp_project / "tasks" / "test-feature.yml"
    write_task_file(task_file, sample_spec, update_timestamp=False)

    yield tmp_project, task_file
