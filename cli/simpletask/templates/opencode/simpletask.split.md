---
description: Split complex tasks into atomic subtasks to reduce cognitive load for AI execution
---

User input: $ARGUMENTS

**Purpose:** This tool ensures AI models have minimal context per task by splitting complex tasks into ultra-atomic units (1-2 steps, 5-10 minutes). This eliminates ambiguity and decision-making during implementation.

**CRITICAL: This is a TASK REFINEMENT phase. You will automatically split ALL complex tasks, remove originals, add subtasks, renumber IDs, and update the task file. No preview, no confirmation - execute immediately.**

---

## Step 1: Load Task File

```
simpletask_get()  # Uses current git branch
Returns: SimpleTaskGetResponse with spec, file_path, summary
```

If task file not found: Report "No task file found. Run /simpletask.plan first." and STOP.

---

## Step 1.5: Codebase Analysis & Design (Conditional)

**SKIP this step if:**
- `simpletask_get()` shows `spec.design` is already populated (has patterns, constraints, or references)
- `simpletask_get()` shows `spec.quality_requirements` already configured

**If design section is empty or missing, execute this mandatory codebase analysis:**

This phase analyzes the codebase to populate design guidance and quality requirements before splitting tasks.

### 1.5.1: Find Reference Implementations

Use the Task tool with the `explore` agent to find similar existing code:

```
Task(
  subagent_type="explore",
  description="Find reference implementations",
  prompt="Find files similar to [feature description]. Look for:
- Similar functionality or patterns
- Existing implementations we should follow
- Code that solves related problems
Thoroughness: [quick/medium/very thorough]"
)
```

Set thoroughness based on task complexity:
- **"quick"** - Simple tasks with obvious patterns
- **"medium"** - Most tasks requiring moderate exploration
- **"very thorough"** - Complex tasks or unfamiliar codebases

Document findings:
```
Use simpletask_design() MCP tool to add references:
- Call simpletask_design(
    action="set",
    field="reference",
    value="[file path]",
    reason="[why this is relevant]"
  )
- Repeat for each reference implementation
```

### 1.5.2: Document Patterns to Follow

Use the explore agent to identify coding patterns:

```
Task(
  subagent_type="explore",
  description="Identify design patterns",
  prompt="Analyze [relevant files] to identify:
- Design patterns used (Repository, Factory, Observer, etc.)
- Code organization patterns
- Naming conventions
- Dependency injection patterns
Thoroughness: [quick/medium/very thorough]"
)
```

Document using simpletask_design():
```
Call simpletask_design(
  action="set",
  field="pattern",
  value="[Pattern description]"
)
- Repeat for each pattern identified
```

### 1.5.3: Define Architectural Constraints

Use the explore agent to understand constraints:

```
Task(
  subagent_type="explore",
  description="Identify architectural constraints",
  prompt="Analyze codebase structure to identify:
- Layer separation rules (UI/business/data)
- Circular dependency constraints
- Module boundaries
- Technology stack limitations
Thoroughness: [quick/medium/very thorough]"
)
```

Document using simpletask_design():
```
Call simpletask_design(
  action="set",
  field="constraint",
  value="[Constraint description]"
)
- Repeat for each constraint
```

### 1.5.4: Identify Security Considerations

Use the explore agent for security analysis:

```
Task(
  subagent_type="explore",
  description="Identify security patterns",
  prompt="Analyze [relevant files] for security patterns:
- Input validation approaches
- Authentication/authorization patterns
- Data sanitization methods
- Sensitive data handling
Thoroughness: [quick/medium/very thorough]"
)
```

Document using simpletask_design():
```
Call simpletask_design(
  action="set",
  field="security",
  value="[Security consideration]"
)
- Repeat for each security consideration
```

### 1.5.5: Define Error Handling Pattern

Use the explore agent to understand error handling:

```
Task(
  subagent_type="explore",
  description="Identify error handling pattern",
  prompt="Find how errors are handled in [similar files]:
- Exception types used
- Error propagation strategy
- Logging approach
- User-facing error messages
Thoroughness: [quick/medium/very thorough]"
)
```

Document using simpletask_design():
```
Call simpletask_design(
  action="set",
  field="error-handling",
  value="[Error handling pattern description]"
)
```

### 1.5.6: Define Quality Requirements

Based on the codebase tech stack, apply a quality preset:

```
Use simpletask_quality() MCP tool to apply preset:
- Call simpletask_quality(
    action="preset",
    preset_name="[python|typescript|node|go|rust|java-maven|java-gradle]"
  )
- Returns fields that were filled (gaps only)
```

**Available presets:** python, typescript, node, go, rust, java-maven, java-gradle

**After completing Step 1.5, reload the task file:**
```
simpletask_get()  # Refresh to see populated design section
```

---

## Step 2: Identify Tasks to Split

**A task MUST be split if it meets ANY criterion:**
- **>2 steps** in the steps array
- **>1 file** in the files array
- **>3 conditions** in done_when array
- **>100 characters** in goal description

**SKIP splitting (already atomic) if:**
- Exactly 1 step AND step <50 characters
- Task name contains: "Add import", "Update version", "Fix typo", "Remove unused", "Rename variable"
- Task name starts with "Fix:" (bug fixes need full context)

**Process:**
```
From simpletask_get() response:
- Iterate spec.tasks array
- Evaluate each against split criteria
- Store complex tasks in complex_tasks list
- Store atomic tasks in atomic_tasks list
```

---

## Step 3: Analyze and Generate Subtasks

For EACH complex task, generate atomic subtasks using these patterns:

### Pattern Recognition Guide

**1. Model/Class Creation** (Multiple methods/fields):
- Subtask 1: Create file with skeleton
- Subtask 2+: Add each field/method separately
- Target: 1 method or 1-3 related fields per subtask

**2. API Endpoint** (Multiple concerns):
- Subtask 1: Create route file
- Subtask 2: Add endpoint skeleton
- Subtask 3: Add request validation
- Subtask 4: Add business logic
- Subtask 5: Add response handling
- Subtask 6: Add error handling

**3. Multi-File Feature** (Touches multiple files):
- Each file operation = separate subtask
- Order: create → modify → delete

**4. Testing** (Multiple test cases):
- Each test case = separate subtask
- Order: happy path → error cases → edge cases

**5. Configuration + Implementation** (Setup then use):
- Subtask 1: Configuration
- Subtask 2: Setup/initialization
- Subtask 3: Core implementation
- Subtask 4: Integration

### Subtask Generation Rules

**Each subtask MUST have:**
- 1-2 steps maximum (preferably 1)
- Single clear objective
- Completable in 5-10 minutes
- No ambiguity

**Naming convention:**
- Action verb + specific target (max 60 chars)
- ✅ "Create User model file with base structure"
- ✅ "Add email field to User model"
- ❌ "Work on User model" (too vague)

**Goal convention:**
- One sentence (30-80 chars)
- Specific outcome
- ✅ "Create src/models/user.py with SQLAlchemy imports and User class skeleton"

**Steps convention:**
- 1-2 concrete actions
- Include specific paths, names
- ✅ "Create file src/models/user.py with imports: from sqlalchemy import Column, String"

### Distribute Task Attributes

**Prerequisites:**
- First subtask: Inherits ALL prerequisites from original
- Subsequent subtasks: Depend on previous subtask
- Exception: Parallel subtasks can share same prerequisite

**Files array:**
- Distribute to relevant subtasks (1 file per subtask ideally)
- action: create | modify | delete

**Done_when conditions:**
- 1-2 specific conditions per subtask
- Must be verifiable

**Code_examples:**
- Attach to most relevant subtask
- Duplicate if applies to multiple

---

## Step 4: Apply Changes Atomically with Batch Operations

**CRITICAL:** Use batch operations to remove complex tasks and add subtasks atomically. All operations succeed or all fail - no partial states.

```python
# Build operations list
operations = []

# Add remove operations for complex tasks
for task in complex_tasks:
    operations.append({"op": "remove", "task_id": task.id})

# Add create operations for subtasks
for subtask in generated_subtasks:
    operations.append({
        "op": "add",
        "name": subtask.name,
        "goal": subtask.goal,
        "steps": subtask.steps
    })

# Execute atomically
result = simpletask_task(action="batch", operations=operations)
# Returns: SimpleTaskBatchResponse with new_item_ids list
```

**Note:** MCP batch operation supports all Task fields including:
- `name`, `goal`, `steps` (basic task info)
- `done_when` (completion verification conditions)
- `files` (files to create/modify/delete)
- `code_examples` (code patterns to follow)
- `prerequisites` (task dependencies)

**Why batch operations?**
- Atomic: All changes apply or none do
- No inconsistent intermediate states if interrupted
- Single write operation for better performance

---

## Step 5: Renumber Task IDs Sequentially

**CRITICAL:** Renumber ALL tasks to sequential IDs (T001, T002, T003...) and update prerequisites.

**5.1: Load updated task file**
```
simpletask_get()
```

**5.2: Create ID mapping**
```python
old_to_new_id = {}
for index, task in enumerate(spec.tasks):
    new_id = f"T{(index + 1):03d}"  # T001, T002, T003
    old_to_new_id[task.id] = new_id
```

**5.3: Update IDs and prerequisites**

Edit `.tasks/[branch].yml` directly:
1. Update each task's `id` field using mapping
2. Update each task's `prerequisites` array using mapping

Example: `prerequisites: [T015, T016]` → `prerequisites: [T003, T004]`

**5.4: Verify**
- All IDs sequential with no gaps
- All prerequisite references valid
- No references to non-existent tasks

---

## Step 6: Validate and Report

**Validate schema:**
```
simpletask_get(validate=True)
# Check validation.valid and validation.errors
```

If validation fails, fix errors and re-validate.

**Generate split summary:**

```
╭─────────────────────────────────────────────────────────────╮
│ Task Splitting Complete                                     │
╰─────────────────────────────────────────────────────────────╯

ORIGINAL STATE
  Total Tasks: X
  Complex Tasks (>2 steps): Y
  Atomic Tasks (kept as-is): Z

SPLITTING RESULTS
  Tasks Removed: Y
  Subtasks Generated: N
  New Total Tasks: M

SPLIT DETAILS
  ✓ T001 "Create User model" (4 steps)
    → T001 "Create User model file with base structure" (1 step)
    → T002 "Add User model fields" (1 step)
    → T003 "Add email unique constraint" (1 step)
    → T004 "Implement hash_password method" (1 step)

COGNITIVE LOAD REDUCTION
  Average steps per task:
    Before: 4.2 steps
    After: 1.3 steps
  
  Estimated completion time per task:
    Before: 15-30 minutes
    After: 5-10 minutes

VALIDATION
  Schema: ✓ Valid
  Task IDs: ✓ Sequential (T001-T0XX)
  Prerequisites: ✓ All valid references

───────────────────────────────────────────────────────────────
READY FOR IMPLEMENTATION

Each task is now atomic with minimal context needed.
Any AI model can execute these tasks without ambiguity.

Next steps:
  - Review split tasks: simpletask show
  - Start implementation: /simpletask.implement
───────────────────────────────────────────────────────────────
```

---

## Edge Cases

**No complex tasks found:**
- Report: "No complex tasks found. All tasks are already atomic."
- List task stats (total, 1-step, 2-step)
- Skip to "Ready for implementation"

**Task already very atomic:**
- Skip splitting
- Keep in atomic_tasks list

**Multiple prerequisites:**
- First subtask inherits ALL: `prerequisites: [T001, T002, T005]`
- Subsequent subtasks depend on previous only

**Code example applies to multiple subtasks:**
- Duplicate to all relevant subtasks
- Each subtask should be self-contained

**Split creates >10 subtasks:**
- Proceed with split
- Add warning: "⚠ Task 'X' split into 12+ subtasks - this is acceptable"

**Long prerequisite chains:**
- Linear chains (T001 → T002 → ... → T015) are expected and correct
- Do NOT try to parallelize sequential steps

**No files/done_when in original:**
- Split by steps only
- Generate basic done_when from steps if needed

---

## Important Reminders

**WHY we split:**
- Reduce cognitive load for AI models
- Eliminate ambiguity during execution
- Ensure ANY LLM can execute correctly
- Enable independent verification
- Better parallelization where possible

**WHAT makes a good subtask:**
- 1-2 steps only
- 5-10 minute completion time
- Single clear objective
- No decisions left to implementer
- Self-contained with all context

**WHAT to avoid:**
- Subtasks requiring multiple decisions
- Subtasks modifying multiple unrelated files
- Vague goals like "Set up feature"
- Dependencies on unclear state

**Target metrics per subtask:**
- **1-2 steps** maximum
- **5-10 minutes** to complete
- **1 file** modified (preferably)
- **1-2 done_when** conditions
- **No ambiguity**

If a subtask takes >10 minutes or has >2 steps, split it further.
