"""Unit tests for show command with notes display.

Tests cover:
- Notes section hidden when no notes exist
- Root notes display with bullets
- Audit History section display (present/absent, per-run breakdown, JSON output)
- Task notes display as summary
- Combined root and task notes display
- Note truncation at 160 characters
- Original prompt truncation at 160 characters
- Implementation tasks grouped by iteration when iterations are defined
"""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from simpletask.commands.show import show
from simpletask.core.models import (
    AcceptanceCriterion,
    AuditFinding,
    AuditRun,
    FindingCategory,
    Iteration,
    Severity,
    SimpleTaskSpec,
    Task,
    TaskStatus,
    Verdict,
)
from simpletask.core.yaml_parser import write_task_file
from simpletask.utils.output import OutputFormat


@pytest.fixture
def spec_with_no_notes(tmp_path):
    """Create a task file with no notes."""
    spec = SimpleTaskSpec(
        schema_version="1.0",
        branch="test-branch",
        title="Test Task",
        original_prompt="Test prompt",
        created=datetime.now(UTC),
        acceptance_criteria=[
            AcceptanceCriterion(id="AC1", description="Test criterion", completed=False)
        ],
        notes=None,
        tasks=[
            Task(
                id="T001",
                name="Test Task",
                status=TaskStatus.NOT_STARTED,
                goal="Test goal",
                steps=["Step 1"],
                notes=None,
            )
        ],
    )
    task_file = tmp_path / ".tasks" / "test-branch.yml"
    task_file.parent.mkdir(parents=True, exist_ok=True)
    write_task_file(task_file, spec)
    return task_file, spec


@pytest.fixture
def spec_with_root_notes(tmp_path):
    """Create a task file with only root notes."""
    spec = SimpleTaskSpec(
        schema_version="1.0",
        branch="test-branch",
        title="Test Task",
        original_prompt="Test prompt",
        created=datetime.now(UTC),
        acceptance_criteria=[
            AcceptanceCriterion(id="AC1", description="Test criterion", completed=False)
        ],
        notes=["First root note", "Second root note"],
        tasks=[
            Task(
                id="T001",
                name="Test Task",
                status=TaskStatus.NOT_STARTED,
                goal="Test goal",
                steps=["Step 1"],
                notes=None,
            )
        ],
    )
    task_file = tmp_path / ".tasks" / "test-branch.yml"
    task_file.parent.mkdir(parents=True, exist_ok=True)
    write_task_file(task_file, spec)
    return task_file, spec


@pytest.fixture
def spec_with_task_notes(tmp_path):
    """Create a task file with only task notes."""
    spec = SimpleTaskSpec(
        schema_version="1.0",
        branch="test-branch",
        title="Test Task",
        original_prompt="Test prompt",
        created=datetime.now(UTC),
        acceptance_criteria=[
            AcceptanceCriterion(id="AC1", description="Test criterion", completed=False)
        ],
        notes=None,
        tasks=[
            Task(
                id="T001",
                name="Test Task 1",
                status=TaskStatus.NOT_STARTED,
                goal="Test goal",
                steps=["Step 1"],
                notes=["Task 1 note"],
            ),
            Task(
                id="T002",
                name="Test Task 2",
                status=TaskStatus.NOT_STARTED,
                goal="Test goal",
                steps=["Step 1"],
                notes=["Task 2 note 1", "Task 2 note 2"],
            ),
        ],
    )
    task_file = tmp_path / ".tasks" / "test-branch.yml"
    task_file.parent.mkdir(parents=True, exist_ok=True)
    write_task_file(task_file, spec)
    return task_file, spec


@pytest.fixture
def spec_with_both_notes(tmp_path):
    """Create a task file with both root and task notes."""
    spec = SimpleTaskSpec(
        schema_version="1.0",
        branch="test-branch",
        title="Test Task",
        original_prompt="Test prompt",
        created=datetime.now(UTC),
        acceptance_criteria=[
            AcceptanceCriterion(id="AC1", description="Test criterion", completed=False)
        ],
        notes=["Root note 1", "Root note 2"],
        tasks=[
            Task(
                id="T001",
                name="Test Task",
                status=TaskStatus.NOT_STARTED,
                goal="Test goal",
                steps=["Step 1"],
                notes=["Task note"],
            )
        ],
    )
    task_file = tmp_path / ".tasks" / "test-branch.yml"
    task_file.parent.mkdir(parents=True, exist_ok=True)
    write_task_file(task_file, spec)
    return task_file, spec


@pytest.fixture
def spec_with_long_notes(tmp_path):
    """Create a task file with notes exceeding 160 characters."""
    long_note = "A" * 200  # 200 characters
    spec = SimpleTaskSpec(
        schema_version="1.0",
        branch="test-branch",
        title="Test Task",
        original_prompt="Test prompt",
        created=datetime.now(UTC),
        acceptance_criteria=[
            AcceptanceCriterion(id="AC1", description="Test criterion", completed=False)
        ],
        notes=[long_note],
        tasks=[],
    )
    task_file = tmp_path / ".tasks" / "test-branch.yml"
    task_file.parent.mkdir(parents=True, exist_ok=True)
    write_task_file(task_file, spec)
    return task_file, spec


@pytest.fixture
def spec_with_long_prompt(tmp_path):
    """Create a task file with original_prompt exceeding 160 characters."""
    long_prompt = "B" * 200  # 200 characters
    spec = SimpleTaskSpec(
        schema_version="1.0",
        branch="test-branch",
        title="Test Task",
        original_prompt=long_prompt,
        created=datetime.now(UTC),
        acceptance_criteria=[
            AcceptanceCriterion(id="AC1", description="Test criterion", completed=False)
        ],
    )
    task_file = tmp_path / ".tasks" / "test-branch.yml"
    task_file.parent.mkdir(parents=True, exist_ok=True)
    write_task_file(task_file, spec)
    return task_file, spec


class TestShowCommandNotes:
    """Test show command notes display functionality."""

    def test_show_hides_notes_when_empty(self, spec_with_no_notes, monkeypatch, tmp_path):
        """Verify no notes section when notes are None/empty."""
        task_file, _spec = spec_with_no_notes

        # Mock the project root and task file path
        monkeypatch.chdir(tmp_path)
        with patch("simpletask.commands.show.get_task_file_path", return_value=task_file):
            with patch("simpletask.commands.show.ensure_project") as mock_ensure:
                mock_ensure.return_value.root = tmp_path

                # Capture console output
                with patch("simpletask.commands.show.console") as mock_console:
                    show(branch="test-branch")

                    # Check that "Notes:" was never printed
                    output_calls = [str(call) for call in mock_console.print.call_args_list]
                    notes_printed = any("Notes:" in str(call) for call in output_calls)
                    assert not notes_printed, "Notes section should be hidden when no notes exist"

    def test_show_with_root_notes_only(self, spec_with_root_notes, monkeypatch, tmp_path):
        """Verify root notes display with bullets."""
        task_file, _spec = spec_with_root_notes

        monkeypatch.chdir(tmp_path)
        with patch("simpletask.commands.show.get_task_file_path", return_value=task_file):
            with patch("simpletask.commands.show.ensure_project") as mock_ensure:
                mock_ensure.return_value.root = tmp_path

                with patch("simpletask.commands.show.console") as mock_console:
                    show(branch="test-branch")

                    # Verify notes section header
                    output_calls = [str(call) for call in mock_console.print.call_args_list]
                    assert any(
                        "[bold cyan]Notes:[/bold cyan]" in str(call) for call in output_calls
                    )
                    assert any("Root:" in str(call) for call in output_calls)
                    assert any("• First root note" in str(call) for call in output_calls)
                    assert any("• Second root note" in str(call) for call in output_calls)

    def test_show_with_task_notes_only(self, spec_with_task_notes, monkeypatch, tmp_path):
        """Verify task notes display as summary."""
        task_file, _spec = spec_with_task_notes

        monkeypatch.chdir(tmp_path)
        with patch("simpletask.commands.show.get_task_file_path", return_value=task_file):
            with patch("simpletask.commands.show.ensure_project") as mock_ensure:
                mock_ensure.return_value.root = tmp_path

                with patch("simpletask.commands.show.console") as mock_console:
                    show(branch="test-branch")

                    output_calls = [str(call) for call in mock_console.print.call_args_list]
                    # Should show "3 notes across 2 tasks"
                    assert any("3 notes across 2 tasks" in str(call) for call in output_calls), (
                        "Should show task notes summary"
                    )
                    assert any("simpletask note list" in str(call) for call in output_calls), (
                        "Should show details command"
                    )

    def test_show_with_both_notes(self, spec_with_both_notes, monkeypatch, tmp_path):
        """Verify both root and task notes display."""
        task_file, _spec = spec_with_both_notes

        monkeypatch.chdir(tmp_path)
        with patch("simpletask.commands.show.get_task_file_path", return_value=task_file):
            with patch("simpletask.commands.show.ensure_project") as mock_ensure:
                mock_ensure.return_value.root = tmp_path

                with patch("simpletask.commands.show.console") as mock_console:
                    show(branch="test-branch")

                    output_calls = [str(call) for call in mock_console.print.call_args_list]
                    # Check for root notes
                    assert any("Root:" in str(call) for call in output_calls)
                    assert any("• Root note 1" in str(call) for call in output_calls)
                    # Check for task notes summary
                    assert any("1 note across 1 task" in str(call) for call in output_calls)

    def test_show_truncates_long_notes(self, spec_with_long_notes, monkeypatch, tmp_path):
        """Verify 160 char truncation with ellipsis for notes."""
        task_file, _spec = spec_with_long_notes

        monkeypatch.chdir(tmp_path)
        with patch("simpletask.commands.show.get_task_file_path", return_value=task_file):
            with patch("simpletask.commands.show.ensure_project") as mock_ensure:
                mock_ensure.return_value.root = tmp_path

                with patch("simpletask.commands.show.console") as mock_console:
                    show(branch="test-branch")

                    output_calls = [str(call) for call in mock_console.print.call_args_list]
                    # Find the note output
                    note_output = [call for call in output_calls if "• A" in str(call)]
                    assert len(note_output) > 0, "Should find truncated note"

                    # Check that the note ends with "..."
                    note_str = str(note_output[0])
                    assert "..." in note_str, "Long note should be truncated with ellipsis"
                    # The displayed note should be approximately 160 chars + bullet + spaces
                    # We can't check exact length due to Rich formatting, but ellipsis presence confirms truncation

    def test_show_original_prompt_truncation(self, spec_with_long_prompt, monkeypatch, tmp_path):
        """Verify original prompt uses 160 char limit."""
        task_file, _spec = spec_with_long_prompt

        monkeypatch.chdir(tmp_path)
        with patch("simpletask.commands.show.get_task_file_path", return_value=task_file):
            with patch("simpletask.commands.show.ensure_project") as mock_ensure:
                mock_ensure.return_value.root = tmp_path

                with patch("simpletask.commands.show.console") as mock_console:
                    show(branch="test-branch")

                    output_calls = [str(call) for call in mock_console.print.call_args_list]
                    # Find the prompt output (contains quotes and B's)
                    prompt_output = [call for call in output_calls if '"B' in str(call)]
                    assert len(prompt_output) > 0, "Should find truncated prompt"

                    # Check that prompt ends with "..."
                    prompt_str = str(prompt_output[0])
                    assert "..." in prompt_str, "Long prompt should be truncated with ellipsis"


def _make_spec_with_iterations(tmp_path):
    """Create a task file with two iterations and a mix of assigned/unassigned tasks."""
    spec = SimpleTaskSpec(
        schema_version="1.0",
        branch="test-branch",
        title="Iteration Test",
        original_prompt="Test prompt",
        created=datetime.now(UTC),
        acceptance_criteria=[
            AcceptanceCriterion(id="AC1", description="Test criterion", completed=False)
        ],
        iterations=[
            Iteration(id=1, label="Sprint 1"),
            Iteration(id=2, label="Sprint 2"),
        ],
        tasks=[
            Task(
                id="T001",
                name="Unassigned task",
                status=TaskStatus.COMPLETED,
                goal="g",
                steps=["s"],
                iteration=None,
            ),
            Task(
                id="T002",
                name="Sprint 1 task A",
                status=TaskStatus.COMPLETED,
                goal="g",
                steps=["s"],
                iteration=1,
            ),
            Task(
                id="T003",
                name="Sprint 1 task B",
                status=TaskStatus.NOT_STARTED,
                goal="g",
                steps=["s"],
                iteration=1,
            ),
            Task(
                id="T004",
                name="Sprint 2 task",
                status=TaskStatus.IN_PROGRESS,
                goal="g",
                steps=["s"],
                iteration=2,
            ),
        ],
    )
    task_file = tmp_path / ".tasks" / "test-branch.yml"
    task_file.parent.mkdir(parents=True, exist_ok=True)
    write_task_file(task_file, spec)
    return task_file, spec


class TestShowCommandIterations:
    """Test show command iteration grouping functionality."""

    def _capture_output(self, task_file, tmp_path, monkeypatch):
        """Helper: run show() and return list of printed call strings."""
        monkeypatch.chdir(tmp_path)
        with patch("simpletask.commands.show.get_task_file_path", return_value=task_file):
            with patch("simpletask.commands.show.ensure_project") as mock_ensure:
                mock_ensure.return_value.root = tmp_path
                with patch("simpletask.commands.show.console") as mock_console:
                    show(branch="test-branch")
                    return [str(call) for call in mock_console.print.call_args_list], mock_console

    def test_flat_list_without_iterations(self, tmp_path, monkeypatch):
        """Tasks with no iterations render as a flat list with 2-space indent."""
        spec = SimpleTaskSpec(
            schema_version="1.0",
            branch="test-branch",
            title="Flat Test",
            original_prompt="Test prompt",
            created=datetime.now(UTC),
            acceptance_criteria=[
                AcceptanceCriterion(id="AC1", description="Criterion", completed=False)
            ],
            tasks=[
                Task(
                    id="T001",
                    name="Some task",
                    status=TaskStatus.NOT_STARTED,
                    goal="g",
                    steps=["s"],
                )
            ],
        )
        task_file = tmp_path / ".tasks" / "test-branch.yml"
        task_file.parent.mkdir(parents=True, exist_ok=True)
        write_task_file(task_file, spec)

        output_calls, _ = self._capture_output(task_file, tmp_path, monkeypatch)

        # Should NOT have any iteration header
        assert not any("Iteration" in c for c in output_calls)
        assert not any("Unassigned" in c for c in output_calls)
        # Should have task with 2-space indent
        assert any("  " in c and "T001" in c and "Some task" in c for c in output_calls)

    def test_grouped_by_iterations(self, tmp_path, monkeypatch):
        """Tasks are grouped under iteration rule headers when iterations exist."""
        task_file, _ = _make_spec_with_iterations(tmp_path)
        _output_calls, mock_console = self._capture_output(task_file, tmp_path, monkeypatch)

        # rule() calls carry the header labels
        rule_calls = [str(call) for call in mock_console.rule.call_args_list]
        assert any("Iteration 1" in c and "Sprint 1" in c for c in rule_calls)
        assert any("Iteration 2" in c and "Sprint 2" in c for c in rule_calls)

    def test_unassigned_tasks_appear_first(self, tmp_path, monkeypatch):
        """Unassigned group header appears before any iteration header."""
        task_file, _ = _make_spec_with_iterations(tmp_path)
        _, mock_console = self._capture_output(task_file, tmp_path, monkeypatch)

        rule_calls = [str(call) for call in mock_console.rule.call_args_list]
        unassigned_idx = next(i for i, c in enumerate(rule_calls) if "Unassigned" in c)
        iteration_idx = next(i for i, c in enumerate(rule_calls) if "Iteration 1" in c)
        assert unassigned_idx < iteration_idx

    def test_unassigned_group_hidden_when_all_assigned(self, tmp_path, monkeypatch):
        """Unassigned group is not shown when all tasks belong to an iteration."""
        spec = SimpleTaskSpec(
            schema_version="1.0",
            branch="test-branch",
            title="All Assigned",
            original_prompt="Test prompt",
            created=datetime.now(UTC),
            acceptance_criteria=[
                AcceptanceCriterion(id="AC1", description="Criterion", completed=False)
            ],
            iterations=[Iteration(id=1, label="MVP")],
            tasks=[
                Task(
                    id="T001",
                    name="Assigned task",
                    status=TaskStatus.NOT_STARTED,
                    goal="g",
                    steps=["s"],
                    iteration=1,
                )
            ],
        )
        task_file = tmp_path / ".tasks" / "test-branch.yml"
        task_file.parent.mkdir(parents=True, exist_ok=True)
        write_task_file(task_file, spec)

        _, mock_console = self._capture_output(task_file, tmp_path, monkeypatch)

        rule_calls = [str(call) for call in mock_console.rule.call_args_list]
        assert not any("Unassigned" in c for c in rule_calls)

    def test_empty_iteration_group_hidden(self, tmp_path, monkeypatch):
        """An iteration with no tasks assigned does not produce a rule header."""
        spec = SimpleTaskSpec(
            schema_version="1.0",
            branch="test-branch",
            title="Empty Iteration",
            original_prompt="Test prompt",
            created=datetime.now(UTC),
            acceptance_criteria=[
                AcceptanceCriterion(id="AC1", description="Criterion", completed=False)
            ],
            iterations=[
                Iteration(id=1, label="Sprint 1"),
                Iteration(id=2, label="Sprint 2"),  # no tasks assigned here
            ],
            tasks=[
                Task(
                    id="T001",
                    name="Task in sprint 1",
                    status=TaskStatus.NOT_STARTED,
                    goal="g",
                    steps=["s"],
                    iteration=1,
                )
            ],
        )
        task_file = tmp_path / ".tasks" / "test-branch.yml"
        task_file.parent.mkdir(parents=True, exist_ok=True)
        write_task_file(task_file, spec)

        _, mock_console = self._capture_output(task_file, tmp_path, monkeypatch)

        rule_calls = [str(call) for call in mock_console.rule.call_args_list]
        assert any("Sprint 1" in c for c in rule_calls)
        assert not any("Sprint 2" in c for c in rule_calls)

    def test_progress_counter_in_header(self, tmp_path, monkeypatch):
        """Rule header contains (done/total done) progress counter."""
        task_file, _ = _make_spec_with_iterations(tmp_path)
        _, mock_console = self._capture_output(task_file, tmp_path, monkeypatch)

        rule_calls = [str(call) for call in mock_console.rule.call_args_list]
        # Sprint 1 has T002 (completed) and T003 (not_started) → 1/2 done
        assert any("1/2 done" in c and "Sprint 1" in c for c in rule_calls)
        # Sprint 2 has T004 (in_progress) → 0/1 done
        assert any("0/1 done" in c and "Sprint 2" in c for c in rule_calls)
        # Unassigned has T001 (completed) → 1/1 done
        assert any("1/1 done" in c and "Unassigned" in c for c in rule_calls)

    def test_tasks_indented_under_iteration(self, tmp_path, monkeypatch):
        """Tasks under iteration groups use 4-space indent."""
        task_file, _ = _make_spec_with_iterations(tmp_path)
        output_calls, _ = self._capture_output(task_file, tmp_path, monkeypatch)

        task_lines = [c for c in output_calls if "T002" in c or "T003" in c or "T004" in c]
        assert all("    " in c for c in task_lines), "Grouped tasks must have 4-space indent"


def _make_finding(
    finding_id: str = "F-001",
    verdict: Verdict = Verdict.CONFIRMED,
) -> AuditFinding:
    """Build a minimal valid AuditFinding."""
    return AuditFinding(
        id=finding_id,
        file="cli/simpletask/core/models.py",
        original_severity=Severity.MEDIUM,
        original_category=FindingCategory.CORRECTNESS,
        verdict=verdict,
        summary="Test finding summary",
    )


def _make_spec_with_audit(tmp_path, audit_history=None):
    """Build a SimpleTaskSpec with optional audit_history and write it to disk."""
    spec = SimpleTaskSpec(
        schema_version="1.0",
        branch="test-branch",
        title="Test Task",
        original_prompt="Test prompt",
        created=datetime(2026, 1, 1, tzinfo=UTC),
        acceptance_criteria=[
            AcceptanceCriterion(id="AC1", description="Test criterion", completed=False)
        ],
        audit_history=audit_history,
    )
    task_file = tmp_path / ".tasks" / "test-branch.yml"
    task_file.parent.mkdir(parents=True, exist_ok=True)
    write_task_file(task_file, spec)
    return task_file, spec


class TestAuditHistoryDisplay:
    """Test show command audit history display."""

    def _capture_output(self, task_file, tmp_path, monkeypatch):
        """Return (output_call_strs, mock_console) after invoking show()."""
        monkeypatch.chdir(tmp_path)
        with patch("simpletask.commands.show.get_task_file_path", return_value=task_file):
            with patch("simpletask.commands.show.ensure_project") as mock_ensure:
                mock_ensure.return_value.root = tmp_path
                with patch("simpletask.commands.show.console") as mock_console:
                    show(branch="test-branch")
                    calls = [str(c) for c in mock_console.print.call_args_list]
                    return calls, mock_console

    def test_audit_section_present_with_runs(self, tmp_path, monkeypatch):
        """Audit History section is printed when audit_history has at least one run."""
        run = AuditRun(
            iteration=1,
            base_sha="abc1234",
            head_sha="def5678",
            findings=[
                _make_finding("F-001", Verdict.CONFIRMED),
                _make_finding("F-002", Verdict.FALSE_POSITIVE),
            ],
        )
        task_file, _ = _make_spec_with_audit(tmp_path, audit_history=[run])

        calls, _ = self._capture_output(task_file, tmp_path, monkeypatch)

        assert any("Audit History" in c for c in calls), "Expected Audit History header"
        assert any("1 run" in c for c in calls), "Expected run count in summary line"
        assert any("abc1234..def5678" in c for c in calls), "Expected latest range in summary"
        assert any("run 1" in c for c in calls), "Expected per-run line for iteration 1"
        # Verdict counts: confirmed: 1  false_positive: 1
        per_run_lines = [c for c in calls if "run 1" in c]
        assert per_run_lines, "Expected per-run breakdown line"
        assert any("confirmed" in c for c in per_run_lines)
        assert any("false_positive" in c for c in per_run_lines)

    def test_audit_section_absent_when_null(self, tmp_path, monkeypatch):
        """Audit History section is omitted when audit_history is None."""
        task_file, _ = _make_spec_with_audit(tmp_path, audit_history=None)

        calls, _ = self._capture_output(task_file, tmp_path, monkeypatch)

        assert not any("Audit History" in c for c in calls), (
            "Audit History section must not appear when audit_history is None"
        )

    def test_audit_section_absent_when_empty_list(self, tmp_path, monkeypatch):
        """Audit History section is omitted when audit_history is an empty list."""
        task_file, _ = _make_spec_with_audit(tmp_path, audit_history=[])

        calls, _ = self._capture_output(task_file, tmp_path, monkeypatch)

        assert not any("Audit History" in c for c in calls), (
            "Audit History section must not appear when audit_history is []"
        )

    def test_per_run_breakdown_multiple_runs(self, tmp_path, monkeypatch):
        """Each run gets its own breakdown line, sorted by iteration."""
        run1 = AuditRun(
            iteration=1,
            base_sha="aaa1111",
            head_sha="aaa1112",
            findings=[_make_finding("F-001", Verdict.CONFIRMED)],
        )
        run2 = AuditRun(
            iteration=2,
            base_sha="bbb2222",
            head_sha="bbb2223",
            findings=[_make_finding("F-001", Verdict.FALSE_POSITIVE)],
        )
        task_file, _ = _make_spec_with_audit(tmp_path, audit_history=[run2, run1])

        calls, _ = self._capture_output(task_file, tmp_path, monkeypatch)

        # Summary shows latest audited range (run2 = highest iteration)
        assert any("bbb2222..bbb2223" in c for c in calls), (
            "Latest range should be from highest iteration"
        )
        assert any("2 runs" in c for c in calls), "Should say 2 runs"
        # Both per-run lines must appear
        assert any("run 1" in c for c in calls)
        assert any("run 2" in c for c in calls)

    def test_json_output_includes_audit_history(self, tmp_path, monkeypatch, capsys):
        """JSON output includes audit_history with full run and finding data."""
        import json

        run = AuditRun(
            iteration=1,
            base_sha="deadbeef",
            head_sha="feedcafe",
            findings=[_make_finding("F-001", Verdict.CONFIRMED)],
        )
        task_file, _ = _make_spec_with_audit(tmp_path, audit_history=[run])

        monkeypatch.chdir(tmp_path)
        with patch("simpletask.commands.show.get_task_file_path", return_value=task_file):
            with patch("simpletask.commands.show.ensure_project") as mock_ensure:
                mock_ensure.return_value.root = tmp_path
                show(branch="test-branch", format=OutputFormat.JSON)

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert "audit_history" in output, "JSON output must contain audit_history key"
        assert output["audit_history"] is not None
        assert len(output["audit_history"]) == 1
        run_data = output["audit_history"][0]
        assert run_data["iteration"] == 1
        assert run_data["base_sha"] == "deadbeef"
        assert run_data["head_sha"] == "feedcafe"
        assert len(run_data["findings"]) == 1
        finding_data = run_data["findings"][0]
        assert finding_data["id"] == "F-001"
        assert finding_data["verdict"] == "confirmed"
        assert finding_data["original_severity"] == "medium"
        assert finding_data["original_category"] == "correctness"

    def test_json_output_audit_history_null_when_absent(self, tmp_path, monkeypatch, capsys):
        """JSON output has audit_history: null when audit_history is not set."""
        import json

        task_file, _ = _make_spec_with_audit(tmp_path, audit_history=None)

        monkeypatch.chdir(tmp_path)
        with patch("simpletask.commands.show.get_task_file_path", return_value=task_file):
            with patch("simpletask.commands.show.ensure_project") as mock_ensure:
                mock_ensure.return_value.root = tmp_path
                show(branch="test-branch", format=OutputFormat.JSON)

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert "audit_history" in output, "JSON output must always contain audit_history key"
        assert output["audit_history"] is None
