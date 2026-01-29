---
description: Comprehensive code review and analysis against plan and specification using simpletask.
---

User input: $ARGUMENTS

You are conducting a thorough, technically precise code review. Be brutally honest about issues, inefficiencies, and shortcomings. Your goal is to identify EVERY flaw and provide actionable, specific feedback.

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
   - Ask user: "No task file found for current branch. Which branch should I review?"
   - Do NOT proceed without a task file

**Note:** Branch names with slashes (e.g., `feature/user-auth`) are automatically normalized to filenames with hyphens (e.g., `.tasks/feature-user-auth.yml`). The MCP tools and CLI commands handle normalization automatically.

**Step 2: Analyze Task Completion**

1. Get all task data using MCP tools (with CLI fallback):
   
   **Preferred: Use MCP tool** (if simpletask MCP server is available)
   ```
   Use simpletask_get() MCP tool to retrieve complete task data:
   - Returns SimpleTaskGetResponse with:
     - spec.tasks: array of all tasks with id, name, status, goal, etc.
     - summary.tasks_total, tasks_completed, tasks_in_progress, tasks_not_started, tasks_blocked
   
   From the response:
   - Count tasks by status: filter spec.tasks by status field
   - Identify incomplete tasks: filter where status != "completed"
   - Check done_when conditions for tasks claiming completion
   ```
   
   **Fallback: Use CLI** (if MCP tools not available)
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

2. Parse task data to determine:
   - Total tasks in the task list
   - Tasks with `status: completed`
   - Tasks with `status: in_progress` (should be 0 after implementation)
   - Tasks with `status: not_started` (incomplete)
   - Tasks with `status: blocked` (need attention)
   - Tasks with `status: paused` (intentionally deferred)

3. Identify tasks that CLAIM completion but may lack quality:
   - Check if `done_when` conditions are actually satisfied
   - Verify files listed in `files` array exist/were modified
   - Look for incomplete implementations

**Step 3: Check Acceptance Criteria**

1. Get acceptance criteria data using MCP tools (with CLI fallback):
   
   **Preferred: Use MCP tool** (if simpletask MCP server is available)
   ```
   Use simpletask_get() MCP tool data from Step 1:
   - Check spec.acceptance_criteria: array of criteria with id, description, completed
   - summary.criteria_total, criteria_completed provide counts
   
   From the response:
   - Filter spec.acceptance_criteria where completed == True (marked complete)
   - Filter spec.acceptance_criteria where completed == False (remain incomplete)
   ```
   
   **Fallback: Use CLI** (if MCP tools not available)
   ```bash
   # List acceptance criteria status
   simpletask criteria list
   simpletask criteria list --completed
   simpletask criteria list --incomplete
   ```

2. For each acceptance criterion:
   - Check if `completed: true` or `completed: false`
   - **Verify** that "completed" criteria actually meet requirements (don't trust blindly)
   - Test the actual implementation against the criterion description

3. Document:
   - Which criteria are marked complete (`completed: true`)
   - Which criteria remain incomplete (`completed: false`)
   - Which "complete" criteria don't actually meet requirements (false positives)

**Step 4: Deep Code Analysis**

Examine the actual implementation changes. Review key modified files for:

### Code Quality Issues
- Anti-patterns, code smells, violation of SOLID principles
- Unclear naming, magic numbers, commented-out code
- Poor abstraction, tight coupling, low cohesion
- Missing or inadequate comments for complex logic
- Inconsistent code style

### Architecture & Design
- Questionable design decisions
- Violations of separation of concerns
- Unnecessary complexity or over-engineering
- Missing abstractions or improper layering
- Deviation from existing patterns in the codebase

### Performance
- Inefficient algorithms or data structures (O(n²) when O(n) possible)
- Unnecessary database queries (N+1 problems)
- Missing caching opportunities
- Excessive memory usage or resource waste
- Unnecessary loops or redundant operations

### Security
- Authentication/authorization gaps
- Input validation failures
- Potential injection vulnerabilities (SQL, XSS, command injection)
- Exposed credentials, API keys, or secrets
- Missing HTTPS, encryption, or security headers
- Insecure dependencies

### Error Handling
- Missing error handling
- Edge cases not covered
- Lack of input validation or sanitization
- Poor error messages
- Missing resource cleanup (memory leaks, unclosed connections)

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
   - Key modified files (up to 10)
   - Commit message quality (descriptive or lazy?)
   - Are changes focused or scattered across unrelated areas?

**Step 6: Generate Specific, Actionable Feedback**

Be BRUTALLY HONEST and SPECIFIC. Don't sugarcoat. For each issue found:

**Format for each issue:**
```
[SEVERITY: Critical/High/Medium/Low]
File: path/to/file.py:123
Issue: [Clear description of the problem]
Why it matters: [Technical explanation]
Fix: [Specific, actionable remediation]
```

**Categories to cover:**

1. **CODE QUALITY ISSUES**
   - Every anti-pattern with file path and line reference
   - Code smells with specific examples
   - SOLID principle violations

2. **ARCHITECTURAL CONCERNS**
   - Design problems with technical explanations
   - Separation of concerns violations
   - Missing or improper abstractions

3. **PERFORMANCE PROBLEMS**
   - Inefficiencies with specific examples
   - Algorithm complexity issues
   - Resource waste

4. **SECURITY VULNERABILITIES**
   - Security issues with severity rating
   - Clear remediation steps
   - References to security best practices

5. **TESTING GAPS**
   - Missing test coverage for critical paths
   - Untested edge cases or error conditions
   - Missing integration or E2E tests
   - Brittle or poorly designed tests

6. **DOCUMENTATION ISSUES**
   - Missing or inadequate inline documentation
   - Undocumented API changes
   - Missing README updates

**Step 7: Determine PR Readiness**

Evaluate and report one of:

### READY TO MERGE
- All tasks have `status: completed`
- All acceptance criteria have `completed: true`
- No critical or high severity issues found
- Code quality is solid
- Tests pass and coverage is adequate

### NEEDS CHANGES
- All tasks complete, all criteria met
- BUT has code quality/security/performance issues
- Issues are fixable without major rework

### NOT READY
- Tasks remain with `status: not_started` or `status: in_progress`
- Acceptance criteria remain with `completed: false`
- Critical flaws found that require significant rework
- Missing core functionality

**Step 8: Display Comprehensive Review Summary**

```
╭─────────────────────────────────────────────────────────────╮
│ Code Review: [branch-name]                                  │
╰─────────────────────────────────────────────────────────────╯

TASK COMPLETION
  Tasks: X/Y completed (Z%)
  - Completed: [count]
  - In Progress: [count]
  - Not Started: [count]
  - Blocked: [count]
  
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
  
  Key files:
    - path/to/file1.py
    - path/to/file2.py
    - ...

ISSUES FOUND

  [Critical] CODE QUALITY (X issues)
    - file.py:123 - [issue description]
    - file.py:456 - [issue description]

  [High] SECURITY (X issues)
    - file.py:789 - [issue description]

  [Medium] PERFORMANCE (X issues)
    - file.py:101 - [issue description]

  [Low] DOCUMENTATION (X issues)
    - file.py:112 - [issue description]

IMPROVEMENT SUGGESTIONS
  1. [Specific, actionable suggestion with rationale]
  2. [Another specific suggestion]
  ...

───────────────────────────────────────────────────────────────
PR READINESS: [READY TO MERGE | NEEDS CHANGES | NOT READY]

[Honest assessment with justification]
───────────────────────────────────────────────────────────────
```

**Step 9: Auto-Inject Fix Tasks (if issues found)**

If issues are found, automatically add fix tasks to the task file:

1. For each issue found, create a fix task using MCP tools (with CLI fallback):
   
   **Preferred: Use MCP tool** (if simpletask MCP server is available)
   ```
   Use simpletask_task() MCP tool to add fix tasks:
   - Call simpletask_task(
       action="add",
       name="Fix: [issue summary]",
       goal="[detailed goal with file path and remediation]"
     )
   - Returns SimpleTaskGetResponse with updated task list
   - Repeat for each fix needed
   ```
   
   **Fallback: Use CLI** (if MCP tools not available)
   ```bash
   simpletask task add "Fix: [issue summary]" -g "[detailed goal with file path and remediation]"
   ```

2. Group related issues into single tasks when appropriate:
   - Multiple issues in same file → one task
   - Related security issues → one task
   - Similar code quality issues → one task

3. Example fix tasks:
   
   **Using MCP tools:**
   ```
   simpletask_task(
     action="add",
     name="Fix: Security vulnerability in auth.py",
     goal="Add input validation to prevent SQL injection in login function at line 45"
   )
   
   simpletask_task(
     action="add",
     name="Fix: Performance issue in data_processor.py",
     goal="Replace O(n²) algorithm with O(n) approach in process_items function"
   )
   ```
   
   **Using CLI:**
   ```bash
   simpletask task add "Fix: Security vulnerability in auth.py" -g "Add input validation to prevent SQL injection in login function at line 45"
   
   simpletask task add "Fix: Performance issue in data_processor.py" -g "Replace O(n²) algorithm with O(n) approach in process_items function"
   
   simpletask task add "Fix: Missing error handling in api.py" -g "Add try/catch blocks and proper error responses to API endpoints"
   ```

4. After adding fix tasks, show summary:
   ```
   Fix tasks added to .tasks/[branch-name].yml:
     - T00X: Fix: Security vulnerability in auth.py
     - T00Y: Fix: Performance issue in data_processor.py
     - T00Z: Fix: Missing error handling in api.py
   
   Run /simpletask.implement to execute fix tasks.
   ```

5. Validate the updated task file:
   
   **Preferred: Use MCP tool** (if simpletask MCP server is available)
   ```
   Use simpletask_get() MCP tool with validation:
   - Call simpletask_get(validate=True)
   - Check validation.valid in response
   ```
   
   **Fallback: Use CLI** (if MCP tools not available)
   ```bash
   simpletask schema validate
   ```

---

## Review Workflow

The review command creates a natural feedback loop:

```
/simpletask.plan     → Creates task file with tasks and criteria
        ↓
/simpletask.implement → Executes tasks, updates status
        ↓
/simpletask.review   → Reviews implementation, adds fix tasks if needed
        ↓
    Issues found?
        ↓
    Yes → /simpletask.implement (execute fix tasks)
        ↓
        → /simpletask.review (verify fixes)
        ↓
    No → Ready for PR
```

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
- Filter spec.tasks by status field: "not_started", "in_progress", "completed", "blocked", "paused"
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
simpletask task list --status completed
simpletask task list --status not_started

# List acceptance criteria
simpletask criteria list
simpletask criteria list --completed
simpletask criteria list --incomplete
```

### Add Fix Tasks

**Preferred: Use MCP tools** (if simpletask MCP server is available)
```
Use simpletask_task() MCP tool:

# Add a fix task
simpletask_task(
  action="add",
  name="Fix: [description]",
  goal="[goal]"
)

# Add task with specific branch
simpletask_task(
  action="add",
  branch="[branch-name]",
  name="Fix: [description]",
  goal="[goal]"
)
```

**Fallback: Use CLI** (if MCP tools not available)
```bash
# Add a fix task
simpletask task add "Fix: [description]" -g "[goal]"

# Add task with specific branch
simpletask task add "Fix: [description]" -g "[goal]" -b [branch-name]
```

### Validation

**Preferred: Use MCP tools** (if simpletask MCP server is available)
```
Use simpletask_get() MCP tool with validation:

# Validate task file
simpletask_get(validate=True)
# Check validation.valid and validation.errors in response
```

**Fallback: Use CLI** (if MCP tools not available)
```bash
# Validate task file
simpletask schema validate
```

---

## Important Guidelines

### Be SPECIFIC
- Include file paths, function names, line numbers
- Quote actual code when pointing out issues
- Reference specific acceptance criteria or tasks

### Be HONEST
- Don't hide problems to be nice
- Call out every issue, no matter how small
- If implementation is poor, say so clearly

### Be TECHNICAL
- Explain WHY something is a problem
- Reference best practices, patterns, principles
- Provide technical justification for concerns

### Be ACTIONABLE
- Every issue must have a clear fix
- Fix tasks should be specific and implementable
- Include enough detail for any developer to act on

---

## Quality Gates

Before marking as "READY TO MERGE":

1. **All tasks completed**: 
   - MCP: Check `summary.tasks_completed == summary.tasks_total` in `simpletask_get()` response
   - CLI: `simpletask task list --status completed` shows all tasks
2. **All criteria met**: 
   - MCP: Check `summary.criteria_completed == summary.criteria_total` in `simpletask_get()` response
   - CLI: `simpletask criteria list --incomplete` returns empty
3. **No critical issues**: No security vulnerabilities, no major bugs
4. **Tests pass**: All automated tests pass
5. **Schema valid**: 
   - MCP: `simpletask_get(validate=True)` returns `validation.valid == True`
   - CLI: `simpletask schema validate` passes

If ANY of these fail, the review should report "NEEDS CHANGES" or "NOT READY".
