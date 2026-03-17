---
name: simpletask-review
description: Scope-bounded code review that verifies implementation against original prompt and acceptance criteria only.
user-invocable: true
---

**IMPORTANT: Scope constraint**

This review is strictly scoped to the original prompt and acceptance criteria defined in the task file. Your job is to verify that the implementation satisfies those requirements - nothing more. Do NOT suggest features, refactoring, or improvements beyond what was explicitly requested. Do NOT flag issues in code outside the git diff. Do NOT expand the PR.

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
   - If error occurs, task file does not exist - abort and inform the user
   ```

**Step 2: Analyze Task Completion**

From the `simpletask_get()` response:
- Filter `spec.tasks` by status: completed, in_progress, not_started, blocked, paused
- Use `summary` fields for quick counts

**Step 3: Check Acceptance Criteria**

From the `simpletask_get()` response:
- Check `spec.acceptance_criteria` array for `completed` status
- Use `summary.criteria_total` and `summary.criteria_completed` for counts

**Step 4: Verify Implementation Against Criteria and Diff**

Scope: only the files in `git diff --name-only main..HEAD`. Do not review anything outside the diff.

For each acceptance criterion, check whether the diff actually satisfies it. Also read any implementation notes for context on decisions made.

```
Use simpletask_note() MCP tool to list notes:
- Call simpletask_note(action="list")
- Returns root_notes and task_notes
```

Look for:

### Criteria Satisfaction
- For each criterion: does the diff contain code that implements it?
- Are there criteria marked complete but with no corresponding changes?
- Are there criteria still incomplete that are actually implemented?

### Security (within diff scope only)
- Exposed credentials, API keys, or secrets
- Input validation gaps relevant to the feature
- Injection vulnerabilities in new code only

### Correctness
- Logic errors preventing acceptance criteria from being met
- Missing edge cases for paths described in criteria
- Error handling gaps causing user-visible failures

**Do NOT flag:** code style, naming conventions, missing abstractions, performance of unchanged code, documentation outside feature scope.

**Step 5: Analyze Git Changes**

```bash
git log --oneline main..HEAD
git diff --stat main..HEAD
git diff --name-only main..HEAD | head -20
```

Analyze: commits on branch, files modified, lines changed, scope focus vs scatter.

**Step 6: Generate Scoped, Actionable Feedback**

Only report issues that:
- Prevent an acceptance criterion from being met, OR
- Are Critical/High severity security or correctness issues in changed code

**Categories:**
1. **UNMET CRITERIA** - Acceptance criteria not satisfied
2. **SECURITY** - Critical/High severity in new/changed code only
3. **CORRECTNESS** - Logic errors preventing feature from working
4. **SCOPE CREEP** - Changes beyond original prompt (informational)

**Step 7: Determine PR Readiness**

- **READY TO MERGE**: All tasks completed, all criteria met, no blocking issues
- **NEEDS CHANGES**: All done but has Critical/High severity issues
- **NOT READY**: Tasks incomplete, criteria unmet, or critical flaws

**Step 8: Display Review Summary**

Show: original prompt, task completion stats, criteria status, git changes, blocking issues, observations, and PR readiness determination.

**Step 9: Auto-Inject Fix Tasks (blocking issues only)**

If Critical/High severity blocking issues exist:

1. Create iteration: `simpletask_iteration(action="add", label="review fixes")`
2. Add fix tasks: `simpletask_task(action="add", name="Fix: [issue]", goal="[remediation]", iteration=<id>)`
3. Validate: `simpletask_get(validate=True)`

If no blocking issues: report "No fix tasks needed."

---

## Quality Gates

Before marking as "READY TO MERGE":
1. All tasks completed
2. All criteria met
3. No blocking issues
4. Tests pass
5. Schema valid: `simpletask_get(validate=True)`
