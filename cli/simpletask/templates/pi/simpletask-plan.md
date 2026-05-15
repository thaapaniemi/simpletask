---
description: Create specification and implementation plan from feature description using simpletask CLI.
argument-hint: "<feature description>"
---

User input: $ARGUMENTS

**CRITICAL: This is a PLANNING phase. DO NOT implement code or execute tasks. Your job is to create/update the task file with acceptance criteria and task breakdown — then STOP.**

Response contract:
- Do not reply with an acknowledgement-only message such as "Understood" or "I am ready".
- Start immediately with branch name analysis and confirmation.
- If plan mode or read-only mode is active, inspect using read-only tools only and respond with a
  summary of the proposed plan.
- Do not use MCP tools. Use only `simpletask` CLI commands and standard shell commands.

---

## Step 0: Determine Branch Name

1. Analyze the user prompt to determine branch type prefix:

   | If prompt contains... | Suggest prefix |
   |----------------------|----------------|
   | "fix", "bug", "error", "issue", "broken", "crash" | `fix/` |
   | "refactor", "cleanup", "improve", "optimize" | `refactor/` |
   | "test", "spec", "coverage" | `test/` |
   | "doc", "readme", "documentation" | `docs/` |
   | "chore", "config", "update deps", "upgrade", "bump" | `chore/` |
   | Default (new functionality) | `feature/` |

2. Generate slug from description:
   - Convert to lowercase, remove stop words, take first 3-4 meaningful words, join with hyphens.
   - Examples: "Add user authentication" → `user-authentication`

3. Construct suggested branch name as `[prefix]/[slug]`.

4. **ASK USER TO CONFIRM OR CUSTOMIZE** the suggested branch name before proceeding.

5. Store the confirmed branch name as `[branch-name]` for subsequent steps.

---

## Step 1: Check for Existing Task File

```bash
git branch --show-current
simpletask show --format json 2>&1
```

- If `simpletask show` succeeds: task file exists. If tasks are empty/minimal, proceed to Step 3.
- If it reports a file-not-found error: proceed to Step 2.
- Branch names with slashes (e.g., `feature/user-auth`) are normalized to filenames with hyphens
  (e.g., `.tasks/feature-user-auth.yml`) automatically.

---

## Step 2: Create Git Branch (if needed)

```bash
git checkout -b [branch-name]
```

---

## Step 3: Create or Update Task File

If task file does NOT exist, create it:

```bash
simpletask new "[branch-name]" "[brief title]" "[original user prompt verbatim]" --format json
```

If task file exists but is minimal, proceed to Step 4 to add criteria and tasks.

---

## Step 3.5: Project Defaults — MANDATORY — DO NOT SKIP

```bash
ls .tasks/defaults.yml 2>/dev/null && echo "exists" || echo "missing"
```

- **If `defaults.yml` exists:** Inform the user that project defaults were auto-merged. No action needed.
- **If `defaults.yml` does NOT exist:** Ask the user:

  > "No project defaults found (`.tasks/defaults.yml` is missing). Would you like to run a
  > codebase analysis now to set up project-level defaults? (yes / no)"

  **Wait for the user's response before continuing.**

  If yes: run the codebase analysis from Step 1.5 of `/simpletask-split` and write results using
  `simpletask design set` and `simpletask quality preset` CLI commands.

  If no: skip — the user can set up defaults later with `simpletask defaults`.

---

## Step 4: Add Acceptance Criteria

Add testable, specific acceptance criteria:

```bash
simpletask criteria add "[criterion description]" --format json
# Repeat for each criterion (typically 3-6)
```

**Write correctness invariants, not implementation descriptions.**

Criteria must describe *what must remain true* after the feature lands. Ask: "If this criterion is
satisfied, can I be confident the feature is correct?"

| Weak (avoid) | Strong (prefer) |
|---|---|
| "Posts to the endpoint" | "Constructed URL resolves to a valid endpoint given the configured base URL" |
| "Config file is parsed" | "All required keys are present; missing or malformed keys produce a descriptive error" |

**Required criteria by feature type:**
- Multi-file features crossing component boundaries: at least one cross-component correctness criterion.
- Features processing external input: at least one robustness criterion for malformed/missing values.
- Always include one user-observable outcome and one quality criterion (tests pass, schema validates).

**Self-check before proceeding:**
1. Multi-file cross-component behavior? → cross-component criterion present?
2. External input? → robustness criterion present?
3. No restatements of task names?
4. At least one externally observable user outcome?

Do NOT proceed to Step 5 until all four checks pass.

---

## Step 5: Plan Implementation Tasks

Add implementation tasks. Each task should be completable in 5-30 minutes:

```bash
simpletask task add "[short descriptive name]" \
  --goal "[one sentence explaining what this accomplishes]" \
  --steps "First specific action" "Second specific action" "Third specific action" \
  --format json
# Repeat for each task
```

---

## Step 6: Validate and Summarize

```bash
simpletask schema validate --format json
simpletask show --format json
```

Report completion:
```
Task file created/updated: .tasks/[normalized-branch-name].yml

Summary:
- Branch: [branch-name]
- Title: [title]
- Acceptance Criteria: [count]
- Implementation Tasks: [count]
- Status: not_started

Next steps:
- For complex features, run /simpletask-split to analyze codebase and split tasks
- For simple features, run /simpletask-implement to execute tasks
```

---

**STOP HERE. Do NOT proceed to implementation.**

The planning phase is complete when:
1. Task file exists at `.tasks/[normalized-branch-name].yml`
2. All acceptance criteria are defined
3. All implementation tasks are detailed with name, goal, and steps
4. `simpletask schema validate` passes
