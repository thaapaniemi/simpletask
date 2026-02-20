---
description: Create specification and implementation plan from feature description using simpletask.
---

User input: $ARGUMENTS

**CRITICAL: This is a PLANNING phase. DO NOT implement code or execute tasks. Your job is to create/update the task file with acceptance criteria and task breakdown - then STOP.**

**Step 0: Determine Branch Name**

1. **Analyze the user prompt to determine branch type prefix:**
   
   | If prompt contains... | Suggest prefix |
   |----------------------|----------------|
   | "fix", "bug", "error", "issue", "broken", "crash" | `fix/` |
   | "refactor", "cleanup", "improve", "optimize" | `refactor/` |
   | "test", "spec", "coverage" | `test/` |
   | "doc", "readme", "documentation" | `docs/` |
   | "chore", "config", "update deps", "upgrade", "bump" | `chore/` |
   | Default (new functionality) | `feature/` |

2. **Generate slug from description:**
   - Convert to lowercase
   - Remove stop words (the, a, an, for, to, of, in, on, at, by, with, from, as, is, are, was, were, be, have, has)
   - Filter words shorter than 3 characters
   - Take first 3-4 meaningful words, join with hyphens
   - Examples:
     - "Add user authentication" → `user-authentication`
     - "Fix login page crash" → `login-page-crash`
     - "Refactor database queries" → `database-queries`

3. **Construct suggested branch name:**
   - Format: `[prefix]/[slug]`
   - Examples:
     - `feature/user-authentication`
     - `fix/login-page-crash`
     - `refactor/database-queries`

4. **ASK USER TO CONFIRM OR CUSTOMIZE:**
   
   Present the suggested branch name and ask user to confirm or provide a custom name:
   
   ```
   Suggested branch name: feature/user-authentication
   
   Common prefixes:
     feature/  - New functionality
     fix/      - Bug fixes
     refactor/ - Code improvements
     chore/    - Maintenance tasks
     docs/     - Documentation
     test/     - Test additions
   
   Accept this branch name, or provide a custom name?
   ```
   
   - If user accepts → use the suggested name
   - If user provides custom name → use the custom name
   - Custom name should follow `prefix/slug` format

5. **Store the confirmed branch name as `[branch-name]` for subsequent steps.**

**Step 1: Check for Existing Task File**

1. Get current git branch name:
   ```bash
   git branch --show-current
   ```

2. Check if already on a feature branch with existing task file:
   
   ```
   Use simpletask_get() MCP tool to check for existing task:
   - Call simpletask_get() to use current git branch
   - If successful, task file exists - analyze spec.tasks to see if empty/minimal
   - If error (FileNotFoundError), task file does not exist
   ```

3. If task file exists for current branch:
   - Analyze output to see if tasks are empty or minimal
   - If tasks already exist, analyze and report current state
   - If tasks are empty/minimal, proceed to Step 3 to add detailed tasks
   - Use current branch name as `[branch-name]`
   
4. If task file does NOT exist:
   - If on main/master/develop: proceed to Step 2 to create new branch
   - If on other branch: ask user if they want to create task file for current branch or create new branch

**Note:** Branch names with slashes (e.g., `feature/user-auth`) are automatically normalized to filenames with hyphens (e.g., `.tasks/feature-user-auth.yml`). The MCP tools handle normalization automatically.

**Step 2: Create Git Branch (if needed)**

If creating a new branch (from Step 0's confirmed `[branch-name]`):
```bash
git checkout -b [branch-name]
```

**Step 3: Create or Update Task File**

1. If task file does NOT exist, create it:
   
   ```
   Use simpletask_new() MCP tool to create task file:
   - Call simpletask_new(
       branch="[branch-name]",
       title="[brief title from user prompt]",
       prompt="[original user request verbatim]",
       criteria=[]
     )
   - This creates .tasks/[normalized-branch-name].yml
   - Returns SimpleTaskWriteResponse with file_path and summary
   ```

2. If task file exists but is minimal, you can update it by adding criteria and tasks in subsequent steps.

**Step 4: Add Acceptance Criteria**

Add testable, specific acceptance criteria using simpletask_criteria() MCP tool:

```
Use simpletask_criteria() MCP tool to add each criterion:
- Call simpletask_criteria(
    action="add",
    description="Specific, testable outcome"
  )
- Repeat for each criterion (typically 3-6 criteria)
```

Guidelines for acceptance criteria:
- Must be testable (can verify if met)
- Specific and unambiguous
- Focus on user-visible outcomes
- Include quality checks (tests, coverage, etc.)

Example acceptance criteria:
- AC1: "Feature X renders correctly in the UI"
- AC2: "API endpoint returns correct response format"
- AC3: "All existing tests pass"
- AC4: "New functionality is covered by unit tests"

**Step 5: Plan Implementation Tasks**

Add implementation tasks using simpletask_task() MCP tool. Each task should be:
- Completable in 5-30 minutes
- Detailed enough for ANY LLM to execute without clarification
- Include specific steps (what to do)

```
Use simpletask_task() MCP tool to add each task:
- Call simpletask_task(
    action="add",
    name="Short descriptive task name",
    goal="One sentence explaining what this accomplishes",
    steps=[
      "First specific action",
      "Second specific action",
      "Third specific action"
    ],
    iteration=<iteration_id>  # Optional: assign to an iteration if iterations are defined
  )
- Repeat for each implementation task
```

**Optionally group tasks into iterations** for phased delivery (e.g., MVP, polish, v2):

```
Use simpletask_iteration() MCP tool to create iterations first:
- simpletask_iteration(action="add", label="MVP")
- simpletask_iteration(action="add", label="Polish")
Then assign tasks: simpletask_task(action="add", name="...", iteration=1)
```

```bash
# CLI equivalent
simpletask iteration add "MVP"
simpletask task add "First feature" --iteration 1
```

**Expected task structure:**
```yaml
tasks:
  - id: T001
    name: Short descriptive name
    status: not_started
    goal: One sentence explaining what this task accomplishes
    steps:
      - "First specific action - be explicit"
      - "Second specific action - include details"
      - "Third specific action - mention specifics"
```

**Step 6: Validate and Summarize**

1. Validate the task file:
   
   ```
   Use simpletask_get() MCP tool with validation:
   - Call simpletask_get(validate=True)
   - Check validation.valid in response
   - If validation.valid is False, check validation.errors for details
   ```

2. Show the complete task:
   
   ```
   Use simpletask_get() MCP tool:
   - Call simpletask_get()
   - Display spec.branch, spec.title
   - Display summary.criteria_total, summary.tasks_total
   - List spec.acceptance_criteria and spec.tasks
   ```

3. Report completion:
   ```
   Task file created/updated: .tasks/[normalized-branch-name].yml
   
   Summary:
   - Branch: [branch-name]
   - Title: [title]
   - Acceptance Criteria: [count]
   - Implementation Tasks: [count]
   - Status: not_started
   
   Next steps:
   - For complex features, run /simpletask.split to analyze codebase and split tasks into atomic units
   - For simple features, run /simpletask.implement to execute tasks
   ```

---

**STOP HERE. Do NOT proceed to implementation.**

The planning phase is complete when:
1. Task file exists at `.tasks/[normalized-branch-name].yml`
2. All acceptance criteria are defined
3. All implementation tasks are detailed with name, goal, and steps
4. Validation passes
