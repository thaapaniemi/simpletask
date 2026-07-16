---
description: Run the current simpletask audit workflow in Pi using CLI commands.
argument-hint: ""
---

User input: $ARGUMENTS

Use this prompt for auditing only. Do not fix code. Review the current branch, triage findings with the user, and create tracking items only after approval.

Mandates:
- Phase 1 is unrestricted review - not scoped to acceptance criteria.
- Phase 2 requires user approval before creating any iteration, criteria, or tasks.
- If a `gilfoyle` review agent or equivalent delegation mechanism is available in the environment, you may use it for the initial roast. Otherwise perform the audit inline and continue without asking.

Response contract:
- Do not start with an acknowledgement-only message.
- Start immediately with `git branch --show-current`.
- If the environment is read-only, inspect only and stop after presenting findings. Do not attempt task creation.

1. Identify the current branch:
   - `git branch --show-current`
2. Load current task and audit state:
   - `simpletask show --format json`
   - If no task file exists, report: `No task file found for this branch. Run /simpletask.plan first.` and stop.
3. Capture `HEAD` and determine the diff base:
    - `git rev-parse HEAD`
    - Read `audit_history` from `simpletask show --format json`
    - If `audit_history` is non-empty, use the `head_sha` from the run with the highest `iteration` as the candidate diff base
    - If that SHA is a valid ancestor of `HEAD`, use it as `DIFF_BASE`
    - Otherwise use that run's `base_sha` if it is a valid ancestor of `HEAD`
    - Otherwise use `main` or `master`
4. Gather audit inputs:
   - `git log --oneline ${DIFF_BASE}..HEAD`
   - `git diff --stat ${DIFF_BASE}..HEAD`
   - `git diff --name-only ${DIFF_BASE}..HEAD`
   - `git diff ${DIFF_BASE}..HEAD`
5. If prior audits exist, load dismissed findings:
    - `simpletask audit dismissed`
    - Inspect prior `confirmed` and `reclassified` findings in `audit_history`
    - Inspect existing tasks for already-tracked audit fixes, especially findings with `task_id` already linked
6. Run the unrestricted audit:
   - If the environment supports a `gilfoyle`-style review agent, you may delegate the initial diff review.
   - Otherwise review the diff inline yourself.
7. Parse findings into severity, category, file, summary, and suggestion.
8. Verify each finding against the actual source before triage:
    - Read the referenced file locations
    - Grep for validators, callers, and error handlers as needed
    - Record verdicts as `confirmed`, `false_positive`, `reclassified`, or `uncertain`
    - Compare each verified finding against prior `confirmed`/`reclassified` findings and existing audit-fix tasks by underlying issue, not by `F-xxx` ID
    - Mark findings already tracked by an existing task as already tracked and do not propose a duplicate criterion/task
    - Mark findings already present in prior confirmed audit history without a task as already known and do not create a duplicate criterion/task unless the user explicitly asks to re-track it
9. Present the findings in two buckets and wait for user approval:
   - `RECOMMENDED TO FIX`
   - `OPTIONAL / COSMETIC`
10. Only after user approval, create tracking items:
    - `simpletask iteration add "audit fixes"`
    - `simpletask criteria add "..." --format json` only for approved security, correctness, or error-handling gaps that are truly new and not already tracked
    - `simpletask task add "Fix: ..." -g "..." --format json` only for approved findings that are truly new and not already tracked
11. Persist the audit run:
    - `simpletask audit add-run --iteration N --base-sha <diff-base-sha> --head-sha <head-sha> --findings <json-file>`
    - Include all reviewed findings, including false positives and uncertain items
12. Validate the task file:
   - `simpletask schema validate --format json`
13. Report audit scope, findings, approved tasks, persistence result, and validation result.

Rules:
- Use `simpletask` CLI commands for task management and audit persistence.
- Always pass `--format json` to simpletask CLI commands that support it.
- When deriving `DIFF_BASE`, use the actual `audit_history` array from `simpletask show --format json` rather than MCP-only summary fields.
- Do not create any task-tracking items before the user approves the triage output.
- Do not fix code or create commits in this workflow.
