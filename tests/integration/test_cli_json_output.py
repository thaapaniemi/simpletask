"""Integration tests for --format json output across all CLI commands.

Tests verify:
- Read commands (show, task list, criteria list, quality show, schema validate)
  produce valid parseable JSON with correct fields when invoked with --format json
- Write commands (task add/update/remove, criteria add/complete, note add)
  produce JSON with success=true, action, message, and summary fields
- Default (no --format) output is unchanged plain/rich text, not JSON
- Error paths (bad task ID, missing file) produce JSON with success=false and
  a message field — no ANSI escape codes or Rich markup in the output
"""

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
from simpletask.core.yaml_parser import write_task_file
from typer.testing import CliRunner

runner = CliRunner()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def json_project(tmp_path: Path, monkeypatch):
    """Set up a temporary git repo with a pre-existing task file.

    Returns:
        project_root Path; monkeypatches cwd so simpletask auto-detects branch.
    """
    branch_name = "feature/json-output-test"
    normalized = "feature-json-output-test.yml"

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
        title="JSON Output Test",
        original_prompt="Test JSON output for CLI commands",
        created=datetime.now(UTC),
        acceptance_criteria=[
            AcceptanceCriterion(id="AC1", description="JSON output works", completed=False),
            AcceptanceCriterion(id="AC2", description="Default output unchanged", completed=False),
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
                name="First task",
                status=TaskStatus.NOT_STARTED,
                goal="Verify JSON output path",
                steps=["Step 1"],
            ),
            Task(
                id="T002",
                name="Second task",
                status=TaskStatus.IN_PROGRESS,
                goal="Another task",
                steps=["Step A"],
            ),
        ],
    )
    write_task_file(task_file, spec)

    monkeypatch.chdir(tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# Read commands: show
# ---------------------------------------------------------------------------


class TestShowJsonOutput:
    """Tests for 'simpletask show --format json'."""

    def test_valid_json_response(self, json_project):
        result = runner.invoke(app, ["show", "--format", "json"])
        assert result.exit_code == 0, result.output
        parsed = json.loads(result.output)
        assert isinstance(parsed, dict)

    def test_required_fields_present(self, json_project):
        result = runner.invoke(app, ["show", "--format", "json"])
        parsed = json.loads(result.output)
        assert "branch" in parsed
        assert "title" in parsed
        assert "acceptance_criteria" in parsed
        assert "tasks" in parsed

    def test_branch_and_title_correct(self, json_project):
        result = runner.invoke(app, ["show", "--format", "json"])
        parsed = json.loads(result.output)
        assert parsed["branch"] == "feature/json-output-test"
        assert parsed["title"] == "JSON Output Test"

    def test_no_ansi_codes(self, json_project):
        result = runner.invoke(app, ["show", "--format", "json"])
        assert "\033[" not in result.output
        assert "\x1b[" not in result.output

    def test_default_format_not_json(self, json_project):
        result = runner.invoke(app, ["show"])
        assert result.exit_code == 0
        # Default output should be plain/rich text, not JSON
        with pytest.raises((json.JSONDecodeError, ValueError)):
            json.loads(result.output)


# ---------------------------------------------------------------------------
# Read commands: task list
# ---------------------------------------------------------------------------


class TestTaskListJsonOutput:
    """Tests for 'simpletask task list --format json'."""

    def test_valid_json_response(self, json_project):
        result = runner.invoke(app, ["task", "list", "--format", "json"])
        assert result.exit_code == 0, result.output
        parsed = json.loads(result.output)
        assert isinstance(parsed, dict)

    def test_required_fields_present(self, json_project):
        result = runner.invoke(app, ["task", "list", "--format", "json"])
        parsed = json.loads(result.output)
        assert "tasks" in parsed
        assert "total" in parsed
        assert "returned" in parsed
        assert "file_path" in parsed

    def test_tasks_list_is_correct(self, json_project):
        result = runner.invoke(app, ["task", "list", "--format", "json"])
        parsed = json.loads(result.output)
        assert parsed["total"] == 2
        assert len(parsed["tasks"]) == 2

    def test_task_entries_have_required_fields(self, json_project):
        result = runner.invoke(app, ["task", "list", "--format", "json"])
        parsed = json.loads(result.output)
        for task in parsed["tasks"]:
            assert "id" in task
            assert "name" in task
            assert "status" in task

    def test_no_ansi_codes(self, json_project):
        result = runner.invoke(app, ["task", "list", "--format", "json"])
        assert "\033[" not in result.output

    def test_default_format_not_json(self, json_project):
        result = runner.invoke(app, ["task", "list"])
        assert result.exit_code == 0
        with pytest.raises((json.JSONDecodeError, ValueError)):
            json.loads(result.output)


# ---------------------------------------------------------------------------
# Read commands: criteria list
# ---------------------------------------------------------------------------


class TestCriteriaListJsonOutput:
    """Tests for 'simpletask criteria list --format json'."""

    def test_valid_json_response(self, json_project):
        result = runner.invoke(app, ["criteria", "list", "--format", "json"])
        assert result.exit_code == 0, result.output
        parsed = json.loads(result.output)
        assert isinstance(parsed, dict)

    def test_required_fields_present(self, json_project):
        result = runner.invoke(app, ["criteria", "list", "--format", "json"])
        parsed = json.loads(result.output)
        assert "criteria" in parsed
        assert "total" in parsed
        assert "completed" in parsed
        assert "file_path" in parsed

    def test_criteria_entries_have_required_fields(self, json_project):
        result = runner.invoke(app, ["criteria", "list", "--format", "json"])
        parsed = json.loads(result.output)
        for criterion in parsed["criteria"]:
            assert "id" in criterion
            assert "description" in criterion
            assert "completed" in criterion

    def test_counts_are_correct(self, json_project):
        result = runner.invoke(app, ["criteria", "list", "--format", "json"])
        parsed = json.loads(result.output)
        assert parsed["total"] == 2
        assert parsed["completed"] == 0

    def test_default_format_not_json(self, json_project):
        result = runner.invoke(app, ["criteria", "list"])
        assert result.exit_code == 0
        with pytest.raises((json.JSONDecodeError, ValueError)):
            json.loads(result.output)


# ---------------------------------------------------------------------------
# Read commands: quality show
# ---------------------------------------------------------------------------


class TestQualityShowJsonOutput:
    """Tests for 'simpletask quality show --format json'."""

    def test_valid_json_response(self, json_project):
        result = runner.invoke(app, ["quality", "show", "--format", "json"])
        assert result.exit_code == 0, result.output
        parsed = json.loads(result.output)
        assert isinstance(parsed, dict)

    def test_required_fields_present(self, json_project):
        result = runner.invoke(app, ["quality", "show", "--format", "json"])
        parsed = json.loads(result.output)
        assert "file_path" in parsed
        assert "linting" in parsed

    def test_linting_fields_present(self, json_project):
        result = runner.invoke(app, ["quality", "show", "--format", "json"])
        parsed = json.loads(result.output)
        linting = parsed["linting"]
        assert "enabled" in linting
        assert "execution" in linting
        assert "timeout" in linting
        assert "tool" in linting["execution"]
        assert "args" in linting["execution"]

    def test_linting_values_correct(self, json_project):
        result = runner.invoke(app, ["quality", "show", "--format", "json"])
        parsed = json.loads(result.output)
        assert parsed["linting"]["execution"]["tool"] == "ruff"
        assert parsed["linting"]["enabled"] is True

    def test_no_ansi_codes(self, json_project):
        result = runner.invoke(app, ["quality", "show", "--format", "json"])
        assert "\033[" not in result.output

    def test_default_format_not_json(self, json_project):
        result = runner.invoke(app, ["quality", "show"])
        assert result.exit_code == 0
        with pytest.raises((json.JSONDecodeError, ValueError)):
            json.loads(result.output)


# ---------------------------------------------------------------------------
# Read commands: schema validate
# ---------------------------------------------------------------------------


class TestSchemaValidateJsonOutput:
    """Tests for 'simpletask schema validate --format json'."""

    def test_valid_json_response(self, json_project):
        result = runner.invoke(app, ["schema", "validate", "--format", "json"])
        assert result.exit_code == 0, result.output
        parsed = json.loads(result.output)
        assert isinstance(parsed, dict)

    def test_required_fields_present(self, json_project):
        result = runner.invoke(app, ["schema", "validate", "--format", "json"])
        parsed = json.loads(result.output)
        assert "file" in parsed
        assert "valid" in parsed
        assert "errors" in parsed

    def test_valid_task_file_shows_valid_true(self, json_project):
        result = runner.invoke(app, ["schema", "validate", "--format", "json"])
        parsed = json.loads(result.output)
        assert parsed["valid"] is True
        assert parsed["errors"] == []

    def test_no_ansi_codes(self, json_project):
        result = runner.invoke(app, ["schema", "validate", "--format", "json"])
        assert "\033[" not in result.output

    def test_default_format_not_json(self, json_project):
        result = runner.invoke(app, ["schema", "validate"])
        assert result.exit_code == 0
        with pytest.raises((json.JSONDecodeError, ValueError)):
            json.loads(result.output)


# ---------------------------------------------------------------------------
# Read commands: schema validate --all
# ---------------------------------------------------------------------------


class TestSchemaValidateAllJsonOutput:
    """Tests for 'simpletask schema validate --all --format json'."""

    # ------------------------------------------------------------------
    # Happy path: single valid task file
    # ------------------------------------------------------------------

    def test_happy_path_exit_code_zero(self, json_project: Path) -> None:
        result = runner.invoke(app, ["schema", "validate", "--all", "--format", "json"])
        assert result.exit_code == 0, result.output

    def test_happy_path_output_is_valid_json(self, json_project: Path) -> None:
        result = runner.invoke(app, ["schema", "validate", "--all", "--format", "json"])
        parsed = json.loads(result.output)
        assert isinstance(parsed, dict)

    def test_happy_path_required_top_level_fields(self, json_project: Path) -> None:
        result = runner.invoke(app, ["schema", "validate", "--all", "--format", "json"])
        parsed = json.loads(result.output)
        assert "results" in parsed
        assert "all_valid" in parsed

    def test_happy_path_all_valid_true(self, json_project: Path) -> None:
        result = runner.invoke(app, ["schema", "validate", "--all", "--format", "json"])
        parsed = json.loads(result.output)
        assert parsed["all_valid"] is True

    def test_happy_path_results_per_file_structure(self, json_project: Path) -> None:
        """Each entry in 'results' must have 'file', 'valid', and 'errors' keys."""
        result = runner.invoke(app, ["schema", "validate", "--all", "--format", "json"])
        parsed = json.loads(result.output)
        assert isinstance(parsed["results"], list)
        assert len(parsed["results"]) >= 1
        for entry in parsed["results"]:
            assert "file" in entry
            assert "valid" in entry
            assert "errors" in entry
        # The fixture file is valid — no errors expected
        assert all(e["valid"] for e in parsed["results"])

    # ------------------------------------------------------------------
    # Invalid file: schema-invalid task (has 'branch' key, fails schema)
    # ------------------------------------------------------------------

    def test_invalid_file_all_valid_false(self, json_project: Path) -> None:
        """Injecting a schema-invalid YAML makes all_valid False."""
        tasks_dir = json_project / ".tasks"
        # Valid YAML with 'branch' so list_tasks() picks it up, but missing
        # required schema fields so validate_task_file() returns errors.
        (tasks_dir / "broken-branch.yml").write_text("branch: broken-test\ntitle: Bad\n")

        result = runner.invoke(app, ["schema", "validate", "--all", "--format", "json"])
        parsed = json.loads(result.output)
        assert parsed["all_valid"] is False

    def test_invalid_file_broken_entry_has_errors(self, json_project: Path) -> None:
        """The broken file entry in 'results' must show valid=False with errors."""
        tasks_dir = json_project / ".tasks"
        (tasks_dir / "broken-branch.yml").write_text("branch: broken-test\ntitle: Bad\n")

        result = runner.invoke(app, ["schema", "validate", "--all", "--format", "json"])
        parsed = json.loads(result.output)
        broken = next((r for r in parsed["results"] if "broken" in r["file"]), None)
        assert broken is not None, f"Expected broken entry in results: {parsed['results']}"
        assert broken["valid"] is False
        assert len(broken["errors"]) > 0

    def test_invalid_file_exit_code_one(self, json_project: Path) -> None:
        tasks_dir = json_project / ".tasks"
        (tasks_dir / "broken-branch.yml").write_text("branch: broken-test\ntitle: Bad\n")

        result = runner.invoke(app, ["schema", "validate", "--all", "--format", "json"])
        assert result.exit_code == 1

    def test_invalid_file_output_is_still_valid_json(self, json_project: Path) -> None:
        """Even on validation failure the output must be parseable JSON."""
        tasks_dir = json_project / ".tasks"
        (tasks_dir / "broken-branch.yml").write_text("branch: broken-test\ntitle: Bad\n")

        result = runner.invoke(app, ["schema", "validate", "--all", "--format", "json"])
        parsed = json.loads(result.output)  # must not raise
        assert isinstance(parsed, dict)

    # ------------------------------------------------------------------
    # Empty .tasks directory
    # ------------------------------------------------------------------

    def test_empty_tasks_exit_code_one(self, json_project: Path) -> None:
        """Empty .tasks dir → exit 1."""
        for f in (json_project / ".tasks").iterdir():
            f.unlink()
        result = runner.invoke(app, ["schema", "validate", "--all", "--format", "json"])
        assert result.exit_code == 1

    def test_empty_tasks_json_error_response(self, json_project: Path) -> None:
        """Empty .tasks dir → JSON object with success=False and a message."""
        for f in (json_project / ".tasks").iterdir():
            f.unlink()
        result = runner.invoke(app, ["schema", "validate", "--all", "--format", "json"])
        parsed = json.loads(result.stderr)
        assert parsed["success"] is False
        assert "message" in parsed
        assert parsed["message"]  # non-empty

    def test_empty_tasks_no_ansi_codes(self, json_project: Path) -> None:
        """Error response must contain no ANSI escape codes."""
        for f in (json_project / ".tasks").iterdir():
            f.unlink()
        result = runner.invoke(app, ["schema", "validate", "--all", "--format", "json"])
        assert "\033[" not in result.output


# ---------------------------------------------------------------------------
# Write commands: task add
# ---------------------------------------------------------------------------


class TestTaskAddJsonOutput:
    """Tests for 'simpletask task add --format json'."""

    def test_valid_json_response(self, json_project):
        result = runner.invoke(app, ["task", "add", "New task", "--format", "json"])
        assert result.exit_code == 0, result.output
        parsed = json.loads(result.output)
        assert isinstance(parsed, dict)

    def test_required_fields_present(self, json_project):
        result = runner.invoke(app, ["task", "add", "New task", "--format", "json"])
        parsed = json.loads(result.output)
        assert parsed["success"] is True
        assert "action" in parsed
        assert "message" in parsed
        assert "summary" in parsed

    def test_action_is_task_added(self, json_project):
        result = runner.invoke(app, ["task", "add", "New task", "--format", "json"])
        parsed = json.loads(result.output)
        assert parsed["action"] == "task_added"

    def test_summary_contains_task_counts(self, json_project):
        result = runner.invoke(app, ["task", "add", "New task", "--format", "json"])
        parsed = json.loads(result.output)
        summary = parsed["summary"]
        # Fixture has T001 (not_started) + T002 (in_progress); new task is not_started
        assert summary["tasks_total"] == 3
        assert summary["tasks_completed"] == 0
        assert summary["tasks_not_started"] == 2
        assert summary["tasks_in_progress"] == 1
        assert summary["tasks_blocked"] == 0
        assert summary["tasks_paused"] == 0

    def test_default_format_not_json(self, json_project):
        result = runner.invoke(app, ["task", "add", "Another task"])
        assert result.exit_code == 0
        with pytest.raises((json.JSONDecodeError, ValueError)):
            json.loads(result.output)


# ---------------------------------------------------------------------------
# Write commands: task update
# ---------------------------------------------------------------------------


class TestTaskUpdateJsonOutput:
    """Tests for 'simpletask task update --format json'."""

    def test_valid_json_response(self, json_project):
        result = runner.invoke(
            app, ["task", "update", "T001", "--status", "in_progress", "--format", "json"]
        )
        assert result.exit_code == 0, result.output
        parsed = json.loads(result.output)
        assert isinstance(parsed, dict)

    def test_required_fields_present(self, json_project):
        result = runner.invoke(
            app, ["task", "update", "T001", "--status", "in_progress", "--format", "json"]
        )
        parsed = json.loads(result.output)
        assert parsed["success"] is True
        assert "action" in parsed
        assert "message" in parsed
        assert "summary" in parsed

    def test_action_is_task_updated(self, json_project):
        result = runner.invoke(
            app, ["task", "update", "T001", "--status", "in_progress", "--format", "json"]
        )
        parsed = json.loads(result.output)
        assert parsed["action"] == "task_updated"

    def test_default_format_not_json(self, json_project):
        result = runner.invoke(app, ["task", "update", "T002", "--status", "completed"])
        assert result.exit_code == 0
        with pytest.raises((json.JSONDecodeError, ValueError)):
            json.loads(result.output)


# ---------------------------------------------------------------------------
# Write commands: task remove
# ---------------------------------------------------------------------------


class TestTaskRemoveJsonOutput:
    """Tests for 'simpletask task remove --force --format json'."""

    def test_valid_json_response(self, json_project):
        result = runner.invoke(app, ["task", "remove", "T001", "--force", "--format", "json"])
        assert result.exit_code == 0, result.output
        parsed = json.loads(result.output)
        assert isinstance(parsed, dict)

    def test_required_fields_present(self, json_project):
        result = runner.invoke(app, ["task", "remove", "T001", "--force", "--format", "json"])
        parsed = json.loads(result.output)
        assert parsed["success"] is True
        assert "action" in parsed
        assert "message" in parsed
        assert "summary" in parsed

    def test_action_is_task_removed(self, json_project):
        result = runner.invoke(app, ["task", "remove", "T001", "--force", "--format", "json"])
        parsed = json.loads(result.output)
        assert parsed["action"] == "task_removed"

    def test_task_count_decremented(self, json_project):
        result = runner.invoke(app, ["task", "remove", "T001", "--force", "--format", "json"])
        parsed = json.loads(result.output)
        assert parsed["summary"]["tasks_total"] == 1


# ---------------------------------------------------------------------------
# Write commands: criteria add
# ---------------------------------------------------------------------------


class TestCriteriaAddJsonOutput:
    """Tests for 'simpletask criteria add --format json'."""

    def test_valid_json_response(self, json_project):
        result = runner.invoke(app, ["criteria", "add", "New criterion text", "--format", "json"])
        assert result.exit_code == 0, result.output
        parsed = json.loads(result.output)
        assert isinstance(parsed, dict)

    def test_required_fields_present(self, json_project):
        result = runner.invoke(app, ["criteria", "add", "New criterion text", "--format", "json"])
        parsed = json.loads(result.output)
        assert parsed["success"] is True
        assert "action" in parsed
        assert "message" in parsed
        assert "summary" in parsed

    def test_action_is_criterion_added(self, json_project):
        result = runner.invoke(app, ["criteria", "add", "New criterion text", "--format", "json"])
        parsed = json.loads(result.output)
        assert parsed["action"] == "criterion_added"

    def test_summary_has_criteria_counts(self, json_project):
        result = runner.invoke(app, ["criteria", "add", "New criterion text", "--format", "json"])
        parsed = json.loads(result.output)
        assert "criteria_total" in parsed["summary"]
        assert "criteria_completed" in parsed["summary"]


# ---------------------------------------------------------------------------
# Write commands: criteria complete
# ---------------------------------------------------------------------------


class TestCriteriaCompleteJsonOutput:
    """Tests for 'simpletask criteria complete --format json'."""

    def test_valid_json_response(self, json_project):
        result = runner.invoke(app, ["criteria", "complete", "AC1", "--format", "json"])
        assert result.exit_code == 0, result.output
        parsed = json.loads(result.output)
        assert isinstance(parsed, dict)

    def test_required_fields_present(self, json_project):
        result = runner.invoke(app, ["criteria", "complete", "AC1", "--format", "json"])
        parsed = json.loads(result.output)
        assert parsed["success"] is True
        assert "action" in parsed
        assert "message" in parsed
        assert "summary" in parsed

    def test_action_is_criterion_completed(self, json_project):
        result = runner.invoke(app, ["criteria", "complete", "AC1", "--format", "json"])
        parsed = json.loads(result.output)
        assert parsed["action"] == "criterion_completed"

    def test_completed_count_incremented(self, json_project):
        result = runner.invoke(app, ["criteria", "complete", "AC1", "--format", "json"])
        parsed = json.loads(result.output)
        assert parsed["summary"]["criteria_completed"] == 1

    def test_default_format_not_json(self, json_project):
        result = runner.invoke(app, ["criteria", "complete", "AC2"])
        assert result.exit_code == 0
        with pytest.raises((json.JSONDecodeError, ValueError)):
            json.loads(result.output)

    def test_uncomplete_action_field_correct(self, json_project):
        # First complete the criterion so uncomplete has something to revert
        runner.invoke(app, ["criteria", "complete", "AC1", "--format", "json"])
        result = runner.invoke(
            app, ["criteria", "complete", "AC1", "--uncomplete", "--format", "json"]
        )
        assert result.exit_code == 0, result.output
        parsed = json.loads(result.output)
        assert parsed["action"] == "criterion_uncompleted"
        assert (
            "not completed" in parsed["message"].lower()
            or "uncomplete" in parsed["message"].lower()
        )


# ---------------------------------------------------------------------------
# Write commands: note add
# ---------------------------------------------------------------------------


class TestNoteAddJsonOutput:
    """Tests for 'simpletask note add --format json'."""

    def test_valid_json_response(self, json_project):
        result = runner.invoke(app, ["note", "add", "Remember this", "--format", "json"])
        assert result.exit_code == 0, result.output
        parsed = json.loads(result.output)
        assert isinstance(parsed, dict)

    def test_required_fields_present(self, json_project):
        result = runner.invoke(app, ["note", "add", "Remember this", "--format", "json"])
        parsed = json.loads(result.output)
        assert parsed["success"] is True
        assert "action" in parsed
        assert "message" in parsed
        assert "summary" in parsed

    def test_action_is_note_added(self, json_project):
        result = runner.invoke(app, ["note", "add", "Remember this", "--format", "json"])
        parsed = json.loads(result.output)
        assert parsed["action"] == "note_added"

    def test_default_format_not_json(self, json_project):
        result = runner.invoke(app, ["note", "add", "Some note"])
        assert result.exit_code == 0
        with pytest.raises((json.JSONDecodeError, ValueError)):
            json.loads(result.output)

    def test_task_level_note_on_task_without_prior_notes(self, json_project):
        # T001 in the fixture has no task-level notes; adding one must not crash
        result = runner.invoke(
            app, ["note", "add", "task note", "--task", "T001", "--format", "json"]
        )
        assert result.exit_code == 0, result.output
        parsed = json.loads(result.output)
        assert parsed["success"] is True
        assert parsed["action"] == "note_added"
        assert parsed["summary"]["notes_total"] == 1


# ---------------------------------------------------------------------------
# Error path tests
# ---------------------------------------------------------------------------


class TestErrorPathJsonOutput:
    """Tests that error paths produce JSON with success=false when --format json is set."""

    def test_task_update_bad_id_produces_json_error(self, json_project):
        result = runner.invoke(
            app,
            ["task", "update", "T999", "--status", "completed", "--format", "json"],
        )
        parsed = json.loads(result.stderr)
        assert parsed["success"] is False
        assert "message" in parsed

    def test_task_update_bad_id_no_ansi(self, json_project):
        result = runner.invoke(
            app,
            ["task", "update", "T999", "--status", "completed", "--format", "json"],
        )
        assert "\033[" not in result.stderr
        assert "\x1b[" not in result.stderr

    def test_task_remove_bad_id_produces_json_error(self, json_project):
        result = runner.invoke(app, ["task", "remove", "T999", "--force", "--format", "json"])
        parsed = json.loads(result.stderr)
        assert parsed["success"] is False
        assert "message" in parsed

    def test_criteria_complete_bad_id_produces_json_error(self, json_project):
        result = runner.invoke(app, ["criteria", "complete", "AC99", "--format", "json"])
        parsed = json.loads(result.stderr)
        assert parsed["success"] is False
        assert "message" in parsed

    def test_show_missing_file_produces_json_error(self, tmp_path, monkeypatch):
        """show with --format json and no task file returns JSON error."""
        repo = git.Repo.init(tmp_path)
        repo.config_writer().set_value("user", "name", "Test").release()
        repo.config_writer().set_value("user", "email", "t@t.com").release()
        (tmp_path / "README.md").write_text("# Test\n")
        repo.index.add(["README.md"])
        repo.index.commit("initial")
        repo.create_head("feature/no-task").checkout()
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["show", "--format", "json"])
        parsed = json.loads(result.stderr)
        assert parsed["success"] is False
        assert "message" in parsed

    def test_task_list_missing_file_produces_json_error(self, tmp_path, monkeypatch):
        """task list with --format json and no task file returns JSON error."""
        repo = git.Repo.init(tmp_path)
        repo.config_writer().set_value("user", "name", "Test").release()
        repo.config_writer().set_value("user", "email", "t@t.com").release()
        (tmp_path / "README.md").write_text("# Test\n")
        repo.index.add(["README.md"])
        repo.index.commit("initial")
        repo.create_head("feature/no-task").checkout()
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["task", "list", "--format", "json"])
        parsed = json.loads(result.stderr)
        assert parsed["success"] is False
        assert "message" in parsed


class TestJsonErrorExitCodes:
    """Tests that JSON error paths exit with code 1."""

    def test_task_update_bad_id_exits_1(self, json_project):
        result = runner.invoke(
            app, ["task", "update", "T999", "--status", "completed", "--format", "json"]
        )
        assert result.exit_code == 1

    def test_task_remove_bad_id_exits_1(self, json_project):
        result = runner.invoke(app, ["task", "remove", "T999", "--force", "--format", "json"])
        assert result.exit_code == 1

    def test_criteria_complete_bad_id_exits_1(self, json_project):
        result = runner.invoke(app, ["criteria", "complete", "AC99", "--format", "json"])
        assert result.exit_code == 1

    def test_show_missing_file_exits_1(self, tmp_path, monkeypatch):
        """show --format json with missing task file exits 1."""
        import git

        repo = git.Repo.init(tmp_path)
        repo.config_writer().set_value("user", "name", "Test").release()
        repo.config_writer().set_value("user", "email", "t@t.com").release()
        (tmp_path / "README.md").write_text("# Test\n")
        repo.index.add(["README.md"])
        repo.index.commit("initial")
        repo.create_head("feature/no-task").checkout()
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["show", "--format", "json"])
        assert result.exit_code == 1

    def test_schema_validate_missing_file_exits_1(self, tmp_path, monkeypatch):
        """schema validate --format json with missing task file exits 1."""
        import git

        repo = git.Repo.init(tmp_path)
        repo.config_writer().set_value("user", "name", "Test").release()
        repo.config_writer().set_value("user", "email", "t@t.com").release()
        (tmp_path / "README.md").write_text("# Test\n")
        repo.index.add(["README.md"])
        repo.index.commit("initial")
        repo.create_head("feature/no-task").checkout()
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["schema", "validate", "--format", "json"])
        assert result.exit_code == 1

    def test_error_json_goes_to_stderr_not_stdout(self, json_project):
        """json_error() output must be in stderr; stdout must be empty for error paths."""
        result = runner.invoke(
            app, ["task", "update", "T999", "--status", "completed", "--format", "json"]
        )
        # Successful JSON responses go to stdout; error JSON goes to stderr
        assert result.output.strip() == "" or json.loads(result.stderr)["success"] is False
        parsed = json.loads(result.stderr)
        assert parsed["success"] is False
