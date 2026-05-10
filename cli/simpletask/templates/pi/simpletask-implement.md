---
description: Execute the current simpletask implementation workflow in Pi using CLI commands.
argument-hint: "[task-id ...]"
---

User input: $ARGUMENTS

Invoking `/simpletask-implement` is itself the user's request to perform implementation work now.
If no task IDs or extra arguments are provided, treat the current branch task file as the work to
execute. Do not wait for the user to provide a "first task" unless the task file is missing or
invalid.

Use this prompt for implementation work only. Do not create or rewrite the plan unless the task
file is clearly missing or invalid.

Mandates:
- Create exactly one final Conventional Commit when all requested work is done. Do not create
  multiple commits.
- Run quality checks before marking any task `completed`.
- Do not skip quality checks, implement tasks with unmet prerequisites, or create multiple commits.

Response contract:
- Do not reply with an acknowledgement-only message such as "Understood", "I have read the
  instructions", "I am ready", or "please provide the first task".
- In normal mode, do not restate the workflow. Start immediately with `git branch --show-current`.
- If a system reminder says plan mode or read-only mode is active, do not try to execute or
  acknowledge.
- In that read-only case, inspect using read-only tools only and respond with `Plan:` followed by a
  numbered list for exactly one executable task.
- In that `Plan:` output, include the selected task ID, the files to inspect or change later, and
  the verification commands to run during execution mode.
- End the read-only response with exactly one short line: `Choose Execute the plan to continue.`
- During read-only plan mode, do not insist on `simpletask` CLI if it is blocked by the
  environment allowlist; use direct task-file and source-file reads instead. Once execution mode
  is available, switch back to `simpletask` CLI for task management.

1. Identify the current branch:
   - `git branch --show-current`
2. Show the current task summary:
   - `simpletask show --format json`
3. Inspect implementation state before editing code:
   - `simpletask task list --flat --format json`
   - `simpletask criteria list --format json`
   - `simpletask quality show --format json`
   - For full task detail (steps, done_when, prerequisites, files, notes), run:
     `simpletask show --format json`
4. If the user specified task IDs, restrict work to those IDs. Otherwise, select exactly one
   executable task at a time:
   - prefer a task already in `in_progress`; finish it before starting another
   - otherwise select a task whose status is `not_started`
   - all prerequisites are already completed
5. Before changing code, mark only the selected task in progress for the current work:
   - `simpletask task update T001 --status in_progress --format json`
   - do not move a second task to `in_progress` until the current task leaves that state
6. Implement using the task's `goal`, `steps`, `done_when`, `files`, `constraints`, `design`, and
   the current codebase context.
7. Record only meaningful blockers or decisions:
   - `simpletask note add "..." --task T001 --format json`
8. Before marking a task complete:
   - confirm every `done_when` condition is satisfied
   - run `simpletask quality check --format json`
9. As soon as the implementation attempt is done, update the task status immediately:
   - success after `done_when` verification and quality checks: `simpletask task update T001 --status completed --format json`
   - blocked: `simpletask task update T001 --status blocked --format json`
   - intentionally deferred: `simpletask task update T001 --status paused --format json`
   - do not leave finished work in `in_progress`
10. Mark any satisfied acceptance criteria:
   - `simpletask criteria complete AC1 --format json`
11. When the requested implementation work is done, validate the task file:
   - `simpletask schema validate --format json`
12. If all requested tasks completed successfully, create one Conventional Commit:
   - `git add -A`
   - `git commit -m "type(scope): description"`
   - Use the correct type (`feat`, `fix`, `refactor`, `test`, `docs`, `chore`) based on the work.
   - Do NOT include simpletask IDs (e.g. T001, AC1) or issue tracker numbers (e.g. #123) in the commit message.
   - Skip the commit if any task ended `blocked` or `paused` — unstable work should not be committed.
13. Report completed tasks, blocked or paused tasks, completed criteria, quality-check result, and
   commit details.

Rules:
- Use `simpletask` CLI commands for task management.
- Always pass `--format json` to every simpletask CLI command for structured, ANSI-free output.
- Do not start tasks with unmet prerequisites.
- Keep at most one task in `in_progress` at a time.
- Do not mark a task completed before quality checks pass.
- Keep code changes minimal and focused on the selected task.
- If quality configuration is missing or the task file is invalid, stop and explain the blocker.
