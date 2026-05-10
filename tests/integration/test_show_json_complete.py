"""Test that show --format json includes all task fields."""

import json
from datetime import UTC, datetime
from pathlib import Path

import git
import pytest
from simpletask import app
from simpletask.core.models import (
    AcceptanceCriterion,
    LintingConfig,
    QualityRequirements,
    SimpleTaskSpec,
    Task,
    TaskStatus,
    TestingConfig,
    ToolName,
    TypeCheckConfig,
)
from typer.testing import CliRunner

runner = CliRunner()


@pytest.fixture
def json_project(tmp_path: Path, monkeypatch):
    """Set up a temporary git repo with a pre-existing task file."""
    branch_name = "feature/show-complete-test"
    normalized = "feature-show-complete-test.yml"

    repo = git.Repo.init(tmp_path)
    repo.config_writer().set_value("user", "name", "Test").release()
    repo.config_writer().set_value("user", "email", "t@t.com").release()
    (tmp_path / "README.md").write_text("# Test\n")
    repo.index.add(["README.md"])
    repo.index.commit("initial")
    new_branch = repo.create_head(branch_name)
    new_branch.checkout()

    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()
    task_file = tasks_dir / normalized

    spec = SimpleTaskSpec(
        schema_version="1.0",
        branch=branch_name,
        title="Show Complete Fields Test",
        original_prompt="Test show command includes all fields",
        created=datetime.now(UTC),
        acceptance_criteria=[
            AcceptanceCriterion(id="AC1", description="Include all fields", completed=False),
        ],
        quality_requirements=QualityRequirements(
            linting=LintingConfig(enabled=True, tool=ToolName.RUFF, args=["check", "."]),
            type_checking=TypeCheckConfig(enabled=True, tool=ToolName.MYPY, args=["."]),
            testing=TestingConfig(
                enabled=True,
                tool=ToolName.PYTEST,
                args=["--cov=cli/simpletask"],
                min_coverage=80,
            ),
        ),
        tasks=[
            Task(
                id="T001",
                name="Test task",
                status=TaskStatus.NOT_STARTED,
                goal="Verify all fields present",
                steps=["Step 1", "Step 2"],
                done_when=["All tests pass"],
                prerequisites=None,
                files=None,
                code_examples=None,
                notes=["Important note"],
                iteration=None,
            ),
        ],
        context={"version": "1.0", "environment": "test"},
    )

    spec.model_dump_json()  # Validate the model
    task_file.write_text(json.dumps(json.loads(spec.model_dump_json()), indent=2))

    monkeypatch.chdir(tmp_path)
    return tmp_path


class TestShowJsonCompleteFields:
    """Verify show --format json includes complete task information."""

    def test_show_json_includes_all_task_fields(self, json_project: Path) -> None:
        """show --format json should include steps, done_when, prerequisites, files, code_examples, notes."""
        result = runner.invoke(app, ["show", "--format", "json"])
        assert result.exit_code == 0, f"Exit code: {result.exit_code}, Output: {result.output}"

        parsed = json.loads(result.output)
        assert "tasks" in parsed

        # Check first task has all expected fields
        if parsed["tasks"]:
            task = parsed["tasks"][0]
            expected_fields = {
                "id",
                "name",
                "status",
                "goal",
                "steps",
                "done_when",
                "prerequisites",
                "files",
                "code_examples",
                "notes",
                "iteration",
            }
            for field in expected_fields:
                assert field in task, f"Task missing field: {field}"

    def test_show_json_includes_iterations_and_context(self, json_project: Path) -> None:
        """show --format json should include top-level iterations and context."""
        result = runner.invoke(app, ["show", "--format", "json"])
        assert result.exit_code == 0

        parsed = json.loads(result.output)
        assert "iterations" in parsed, "Missing iterations in output"
        assert "context" in parsed, "Missing context in output"
        assert isinstance(parsed["iterations"], list)
        assert isinstance(parsed["context"], dict)
