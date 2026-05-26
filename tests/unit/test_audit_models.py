"""Unit tests for audit-related Pydantic models.

Tests cover:
- AuditFinding model validation: valid inputs, required fields, invalid enums
- AuditFinding reclassified validator: corrected fields required/rejected based on verdict
- AuditRun model: valid input, empty findings rejected
- SimpleTaskSpec with audit_history: None accepted, valid list accepted, schema version 1.2
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from simpletask.core.models import (
    AcceptanceCriterion,
    AuditFinding,
    AuditRun,
    FindingCategory,
    Severity,
    SimpleTaskSpec,
    Verdict,
)

from tests.conftest import make_finding

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_spec_with_audit(runs: list[AuditRun] | None = None) -> SimpleTaskSpec:
    return SimpleTaskSpec(
        schema_version="1.2",
        branch="test-branch",
        title="Test",
        original_prompt="test prompt",
        created=datetime.now(UTC),
        acceptance_criteria=[AcceptanceCriterion(id="AC1", description="Done", completed=False)],
        audit_history=runs,
    )


# ---------------------------------------------------------------------------
# AuditFinding validation
# ---------------------------------------------------------------------------


class TestAuditFindingValid:
    def test_confirmed_finding_no_corrected_fields(self):
        finding = make_finding(verdict=Verdict.CONFIRMED)
        assert finding.verdict == Verdict.CONFIRMED
        assert finding.corrected_severity is None
        assert finding.corrected_category is None

    def test_false_positive_finding(self):
        finding = make_finding(verdict=Verdict.FALSE_POSITIVE)
        assert finding.verdict == Verdict.FALSE_POSITIVE

    def test_uncertain_finding(self):
        finding = make_finding(verdict=Verdict.UNCERTAIN)
        assert finding.verdict == Verdict.UNCERTAIN

    def test_reclassified_with_both_corrected_fields(self):
        finding = make_finding(
            verdict=Verdict.RECLASSIFIED,
            corrected_severity=Severity.LOW,
            corrected_category=FindingCategory.PERFORMANCE,
        )
        assert finding.corrected_severity == Severity.LOW
        assert finding.corrected_category == FindingCategory.PERFORMANCE

    def test_id_pattern_valid(self):
        finding = make_finding(id="F-001")
        assert finding.id == "F-001"

        finding_long = make_finding(id="F-1234")
        assert finding_long.id == "F-1234"

    def test_optional_task_id(self):
        finding = AuditFinding(
            id="F-001",
            file="src/foo.py",
            original_severity=Severity.MEDIUM,
            original_category=FindingCategory.CORRECTNESS,
            verdict=Verdict.CONFIRMED,
            summary="Test",
            task_id="T001",
        )
        assert finding.task_id == "T001"


class TestAuditFindingRequiredFields:
    def test_missing_id_raises(self):
        with pytest.raises(ValidationError, match="id"):
            AuditFinding(
                file="src/foo.py",
                original_severity="high",
                original_category="security",
                verdict="confirmed",
                summary="Test",
            )

    def test_missing_file_raises(self):
        with pytest.raises(ValidationError, match="file"):
            AuditFinding(
                id="F-001",
                original_severity="high",
                original_category="security",
                verdict="confirmed",
                summary="Test",
            )

    def test_missing_summary_raises(self):
        with pytest.raises(ValidationError, match="summary"):
            AuditFinding(
                id="F-001",
                file="src/foo.py",
                original_severity="high",
                original_category="security",
                verdict="confirmed",
            )

    def test_invalid_severity_enum_raises(self):
        with pytest.raises(ValidationError):
            AuditFinding(
                id="F-001",
                file="src/foo.py",
                original_severity="extreme",
                original_category="security",
                verdict="confirmed",
                summary="Test",
            )

    def test_invalid_category_enum_raises(self):
        with pytest.raises(ValidationError):
            AuditFinding(
                id="F-001",
                file="src/foo.py",
                original_severity="high",
                original_category="unknown_category",
                verdict="confirmed",
                summary="Test",
            )

    def test_invalid_verdict_enum_raises(self):
        with pytest.raises(ValidationError):
            AuditFinding(
                id="F-001",
                file="src/foo.py",
                original_severity="high",
                original_category="security",
                verdict="invalid_verdict",
                summary="Test",
            )

    def test_invalid_id_pattern_raises(self):
        with pytest.raises(ValidationError):
            AuditFinding(
                id="FINDING-001",  # wrong pattern
                file="src/foo.py",
                original_severity="high",
                original_category="security",
                verdict="confirmed",
                summary="Test",
            )


class TestAuditFindingReclassifiedValidator:
    def test_reclassified_missing_corrected_severity_raises(self):
        with pytest.raises(ValidationError, match="corrected_severity is required"):
            AuditFinding(
                id="F-001",
                file="src/foo.py",
                original_severity=Severity.HIGH,
                original_category=FindingCategory.SECURITY,
                verdict=Verdict.RECLASSIFIED,
                corrected_category=FindingCategory.PERFORMANCE,
                summary="Test",
            )

    def test_reclassified_missing_corrected_category_raises(self):
        with pytest.raises(ValidationError, match="corrected_category is required"):
            AuditFinding(
                id="F-001",
                file="src/foo.py",
                original_severity=Severity.HIGH,
                original_category=FindingCategory.SECURITY,
                verdict=Verdict.RECLASSIFIED,
                corrected_severity=Severity.LOW,
                summary="Test",
            )

    def test_confirmed_with_corrected_severity_raises(self):
        with pytest.raises(ValidationError, match="corrected_severity must not be set"):
            make_finding(verdict=Verdict.CONFIRMED, corrected_severity=Severity.LOW)

    def test_false_positive_with_corrected_category_raises(self):
        with pytest.raises(ValidationError, match="corrected_category must not be set"):
            make_finding(
                verdict=Verdict.FALSE_POSITIVE,
                corrected_category=FindingCategory.STYLE,
            )

    def test_uncertain_with_both_corrected_raises(self):
        with pytest.raises(ValidationError):
            make_finding(
                verdict=Verdict.UNCERTAIN,
                corrected_severity=Severity.MEDIUM,
                corrected_category=FindingCategory.TESTING,
            )


# ---------------------------------------------------------------------------
# AuditRun validation
# ---------------------------------------------------------------------------


class TestAuditRunValid:
    def test_valid_run(self):
        run = AuditRun(
            iteration=1,
            base_sha="abc1234",
            head_sha="def5678",
            findings=[make_finding()],
        )
        assert run.iteration == 1
        assert run.base_sha == "abc1234"
        assert len(run.findings) == 1

    def test_multiple_findings(self):
        run = AuditRun(
            iteration=2,
            base_sha="def5678",
            head_sha="fedcba9",
            findings=[make_finding("F-001"), make_finding("F-002"), make_finding("F-003")],
        )
        assert len(run.findings) == 3


class TestAuditRunValidation:
    def test_empty_findings_rejected(self):
        with pytest.raises(ValidationError, match="at least 1"):
            AuditRun(iteration=1, base_sha="abc1234", head_sha="def5678", findings=[])

    def test_iteration_ge_1(self):
        with pytest.raises(ValidationError):
            AuditRun(iteration=0, base_sha="abc1234", head_sha="def5678", findings=[make_finding()])

    def test_missing_base_sha_raises(self):
        with pytest.raises(ValidationError, match="base_sha"):
            AuditRun(iteration=1, findings=[make_finding()])


# ---------------------------------------------------------------------------
# SimpleTaskSpec with audit_history
# ---------------------------------------------------------------------------


class TestSimpleTaskSpecAuditHistory:
    def test_none_audit_history_accepted(self):
        spec = make_spec_with_audit(None)
        assert spec.audit_history is None

    def test_valid_audit_history_accepted(self):
        run = AuditRun(
            iteration=1,
            base_sha="abc1234",
            head_sha="def5678",
            findings=[make_finding()],
        )
        spec = make_spec_with_audit([run])
        assert spec.audit_history is not None
        assert len(spec.audit_history) == 1

    def test_schema_version_12_accepted(self):
        spec = make_spec_with_audit(None)
        assert spec.schema_version == "1.2"

    def test_schema_version_10_still_accepted(self):
        spec = SimpleTaskSpec(
            schema_version="1.0",
            branch="old-branch",
            title="Old",
            original_prompt="old prompt",
            created=datetime.now(UTC),
            acceptance_criteria=[
                AcceptanceCriterion(id="AC1", description="Done", completed=False)
            ],
        )
        assert spec.schema_version == "1.0"

    def test_schema_version_unsupported_raises(self):
        with pytest.raises(ValidationError, match="Unsupported schema version"):
            SimpleTaskSpec(
                schema_version="2.0",
                branch="test",
                title="Test",
                original_prompt="test",
                created=datetime.now(UTC),
                acceptance_criteria=[
                    AcceptanceCriterion(id="AC1", description="Done", completed=False)
                ],
            )


# ---------------------------------------------------------------------------
# T013: AuditRun.base_sha format validation
# ---------------------------------------------------------------------------


class TestAuditRunBaseSha:
    def test_empty_string_rejected(self):
        with pytest.raises(ValidationError):
            AuditRun(iteration=1, base_sha="", head_sha="def5678", findings=[make_finding()])

    def test_non_hex_string_rejected(self):
        with pytest.raises(ValidationError):
            AuditRun(
                iteration=1,
                base_sha="not-a-sha",
                head_sha="def5678",
                findings=[make_finding()],
            )

    def test_too_short_rejected(self):
        with pytest.raises(ValidationError):
            AuditRun(
                iteration=1,
                base_sha="abc123",
                head_sha="def5678",
                findings=[make_finding()],
            )  # 6 chars < 7

    def test_valid_7_char_sha_accepted(self):
        run = AuditRun(
            iteration=1,
            base_sha="abc1234",
            head_sha="def5678",
            findings=[make_finding()],
        )
        assert run.base_sha == "abc1234"

    def test_valid_40_char_sha_accepted(self):
        sha40 = "e80d2978b776c7e886d220a168479ab24aa2160b"
        run = AuditRun(iteration=1, base_sha=sha40, head_sha=sha40, findings=[make_finding()])
        assert run.base_sha == sha40


class TestAuditRunHeadSha:
    def test_missing_head_sha_rejected(self):
        with pytest.raises(ValidationError, match="head_sha"):
            AuditRun(iteration=1, base_sha="abc1234", findings=[make_finding()])

    def test_invalid_head_sha_rejected(self):
        with pytest.raises(ValidationError):
            AuditRun(
                iteration=1,
                base_sha="abc1234",
                head_sha="not-a-sha",
                findings=[make_finding()],
            )

    def test_valid_head_sha_accepted(self):
        run = AuditRun(
            iteration=1,
            base_sha="abc1234",
            head_sha="def5678",
            findings=[make_finding()],
        )
        assert run.head_sha == "def5678"


# ---------------------------------------------------------------------------
# T014: AuditFinding.id pattern intent
# ---------------------------------------------------------------------------


class TestAuditFindingIdPattern:
    def test_f_1000_accepted(self):
        finding = make_finding(id="F-1000")
        assert finding.id == "F-1000"

    def test_f_01_rejected(self):
        with pytest.raises(ValidationError):
            make_finding(id="F-01")


# ---------------------------------------------------------------------------
# T025: TestGetNextFindingIdScope (moved from test_audit_ops.py - tests model construction)
# ---------------------------------------------------------------------------


class TestGetNextFindingIdScope:
    def test_two_runs_can_each_have_f001(self):
        """Finding IDs are per-run; two separate runs may both contain F-001."""
        run1 = AuditRun(
            iteration=1,
            base_sha="abc0001",
            head_sha="abc0002",
            findings=[make_finding("F-001", Verdict.CONFIRMED)],
        )
        run2 = AuditRun(
            iteration=2,
            base_sha="abc0002",
            head_sha="abc0003",
            findings=[make_finding("F-001", Verdict.FALSE_POSITIVE)],
        )
        spec = make_spec_with_audit([run1, run2])
        assert spec.audit_history is not None
        assert spec.audit_history[0].findings[0].id == "F-001"
        assert spec.audit_history[1].findings[0].id == "F-001"
