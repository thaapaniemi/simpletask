"""Integration tests for task CLI field options.

Tests verify that CLI task add and task update commands properly handle
--step, --done-when, --prerequisite, and --file options.
"""

import subprocess
from datetime import UTC, datetime
from pathlib import Path

import git
import pytest
from simpletask.core.models import (
    AcceptanceCriterion,
    FileAction,
    SimpleTaskSpec,
    Task,
    TaskStatus,
)
from simpletask.core.yaml_parser import parse_task_file, write_task_file


@pytest.fixture
def task_cli_project(tmp_path: Path) -> tuple[Path, str, Path]:
    """Set up a temporary git repo with a pre-existing task file.

    Args:
        tmp_path: Pytest temp directory fixture

    Returns:
        Tuple of (project_root, branch_name, task_file_path)
    """
    branch_name = "feature/cli-fields-test"
    normalized_filename = "feature-cli-fields-test.yml"

    # Initialize git repository
    repo = git.Repo.init(tmp_path)

    # Create initial commit
    initial_file = tmp_path / "README.md"
    initial_file.write_text("# Test Project\n")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")

    # Create and checkout feature branch
    new_branch = repo.create_head(branch_name)
    new_branch.checkout()

    # Create .tasks directory
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir(exist_ok=True)

    # Create initial task file
    task_file = tasks_dir / normalized_filename
    spec = SimpleTaskSpec(
        schema_version="1.0",
        branch=branch_name,
        title="CLI Fields Test",
        original_prompt="Test CLI task field options",
        created=datetime.now(UTC),
        acceptance_criteria=[
            AcceptanceCriterion(id="AC1", description="CLI field options work", completed=False),
        ],
        constraints=None,
        context=None,
        notes=None,
        quality_requirements=None,
        design=None,
        iterations=None,
        tasks=[
            Task(
                id="T001",
                name="Existing Task",
                status=TaskStatus.NOT_STARTED,
                goal="Initial task for testing",
                steps=["Initial step"],
                done_when=None,
                code_examples=None,
                prerequisites=None,
                files=None,
                notes=None,
                iteration=None,
            ),
        ],
    )
    write_task_file(task_file, spec)

    return tmp_path, branch_name, task_file


class TestTaskAddNewOptions:
    """Tests for task add command with new field options."""

    def test_task_add_with_steps(self, task_cli_project: tuple[Path, str, Path]) -> None:
        """Test that task add --step option persists steps to YAML."""
        project_root, _, _ = task_cli_project

        result = subprocess.run(
            [
                "simpletask",
                "task",
                "add",
                "Test Task",
                "--step",
                "Step one",
                "--step",
                "Step two",
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # Find the task file and verify steps
        tasks_dir = project_root / ".tasks"
        task_file = next(iter(tasks_dir.glob("*.yml")))
        spec = parse_task_file(task_file)

        # Find the newly created task
        new_task = None
        for task in spec.tasks or []:
            if task.name == "Test Task":
                new_task = task
                break

        assert new_task is not None, "New task not found"
        assert new_task.steps == ["Step one", "Step two"], (
            f"Steps not persisted correctly: {new_task.steps}"
        )

    def test_task_add_with_done_when(self, task_cli_project: tuple[Path, str, Path]) -> None:
        """Test that task add --done-when option persists conditions to YAML."""
        project_root, _, _ = task_cli_project

        result = subprocess.run(
            [
                "simpletask",
                "task",
                "add",
                "Deploy Task",
                "--done-when",
                "Pipeline green",
                "--done-when",
                "Coverage > 80%",
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # Verify done_when conditions
        tasks_dir = project_root / ".tasks"
        task_file = next(iter(tasks_dir.glob("*.yml")))
        spec = parse_task_file(task_file)

        deploy_task = None
        for task in spec.tasks or []:
            if task.name == "Deploy Task":
                deploy_task = task
                break

        assert deploy_task is not None, "Deploy task not found"
        assert deploy_task.done_when == ["Pipeline green", "Coverage > 80%"], (
            f"Done-when conditions not persisted: {deploy_task.done_when}"
        )

    def test_task_add_with_prerequisites(self, task_cli_project: tuple[Path, str, Path]) -> None:
        """Test that task add --prerequisite option links tasks."""
        project_root, _, _ = task_cli_project

        # First add a task that will be a prerequisite
        result1 = subprocess.run(
            ["simpletask", "task", "add", "Task A"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        assert result1.returncode == 0, f"Failed to add Task A: {result1.stderr}"

        # Extract the ID of Task A (format: "Added task T00X: Task A")
        task_a_id = None
        for line in result1.stdout.split("\n"):
            if "Task A" in line and "Added task" in line:
                # Extract T00X format
                parts = line.split()
                for part in parts:
                    # Remove trailing colon if present
                    cleaned_part = part.rstrip(":")
                    if cleaned_part.startswith("T") and cleaned_part[1:].isdigit():
                        task_a_id = cleaned_part
                        break

        assert task_a_id is not None, f"Could not extract Task A ID from output: {result1.stdout}"

        # Now add Task B with Task A as prerequisite
        result2 = subprocess.run(
            [
                "simpletask",
                "task",
                "add",
                "Task B",
                "--prerequisite",
                task_a_id,
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        assert result2.returncode == 0, f"Failed to add Task B: {result2.stderr}"

        # Verify the prerequisite link
        tasks_dir = project_root / ".tasks"
        task_file = next(iter(tasks_dir.glob("*.yml")))
        spec = parse_task_file(task_file)

        task_b = None
        for task in spec.tasks or []:
            if task.name == "Task B":
                task_b = task
                break

        assert task_b is not None, "Task B not found"
        assert task_b.prerequisites == [task_a_id], (
            f"Prerequisites not set correctly: {task_b.prerequisites}"
        )

    def test_task_add_with_file(self, task_cli_project: tuple[Path, str, Path]) -> None:
        """Test that task add --file option persists FileAction objects."""
        project_root, _, _ = task_cli_project

        result = subprocess.run(
            [
                "simpletask",
                "task",
                "add",
                "Models Task",
                "--file",
                "src/models.py:create",
                "--file",
                "tests/test_models.py:create",
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # Verify file actions
        tasks_dir = project_root / ".tasks"
        task_file = next(iter(tasks_dir.glob("*.yml")))
        spec = parse_task_file(task_file)

        models_task = None
        for task in spec.tasks or []:
            if task.name == "Models Task":
                models_task = task
                break

        assert models_task is not None, "Models task not found"
        assert len(models_task.files or []) == 2, (
            f"Expected 2 files, got {len(models_task.files or [])}"
        )
        assert models_task.files[0] == FileAction(path="src/models.py", action="create")
        assert models_task.files[1] == FileAction(path="tests/test_models.py", action="create")

    def test_task_add_file_invalid_format(self, task_cli_project: tuple[Path, str, Path]) -> None:
        """Test that invalid --file format is rejected with clear error."""
        project_root, _, _ = task_cli_project

        result = subprocess.run(
            [
                "simpletask",
                "task",
                "add",
                "Bad File Task",
                "--file",
                "badformat",  # Missing colon
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0, "Command should fail with invalid file format"
        # Error message should mention the format or path:action pattern
        assert (
            "Invalid" in result.stderr
            or "path:action" in result.stderr
            or "format" in result.stderr.lower()
        ), f"Error message should mention format issue, got: {result.stderr}"

    def test_task_update_with_steps(self, task_cli_project: tuple[Path, str, Path]) -> None:
        """Test that task update --step option replaces steps."""
        project_root, _, _ = task_cli_project

        # Update the existing T001 task with new steps
        result = subprocess.run(
            [
                "simpletask",
                "task",
                "update",
                "T001",
                "--step",
                "New step",
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # Verify steps were replaced
        tasks_dir = project_root / ".tasks"
        task_file = next(iter(tasks_dir.glob("*.yml")))
        spec = parse_task_file(task_file)

        t001 = None
        for task in spec.tasks or []:
            if task.id == "T001":
                t001 = task
                break

        assert t001 is not None, "T001 not found"
        assert t001.steps == ["New step"], f"Steps not replaced correctly: {t001.steps}"

    def test_task_update_with_file(self, task_cli_project: tuple[Path, str, Path]) -> None:
        """Test that task update --file option replaces file actions."""
        project_root, _, _ = task_cli_project

        # Update T001 with file actions
        result = subprocess.run(
            [
                "simpletask",
                "task",
                "update",
                "T001",
                "--file",
                "src/auth.py:modify",
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # Verify file actions
        tasks_dir = project_root / ".tasks"
        task_file = next(iter(tasks_dir.glob("*.yml")))
        spec = parse_task_file(task_file)

        t001 = None
        for task in spec.tasks or []:
            if task.id == "T001":
                t001 = task
                break

        assert t001 is not None, "T001 not found"
        assert len(t001.files or []) == 1, f"Expected 1 file, got {len(t001.files or [])}"
        assert t001.files[0] == FileAction(path="src/auth.py", action="modify")
