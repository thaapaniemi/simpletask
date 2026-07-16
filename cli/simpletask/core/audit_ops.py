"""Audit operations for simpletask.

This module provides functions for managing code audit history on task specifications.
Audit runs capture findings from code reviews, track verdicts, and support
incremental auditing by persisting dismissed findings across runs.
"""

from typing import TypedDict

from pydantic import ValidationError

from .models import AuditFinding, AuditRun, SimpleTaskSpec, Verdict


class AuditRunSummaryDict(TypedDict):
    """Summary of a single audit run as returned by list_audit_runs()."""

    iteration: int
    base_sha: str
    head_sha: str
    findings_total: int
    verdict_counts: dict[str, int]


def get_next_finding_id(findings: list[AuditFinding]) -> str:
    """Generate the next sequential finding ID in F-NNN format.

    Scans existing finding IDs (expected pattern F-NNN) and returns
    the next integer after the highest found. Falls back to F-001 if
    no parseable IDs exist.

    Note: Finding IDs are scoped per run, not globally unique across all runs
    in audit_history. Two separate runs may each contain F-001 without conflict.
    This function operates on the findings list provided to it; callers are
    responsible for passing only the relevant run's findings.

    Args:
        findings: Existing findings to inspect for highest ID.

    Returns:
        Next finding ID string, e.g. 'F-001', 'F-042'.
    """
    max_num = 0
    for finding in findings:
        # ID format: F-NNN (3+ digits)
        parts = finding.id.split("-", 1)
        if len(parts) == 2 and parts[1].isdigit():
            max_num = max(max_num, int(parts[1]))
    return f"F-{max_num + 1:03d}"


def add_audit_run(
    spec: SimpleTaskSpec,
    iteration: int,
    base_sha: str,
    head_sha: str,
    findings: list[AuditFinding],
) -> SimpleTaskSpec:
    """Append a new audit run to the spec's audit_history.

    Args:
        spec: Current task specification.
        iteration: Monotonically increasing audit iteration number (ge=1).
        base_sha: Git SHA of the base commit audited (7-40 hex characters).
        head_sha: Git SHA of the HEAD commit audited (7-40 hex characters).
        findings: Non-empty list of AuditFinding objects.

    Returns:
        Updated SimpleTaskSpec with the new AuditRun appended.

    Raises:
        ValueError: If iteration already exists in audit_history.
        ValueError: If AuditRun construction fails due to invalid inputs (invalid iteration,
            base_sha/head_sha format, or empty findings list).
    """
    existing_history = spec.audit_history or []
    # Iteration IDs must be unique per task file; duplicate submissions are rejected
    # so each iteration can only have one canonical audit snapshot.
    existing_iterations = {run.iteration for run in existing_history}
    if iteration in existing_iterations:
        raise ValueError(
            f"Audit run for iteration {iteration} already exists. "
            f"Each iteration may only have one audit run."
        )

    try:
        new_run = AuditRun(
            iteration=iteration, base_sha=base_sha, head_sha=head_sha, findings=findings
        )
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc
    updated_history = [*existing_history, new_run]
    return spec.model_copy(update={"audit_history": updated_history})


def list_audit_runs(spec: SimpleTaskSpec) -> list[AuditRunSummaryDict]:
    """Return summary information for all audit runs.

    Each summary includes the iteration number, base SHA, total finding count,
    and per-verdict breakdown.

    Args:
        spec: Task specification to inspect.

    Returns:
        List of AuditRunSummaryDict entries sorted by iteration ascending.
        Empty list if no audit history exists.
    """
    if not spec.audit_history:
        return []

    summaries: list[AuditRunSummaryDict] = []
    for run in spec.audit_history:
        verdict_counts: dict[str, int] = {}
        for finding in run.findings:
            verdict_counts[finding.verdict.value] = verdict_counts.get(finding.verdict.value, 0) + 1
        summaries.append(
            {
                "iteration": run.iteration,
                "base_sha": run.base_sha,
                "head_sha": run.head_sha,
                "findings_total": len(run.findings),
                "verdict_counts": verdict_counts,
            }
        )

    return sorted(summaries, key=lambda s: s["iteration"])


def get_audit_run(spec: SimpleTaskSpec, iteration: int) -> AuditRun:
    """Retrieve a specific audit run by iteration number.

    Args:
        spec: Task specification to search.
        iteration: Iteration number of the audit run to retrieve.

    Returns:
        The matching AuditRun.

    Raises:
        ValueError: If no audit run exists for the given iteration.
    """
    if spec.audit_history:
        for run in spec.audit_history:
            if run.iteration == iteration:
                return run

    existing = sorted(r.iteration for r in (spec.audit_history or []))
    raise ValueError(
        f"No audit run found for iteration {iteration}. Existing audit iterations: {existing}"
    )


def get_dismissed_findings(spec: SimpleTaskSpec) -> list[AuditFinding]:
    """Collect all dismissed findings (false_positive or uncertain) across all runs.

    Args:
        spec: Task specification to inspect.

    Returns:
        List of AuditFinding objects with verdict=false_positive or verdict=uncertain.
        Empty list if no audit history exists or no dismissed findings exist.
    """
    dismissed_verdicts = {Verdict.FALSE_POSITIVE, Verdict.UNCERTAIN}
    dismissed: list[AuditFinding] = []

    if not spec.audit_history:
        return dismissed

    for run in spec.audit_history:
        for finding in run.findings:
            if finding.verdict in dismissed_verdicts:
                dismissed.append(finding)

    return dismissed


__all__ = [
    "add_audit_run",
    "get_audit_run",
    "get_dismissed_findings",
    "list_audit_runs",
]
