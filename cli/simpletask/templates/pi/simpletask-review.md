---
description: Scope-bounded code review against acceptance criteria using simpletask CLI.
argument-hint: ""
---

User input: $ARGUMENTS

**IMPORTANT: Scope constraint**

This review is strictly scoped to the original prompt and acceptance criteria defined in the task
file. Verify that the implementation satisfies those requirements — nothing more. Do NOT suggest
features, refactoring, or improvements beyond what was explicitly requested. Do NOT flag issues in
code outside the git diff.

Response contract:
- Do not reply with an acknowledgement-only message.
- Start immediately with loading the task file.
- Do not use MCP tools. Use only `simpletask` CLI commands and standard shell commands.

---

## Step 1: Identify Task File

```bash
git branch --show-current
simpletask show --format json
```

If the task file does not exist, abort and inform the user.

---

## Step 2: Analyze Task Completion

```bash
simpletask task list --flat --format json
simpletask task list --status completed --format json
simpletask task list --status not_started --format json
simpletask task list --status in_progress --format json
simpletask task list --status blocked --format json
simpletask task list --status paused --format json
```

---

## Step 3: Check Acceptance Criteria

```bash
simpletask criteria list --format json
simpletask criteria list --completed --format json
simpletask criteria list --incomplete --format json
```

---

## Step 4: Verify Implementation Against Criteria and Diff

Scope: only the files in `git diff --name-only main..HEAD` (or `master..HEAD`).

Also read implementation notes for context:

```bash
simpletask note list --format json
```

For each acceptance criterion, check whether the diff actually satisfies it. Look for:

### Criteria Satisfaction
- Does the diff contain code that implements each criterion?
- Are criteria marked complete with no corresponding changes in the diff?
- Are criteria still marked incomplete that are actually implemented?

### Security (within diff scope only)
- Exposed credentials or secrets introduced by the diff
- Input validation gaps relevant to the feature
- Injection vulnerabilities (SQL, XSS, command injection) in new code only

### Correctness
- Logic errors in changed code that prevent acceptance criteria from being met
- Missing edge cases for paths described in the acceptance criteria
- Error handling gaps in new code that cause user-visible failures

**Do NOT flag:** code style, naming conventions, performance of unchanged code, documentation
outside feature scope, or architectural patterns in unmodified files.

---

## Step 5: Analyze Git Changes

```bash
git log --oneline main..HEAD 2>/dev/null || git log --oneline master..HEAD
git diff --stat main..HEAD 2>/dev/null || git diff --stat master..HEAD
git diff --name-only main..HEAD 2>/dev/null || git diff --name-only master..HEAD
```

- Count commits on feature branch
- Note files modified, lines added/removed
- Flag any modified files unrelated to the original prompt (scope creep signal)

---

## Step 6: Cross-Cutting Design Notes

Scope: only the git diff. Design notes are **informational only** — they do NOT block merge and do
NOT create fix tasks.

Ask these 4 questions against the diff:

| # | Question | What to look for |
|---|----------|-----------------|
| 1 | **Data flow across files** | Does data mutate as it crosses file boundaries in ways that could silently lose information? |
| 2 | **Robustness under unexpected inputs** | Are there input shapes or missing keys that could cause silent failures in new code? |
| 3 | **Error semantics** | Do error paths in the diff propagate enough context for callers to act correctly? |
| 4 | **Test fidelity** | Do new/changed tests actually exercise the behavior in the acceptance criteria? |

Produce **zero to 5 design notes**. Zero is correct if no observation is well-supported by the
diff. Each note **must**:
- Be prefixed with `[DATA_FLOW]`, `[ROBUSTNESS]`, `[ERROR_SEM]`, or `[TEST_FIDELITY]`
- Reference a specific `file:line` from the diff
- Be 1-2 sentences — informational only, no fix required

**Before persisting notes, clear prior auto-generated notes to avoid duplicates:**

```bash
simpletask note remove --all --format json
```

Then persist each design note:

```bash
simpletask note add "[CATEGORY] file:line — observation" --format json
# Repeat for each note (max 5)
```

If 3 or more notes share the same category, append to the summary:
`CRITERIA GAP DETECTED: [N]/[total] design notes concern [CATEGORY].`

---

## Step 7: Generate Scoped, Actionable Feedback

Only report issues that:
- Prevent an acceptance criterion from being met, OR
- Are Critical/High severity security or correctness issues in the changed code

```
[SEVERITY: Critical/High]
File: path/to/file.py:123
Criterion: [ACx — criterion description, or "regression risk"]
Issue: [Clear description of the problem]
Why it matters: [How this breaks the stated requirement]
Fix: [Specific, actionable remediation]
```

Categories: **UNMET CRITERIA**, **SECURITY**, **CORRECTNESS**, **SCOPE CREEP** (informational)

Medium/Low observations are noted in the summary but do NOT trigger fix tasks.

---

## Step 8: Determine PR Readiness

### READY TO MERGE
- All tasks have `status: completed`
- All acceptance criteria have `completed: true`
- No Critical or High severity blocking issues
- Changes are scoped to the original prompt

### NEEDS CHANGES
- All tasks complete and all criteria done
- BUT has Critical/High severity issues fixable without major rework

### NOT READY
- Tasks remain `not_started` or `in_progress`
- Acceptance criteria remain with `completed: false`
- Critical flaws prevent the feature from working as specified

---

## Step 9: Display Review Summary

```
╭─────────────────────────────────────────────────────────────╮
│ Code Review: [branch-name]                                  │
╰─────────────────────────────────────────────────────────────╯

ORIGINAL PROMPT
  [original_prompt from task file — one line summary]

TASK COMPLETION
  Tasks: X/Y completed (Z%)
  - Completed: [count]
  - In Progress: [count]
  - Not Started: [count]
  - Blocked: [count]
  - Paused: [count]

ACCEPTANCE CRITERIA
  Criteria: X/Y met (Z%)
  Unmet: AC1: [description], AC2: [description]

GIT CHANGES
  Branch: [branch-name]
  Commits: N commits ahead of main
  Changes: M files modified, +A/-R lines
  Scope: [FOCUSED | CONTAINS OUT-OF-SCOPE CHANGES]

BLOCKING ISSUES (require fix tasks)
  [Critical/High] UNMET CRITERIA (X issues)
    - ACX: file.py:123 — [issue description]
  [Critical/High] SECURITY / CORRECTNESS (X issues)
    - file.py:789 — [issue description]

DESIGN NOTES (informational — no tasks created)
  - [DATA_FLOW] file.py:42 — [note]
  - [ROBUSTNESS] other.py:17 — [note]

OBSERVATIONS (minor — informational, no tasks created)
  - [Low/Medium severity notes about the diff, if any]

───────────────────────────────────────────────────────────────
PR READINESS: [READY TO MERGE | NEEDS CHANGES | NOT READY]

[Assessment with justification referencing specific criteria]
───────────────────────────────────────────────────────────────
```

---

## Step 10: Auto-Inject Fix Tasks (blocking issues only)

Only create fix tasks for **Critical or High severity** issues that prevent acceptance criteria from
being met or introduce security/correctness regressions. Do NOT create tasks for Medium/Low issues.

If blocking issues exist:

```bash
# Create a review-fixes iteration
simpletask iteration add "review fixes" --format json

# Add fix tasks (use the iteration ID returned above)
simpletask task add "Fix: [issue summary]" \
  --goal "[detailed goal with file path and remediation]" \
  --iteration [iter_id] \
  --format json
# Repeat for each blocking issue
```

After adding fix tasks:

```bash
simpletask schema validate --format json
```

If no blocking issues: report "No fix tasks needed." Do NOT create an iteration or any tasks.

---

## Review Workflow

```
/simpletask-plan      → Creates task file with tasks and criteria
        ↓
/simpletask-implement → Executes tasks, updates status
        ↓
/simpletask-review    → Verifies implementation against criteria
        ↓
    Blocking issues? → /simpletask-implement (fix tasks only) → /simpletask-review
        ↓
    No → Ready for PR
```

---

## Rules

- Do not use MCP tools. Use `simpletask` CLI commands and shell commands only.
- Always pass `--format json` to every simpletask CLI command.
- Only review files in the git diff — do not audit the whole codebase.
- Only flag issues that violate acceptance criteria or introduce blocking regressions.
- Be specific: include file paths, function names, and line numbers.
- Every fix task must have a clear, implementable goal referencing the exact criterion.
