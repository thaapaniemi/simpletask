"""Integration tests for simpletask_audit MCP tool.

Tests cover:
- add_run: creates audit_history, persists to YAML, correct response
- add_run validation: missing required fields, invalid enum values
- list_runs: returns summaries after multiple runs
- get_run: returns specific run, raises for nonexistent iteration
- get_dismissed: filters correctly across multiple runs
- simpletask_get integration: include_audit flag behavior
- StatusSummary: audit_runs_total and latest_audit_{base,head}_sha computed correctly
"""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from simpletask.core.models import (
    AcceptanceCriterion,
    AuditFinding,
    AuditRun,
    FindingCategory,
    Severity,
    SimpleTaskSpec,
    Verdict,
)
from simpletask.core.yaml_parser import parse_task_file, write_task_file
from simpletask.mcp.models import compute_status_summary
from simpletask.mcp.server import audit, get

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_finding_dict(
    id: str = "F-001",
    verdict: str = "confirmed",
) -> dict:
    d: dict = {
        "id": id,
        "file": "src/foo.py",
        "original_severity": "high",
        "original_category": "security",
        "verdict": verdict,
        "summary": "Test finding",
    }
    if verdict == "reclassified":
        d["corrected_severity"] = "low"
        d["corrected_category"] = "style"
    return d


def make_spec_with_task(task_file: Path) -> Path:
    """Write a minimal spec to a task file and return the file path."""
    spec = SimpleTaskSpec(
        schema_version="1.0",
        branch="test-audit-branch",
        title="Audit Test",
        original_prompt="test prompt",
        created=datetime.now(UTC),
        acceptance_criteria=[AcceptanceCriterion(id="AC1", description="Done", completed=False)],
    )
    write_task_file(task_file, spec)
    return task_file


# ---------------------------------------------------------------------------
# add_run action
# ---------------------------------------------------------------------------


class TestAuditAddRun:
    def test_add_run_creates_audit_history(self, tmp_path):
        task_file = tmp_path / "task.yml"
        make_spec_with_task(task_file)

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file
            response = audit(
                action="add_run",
                iteration=1,
                base_sha="abc1234",
                head_sha="def5678",
                findings=[make_finding_dict()],
            )

        assert response.action == "audit_run_added"
        assert response.file_path == str(task_file)

        # Verify persisted to disk
        persisted = parse_task_file(task_file)
        assert persisted.audit_history is not None
        assert len(persisted.audit_history) == 1
        assert persisted.audit_history[0].iteration == 1
        assert persisted.audit_history[0].base_sha == "abc1234"
        assert persisted.audit_history[0].head_sha == "def5678"

    def test_add_run_accepts_string_iteration(self, tmp_path):
        task_file = tmp_path / "task.yml"
        make_spec_with_task(task_file)

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file
            response = audit(
                action="add_run",
                iteration="1",  # string integer (Qwen CLI compat)
                base_sha="abc1234",
                head_sha="def5678",
                findings=[make_finding_dict()],
            )

        assert response.action == "audit_run_added"

    def test_add_run_multiple_findings(self, tmp_path):
        task_file = tmp_path / "task.yml"
        make_spec_with_task(task_file)

        findings = [
            make_finding_dict("F-001", "confirmed"),
            make_finding_dict("F-002", "false_positive"),
            make_finding_dict("F-003", "uncertain"),
        ]

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file
            audit(
                action="add_run",
                iteration=1,
                base_sha="abc0001",
                head_sha="abc0002",
                findings=findings,
            )

        persisted = parse_task_file(task_file)
        assert len(persisted.audit_history[0].findings) == 3  # type: ignore[index]

    def test_add_run_missing_iteration_raises(self, tmp_path):
        task_file = tmp_path / "task.yml"
        make_spec_with_task(task_file)

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file
            with pytest.raises(ValueError, match="iteration"):
                audit(action="add_run", base_sha="abc1234", findings=[make_finding_dict()])

    def test_add_run_missing_base_sha_raises(self, tmp_path):
        task_file = tmp_path / "task.yml"
        make_spec_with_task(task_file)

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file
            with pytest.raises(ValueError, match="base_sha"):
                audit(action="add_run", iteration=1, findings=[make_finding_dict()])

    def test_add_run_missing_head_sha_raises(self, tmp_path):
        task_file = tmp_path / "task.yml"
        make_spec_with_task(task_file)

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file
            with pytest.raises(ValueError, match="head_sha"):
                audit(
                    action="add_run",
                    iteration=1,
                    base_sha="abc1234",
                    findings=[make_finding_dict()],
                )

    def test_add_run_empty_findings_raises(self, tmp_path):
        task_file = tmp_path / "task.yml"
        make_spec_with_task(task_file)

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file
            with pytest.raises(ValueError, match="findings"):
                audit(
                    action="add_run",
                    iteration=1,
                    base_sha="abc1234",
                    head_sha="def5678",
                    findings=[],
                )

    def test_add_run_invalid_finding_enum_raises(self, tmp_path):
        task_file = tmp_path / "task.yml"
        make_spec_with_task(task_file)

        bad_finding = make_finding_dict()
        bad_finding["verdict"] = "totally_invalid"

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file
            with pytest.raises(ValueError):  # Pydantic ValidationError is subclass of ValueError
                audit(
                    action="add_run",
                    iteration=1,
                    base_sha="abc1234",
                    head_sha="def5678",
                    findings=[bad_finding],
                )

    def test_add_run_duplicate_iteration_raises(self, tmp_path):
        task_file = tmp_path / "task.yml"
        make_spec_with_task(task_file)

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file
            audit(
                action="add_run",
                iteration=1,
                base_sha="abc0001",
                head_sha="abc0002",
                findings=[make_finding_dict()],
            )
            with pytest.raises(ValueError, match="iteration 1 already exists"):
                audit(
                    action="add_run",
                    iteration=1,
                    base_sha="abc0002",
                    head_sha="abc0003",
                    findings=[make_finding_dict()],
                )


# ---------------------------------------------------------------------------
# list_runs action
# ---------------------------------------------------------------------------


class TestAuditListRuns:
    def test_list_runs_empty(self, tmp_path):
        task_file = tmp_path / "task.yml"
        make_spec_with_task(task_file)

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file
            response = audit(action="list_runs")

        assert response.action == "audit_list_runs"
        assert response.audit_run_summaries == []

    def test_list_runs_returns_summaries(self, tmp_path):
        task_file = tmp_path / "task.yml"
        make_spec_with_task(task_file)

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file
            audit(
                action="add_run",
                iteration=1,
                base_sha="abc0001",
                head_sha="abc0002",
                findings=[make_finding_dict()],
            )
            audit(
                action="add_run",
                iteration=2,
                base_sha="bbb0002",
                head_sha="bbb0003",
                findings=[make_finding_dict("F-002")],
            )
            response = audit(action="list_runs")

        assert response.audit_run_summaries is not None
        assert len(response.audit_run_summaries) == 2
        iterations = [r.iteration for r in response.audit_run_summaries]
        assert iterations == [1, 2]
        assert response.audit_run_summaries[0].head_sha == "abc0002"
        assert response.audit_run_summaries[1].head_sha == "bbb0003"


# ---------------------------------------------------------------------------
# get_run action
# ---------------------------------------------------------------------------


class TestAuditGetRun:
    def test_get_run_returns_specific_run(self, tmp_path):
        task_file = tmp_path / "task.yml"
        make_spec_with_task(task_file)

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file
            audit(
                action="add_run",
                iteration=1,
                base_sha="abc0001",
                head_sha="abc0002",
                findings=[make_finding_dict()],
            )
            audit(
                action="add_run",
                iteration=2,
                base_sha="abc0002",
                head_sha="abc0003",
                findings=[make_finding_dict("F-002")],
            )
            response = audit(action="get_run", iteration=1)

        assert response.action == "audit_get_run"
        assert response.audit_run_detail is not None
        assert response.audit_run_detail.iteration == 1
        assert response.audit_run_detail.base_sha == "abc0001"
        assert response.audit_run_detail.head_sha == "abc0002"

    def test_get_run_missing_iteration_raises(self, tmp_path):
        task_file = tmp_path / "task.yml"
        make_spec_with_task(task_file)

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file
            with pytest.raises(ValueError, match="iteration"):
                audit(action="get_run")

    def test_get_run_nonexistent_iteration_raises(self, tmp_path):
        task_file = tmp_path / "task.yml"
        make_spec_with_task(task_file)

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file
            audit(
                action="add_run",
                iteration=1,
                base_sha="abc1234",
                head_sha="def5678",
                findings=[make_finding_dict()],
            )
            with pytest.raises(ValueError, match="No audit run found"):
                audit(action="get_run", iteration=99)


# ---------------------------------------------------------------------------
# get_dismissed action
# ---------------------------------------------------------------------------


class TestAuditGetDismissed:
    def test_get_dismissed_empty(self, tmp_path):
        task_file = tmp_path / "task.yml"
        make_spec_with_task(task_file)

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file
            response = audit(action="get_dismissed")

        assert response.action == "audit_get_dismissed"
        assert response.dismissed_findings == []

    def test_get_dismissed_filters_correctly(self, tmp_path):
        task_file = tmp_path / "task.yml"
        make_spec_with_task(task_file)

        findings = [
            make_finding_dict("F-001", "confirmed"),
            make_finding_dict("F-002", "false_positive"),
            make_finding_dict("F-003", "uncertain"),
            make_finding_dict("F-004", "reclassified"),
        ]

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file
            audit(
                action="add_run",
                iteration=1,
                base_sha="abc1234",
                head_sha="def5678",
                findings=findings,
            )
            response = audit(action="get_dismissed")

        assert response.dismissed_findings is not None
        dismissed_ids = {f.id for f in response.dismissed_findings}
        assert dismissed_ids == {"F-002", "F-003"}


# ---------------------------------------------------------------------------
# Invalid action
# ---------------------------------------------------------------------------


class TestAuditInvalidAction:
    """Defensive guard: verify the audit tool rejects unknown action strings.

    The audit() tool uses a Literal type for its action parameter. MCP clients that
    bypass schema validation (or future callers using the function directly) could still
    pass an unexpected string. This test ensures the explicit 'Unknown action' guard at
    the bottom of the dispatch block fires rather than silently doing nothing.
    """

    def test_invalid_action_raises(self, tmp_path):
        task_file = tmp_path / "task.yml"
        make_spec_with_task(task_file)

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file
            with pytest.raises(ValueError, match="Unknown action"):
                audit(action="invalid_action")


# ---------------------------------------------------------------------------
# simpletask_get integration: include_audit flag
# ---------------------------------------------------------------------------


class TestGetIncludeAudit:
    def test_default_excludes_audit_history(self, tmp_path):
        task_file = tmp_path / "task.yml"
        spec = SimpleTaskSpec(
            schema_version="1.1",
            branch="test-branch",
            title="Test",
            original_prompt="test",
            created=datetime.now(UTC),
            acceptance_criteria=[
                AcceptanceCriterion(id="AC1", description="Done", completed=False)
            ],
            audit_history=[
                AuditRun(
                    iteration=1,
                    base_sha="abc1234",
                    head_sha="def5678",
                    findings=[
                        AuditFinding(
                            id="F-001",
                            file="src/foo.py",
                            original_severity=Severity.HIGH,
                            original_category=FindingCategory.SECURITY,
                            verdict=Verdict.CONFIRMED,
                            summary="Test",
                        )
                    ],
                )
            ],
        )
        write_task_file(task_file, spec)

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file
            response = get()

        assert response.spec.audit_history is None
        assert response.filters_applied is not None
        assert response.filters_applied["include_audit"] is False

    def test_include_audit_true_includes_history(self, tmp_path):
        task_file = tmp_path / "task.yml"
        spec = SimpleTaskSpec(
            schema_version="1.1",
            branch="test-branch",
            title="Test",
            original_prompt="test",
            created=datetime.now(UTC),
            acceptance_criteria=[
                AcceptanceCriterion(id="AC1", description="Done", completed=False)
            ],
            audit_history=[
                AuditRun(
                    iteration=1,
                    base_sha="abc1234",
                    head_sha="def5678",
                    findings=[
                        AuditFinding(
                            id="F-001",
                            file="src/foo.py",
                            original_severity=Severity.HIGH,
                            original_category=FindingCategory.SECURITY,
                            verdict=Verdict.CONFIRMED,
                            summary="Test",
                        )
                    ],
                )
            ],
        )
        write_task_file(task_file, spec)

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file
            response = get(include_audit=True)

        assert response.spec.audit_history is not None
        assert len(response.spec.audit_history) == 1

    def test_full_true_includes_audit_history(self, tmp_path):
        task_file = tmp_path / "task.yml"
        spec = SimpleTaskSpec(
            schema_version="1.1",
            branch="test-branch",
            title="Test",
            original_prompt="test",
            created=datetime.now(UTC),
            acceptance_criteria=[
                AcceptanceCriterion(id="AC1", description="Done", completed=False)
            ],
            audit_history=[
                AuditRun(
                    iteration=1,
                    base_sha="abc1234",
                    head_sha="def5678",
                    findings=[
                        AuditFinding(
                            id="F-001",
                            file="src/foo.py",
                            original_severity=Severity.HIGH,
                            original_category=FindingCategory.SECURITY,
                            verdict=Verdict.CONFIRMED,
                            summary="Test",
                        )
                    ],
                )
            ],
        )
        write_task_file(task_file, spec)

        with patch("simpletask.mcp.server.get_current_task_file_path") as mock_path:
            mock_path.return_value = task_file
            response = get(full=True)

        assert response.spec.audit_history is not None
        assert response.filters_applied is None
        assert response.spec.schema_version == "1.2"


# ---------------------------------------------------------------------------
# StatusSummary audit fields
# ---------------------------------------------------------------------------


class TestStatusSummaryAuditFields:
    def test_no_audits_returns_zero_and_none(self):
        spec = SimpleTaskSpec(
            schema_version="1.1",
            branch="test",
            title="Test",
            original_prompt="test",
            created=datetime.now(UTC),
            acceptance_criteria=[
                AcceptanceCriterion(id="AC1", description="Done", completed=False)
            ],
        )
        summary = compute_status_summary(spec)
        assert summary.audit_runs_total == 0
        assert summary.latest_audit_base_sha is None
        assert summary.latest_audit_head_sha is None

    def test_single_audit_run_computed_correctly(self):
        spec = SimpleTaskSpec(
            schema_version="1.1",
            branch="test",
            title="Test",
            original_prompt="test",
            created=datetime.now(UTC),
            acceptance_criteria=[
                AcceptanceCriterion(id="AC1", description="Done", completed=False)
            ],
            audit_history=[
                AuditRun(
                    iteration=1,
                    base_sha="abc1111",
                    head_sha="bbb1111",
                    findings=[
                        AuditFinding(
                            id="F-001",
                            file="src/foo.py",
                            original_severity=Severity.HIGH,
                            original_category=FindingCategory.SECURITY,
                            verdict=Verdict.CONFIRMED,
                            summary="Test",
                        )
                    ],
                )
            ],
        )
        summary = compute_status_summary(spec)
        assert summary.audit_runs_total == 1
        assert summary.latest_audit_base_sha == "abc1111"
        assert summary.latest_audit_head_sha == "bbb1111"

    def test_multiple_runs_latest_sha_is_last(self):
        spec = SimpleTaskSpec(
            schema_version="1.1",
            branch="test",
            title="Test",
            original_prompt="test",
            created=datetime.now(UTC),
            acceptance_criteria=[
                AcceptanceCriterion(id="AC1", description="Done", completed=False)
            ],
            audit_history=[
                AuditRun(
                    iteration=1,
                    base_sha="abc0001",
                    head_sha="abc0002",
                    findings=[
                        AuditFinding(
                            id="F-001",
                            file="src/foo.py",
                            original_severity=Severity.HIGH,
                            original_category=FindingCategory.SECURITY,
                            verdict=Verdict.CONFIRMED,
                            summary="Test",
                        )
                    ],
                ),
                AuditRun(
                    iteration=2,
                    base_sha="abc0002",
                    head_sha="abc0003",
                    findings=[
                        AuditFinding(
                            id="F-002",
                            file="src/bar.py",
                            original_severity=Severity.MEDIUM,
                            original_category=FindingCategory.CORRECTNESS,
                            verdict=Verdict.FALSE_POSITIVE,
                            summary="Another test",
                        )
                    ],
                ),
            ],
        )
        summary = compute_status_summary(spec)
        assert summary.audit_runs_total == 2
        assert summary.latest_audit_base_sha == "abc0002"
        assert summary.latest_audit_head_sha == "abc0003"

    def test_latest_sha_uses_max_iteration_not_insertion_order(self):
        """latest_audit_base_sha must reflect highest iteration, not last-inserted run."""
        spec = SimpleTaskSpec(
            schema_version="1.1",
            branch="test",
            title="Test",
            original_prompt="test",
            created=datetime.now(UTC),
            acceptance_criteria=[
                AcceptanceCriterion(id="AC1", description="Done", completed=False)
            ],
            audit_history=[
                # iteration 2 inserted first (higher number, earlier in list)
                AuditRun(
                    iteration=2,
                    base_sha="bbb2222",
                    head_sha="ccc2222",
                    findings=[
                        AuditFinding(
                            id="F-001",
                            file="src/foo.py",
                            original_severity=Severity.HIGH,
                            original_category=FindingCategory.SECURITY,
                            verdict=Verdict.CONFIRMED,
                            summary="Test",
                        )
                    ],
                ),
                # iteration 1 inserted second (lower number, later in list)
                AuditRun(
                    iteration=1,
                    base_sha="aaa1111",
                    head_sha="bbb1111",
                    findings=[
                        AuditFinding(
                            id="F-002",
                            file="src/bar.py",
                            original_severity=Severity.MEDIUM,
                            original_category=FindingCategory.CORRECTNESS,
                            verdict=Verdict.FALSE_POSITIVE,
                            summary="Another test",
                        )
                    ],
                ),
            ],
        )
        summary = compute_status_summary(spec)
        assert summary.audit_runs_total == 2
        # Must return sha_newer (iteration=2), not sha_older (last inserted)
        assert summary.latest_audit_base_sha == "bbb2222"
        assert summary.latest_audit_head_sha == "ccc2222"
