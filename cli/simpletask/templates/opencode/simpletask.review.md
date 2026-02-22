---
description: Scope-bounded code review: verifies implementation against original prompt and acceptance criteria only.
---

User input: $ARGUMENTS

**IMPORTANT: Scope constraint**

This review is strictly scoped to the original prompt and acceptance criteria defined in the task file. Your job is to verify that the implementation satisfies those requirements — nothing more. Do NOT suggest features, refactoring, or improvements beyond what was explicitly requested. Do NOT flag issues in code outside the git diff. Do NOT expand the PR.

**Step 1: Identify Task File**

1. Get current git branch name:
   ```bash
   git branch --show-current
   ```

2. Load task file using MCP tools:
   
   ```
   Use simpletask_get() MCP tool to retrieve task data:
   - Call simpletask_get() to use current git branch (auto-detected)
   - Returns SimpleTaskGetResponse with spec, file_path, and summary
   - If error occurs, task file does not exist — abort and inform the user
   ```
   
   simpletask show

**Step 2: Analyze Task Completion**

1. Get all task data using MCP tools:
   
   ```
   Use simpletask_get() MCP tool to retrieve complete task data:
   - Returns SimpleTaskGetResponse with:
     - spec.tasks: array of all tasks with id, name, status, goal, steps, etc.
     - summary.tasks_total, tasks_completed, tasks_in_progress, tasks_not_started, tasks_blocked
   
   From the response:
   - Filter spec.tasks where status == "completed"
   - Filter spec.tasks where status == "in_progress" (should be 0 after implementation)
   - Filter spec.tasks where status == "not_started" (incomplete)
   - Filter spec.tasks where status == "blocked" (need attention)
   - Filter spec.tasks where status == "paused" (intentionally deferred)
   ```
   
   ```bash
   # List all tasks and their statuses
   simpletask task list
   
   # Count tasks by status
   simpletask task list --status completed
   simpletask task list --status in_progress
   simpletask task list --status not_started
   simpletask task list --status blocked
   simpletask task list --status paused
   ```

**Step 3: Check Acceptance Criteria**

1. Get acceptance criteria data using MCP tools:
   
   ```
   Use simpletask_get() MCP tool data from Step 1:
   - Check spec.acceptance_criteria: array of criteria with id, description, completed
   - summary.criteria_total, criteria_completed provide counts
   
   From the response:
   - Filter spec.acceptance_criteria where completed == True (marked complete)
   - Filter spec.acceptance_criteria where completed == False (remain incomplete)
   ```
   
   # List acceptance criteria status
   simpletask criteria list
   simpletask criteria list --completed
   simpletask criteria list --incomplete

**Step 4: Verify Implementation Against Criteria and Diff**

Scope: only the files in `git diff --name-only main..HEAD` (or master..HEAD). Do not review anything outside the diff.

For each acceptance criterion, check whether the diff actually satisfies it. Also read any implementation notes for context on decisions made.

```
Use simpletask_note() MCP tool to list notes:
- Call simpletask_note(action="list")
- Returns root_notes (feature-wide decisions) and task_notes (task-specific context)
- Use notes to understand non-obvious implementation decisions before raising issues
```

simpletask note list

Look for:

### Criteria Satisfaction
- For each criterion: does the diff contain code that implements it?
- Are there acceptance criteria that are marked complete but have no corresponding changes in the diff?
- Are there criteria still marked incomplete that are actually implemented?

### Security (within diff scope only)
- Exposed credentials, API keys, or secrets introduced by the diff
- Input validation gaps that are directly relevant to the feature being implemented
- Injection vulnerabilities (SQL, XSS, command injection) in new code only

### Correctness
- Logic errors in the changed code that would prevent acceptance criteria from being met
- Missing edge cases for paths described in the acceptance criteria
- Error handling gaps in new code that would cause failures visible to users

**Do NOT flag:** code style, naming conventions, missing abstractions, performance of unchanged code, documentation outside the feature scope, test coverage for untouched code paths, or architectural patterns in unmodified files.

**Step 5: Analyze Git Changes**

1. Get branch comparison:
   ```bash
   git log --oneline main..HEAD
   # or
   git log --oneline master..HEAD
   ```

2. Get diff statistics:
   ```bash
   git diff --stat main..HEAD
   # or
   git diff --stat master..HEAD
   ```

3. List modified files:
   ```bash
   git diff --name-only main..HEAD | head -20
   ```

4. Analyze:
   - Number of commits on feature branch
   - Files modified, lines added/removed
   - Are changes focused on the feature or scattered across unrelated areas? (Scope creep signal)
   - Do any modified files look unrelated to the original prompt? Flag these.

**Step 6: Generate Scoped, Actionable Feedback**

Only report issues that:
- Prevent an acceptance criterion from being met, OR
- Are Critical/High severity security or correctness issues in the changed code

**Format for each issue:**
```
[SEVERITY: Critical/High]
File: path/to/file.py:123
Criterion: [ACx - criterion description this relates to, or "regression risk"]
Issue: [Clear description of the problem]
Why it matters: [How this breaks or undermines the stated requirement]
Fix: [Specific, actionable remediation]
```

**Categories:**

1. **UNMET CRITERIA** — Acceptance criteria not satisfied by the implementation
2. **SECURITY** — Critical/High severity issues in new/changed code only
3. **CORRECTNESS** — Logic errors preventing the feature from working as specified
4. **SCOPE CREEP** — Changes that go beyond the original prompt (informational — do NOT create tasks)

Medium/Low severity observations (style, naming, minor inefficiencies) are noted in the summary but do NOT trigger fix tasks.

**Step 7: Determine PR Readiness**

Evaluate and report one of:

### READY TO MERGE
- All tasks have `status: completed`
- All acceptance criteria have `completed: true`
- No Critical or High severity blocking issues found
- Changes are scoped to the original prompt

### NEEDS CHANGES
- All tasks complete, all criteria marked done
- BUT has Critical/High severity security or correctness issues in the diff
- Issues are fixable without major rework

### NOT READY
- Tasks remain with `status: not_started` or `status: in_progress`
- Acceptance criteria remain with `completed: false`
- Critical flaws prevent the feature from working as specified

**Step 8: Display Review Summary**

```
╭─────────────────────────────────────────────────────────────╮
│ Code Review: [branch-name]                                  │
╰─────────────────────────────────────────────────────────────╯

ORIGINAL PROMPT
  [spec.prompt from task file — one line summary]

TASK COMPLETION
  Tasks: X/Y completed (Z%)
  - Completed: [count]
  - In Progress: [count]
  - Not Started: [count]
  - Blocked: [count]
  - Paused: [count]
  
  Incomplete tasks:
    - T00X: [task name]
    - T00Y: [task name]

ACCEPTANCE CRITERIA
  Criteria: X/Y met (Z%)
  
  Unmet criteria:
    - AC1: [description]
    - AC2: [description]

GIT CHANGES
  Branch: [branch-name]
  Commits: N commits ahead of main
  Changes: M files modified, +A/-R lines
  
  Key files changed:
    - path/to/file1.py
    - path/to/file2.py
    - ...
  
  Scope: [FOCUSED | CONTAINS OUT-OF-SCOPE CHANGES]

BLOCKING ISSUES (require fix tasks)

  [Critical/High] UNMET CRITERIA (X issues)
    - AC1: file.py:123 - [issue description]

  [Critical/High] SECURITY (X issues)
    - file.py:789 - [issue description]

  [Critical/High] CORRECTNESS (X issues)
    - file.py:101 - [issue description]

OBSERVATIONS (informational only — no tasks created)
  - [Low/Medium severity notes about the diff, if any]

───────────────────────────────────────────────────────────────
PR READINESS: [READY TO MERGE | NEEDS CHANGES | NOT READY]

[Assessment with justification referencing specific criteria]
───────────────────────────────────────────────────────────────
```

**Step 9: Auto-Inject Fix Tasks (blocking issues only)**

Only auto-inject fix tasks if there are **Critical or High severity** issues that prevent acceptance criteria from being met or introduce regressions/security vulnerabilities in the diff. Do NOT create tasks for Medium/Low/Observations.

If blocking issues exist:

1. Create a new iteration to group fix tasks:
   
   ```
   Use simpletask_iteration() MCP tool:
   - Call simpletask_iteration(action="add", label="review fixes")
   - Returns new iteration ID to use when adding fix tasks
   ```
   
   ```bash
   simpletask iteration add "review fixes"
   ```

2. For each **blocking** issue only, create a fix task:
   
   ```
   Use simpletask_task() MCP tool to add fix tasks:
   - Call simpletask_task(
       action="add",
       name="Fix: [issue summary]",
       goal="[detailed goal with file path and remediation]",
       iteration=<iter_id>
     )
   ```
   
   simpletask task add "Fix: [issue summary]" -g "[detailed goal with file path and remediation]" -i <iter_id>

3. After adding fix tasks, show summary:
   ```
   Fix tasks added to .tasks/[branch-name].yml:
     - T00X: Fix: [blocking issue 1]
     - T00Y: Fix: [blocking issue 2]
   
   Observations (not tracked as tasks):
     - [Medium/Low items listed here for awareness]
   
   Run /simpletask.implement to execute fix tasks.
   ```

4. Validate the updated task file:
   
   ```
   Use simpletask_get() MCP tool with validation:
   - Call simpletask_get(validate=True)
   - Check validation.valid in response
   ```
   
   simpletask schema validate

If no blocking issues exist: report "No fix tasks needed." Do NOT create an iteration or any tasks.

---

## Review Workflow

```
/simpletask.plan      → Creates task file with tasks and criteria
        ↓
/simpletask.implement → Executes tasks, updates status
        ↓
/simpletask.review    → Verifies implementation against original criteria
        ↓
    Blocking issues?
        ↓
    Yes (Critical/High) → /simpletask.implement (fix tasks only)
        ↓
        → /simpletask.review (verify fixes)
        ↓
    No → Ready for PR
```

---

## CLI Command Reference

### View Task Information

```
Use simpletask_get() MCP tool to retrieve complete task data:
- Returns SimpleTaskGetResponse with spec and summary
- spec.tasks: array of all tasks with full details
- spec.acceptance_criteria: array of all criteria
- summary: pre-computed status counts

Filter and query the response data:
- Filter spec.tasks by status field: "not_started", "in_progress", "completed", "blocked", "paused"
- Filter spec.acceptance_criteria by completed field: true/false
- Use summary fields for quick counts
```

# Show full task details
simpletask show

# List all tasks
simpletask task list

# List tasks by status
simpletask task list --status completed
simpletask task list --status not_started
simpletask task list --status in_progress
simpletask task list --status blocked
simpletask task list --status paused

# List acceptance criteria
simpletask criteria list
simpletask criteria list --completed
simpletask criteria list --incomplete
### Add Fix Tasks (blocking issues only)

```
Use simpletask_task() MCP tool:

# Add a fix task (only for Critical/High blocking issues)
simpletask_task(
  action="add",
  name="Fix: [description]",
  goal="[goal]",
  iteration=<iter_id>
)
```

# Add a fix task
simpletask task add "Fix: [description]" -g "[goal]" -i <iter_id>
### Validation

```
Use simpletask_get() MCP tool with validation:

# Validate task file
simpletask_get(validate=True)
# Check validation.valid and validation.errors in response
```

# Validate task file
simpletask schema validate

---

## Important Guidelines

### Stay Scoped
- Only review files in the git diff
- Only flag issues that violate stated acceptance criteria or introduce blocking regressions
- Do NOT audit the whole codebase — that is not what this command is for
- If you notice improvements outside scope, do NOT create tasks for them

### Be SPECIFIC
- Include file paths, function names, line numbers
- Quote actual code when pointing out issues
- Reference specific acceptance criteria by ID

### Be HONEST
- Don't hide genuine blocking problems
- Distinguish clearly between blocking issues (require fix) and observations (informational)
- If the implementation is out of scope (added extra things not requested), say so

### Be ACTIONABLE
- Every fix task must have a clear, implementable goal
- Reference the exact criterion it relates to

---

## Quality Gates

<!-- NOTE: OpenCode intentionally provides both MCP and CLI references here for 
     comprehensive guidance, while Qwen/Gemini templates focus on CLI-only workflow.
     This asymmetry is by design and should not be "harmonized" away. -->

Before marking as "READY TO MERGE":

1. **All tasks completed**: 
   - MCP: Check `summary.tasks_completed == summary.tasks_total` in `simpletask_get()` response
   - CLI: `simpletask task list --status completed` shows all tasks
2. **All criteria met**: 
   - MCP: Check `summary.criteria_completed == summary.criteria_total` in `simpletask_get()` response
   - CLI: `simpletask criteria list --incomplete` returns empty
3. **No blocking issues**: No Critical/High security vulnerabilities or correctness failures in the diff
4. **Tests pass**: All automated tests pass
5. **Schema valid**: 
   - MCP: `simpletask_get(validate=True)` returns `validation.valid == True`
   - CLI: `simpletask schema validate` passes

If ANY of these fail, the review should report "NEEDS CHANGES" or "NOT READY".
