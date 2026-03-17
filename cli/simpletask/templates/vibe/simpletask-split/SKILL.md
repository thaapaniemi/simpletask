---
name: simpletask-split
description: Split complex tasks into atomic subtasks to reduce cognitive load for AI execution.
user-invocable: true
---

**Purpose:** This skill ensures AI models have minimal context per task by splitting complex tasks into ultra-atomic units (1-2 steps, 5-10 minutes). This eliminates ambiguity and decision-making during implementation.

**CRITICAL: This is a TASK REFINEMENT phase. You will automatically split ALL complex tasks, remove originals, add subtasks, renumber IDs, and update the task file. No preview, no confirmation - execute immediately.**

---

## Step 1: Load Task File

```
simpletask_get()  # Uses current git branch
Returns: SimpleTaskGetResponse with spec, file_path, summary
```

If task file not found: Report "No task file found. Run /simpletask-plan first." and STOP.

---

## Step 1.5: Codebase Analysis & Design (Conditional)

**SKIP this step if:**
- `simpletask_get()` shows `spec.design` is already populated (has patterns, constraints, or references)
- `simpletask_get()` shows `spec.quality_requirements` already configured

**If design section is empty or missing, execute this mandatory codebase analysis:**

### 1.5.1: Find Reference Implementations

Search the codebase for similar existing code. Look for:
- Similar functionality or patterns
- Existing implementations to follow
- Code that solves related problems

Document findings:
```
Use simpletask_design() MCP tool to add references:
- Call simpletask_design(
    action="set",
    field="reference",
    value="[file path]",
    reason="[why this is relevant]"
  )
```

### 1.5.2: Document Patterns to Follow

Analyze relevant files to identify coding patterns (Repository, Factory, Observer, etc.), code organization, naming conventions, and dependency injection patterns.

```
Call simpletask_design(
  action="set",
  field="pattern",
  value="[Pattern description]"
)
```

### 1.5.3: Define Architectural Constraints

Analyze codebase structure for layer separation rules, module boundaries, and technology stack limitations.

```
Call simpletask_design(
  action="set",
  field="constraint",
  value="[Constraint description]"
)
```

### 1.5.4: Identify Security Considerations

Analyze relevant files for input validation, authentication/authorization patterns, data sanitization, and sensitive data handling.

```
Call simpletask_design(
  action="set",
  field="security",
  value="[Security consideration]"
)
```

### 1.5.5: Define Error Handling Pattern

Identify how errors are handled: exception types, error propagation, logging, and user-facing messages.

```
Call simpletask_design(
  action="set",
  field="error-handling",
  value="[Error handling pattern]"
)
```

### 1.5.6: Define Quality Requirements

Based on the codebase tech stack, apply a quality preset:

```
Call simpletask_quality(
  action="preset",
  preset_name="[python|typescript|node|go|rust|java-maven|java-gradle]"
)
```

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

---

## Step 3: Analyze and Generate Subtasks

For EACH complex task, generate atomic subtasks using these patterns:

### Pattern Recognition Guide

**1. Model/Class Creation** (Multiple methods/fields):
- Subtask per field/method group

**2. API Endpoint** (Multiple concerns):
- Route file, endpoint skeleton, validation, logic, response, error handling

**3. Multi-File Feature** (Touches multiple files):
- Each file operation = separate subtask

**4. Testing** (Multiple test cases):
- Each test case = separate subtask

**5. Configuration + Implementation** (Setup then use):
- Config, setup, core implementation, integration

### Subtask Generation Rules

**Each subtask MUST have:**
- 1-2 steps maximum (preferably 1)
- Single clear objective
- Completable in 5-10 minutes
- No ambiguity

---

## Step 4: Apply Changes Atomically with Batch Operations

**CRITICAL:** Use batch operations to remove complex tasks and add subtasks atomically.

```python
operations = []

# Remove complex tasks
for task in complex_tasks:
    operations.append({"op": "remove", "task_id": task.id})

# Add subtasks
for subtask in generated_subtasks:
    operations.append({
        "op": "add",
        "name": subtask.name,
        "goal": subtask.goal,
        "steps": subtask.steps
    })

# Execute atomically
result = simpletask_task(action="batch", operations=operations)
```

---

## Step 5: Renumber Task IDs Sequentially

Renumber ALL tasks to sequential IDs (T001, T002, T003...) and update prerequisites.

1. Load updated task file with `simpletask_get()`
2. Create ID mapping: old_id -> new_id
3. Edit `.tasks/[branch].yml` directly to update IDs and prerequisite references
4. Verify all IDs sequential, all prerequisite references valid

---

## Step 6: Validate and Report

```
simpletask_get(validate=True)
```

Generate split summary showing: original state, splitting results, cognitive load reduction, and validation status.

Next steps:
- Review split tasks: `simpletask show`
- Start implementation: `/simpletask-implement`
