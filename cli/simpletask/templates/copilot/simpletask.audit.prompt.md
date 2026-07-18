---
description: Run a two-phase audit, verify findings, and track approved fixes with simpletask.
---

User input: ${input:userInput}

**PURPOSE:** Two-phase workflow that combines an unrestricted code audit with structured triage that converts approved findings into simpletask iterations, acceptance criteria, and fix tasks.

**CRITICAL MANDATES**
1. Phase 1 is an unrestricted review - not scoped to acceptance criteria. Review architecture, performance, security, naming, patterns, error handling, and testing gaps across the diff.
2. Phase 2 requires user approval before creating any tasks. Present recommended and optional findings, then wait.
3. Do not edit or fix code. This workflow only reviews and creates tracking items.
4. Perform the initial unrestricted audit inline without relying on external subagents or dependencies.

**PHASE 1: REVIEW**
1. Load task context:
   - `simpletask_get(full=True)`
   - `git rev-parse HEAD`
   - If no task file exists, report: `No task file found for this branch. Run /simpletask.plan first.` and stop.
2. Determine diff base:
   - Read `summary.latest_audit_head_sha` and `summary.latest_audit_base_sha`.
   - If `summary.latest_audit_head_sha` is a valid ancestor of `HEAD`, use it as `DIFF_BASE`.
   - Otherwise, if `summary.latest_audit_base_sha` is a valid ancestor of `HEAD`, use it as `DIFF_BASE`.
   - Otherwise fall back to `main` or `master`.
3. Gather review inputs:
   - `git branch --show-current`
   - `git log --oneline ${DIFF_BASE}..HEAD`
   - `git diff --stat ${DIFF_BASE}..HEAD`
   - `git diff --name-only ${DIFF_BASE}..HEAD`
   - `git diff ${DIFF_BASE}..HEAD`
4. Inspect existing tasks for already-tracked audit fixes and avoid duplicates.
5. Run the unrestricted review:
   - Perform the unrestricted review inline against the full branch, prompt, commits, file list, diff base, full diff, and prior dismissed findings.
   - Use repository search and file inspection to verify every finding; do not delegate to an external subagent.
6. Parse findings into: `id`, `severity`, `category`, `file`, `description`, `suggestion`.
7. Verify each finding against the real codebase using `Read`, `Grep`, and `Glob`.
    - Verdicts: `CONFIRMED`, `FALSE-POSITIVE`, `RECLASSIFIED`, `UNCERTAIN`.
    - Drop false positives from triage output, but persist them later in audit history.
    - For `RECLASSIFIED`, track corrected severity/category.
    - Treat `UNCERTAIN` findings as optional during triage.
    - Compare each verified finding against prior `confirmed`/`reclassified` findings and existing audit-fix tasks by underlying issue, not by `F-xxx` ID.
    - Mark findings already tracked by an existing task as already tracked and do not propose a duplicate criterion/task.
    - Mark findings already present in prior confirmed audit history without a task as already known and do not create a duplicate criterion/task unless the user explicitly asks to re-track it.

**PHASE 2: TRIAGE**
1. Auto-classify findings:
   - Recommended: all `Critical`/`High`, plus concrete `Medium` security/correctness issues.
   - Optional: all `Low`, all `style`, uncertain findings, and theoretical `Medium` issues.
   - In convergence mode (`summary.audit_runs_total >= 2`), recommend only `Critical` and `High` findings.
2. Present the findings in two buckets and wait for user approval:
   - `RECOMMENDED TO FIX`
   - `OPTIONAL / COSMETIC`
3. After approval:
    - Create an iteration: `simpletask_iteration(action="add", label="audit fixes")`
    - Add new acceptance criteria only for approved security, correctness, or error-handling gaps that are truly new and not already tracked.
    - Create fix tasks only for approved findings that are truly new and not already tracked, using `simpletask_task(action="add", ...)` or `action="batch"` when creating 3+ tasks.
4. Persist approved fixes with the supported `simpletask_iteration`, `simpletask_criteria`,
   and `simpletask_task` tools. Report all reviewed findings, including false positives and
   uncertain items, in the response.
5. Validate task file schema:
   - `simpletask_get(validate=True, full=True)`

**OUTPUT**
Report:
- audit scope and diff base
- total findings and verification verdict counts
- recommended vs optional findings
- created iteration, criteria, and tasks
- audit history persistence result
- schema validation result

**TOOL REFERENCE**
MCP tools used: `simpletask_get`, `simpletask_iteration`, `simpletask_criteria`, `simpletask_task`.
The audit is performed inline using repository search and file inspection.

**WORKFLOW**
`/simpletask.plan` -> `/simpletask.split` -> `/simpletask.implement` -> `/simpletask.audit` -> `/simpletask.review`
