# MCP Integration Guide

This guide covers how to integrate simpletask with AI editors using the Model Context Protocol (MCP).

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration](#configuration)
  - [OpenCode](#opencode)
  - [Qwen-CLI](#qwen-cli)
  - [Gemini CLI](#gemini-cli)
  - [Other MCP Clients](#other-mcp-clients)
- [Available Tools](#available-tools)
  - [get](#get)
  - [list](#list)
  - [new](#new)
  - [task](#task)
  - [criteria](#criteria)
- [Usage Examples](#usage-examples)
  - [Example 1: Understanding Task Context](#example-1-understanding-task-context)
  - [Example 2: Checking Progress](#example-2-checking-progress)
  - [Example 3: Creating a New Task](#example-3-creating-a-new-task)
  - [Example 4: Managing Task Progress](#example-4-managing-task-progress)
- [Troubleshooting](#troubleshooting)
  - [Server Not Responding](#server-not-responding)
  - [Tool Not Found](#tool-not-found)
  - [Permission Denied](#permission-denied)
  - [Invalid Branch Name](#invalid-branch-name)
  - [Validation Errors](#validation-errors)
- [Technical Details](#technical-details)

## Quick Start

**1. Install simpletask** (if not already installed):

```sh
uv tool install simpletask --from git+https://github.com/thaapaniemi/simpletask.git
```

**2. Start the MCP server** (leave this running):

```sh
simpletask serve
```

The server runs on stdio transport and waits for MCP client connections.

**3. Configure your AI editor** (see [Configuration](#configuration) below)

**4. Test the integration** - Ask your AI assistant:
```
"What task am I currently working on?"
"List all available tasks in this project"
"What are the acceptance criteria for this task?"
```

## Configuration

### OpenCode

OpenCode is an AI code editor with native MCP support.

**Configuration file location:**
- Linux/macOS: `~/.config/opencode/opencode.json`
- Windows: `%APPDATA%\opencode\opencode.json`

**Add this configuration:**

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "simpletask": {
      "type": "local",
      "command": ["simpletask", "serve"],
      "enabled": true
    }
  }
}
```

**If simpletask is installed in a virtualenv**, use the full path:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "simpletask": {
      "type": "local",
      "command": ["/path/to/venv/bin/simpletask", "serve"],
      "enabled": true
    }
  }
}
```

To find the full path:
```sh
which simpletask
# or
uv tool dir simpletask
```

**Restart OpenCode** after adding the configuration.

**Verify connection:**
Open OpenCode and ask the AI:
```
"Can you list the available simpletask tools?"
```

You should see `simpletask_get`, `simpletask_list`, `simpletask_new`, `simpletask_task`, and `simpletask_criteria` in the response (MCP clients automatically prefix tool names with the server name).

### Qwen-CLI

Qwen-CLI is a command-line AI assistant with MCP support.

**Configuration file location:**
- Linux/macOS: `~/.config/qwen-cli/config.json`
- Windows: `%APPDATA%\qwen-cli\config.json`

**Add this configuration:**

```json
{
  "mcp_servers": {
    "simpletask": {
      "command": "simpletask",
      "args": ["serve"],
      "transport": "stdio"
    }
  }
}
```

**If simpletask is installed in a virtualenv**, use the full path:

```json
{
  "mcp_servers": {
    "simpletask": {
      "command": "/home/user/.local/share/uv/tools/simpletask/bin/simpletask",
      "args": ["serve"],
      "transport": "stdio"
    }
  }
}
```

**Restart Qwen-CLI** after adding the configuration.

**Verify connection:**
```sh
qwen-cli "List available MCP tools"
```

### Gemini CLI

Gemini CLI is a command-line AI assistant with MCP support.

**Configuration file location:**
- Linux/macOS: `~/.gemini/settings.json`
- Windows: `%USERPROFILE%\.gemini\settings.json`

**Add this configuration:**

```json
{
  "mcpServers": {
    "simpletask": {
      "command": "simpletask",
      "args": ["serve"],
      "transport": "stdio"
    }
  }
}
```

**Important:** Gemini CLI uses `mcpServers` (camelCase), not `mcp_servers` like Qwen-CLI.

**If simpletask is installed in a virtualenv**, use the full path:

```json
{
  "mcpServers": {
    "simpletask": {
      "command": "/home/user/.local/share/uv/tools/simpletask/bin/simpletask",
      "args": ["serve"],
      "transport": "stdio"
    }
  }
}
```

**Restart Gemini CLI** after adding the configuration.

**Verify connection:**
```sh
gemini "List available MCP tools"
```

### Other MCP Clients

Any MCP-compatible client can connect to simpletask's MCP server using stdio transport.

**Generic configuration pattern:**

```json
{
  "servers": {
    "simpletask": {
      "command": "simpletask",
      "args": ["serve"],
      "transport": "stdio"
    }
  }
}
```

**Key requirements:**
- **Transport**: stdio (standard input/output)
- **Command**: Path to `simpletask` executable
- **Args**: `["serve"]`

Refer to your MCP client's documentation for specific configuration file location and format.

## Available Tools

The simpletask MCP server exposes 5 tools for task management.

### get

Get complete task specification with pre-computed status summary.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `branch` | string | No | current branch | Branch name (e.g., `feature/auth`) or omit for current git branch |
| `validate` | boolean | No | `false` | Include schema validation result in response |

**Returns:**

A `SimpleTaskGetResponse` object with:

```typescript
{
  spec: {
    schema_version: string
    branch: string
    title: string
    original_prompt: string
    created: string (ISO 8601)
    acceptance_criteria: [
      {
        id: string
        description: string
        completed: boolean
      }
    ]
    constraints?: string[]
    context?: object
    tasks?: [
      {
        id: string
        name: string
        status: "not_started" | "in_progress" | "completed" | "blocked" | "paused"
        goal: string
        done_when?: string[]
        steps?: string[]
        prerequisites?: string[]
        code_examples?: object[]
        files?: string[]
      }
    ]
  }
  file_path: string
  summary: {
    branch: string
    title: string
    overall_status: string
    criteria_total: number
    criteria_completed: number
    tasks_total: number
    tasks_completed: number
    tasks_in_progress: number
    tasks_not_started: number
    tasks_blocked: number
    tasks_paused: number
  }
  validation?: {
    valid: boolean
    errors: string[]
  }
}
```

**Example usage:**

```python
# Get current branch's task
result = simpletask_get()

# Get specific branch's task
result = simpletask_get(branch="feature/auth")

# Include validation
result = simpletask_get(validate=True)
```

**AI prompts:**
- "What task am I working on?"
- "Show me the acceptance criteria for this task"
- "What's the status of the feature/auth task?"
- "Validate the current task file"

### list

List all task file branch names in the project.

**Parameters:** None

**Returns:**

Array of branch name strings:

```typescript
string[]  // ["feature/auth", "bugfix/issue-123", "refactor/cleanup"]
```

**Example usage:**

```python
# List all tasks
branches = simpletask_list()
```

**AI prompts:**
- "List all tasks in this project"
- "What tasks are available?"
- "Show me all branches with task files"

### new

Create a new task file without creating a git branch.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `branch` | string | Yes | - | Branch/task identifier (e.g., `feature/user-auth`) |
| `title` | string | Yes | - | Human-readable task title |
| `prompt` | string | Yes | - | Original user prompt/request |
| `criteria` | array | No | placeholder | List of acceptance criteria descriptions |

**Returns:**

A `SimpleTaskGetResponse` object with the created spec and summary.

**Example usage:**

```python
# Create task with criteria
result = simpletask_new(
    branch="feature/user-auth",
    title="Add user authentication",
    prompt="Implement JWT-based auth with login/logout",
    criteria=[
        "Users can register with email and password",
        "Users can log in and receive JWT token",
        "Protected routes require valid JWT"
    ]
)

# Create task with placeholder criterion
result = simpletask_new(
    branch="bugfix/login-error",
    title="Fix login error handling",
    prompt="Login should show error message on invalid credentials"
)
```

**AI prompts:**
- "Create a new task for user authentication"
- "Start a task for fixing the login bug"
- "Set up a new feature task for notifications"

### task

Manage implementation tasks (add, update, remove).

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `action` | string | Yes | - | Operation: `add`, `update`, or `remove` |
| `branch` | string | No | current branch | Branch name or omit for current git branch |
| `task_id` | string | Conditional | - | Task ID (required for update/remove, e.g., `T001`) |
| `name` | string | Conditional | - | Task name (required for add) |
| `goal` | string | No | - | Task goal/description |
| `status` | string | No | - | Status for update: `not_started`, `in_progress`, `completed`, `blocked`, `paused` |
| `steps` | list[str] | No | `["To be defined"]` | Task implementation steps (for add/update) |
| `done_when` | list[str] | No | `null` | Completion verification conditions (for add/update) |
| `prerequisites` | list[str] | No | `null` | Prerequisite task IDs (for add/update) |
| `files` | list[dict] | No | `null` | Files to modify, each with `path` and `action` fields (for add/update) |
| `code_examples` | list[dict] | No | `null` | Code examples with `language`, `description`, and `code` fields (for add/update) |

**Returns:**

A `SimpleTaskGetResponse` object with the updated spec and summary.

**Example usage:**

```python
# Add a new task with all fields
result = simpletask_task(
    action="add",
    name="Create User model",
    goal="Define database schema for user accounts",
    steps=["Define User class", "Add fields", "Add validation"],
    done_when=["Model passes tests", "No mypy errors"],
    prerequisites=["T001"],  # Depends on task T001
    files=[
        {"path": "src/models/user.py", "action": "create"},
        {"path": "tests/test_user.py", "action": "create"},
    ],
    code_examples=[
        {
            "language": "python",
            "description": "Follow this Pydantic pattern",
            "code": "class BaseModel:\n    model_config = {'extra': 'forbid'}",
        }
    ],
)

# Add a simple task (only required fields)
result = simpletask_task(
    action="add",
    name="Create User model",
    goal="Define database schema for user accounts"
)

# Update task status
result = simpletask_task(
    action="update",
    task_id="T001",
    status="completed"
)

# Update task fields including steps and done_when
result = simpletask_task(
    action="update",
    task_id="T001",
    name="Updated task name",
    goal="Updated description",
    steps=["New step 1", "New step 2"],
    done_when=["Updated condition"],
)

# Remove task
result = simpletask_task(
    action="remove",
    task_id="T001"
)
```

**Batch operations example:**

```python
# Batch operation with full task definitions
result = simpletask_task(
    action="batch",
    operations=[
        {
            "op": "add",
            "name": "Setup database",
            "goal": "Configure database connection",
            "steps": ["Install dependencies", "Configure settings"],
            "done_when": ["Connection works"],
            "files": [{"path": "config/db.py", "action": "create"}],
        },
        {
            "op": "add",
            "name": "Create models",
            "goal": "Define data models",
            "prerequisites": ["T001"],  # Depends on first task
            "files": [{"path": "models/user.py", "action": "create"}],
        },
        {
            "op": "update",
            "task_id": "T003",
            "status": "completed",
        },
    ],
)
# Returns: {"success": true, "new_item_ids": ["T001", "T002"], ...}
```

**AI prompts:**
- "Add a task for setting up the database"
- "Mark task T001 as completed"
- "Update T002 status to in progress"
- "Remove task T003"

### criteria

Manage acceptance criteria (add, complete, remove).

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `action` | string | Yes | - | Operation: `add`, `complete`, or `remove` |
| `branch` | string | No | current branch | Branch name or omit for current git branch |
| `criterion_id` | string | Conditional | - | Criterion ID (required for complete/remove, e.g., `AC1`) |
| `description` | string | Conditional | - | Description (required for add) |
| `completed` | boolean | No | `true` | Completion status for `complete` action |

**Returns:**

A `SimpleTaskGetResponse` object with the updated spec and summary.

**Example usage:**

```python
# Add a new criterion
result = simpletask_criteria(
    action="add",
    description="Users can reset forgotten passwords"
)

# Mark criterion as completed
result = simpletask_criteria(
    action="complete",
    criterion_id="AC2"
)

# Mark criterion as incomplete
result = simpletask_criteria(
    action="complete",
    criterion_id="AC2",
    completed=False
)

# Remove criterion
result = simpletask_criteria(
    action="remove",
    criterion_id="AC3"
)
```

**AI prompts:**
- "Add a criterion for error handling"
- "Mark AC1 as completed"
- "Complete the first acceptance criterion"
- "Remove criterion AC3"

## Usage Examples

### Example 1: Understanding Task Context

**Scenario:** You start working on a task and want the AI to understand what you're building.

**User:**
```
"What am I working on?"
```

**AI workflow:**
1. Calls `simpletask_get()` to get current branch's task
2. Reads `spec.title`, `spec.original_prompt`, `spec.acceptance_criteria`
3. Responds with summary of task goals and requirements

**AI response:**
```
You're working on "Add user authentication" (feature/auth).

Original requirements:
- Users should be able to log in with email and password

Acceptance criteria:
✓ AC1: Users can log in with email and password (completed)
○ AC2: Invalid credentials show error message (pending)
○ AC3: Sessions persist across browser restarts (pending)

Status: 1/3 criteria complete (in progress)

Constraints:
- Use existing auth library
- Follow security best practices
```

### Example 2: Checking Progress

**Scenario:** You want to know how much work is left on the current task.

**User:**
```
"What's the status of this task? How many tasks are left?"
```

**AI workflow:**
1. Calls `simpletask_get()` to get task with summary
2. Reads `summary` field with pre-computed counts
3. Responds with progress breakdown

**AI response:**
```
Task: "Add user authentication" (feature/auth)
Overall status: in_progress

Progress:
- Acceptance Criteria: 1/3 completed (33%)
- Implementation Tasks: 5/8 completed (63%)

Task breakdown:
✓ Completed: 5 tasks
⚙ In progress: 1 task (T006: Add session middleware)
○ Not started: 2 tasks
⛔ Blocked: 0 tasks

You're making good progress! Focus on completing T006, then tackle the 2 remaining tasks.
```

### Example 3: Creating a New Task

**Scenario:** You want to start working on a new feature.

**User:**
```
"Create a task for adding email notifications"
```

**AI workflow:**
1. Calls `simpletask_new()` to create task file
2. Returns created spec with summary
3. Responds with confirmation and next steps

**AI response:**
```
Created task file: .tasks/feature-email-notifications.yml

Task: "Add email notifications"
Branch: feature/email-notifications

Acceptance criteria:
○ AC1: Define acceptance criteria (placeholder)

Next steps:
1. Create the git branch: git checkout -b feature/email-notifications
2. Add specific acceptance criteria
3. Break down into implementation tasks

Would you like me to add acceptance criteria or implementation tasks?
```

**User:**
```
"Add criteria: users receive email on signup, emails have unsubscribe link"
```

**AI workflow:**
1. Calls `simpletask_criteria(action="add", ...)` twice
2. Returns updated spec

**AI response:**
```
Added 2 acceptance criteria:

○ AC2: Users receive email on signup
○ AC3: Emails have unsubscribe link

Current progress: 0/3 criteria complete
```

### Example 4: Managing Task Progress

**Scenario:** You completed a task and want to update its status.

**User:**
```
"I finished the login form, mark T001 as done"
```

**AI workflow:**
1. Calls `simpletask_task(action="update", task_id="T001", status="completed")`
2. Returns updated summary
3. Suggests next steps

**AI response:**
```
✓ Marked T001 as completed

Task: "Add user authentication" (feature/auth)

Progress update:
- Tasks: 6/8 completed (was 5/8)
- Criteria: 1/3 completed

Remaining tasks:
○ T007: Add password reset flow (not_started)
○ T008: Write integration tests (not_started)

Would you like to start working on T007?
```

**User:**
```
"Yes, and also mark AC1 as complete since login works now"
```

**AI workflow:**
1. Calls `simpletask_task(action="update", task_id="T007", status="in_progress")`
2. Calls `simpletask_criteria(action="complete", criterion_id="AC1")`
3. Returns updated summary

**AI response:**
```
Updated task status:

✓ AC1: Users can log in with email and password (completed)
⚙ T007: Add password reset flow (in_progress)

Progress: 2/3 criteria complete, 6/8 tasks complete

Ready to work on T007. The task goal is: "Allow users to reset forgotten passwords via email link"
```

## Troubleshooting

### Server Not Responding

**Symptoms:**
- AI says "Cannot connect to simpletask"
- "MCP server error: connection refused"

**Solutions:**

1. **Verify simpletask is installed:**
   ```sh
   simpletask --version
   ```

2. **Check configuration path:**
   ```sh
   which simpletask
   ```
   Update your editor config with the full path if needed.

3. **Test server manually:**
   ```sh
   simpletask serve
   ```
   Server should start without errors. Press Ctrl+C to stop.

4. **Check permissions:**
   ```sh
   ls -la $(which simpletask)
   ```
   Executable bit should be set (`-rwxr-xr-x`).

5. **Restart your AI editor** after configuration changes.

### Tool Not Found

**Symptoms:**
- AI says "I don't have access to simpletask tools"
- "Unknown tool: simpletask_get"

**Solutions:**

1. **Verify configuration syntax:**
   - Check JSON is valid (use `jq` or a JSON validator)
   - Ensure `"command"` field is a proper array format: `["simpletask", "serve"]`

2. **Check server is configured:**
   Look for `"simpletask"` in your editor's MCP servers config.

3. **Restart editor completely:**
   Quit and relaunch (don't just reload window).

4. **Check editor logs:**
   - OpenCode: Help → Toggle Developer Tools → Console

### Permission Denied

**Symptoms:**
- "Permission denied: simpletask"
- "Cannot execute: /path/to/simpletask"

**Solutions:**

1. **Make simpletask executable:**
   ```sh
   chmod +x $(which simpletask)
   ```

2. **Check virtualenv activation:**
   If using virtualenv, ensure the correct Python environment is active:
   ```sh
   which python
   # Should point to virtualenv
   ```

3. **Use absolute path:**
   In your config, use full path instead of just `"simpletask"`:
   ```json
   "command": ["/home/user/.local/share/uv/tools/simpletask/bin/simpletask", "serve"]
   ```

### Invalid Branch Name

**Symptoms:**
- "FileNotFoundError: Task file not found"
- "Branch 'feature/../../etc/passwd' not found"

**Solutions:**

1. **Check branch exists:**
   ```sh
   git branch
   ```

2. **Verify task file exists:**
   ```sh
   ls .tasks/
   ```
   Remember: `feature/auth` → `.tasks/feature-auth.yml`

3. **Use correct branch format:**
   - ✓ Good: `feature/auth`, `bugfix/issue-123`
   - ✗ Bad: `../etc/passwd`, `/absolute/path`

4. **Create task file if missing:**
   ```sh
   simpletask new "Task title" --branch feature/auth
   ```

### Validation Errors

**Symptoms:**
- `simpletask_get(validate=True)` returns `valid: false`
- Errors about missing fields or invalid values

**Solutions:**

1. **Read error messages carefully:**
   Each error indicates the field and problem.

2. **Check schema version:**
   ```yaml
   schema_version: "1.0"  # Must be "1.0"
   ```

3. **Validate required fields:**
   Required: `schema_version`, `branch`, `title`, `original_prompt`, `created`, `acceptance_criteria`

4. **Check enum values:**
   - Status: `not_started`, `in_progress`, `completed`, `blocked`, `paused`
   - No typos or custom values

5. **Validate with CLI:**
   ```sh
   simpletask schema validate
   ```

6. **Reference schema:**
   See [Schema Reference](SCHEMA.md) for complete schema documentation.

## Technical Details

**Transport:** stdio (standard input/output)

**Protocol:** Model Context Protocol v1.0

**Response format:** JSON (Pydantic models serialized to JSON)

**Security:**
- Path traversal protection via branch name normalization
- Branch names sanitized: `../../etc/passwd` → `----etc-passwd.yml`
- All paths constrained to `.tasks/` directory
- No arbitrary file system access

**Performance:**
- Pre-computed status summaries (no repeated calculations)
- Optional validation (default: off to reduce overhead)
- File I/O only when tools are called
- No caching (always returns current state)

**Error handling:**
- `FileNotFoundError`: Task file doesn't exist for branch
- `InvalidTaskFileError`: YAML is malformed or invalid
- `ValueError`: Not in a git repository or invalid parameters

**Limitations:**
- Cannot create git branches (use git CLI)
- No real-time file watching (must call tools to get updates)

---

For developer/technical documentation, see [AGENTS.md](../AGENTS.md#mcp-server).

For general simpletask usage, see [README.md](../README.md).
