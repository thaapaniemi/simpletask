"""Unit tests for audit_ops module.

Tests cover:
- get_next_finding_id: ID generation
- add_audit_run: appends run, validates, rejects duplicate iteration
- list_audit_runs: returns summaries with correct verdict counts
- get_audit_run: returns correct run, raises for missing iteration
- get_dismissed_findings: filters only false_positive and uncertain
"""

from datetime import UTC, datetime

import pytest
from simpletask.core.audit_ops import (
    add_audit_run,
    get_audit_run,
    get_dismissed_findings,
    get_next_finding_id,
    list_audit_runs,
)
from simpletask.core.models import (
    AcceptanceCriterion,
    AuditFinding,
    AuditRun,
    SimpleTaskSpec,
    Verdict,
)

from tests.conftest import make_finding

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_spec(runs: list[AuditRun] | None = None) -> SimpleTaskSpec:
    schema_version = "1.2" if runs else "1.1"
    return SimpleTaskSpec(
        schema_version=schema_version,
        branch="test-branch",
        title="Test",
        original_prompt="test prompt",
        created=datetime.now(UTC),
        acceptance_criteria=[AcceptanceCriterion(id="AC1", description="Done", completed=False)],
        audit_history=runs,
    )


def make_run(iteration: int = 1, findings: list[AuditFinding] | None = None) -> AuditRun:
    return AuditRun(
        iteration=iteration,
        base_sha=f"abc{iteration:04d}",
        head_sha=f"def{iteration:04d}",
        findings=findings or [make_finding()],
    )


# ---------------------------------------------------------------------------
# get_next_finding_id
# ---------------------------------------------------------------------------


class TestGetNextFindingId:
    def test_empty_findings_returns_f001(self):
        assert get_next_finding_id([]) == "F-001"

    def test_single_existing_finding(self):
        findings = [make_finding("F-001")]
        assert get_next_finding_id(findings) == "F-002"

    def test_sequential_findings(self):
        findings = [make_finding("F-001"), make_finding("F-002"), make_finding("F-003")]
        assert get_next_finding_id(findings) == "F-004"

    def test_non_sequential_returns_max_plus_one(self):
        findings = [make_finding("F-001"), make_finding("F-010")]
        assert get_next_finding_id(findings) == "F-011"

    def test_zero_padded_three_digits(self):
        result = get_next_finding_id([])
        assert result == "F-001"
        assert len(result.split("-")[1]) >= 3


# ---------------------------------------------------------------------------
# add_audit_run
# ---------------------------------------------------------------------------


class TestAddAuditRun:
    def test_adds_run_to_empty_history(self):
        spec = make_spec()
        assert spec.audit_history is None

        updated = add_audit_run(spec, 1, "abc1234", "def5678", [make_finding()])
        assert updated.audit_history is not None
        assert len(updated.audit_history) == 1
        assert updated.audit_history[0].iteration == 1
        assert updated.audit_history[0].base_sha == "abc1234"
        assert updated.audit_history[0].head_sha == "def5678"

    def test_appends_run_to_existing_history(self):
        spec = make_spec([make_run(1)])
        updated = add_audit_run(spec, 2, "def4567", "fedcba9", [make_finding()])
        assert len(updated.audit_history) == 2  # type: ignore[arg-type]
        assert updated.audit_history[1].iteration == 2  # type: ignore[index]

    def test_does_not_mutate_original_spec(self):
        spec = make_spec()
        add_audit_run(spec, 1, "abc1234", "def5678", [make_finding()])
        assert spec.audit_history is None

    def test_raises_for_duplicate_iteration(self):
        spec = make_spec([make_run(1)])
        with pytest.raises(ValueError, match="iteration 1 already exists"):
            add_audit_run(spec, 1, "xyz", "def5678", [make_finding()])

    def test_raises_for_empty_findings(self):
        spec = make_spec()
        with pytest.raises(ValueError, match="List should have at least 1 item"):
            add_audit_run(spec, 1, "abc1234", "def5678", [])

    def test_raises_for_invalid_base_sha(self):
        spec = make_spec()
        with pytest.raises(ValueError, match="base_sha"):
            add_audit_run(spec, 1, "not-a-sha", "def5678", [make_finding()])

    def test_raises_for_invalid_head_sha(self):
        spec = make_spec()
        with pytest.raises(ValueError, match="head_sha"):
            add_audit_run(spec, 1, "abc1234", "not-a-sha", [make_finding()])

    def test_raises_for_too_short_base_sha(self):
        spec = make_spec()
        with pytest.raises(ValueError, match="base_sha"):
            add_audit_run(spec, 1, "abc123", "def5678", [make_finding()])  # 6 chars

    def test_raises_for_iteration_less_than_one(self):
        spec = make_spec()
        with pytest.raises(ValueError, match="iteration"):
            add_audit_run(spec, 0, "abc1234", "def5678", [make_finding()])


# ---------------------------------------------------------------------------
# list_audit_runs
# ---------------------------------------------------------------------------


class TestListAuditRuns:
    def test_empty_history_returns_empty_list(self):
        spec = make_spec()
        assert list_audit_runs(spec) == []

    def test_returns_summaries_sorted_by_iteration(self):
        spec = make_spec([make_run(2), make_run(1)])
        result = list_audit_runs(spec)
        assert [r["iteration"] for r in result] == [1, 2]

    def test_summary_contains_expected_keys(self):
        spec = make_spec([make_run(1)])
        result = list_audit_runs(spec)
        assert len(result) == 1
        summary = result[0]
        assert "iteration" in summary
        assert "base_sha" in summary
        assert "head_sha" in summary
        assert "findings_total" in summary
        assert "verdict_counts" in summary

    def test_verdict_counts_accurate(self):
        findings = [
            make_finding("F-001", Verdict.CONFIRMED),
            make_finding("F-002", Verdict.CONFIRMED),
            make_finding("F-003", Verdict.FALSE_POSITIVE),
            make_finding("F-004", Verdict.UNCERTAIN),
        ]
        spec = make_spec(
            [AuditRun(iteration=1, base_sha="abc1234", head_sha="def5678", findings=findings)]
        )
        result = list_audit_runs(spec)
        counts = result[0]["verdict_counts"]
        assert counts["confirmed"] == 2
        assert counts["false_positive"] == 1
        assert counts["uncertain"] == 1

    def test_findings_total_accurate(self):
        findings = [make_finding(f"F-{i:03d}") for i in range(1, 6)]
        spec = make_spec(
            [AuditRun(iteration=1, base_sha="abc1234", head_sha="def5678", findings=findings)]
        )
        result = list_audit_runs(spec)
        assert result[0]["findings_total"] == 5


# ---------------------------------------------------------------------------
# get_audit_run
# ---------------------------------------------------------------------------


class TestGetAuditRun:
    def test_returns_correct_run(self):
        run1 = make_run(1)
        run2 = make_run(2)
        spec = make_spec([run1, run2])

        result = get_audit_run(spec, 1)
        assert result.iteration == 1
        assert result.base_sha == run1.base_sha

    def test_raises_for_missing_iteration(self):
        spec = make_spec([make_run(1)])
        with pytest.raises(ValueError, match="No audit run found for iteration 99"):
            get_audit_run(spec, 99)

    def test_raises_when_no_history(self):
        spec = make_spec()
        with pytest.raises(ValueError, match="No audit run found"):
            get_audit_run(spec, 1)


# ---------------------------------------------------------------------------
# get_dismissed_findings
# ---------------------------------------------------------------------------


class TestGetDismissedFindings:
    def test_empty_history_returns_empty(self):
        spec = make_spec()
        assert get_dismissed_findings(spec) == []

    def test_no_dismissed_findings_returns_empty(self):
        findings = [make_finding("F-001", Verdict.CONFIRMED)]
        spec = make_spec(
            [AuditRun(iteration=1, base_sha="abc1234", head_sha="def5678", findings=findings)]
        )
        assert get_dismissed_findings(spec) == []

    def test_returns_false_positive_findings(self):
        findings = [
            make_finding("F-001", Verdict.CONFIRMED),
            make_finding("F-002", Verdict.FALSE_POSITIVE),
        ]
        spec = make_spec(
            [AuditRun(iteration=1, base_sha="abc1234", head_sha="def5678", findings=findings)]
        )
        dismissed = get_dismissed_findings(spec)
        assert len(dismissed) == 1
        assert dismissed[0].id == "F-002"

    def test_returns_uncertain_findings(self):
        findings = [
            make_finding("F-001", Verdict.UNCERTAIN),
        ]
        spec = make_spec(
            [AuditRun(iteration=1, base_sha="abc1234", head_sha="def5678", findings=findings)]
        )
        dismissed = get_dismissed_findings(spec)
        assert len(dismissed) == 1
        assert dismissed[0].verdict == Verdict.UNCERTAIN

    def test_collects_across_multiple_runs(self):
        run1 = AuditRun(
            iteration=1,
            base_sha="abc0001",
            head_sha="abc0002",
            findings=[
                make_finding("F-001", Verdict.FALSE_POSITIVE),
                make_finding("F-002", Verdict.CONFIRMED),
            ],
        )
        run2 = AuditRun(
            iteration=2,
            base_sha="abc0002",
            head_sha="abc0003",
            findings=[
                make_finding("F-003", Verdict.UNCERTAIN),
                make_finding("F-004", Verdict.CONFIRMED),
            ],
        )
        spec = make_spec([run1, run2])
        dismissed = get_dismissed_findings(spec)
        ids = {f.id for f in dismissed}
        assert ids == {"F-001", "F-003"}

    def test_does_not_include_confirmed_or_reclassified(self):
        findings = [
            make_finding("F-001", Verdict.CONFIRMED),
            make_finding("F-002", Verdict.RECLASSIFIED),
        ]
        spec = make_spec(
            [AuditRun(iteration=1, base_sha="abc1234", head_sha="def5678", findings=findings)]
        )
        dismissed = get_dismissed_findings(spec)
        assert dismissed == []
