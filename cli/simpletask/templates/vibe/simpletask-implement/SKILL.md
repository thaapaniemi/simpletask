---
name: simpletask-implement
description: Execute task list to implement feature/fix using simpletask.
user-invocable: true
---

**CRITICAL MANDATES**
1. Keep task statuses accurate via MCP updates throughout execution.
2. Run quality checks before marking any task `completed`.
3. Update acceptance criteria after implementation.
4. Create exactly one final Conventional Commit when all work is done.
5. **DO NOT** skip quality checks, implement tasks with unmet prerequisites, or create multiple commits.

**WORKFLOW**
1. Load task state with `simpletask_get`. Identify executable tasks: status `not_started` with all `prerequisites` satisfied. If iterations exist, prioritize tasks in the lowest/current iteration. If the user specifies task IDs, implement only those.
2. For each task:
   a. Set status to `in_progress` via `simpletask_task`.
   b. Implement using task guidance: `steps`, `files`, `done_when`, `constraints`, `code_examples`, and `design` section.
   c. Record significant decisions or blockers with `simpletask_note`.
   d. Verify all `done_when` conditions are met.
   e. Run `simpletask_quality` with `action="check"`.
   f. If quality passes and goals satisfied: set status `completed`.
      Otherwise: set `blocked` or `paused` with a note explaining why.
3. Mark all satisfied acceptance criteria as completed via `simpletask_criteria`.
4. Validate task file schema: `simpletask_get` with `validate=true`.
5. Create one conventional commit covering all changes.

**OUTPUT**
Report: tasks completed, tasks blocked/paused, criteria completed, quality result, commit details.

**TOOL REFERENCE**
MCP tools used: `simpletask_get`, `simpletask_task`, `simpletask_criteria`, `simpletask_note`, `simpletask_quality`.
Status values: `not_started`, `in_progress`, `completed`, `blocked`, `paused`.
Status updates via `simpletask_task`: Returns SimpleTaskWriteResponse with success confirmation.
