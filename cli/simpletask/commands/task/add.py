"""Add implementation task command."""

import typer

from simpletask.commands.task.helpers import _parse_file_actions
from simpletask.core.project import get_task_file_path
from simpletask.core.task_ops import add_implementation_task
from simpletask.core.yaml_parser import InvalidTaskFileError
from simpletask.utils.console import handle_exception, success


def add_command(
    name: str = typer.Argument(..., help="Task name"),
    goal: str | None = typer.Option(None, "--goal", "-g", help="Task goal/description"),
    step: list[str] = typer.Option(None, "--step", help="Implementation step (repeatable)"),  # noqa: B008
    done_when: list[str] = typer.Option(  # noqa: B008
        None, "--done-when", help="Completion condition (repeatable)"
    ),
    prerequisite: list[str] = typer.Option(  # noqa: B008
        None, "--prerequisite", "--prereq", help="Prerequisite task ID (repeatable)"
    ),
    file: list[str] = typer.Option(  # noqa: B008
        None,
        "--file",
        help="File in path:action format e.g. src/models.py:create (repeatable). "
        "code_examples are available via MCP only.",
    ),
    iteration: int | None = typer.Option(
        None, "--iteration", "-i", help="Assign task to iteration by ID"
    ),
    branch: str | None = typer.Option(
        None, "--branch", "-b", help="Branch name (defaults to current git branch)"
    ),
) -> None:
    """Add a new implementation task to the task file.

    Examples:
        simpletask task add "Implement authentication"
        simpletask task add "Add tests" --goal "Write unit tests for auth"
        simpletask task add "Fix bug" --iteration 1
        simpletask task add "Update docs" --branch feature-123
        simpletask task add "Refactor" --step "Identify patterns" --step "Extract methods"
        simpletask task add "Deploy" --done-when "Tests pass" --done-when "Deployed to prod"
        simpletask task add "Task B" --prerequisite T001 --prerequisite T002
        simpletask task add "Models" --file "src/models.py:create" --file "tests/test_models.py:create"

    Raises:
        ValueError: If not in a git repository or branch cannot be determined
        FileNotFoundError: If task file doesn't exist for the specified branch
        InvalidTaskFileError: If task file is malformed and cannot be parsed
    """
    try:
        # Resolve task file path
        file_path = get_task_file_path(branch)
        steps_value = step or None
        done_when_value = done_when or None
        prerequisites_value = prerequisite or None
        file_actions = _parse_file_actions(file) if file else None

        new_id, _ = add_implementation_task(
            file_path,
            name,
            goal,
            steps=steps_value,
            done_when=done_when_value,
            prerequisites=prerequisites_value,
            files=file_actions,
            iteration=iteration,
        )

        iter_suffix = f" (iteration {iteration})" if iteration is not None else ""
        success(f"Added task {new_id}: {name}{iter_suffix}")

    except (ValueError, FileNotFoundError, InvalidTaskFileError) as e:
        handle_exception(e, "adding implementation task")
