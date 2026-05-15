---
description: Analyze codebase and split complex tasks into atomic subtasks using simpletask CLI.
argument-hint: ""
---

User input: $ARGUMENTS

**Purpose:** Ensure AI models have minimal context per task by splitting complex tasks into
ultra-atomic units (1-2 steps, 5-10 minutes each). This eliminates ambiguity and decision-making
during implementation.

**CRITICAL: This is a TASK REFINEMENT phase. Automatically split ALL complex tasks, remove
originals, add subtasks, renumber IDs, and update the task file. No preview, no confirmation —
execute immediately.**

Response contract:
- Do not reply with an acknowledgement-only message.
- Start immediately with loading the task file.
- Do not use MCP tools. Use only `simpletask` CLI commands, direct file reads, and shell commands.

---

## Step 1: Load Task File

```bash
git branch --show-current
simpletask show --format json
simpletask task list --flat --format json
```

If task file not found: Report "No task file found. Run /simpletask-plan first." and STOP.

---

## Step 1.5: Codebase Analysis & Design (Conditional)

**SKIP this step if ANY of the following are true:**
- `simpletask show --format json` shows a populated `design` section (has patterns, constraints, or
  references)
- `simpletask quality show --format json` shows quality requirements already configured
- `.tasks/defaults.yml` exists and contains design patterns or quality requirements

**If design section is empty or missing, execute this mandatory codebase analysis:**

### 1.5.1: Find Reference Implementations

Search the codebase directly for similar existing code:

```bash
# Find files by keyword
find . -name "*.py" | xargs grep -l "[feature keyword]" 2>/dev/null | head -10

# Read relevant files
cat [path/to/reference/file]

# Check architecture docs
cat AGENTS.md 2>/dev/null | head -80
cat README.md 2>/dev/null | head -40
```

Document findings:

```bash
simpletask design set reference "[file path]" "[why this is relevant]" --format json
# Repeat for each reference
```

### 1.5.2: Document Patterns to Follow

Read existing modules to identify patterns:

```bash
# Check project config for tech stack
cat pyproject.toml 2>/dev/null | head -40
cat package.json 2>/dev/null | head -20

# Read similar modules to identify conventions
cat [path/to/similar/module]
```

```bash
simpletask design set pattern "[pattern name or description]" --format json
# Repeat for each pattern
```

### 1.5.3: Define Architectural Constraints

```bash
# Inspect directory structure and imports
ls -la src/ 2>/dev/null || ls -la cli/ 2>/dev/null
grep -r "from \." [src_dir]/ 2>/dev/null | head -20
```

```bash
simpletask design set constraint "[constraint description]" --format json
# Repeat for each constraint
```

### 1.5.4: Identify Security Considerations

```bash
# Check existing validation patterns
grep -rn "validate\|sanitize\|escape" [src_dir]/ 2>/dev/null | head -10
```

```bash
simpletask design set security --category input_validation "[description]" --format json
```

### 1.5.5: Define Error Handling Pattern

```bash
# Check existing error handling
grep -rn "raise \|except \|try:" [src_dir]/ 2>/dev/null | head -15
```

```bash
simpletask design set error-handling "[pattern: exceptions|result_type|error_codes]" --format json
```

### 1.5.6: Define Quality Requirements

Apply a quality preset based on the tech stack:

```bash
simpletask quality preset [python|typescript|node|go|rust|java-maven|java-gradle] --format json
```

**Available presets:** python, typescript, node, go, rust, java-maven, java-gradle

After Step 1.5, reload the task file:

```bash
simpletask show --format json
```

---

## Step 2: Identify Tasks to Split

**A task MUST be split if it meets ANY criterion:**
- **>2 steps** in the steps array
- **>1 file** in the files array
- **>3 conditions** in `done_when`
- **>100 characters** in goal description

**SKIP splitting (already atomic) if:**
- Exactly 1 step AND step <50 characters
- Task name contains: "Add import", "Update version", "Fix typo", "Remove unused"
- Task name starts with "Fix:" (bug fixes need full context)

Read the full task file to evaluate:

```bash
cat .tasks/$(git branch --show-current | sed 's|/|-|g').yml
```

---

## Step 3: Analyze and Generate Subtasks

For EACH complex task, generate atomic subtasks using these patterns:

### Pattern Recognition Guide

**1. Model/Class Creation** — Split by method/field:
- Subtask 1: Create file with skeleton
- Subtask 2+: Add each field/method separately

**2. API Endpoint** — Split by concern:
- Create route file → endpoint skeleton → validation → business logic → error handling

**3. Multi-File Feature** — Each file = one subtask (create → modify → delete order)

**4. Testing** — Each test case = one subtask (happy path → error cases → edge cases)

**5. Configuration + Implementation** — config → setup → implementation → integration

### Subtask Generation Rules

Each subtask MUST have:
- 1-2 steps maximum (preferably 1)
- Single clear objective completable in 5-10 minutes
- No ambiguity or decisions left to the implementer

**Naming:** Action verb + specific target (max 60 chars)
- ✅ "Create User model file with base structure"
- ❌ "Work on User model" (too vague)

**Goal:** One sentence (30-80 chars) describing a specific outcome.

**Steps:** 1-2 concrete actions with specific paths and names.

### Distribute Task Attributes

- **Prerequisites:** First subtask inherits all original prerequisites. Each subsequent subtask
  depends on the previous one.
- **Files:** Distribute 1 file per subtask where possible.
- **done_when:** 1-2 specific verifiable conditions per subtask.
- **code_examples:** Attach to the most relevant subtask.

---

## Step 4: Apply Changes — Remove Complex Tasks, Add Subtasks

Remove each complex task, then add its subtasks:

```bash
# Remove complex tasks
simpletask task remove [T00X] --format json

# Add each subtask
simpletask task add "[subtask name]" \
  --goal "[specific outcome]" \
  --steps "Step 1" "Step 2" \
  --format json
# Repeat for each subtask
```

> Note: Add all subtasks before removing complex tasks if their IDs are needed for prerequisites.

---

## Step 5: Renumber Task IDs Sequentially

After all changes, task IDs may have gaps. Renumber sequentially (T001, T002, T003…):

```bash
# Read current state
cat .tasks/$(git branch --show-current | sed 's|/|-|g').yml
```

Edit the YAML file directly to renumber IDs and update all prerequisite references:
- Map old IDs → new sequential IDs
- Update every `id:` field
- Update every item in `prerequisites:` arrays

```bash
# Verify after editing
simpletask schema validate --format json
```

---

## Step 6: Validate and Report

```bash
simpletask schema validate --format json
simpletask task list --flat --format json
```

Generate a split summary:

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
    ...

VALIDATION
  Schema: ✓ Valid
  Task IDs: ✓ Sequential
  Prerequisites: ✓ All valid references

───────────────────────────────────────────────────────────────
READY FOR IMPLEMENTATION

Next steps:
  - Review split tasks: simpletask show
  - Start implementation: /simpletask-implement
───────────────────────────────────────────────────────────────
```

---

## Edge Cases

- **No complex tasks found:** Report "No complex tasks found. All tasks are already atomic." and stop.
- **Multiple prerequisites:** First subtask inherits ALL; subsequent subtasks depend only on previous.
- **Split creates >10 subtasks:** Proceed — add a warning: "⚠ Task 'X' split into 12+ subtasks".
- **Long prerequisite chains:** Linear chains are expected and correct — do NOT try to parallelize.

---

## Rules

- Do not use MCP tools. Use `simpletask` CLI commands and direct file reads only.
- Always pass `--format json` to every simpletask CLI command.
- Read task YAML files directly when CLI output is not detailed enough.
- Do not modify code files — only the task file and codebase analysis are in scope.
