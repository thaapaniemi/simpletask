---
description: Execute task list to implement feature/fix using simpletask.
---

User input: $ARGUMENTS

**CRITICAL: You MUST update task status after completing each task, commit your changes, and mark acceptance criteria as complete. These are MANDATORY steps, not optional.**

**Step 1: Identify Task File**

1. Get current git branch name:
   ```bash
   git branch --show-current
   ```

2. Load and verify task file exists using MCP tools (with CLI fallback):
   
   **Preferred: Use MCP tool** (if simpletask MCP server is available)
   ```
   Use simpletask_get() MCP tool to retrieve task data:
   - Call simpletask_get(branch=None) to use current git branch
   - Returns SimpleTaskGetResponse with spec, file_path, and summary
   - If error occurs, task file does not exist
   ```
   
   **Fallback: Use CLI** (if MCP tools not available)
   ```bash
   simpletask show
   ```
   
   If task file not found:
   - Ask user: "No task file found for current branch. Run /simpletask.plan first?"
   - Do NOT proceed without a task file

**Note:** Branch names with slashes (e.g., `feature/user-auth`) are automatically normalized to filenames with hyphens (e.g., `.tasks/feature-user-auth.yml`). The MCP tools and CLI commands handle normalization automatically.

**Step 2: Analyze Current State**

1. Get task and criteria data using MCP tools (with CLI fallback):
   
   **Preferred: Use MCP tool** (if simpletask MCP server is available)
   ```
   Use simpletask_get() MCP tool to retrieve complete task data:
   - Returns SimpleTaskGetResponse with spec containing:
     - spec.tasks: list of all tasks with id, name, status, goal, steps, etc.
     - spec.acceptance_criteria: list of criteria with id, description, completed
     - summary.tasks_total, tasks_completed, tasks_not_started, tasks_in_progress, tasks_blocked
     - summary.criteria_total, criteria_completed
   
   From the response:
   - Filter spec.tasks by status to identify not_started and in_progress tasks
   - Check spec.tasks[].prerequisites to build dependency graph
   - List spec.acceptance_criteria with completed=False to see unmet criteria
   ```
   
   **Fallback: Use CLI** (if MCP tools not available)
   ```bash
   # List all tasks and their current status
   simpletask task list
   
   # List acceptance criteria status
   simpletask criteria list
   ```

2. Identify execution order based on:
   - Tasks with `status: not_started` or `status: in_progress`
   - Prerequisites (tasks that must complete first)
   - Build dependency graph and determine execution order

3. If $ARGUMENTS specifies a task ID (e.g., "T003"), start from that task

**Step 3: Execute Tasks in Order**

For EACH task in the execution order:

### 3.1 Mark Task as In Progress

**Preferred: Use MCP tool** (if simpletask MCP server is available)
```
Use simpletask_task() MCP tool to update task status:
- Call simpletask_task(action="update", task_id="[TASK_ID]", status="in_progress")
- Returns SimpleTaskGetResponse with updated task state
```

**Fallback: Use CLI** (if MCP tools not available)
```bash
simpletask task update [TASK_ID] --status in_progress
```

### 3.2 Read Task Details

**Preferred: Use MCP tool** (if simpletask MCP server is available)
```
From the simpletask_get() result obtained earlier, extract task details:
- Find task in spec.tasks where id matches current task ID
- Read task fields:
  - name: What the task is called
  - goal: What this task accomplishes
  - steps: Ordered list of implementation steps (if defined)
  - done_when: Verification conditions (if defined)
  - files: Files to create/modify/delete (if defined)
  - code_examples: Patterns to follow (if defined)
  - prerequisites: Tasks that must be complete first (if defined)
```

**Fallback: Use CLI/direct file read** (if MCP tools not available)
From the task file, extract:
- `name`: What the task is called
- `goal`: What this task accomplishes
- `steps`: Ordered list of implementation steps
- `done_when`: Verification conditions
- `files`: Files to create/modify/delete
- `code_examples`: Patterns to follow
- `prerequisites`: Tasks that must be complete first

### 3.3 Implement the Task

Follow the `steps` array exactly:
1. Execute each step in order
2. Create/modify files as specified in `files`
3. Follow patterns shown in `code_examples`
4. Respect `constraints` from the task file

### 3.4 Verify Completion

Check ALL conditions in `done_when`:
- Run any test commands specified
- Verify file existence/changes
- Confirm expected behavior

Example done_when checks:
```bash
# If done_when includes "pytest tests/test_feature.py passes"
pytest tests/test_feature.py

# If done_when includes "File exists at src/models/user.py"
ls src/models/user.py

# If done_when includes "No lint errors"
ruff check src/
```

### 3.4b Quality Gate Checkpoint (MANDATORY)

**Before marking the task complete, run all configured quality checks for this task.**

1. Get quality requirements from task file:
   
   **Preferred: Use MCP tool** (if simpletask MCP server is available)
   ```
   Use simpletask_quality() MCP tool to check requirements:
   - Call simpletask_quality(action="check")
   - Returns enabled quality requirements with commands to run
   - Example response: {linting: "ruff check .", testing: "pytest --cov=..."}
   ```
   
   **Fallback: Use CLI** (if MCP tools not available)
   ```bash
   simpletask quality check
   ```

2. Run each enabled quality check:
   ```bash
   # Example: If linting is enabled
   ruff check .
   
   # Example: If testing is enabled with coverage
   pytest --cov=cli/simpletask --cov-report=term-missing
   
   # Example: If type checking is enabled
   mypy cli/simpletask
   
   # Example: If formatting is enabled
   black --check .
   ```

3. Fix any issues found before proceeding:
   - Linting errors → Fix code style issues
   - Test failures → Fix bugs or update tests
   - Type errors → Add/fix type hints
   - Format issues → Run formatter (e.g., `black .`)

4. Re-run checks until all pass:
   ```bash
   # Re-run failed checks after fixes
   ruff check .
   pytest
   mypy cli/simpletask
   ```

**DO NOT mark the task as completed until ALL quality checks pass.** This prevents accumulating technical debt and catches issues early.

### 3.5 Mark Task as Completed

**Preferred: Use MCP tool** (if simpletask MCP server is available)
```
Use simpletask_task() MCP tool to update task status:
- Call simpletask_task(action="update", task_id="[TASK_ID]", status="completed")
- Returns SimpleTaskGetResponse with updated task state
```

**Fallback: Use CLI** (if MCP tools not available)
```bash
simpletask task update [TASK_ID] --status completed
```

**Note:** Do NOT commit changes yet. All changes will be committed in a single commit after all tasks are complete.

### 3.6 Repeat for Next Task

Continue with the next task in the execution order until all tasks are complete.

**Step 4: Update Acceptance Criteria - THIS IS MANDATORY**

After completing ALL tasks, evaluate which acceptance criteria are now satisfied.

1. Get current criteria status using MCP tools (with CLI fallback):
   
   **Preferred: Use MCP tool** (if simpletask MCP server is available)
   ```
   Use simpletask_get() MCP tool to retrieve current task data:
   - Check spec.acceptance_criteria array
   - Filter by completed=False to see unmet criteria
   - summary.criteria_completed shows count of completed criteria
   ```
   
   **Fallback: Use CLI** (if MCP tools not available)
   ```bash
   simpletask criteria list
   ```

2. For EACH criterion that is now satisfied, mark it complete:
   
   **Preferred: Use MCP tool** (if simpletask MCP server is available)
   ```
   Use simpletask_criteria() MCP tool:
   - Call simpletask_criteria(action="complete", criterion_id="[CRITERION_ID]")
   - Returns SimpleTaskGetResponse with updated criteria state
   
   Example:
   simpletask_criteria(action="complete", criterion_id="AC1")
   simpletask_criteria(action="complete", criterion_id="AC2")
   simpletask_criteria(action="complete", criterion_id="AC3")
   ```
   
   **Fallback: Use CLI** (if MCP tools not available)
   ```bash
   simpletask criteria complete AC1
   simpletask criteria complete AC2
   simpletask criteria complete AC3
   ```

3. Verify all criteria are marked complete:
   
   **Preferred: Use MCP tool** (if simpletask MCP server is available)
   ```
   Use simpletask_get() MCP tool:
   - Check summary.criteria_completed equals summary.criteria_total
   - Or filter spec.acceptance_criteria by completed=False (should be empty)
   ```
   
   **Fallback: Use CLI** (if MCP tools not available)
   ```bash
   simpletask criteria list --completed
   ```

**Note:** Do NOT commit changes yet. Criteria updates will be committed along with implementation.

**Step 5: Final Verification and Commit**

1. Validate the task file schema:
   
   **Preferred: Use MCP tool** (if simpletask MCP server is available)
   ```
   Use simpletask_get() MCP tool with validation:
   - Call simpletask_get(validate=True)
   - Check validation.valid in response
   - If validation.valid is False, check validation.errors for details
   ```
   
   **Fallback: Use CLI** (if MCP tools not available)
   ```bash
   simpletask schema validate
   ```

2. Show final task state:
   
   **Preferred: Use MCP tool** (if simpletask MCP server is available)
   ```
   Use simpletask_get() MCP tool:
   - Display summary.tasks_total, tasks_completed, tasks_in_progress, tasks_not_started
   - Display summary.criteria_total, criteria_completed
   - Show spec.branch, spec.title, spec.status
   ```
   
   **Fallback: Use CLI** (if MCP tools not available)
   ```bash
   simpletask show
   ```

3. Verify all tasks are completed:
   
   **Preferred: Use MCP tool** (if simpletask MCP server is available)
   ```
   From simpletask_get() response:
   - Check that summary.tasks_completed equals summary.tasks_total
   - Or filter spec.tasks by status != "completed" (should be empty)
   ```
   
   **Fallback: Use CLI** (if MCP tools not available)
   ```bash
   simpletask task list --status completed
   ```

4. If any tasks remain incomplete:
   
   **Preferred: Use MCP tool** (if simpletask MCP server is available)
   ```
   From simpletask_get() response:
   - Filter spec.tasks where status == "not_started" 
   - Filter spec.tasks where status == "in_progress"
   - Filter spec.tasks where status == "blocked"
   ```
   
   **Fallback: Use CLI** (if MCP tools not available)
   ```bash
   simpletask task list --status not_started
   simpletask task list --status in_progress
   simpletask task list --status blocked
   ```

4a. Run Final Quality Check (MANDATORY):
   
   **Before committing, run all configured quality checks one final time to ensure nothing was missed.**
   
   **Preferred: Use MCP tool** (if simpletask MCP server is available)
   ```
   Use simpletask_quality() MCP tool:
   - Call simpletask_quality(action="check")
   - Run each enabled quality command
   - Verify all checks pass before proceeding
   ```
   
   **Fallback: Use CLI** (if MCP tools not available)
   ```bash
   # Check which quality requirements are enabled
   simpletask quality show
   
   # Run each enabled check
   # Example: if linting, testing, type-checking are enabled
   ruff check .
   pytest --cov=cli/simpletask --cov-report=term-missing
   mypy cli/simpletask
   black --check .
   ```
   
   **If any quality check fails:**
   - Fix the issues immediately
   - Re-run the failing checks
   - Do NOT proceed to commit until ALL checks pass
   
   This final gate prevents committing code that fails quality standards.

5. Create a single commit with ALL implementation changes:
   
   First, determine what the feature accomplishes by reading the task file goal/title.
   
   ```bash
   # Stage implementation changes (exclude .tasks/ as it's gitignored)
   git add -A
   
   # Commit using conventional commit format
   # Format: feat: <description of what was implemented>
   # Example: feat: add user authentication system
   # Example: feat: implement JWT-based login flow
   # Example: fix: resolve race condition in task scheduler
   git commit -m "feat: <describe the implemented feature based on branch goal>"
   ```
   
   **Commit message guidelines:**
   - Use `feat:` for new features
   - Use `fix:` for bug fixes
   - Use `refactor:` for code restructuring
   - Use `test:` for adding tests
   - Keep description concise but meaningful
   - Focus on WHAT was implemented, not HOW

**Step 6: Report Progress**

Display summary:

```
Implementation Complete: [branch-name]

Tasks:
  Completed: X/Y
  Remaining: [list any incomplete tasks]

Acceptance Criteria:
  Met: X/Y
  Unmet: [list any unmet criteria]

Files Modified:
  - [list key files]

Commit:
  - feat: [description of implemented feature]

Next Steps:
  - Run /simpletask.review to verify implementation quality
  - Create pull request when ready
```

---

## Execution Order Guidelines

### Respecting Prerequisites

Tasks must be executed respecting their `prerequisites` field:

```yaml
tasks:
  - id: T001
    prerequisites: []      # Can start immediately
  - id: T002
    prerequisites: [T001]  # Must wait for T001
  - id: T003
    prerequisites: [T001]  # Can run parallel with T002
  - id: T004
    prerequisites: [T002, T003]  # Must wait for both
```

Execution order for above:
1. T001 (no prerequisites)
2. T002 and T003 (can run in parallel after T001)
3. T004 (after T002 and T003 complete)

### Handling Blocked Tasks

If a task cannot be completed:

**Preferred: Use MCP tool** (if simpletask MCP server is available)
```
Use simpletask_task() MCP tool:
- Call simpletask_task(action="update", task_id="[TASK_ID]", status="blocked")
```

**Fallback: Use CLI** (if MCP tools not available)
```bash
simpletask task update [TASK_ID] --status blocked
```

Document the blocker in the task file or commit message.

### Partial Implementation

If implementing only specific tasks (from $ARGUMENTS):
1. Start from the specified task
2. Ensure all prerequisites are already complete
3. Continue with dependent tasks if requested

---

## CLI Command Reference

### View Task Information

**Preferred: Use MCP tools** (if simpletask MCP server is available)
```
Use simpletask_get() MCP tool to retrieve complete task data:
- Returns SimpleTaskGetResponse with spec and summary
- spec.tasks: array of all tasks with full details
- spec.acceptance_criteria: array of all criteria
- summary: pre-computed status counts

Filter and query the response data:
- Filter spec.tasks by status field: "not_started", "in_progress", "completed", "blocked"
- Filter spec.acceptance_criteria by completed field: true/false
- Use summary fields for quick counts
```

**Fallback: Use CLI** (if MCP tools not available)
```bash
# Show full task details
simpletask show

# List all tasks
simpletask task list

# List tasks by status
simpletask task list --status not_started
simpletask task list --status in_progress
simpletask task list --status completed
simpletask task list --status blocked

# List acceptance criteria
simpletask criteria list
simpletask criteria list --completed
simpletask criteria list --incomplete
```

### Update Task Status

**Preferred: Use MCP tools** (if simpletask MCP server is available)
```
Use simpletask_task() MCP tool:

# Mark task as in progress
simpletask_task(action="update", task_id="T001", status="in_progress")

# Mark task as completed
simpletask_task(action="update", task_id="T001", status="completed")

# Mark task as blocked
simpletask_task(action="update", task_id="T001", status="blocked")

# Update task name or goal
simpletask_task(action="update", task_id="T001", name="New name")
simpletask_task(action="update", task_id="T001", goal="Updated goal")
```

**Fallback: Use CLI** (if MCP tools not available)
```bash
# Mark task as in progress
simpletask task update T001 --status in_progress

# Mark task as completed
simpletask task update T001 --status completed

# Mark task as blocked
simpletask task update T001 --status blocked

# Update task name or goal
simpletask task update T001 --name "New name"
simpletask task update T001 --goal "Updated goal"
```

### Update Acceptance Criteria

**Preferred: Use MCP tools** (if simpletask MCP server is available)
```
Use simpletask_criteria() MCP tool:

# Mark criterion as completed
simpletask_criteria(action="complete", criterion_id="AC1")

# Mark criterion as not completed (undo)
simpletask_criteria(action="complete", criterion_id="AC1", completed=False)
```

**Fallback: Use CLI** (if MCP tools not available)
```bash
# Mark criterion as completed
simpletask criteria complete AC1

# Mark criterion as not completed (undo)
simpletask criteria complete AC1 --uncomplete
```

### Validation

**Preferred: Use MCP tools** (if simpletask MCP server is available)
```
Use simpletask_get() MCP tool with validation:

# Validate task file against schema
simpletask_get(validate=True)
# Check validation.valid and validation.errors in response
```

**Fallback: Use CLI** (if MCP tools not available)
```bash
# Validate task file against schema
simpletask schema validate

# Validate specific file
simpletask schema validate .tasks/branch-name.yml
```

---

## Example Implementation Session

**Using MCP tools** (preferred):
```
# 1. Check current state
Use simpletask_get() MCP tool
→ Returns: summary shows 3 tasks (0 completed), 4 criteria (0 completed)

# 2. Start first task
Use simpletask_task(action="update", task_id="T001", status="in_progress")
→ Returns: Updated task state

# 3. [Implement T001 - create User model]

# 4. Verify done_when conditions
Run verification commands as specified in task

# 5. Mark task complete (no commit yet)
Use simpletask_task(action="update", task_id="T001", status="completed")
→ Returns: Updated task state

# 6. Continue with T002...
Use simpletask_task(action="update", task_id="T002", status="in_progress")

# [... implement remaining tasks ...]

# 7. After all tasks, mark acceptance criteria
Use simpletask_criteria(action="complete", criterion_id="AC1")
Use simpletask_criteria(action="complete", criterion_id="AC2")

# 8. Final verification
Use simpletask_get(validate=True)
→ Check: validation.valid is True
→ Check: summary shows 3 tasks (3 completed), 4 criteria (4 completed)

# 9. Create single commit with all changes
git add -A
git commit -m "feat: add user authentication system"
```

**Using CLI** (fallback):
```bash
# 1. Check current state
$ simpletask show
Branch: 001-user-auth
Status: not_started
Tasks: 3 (0 completed)
Criteria: 4 (0 completed)

# 2. Start first task
$ simpletask task update T001 --status in_progress
Updated task T001

# 3. [Implement T001 - create User model]

# 4. Verify done_when conditions
$ python -c "from src.models.user import User; print('Import OK')"
Import OK

# 5. Mark task complete (no commit yet)
$ simpletask task update T001 --status completed
Updated task T001

# 6. Continue with T002...
$ simpletask task update T002 --status in_progress

# [... implement remaining tasks ...]

# 7. After all tasks, mark acceptance criteria
$ simpletask criteria complete AC1
Marked AC1 as completed
$ simpletask criteria complete AC2
Marked AC2 as completed

# 8. Final verification
$ simpletask schema validate
Validation passed
$ simpletask show
Branch: 001-user-auth
Status: completed
Tasks: 3 (3 completed)
Criteria: 4 (4 completed)

# 9. Create single commit with all changes
$ git add -A
$ git commit -m "feat: add user authentication system"
[001-user-auth abc1234] feat: add user authentication system
 3 files changed, 150 insertions(+)
```

---

## Troubleshooting

### Task File Not Found
```
Error: No task file found for branch 'feature-x'
```
Solution: Run `/simpletask.plan` first to create the task file.

### Prerequisites Not Met
```
Error: Cannot start T003 - prerequisites [T001, T002] not complete
```
Solution: Complete prerequisite tasks first.

### Validation Errors
```
Error: Schema validation failed
```
Solution: Check task file for missing required fields or invalid values.

### Criteria Still Incomplete
After `/simpletask.review`, if you see "ACCEPTANCE CRITERIA INCOMPLETE":

**Preferred: Use MCP tool** (if simpletask MCP server is available)
```
1. Verify the implementation actually meets the criterion
2. Use simpletask_criteria(action="complete", criterion_id="[ID]")
```

**Fallback: Use CLI** (if MCP tools not available)
```
1. Verify the implementation actually meets the criterion
2. Run: simpletask criteria complete [ID]
3. Commit the updated task file
```

---

## Critical Reminders

**MANDATORY after EACH task:**
1. Update task status to completed using MCP tool `simpletask_task(action="update", task_id="[ID]", status="completed")` or CLI `simpletask task update [ID] --status completed`

**Note:** Changes are NOT committed until all tasks are complete. This allows for a clean, atomic commit.

**MANDATORY after ALL tasks:**
1. Mark each satisfied criterion complete using MCP tool `simpletask_criteria(action="complete", criterion_id="[ID]")` or CLI `simpletask criteria complete [ID]`
2. Validate using MCP tool `simpletask_get(validate=True)` or CLI `simpletask schema validate`
3. Create ONE commit with all implementation changes using conventional commit format

**Why this matters:** 
- One feature branch = one PR = one commit keeps git history clean
- `/simpletask.review` checks the task file for completion status
- If tasks remain `status: not_started` or criteria remain `completed: false`, the review will report "NOT READY" or "NEEDS CHANGES"
- Single atomic commits are easier to review, revert, and understand

**DO NOT:**
- Skip status updates during implementation
- Commit after individual tasks (wait until all tasks complete)
- Leave acceptance criteria unmarked when satisfied
- Proceed without verifying `done_when` conditions
