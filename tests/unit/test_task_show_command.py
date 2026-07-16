"""Unit tests for the task detail command."""

from datetime import UTC, datetime
from unittest.mock import patch

from simpletask.commands.task.show import show_command
from simpletask.core.models import (
    AcceptanceCriterion,
    CodeExample,
    FileAction,
    Iteration,
    SimpleTaskSpec,
    Task,
    TaskStatus,
)
from simpletask.core.yaml_parser import write_task_file


def test_task_show_displays_all_populated_fields_for_requested_task(tmp_path, monkeypatch) -> None:
    """Render every populated field of the selected task, but not another task."""
    selected_task = Task(
        id="T001",
        name="Selected task",
        status=TaskStatus.IN_PROGRESS,
        goal="Show all task fields",
        steps=["First step", "Second step"],
        done_when=["Output is complete"],
        prerequisites=["T000"],
        files=[FileAction(path="src/example.py", action="create")],
        code_examples=[CodeExample(language="python", description="Example", code="pass")],
        notes=["Selected task note"],
        iteration=1,
    )
    spec = SimpleTaskSpec(
        schema_version="1.0",
        branch="test-branch",
        title="Test task details",
        original_prompt="Test prompt",
        created=datetime.now(UTC),
        acceptance_criteria=[AcceptanceCriterion(id="AC1", description="Criterion")],
        iterations=[Iteration(id=1, label="Sprint 1")],
        tasks=[
            Task(
                id="T000",
                name="Prerequisite task",
                status=TaskStatus.COMPLETED,
                goal="Prerequisite",
                steps=["Complete prerequisite"],
            ),
            selected_task,
            Task(
                id="T002",
                name="Unrelated task",
                goal="This must not be displayed",
                steps=["Unrelated step"],
            ),
        ],
    )
    task_file = tmp_path / ".tasks" / "test-branch.yml"
    task_file.parent.mkdir()
    write_task_file(task_file, spec)
    monkeypatch.chdir(tmp_path)

    with patch("simpletask.commands.task.show.get_task_file_path", return_value=task_file):
        with patch("simpletask.commands.task.show.ensure_project") as mock_project:
            mock_project.return_value.root = tmp_path
            with patch("simpletask.commands.task.show.console") as mock_console:
                show_command(task_id="T001", branch="test-branch")

    output = "\n".join(str(call) for call in mock_console.print.call_args_list)
    for expected in (
        "T001",
        "Selected task",
        "in_progress",
        "Show all task fields",
        "First step",
        "Second step",
        "Output is complete",
        "T000",
        "src/example.py",
        "create",
        "python",
        "Example",
        "pass",
        "Selected task note",
        "1",
    ):
        assert expected in output
    assert "T002" not in output
    assert "Unrelated task" not in output
    assert "This must not be displayed" not in output
