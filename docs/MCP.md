# MCP Integration Guide

This guide covers how to integrate simpletask with AI editors using the Model Context Protocol (MCP).

## Table of Contents

- [What is MCP?](#what-is-mcp)
- [Why Use MCP with simpletask?](#why-use-mcp-with-simpletask)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
  - [OpenCode](#opencode)
  - [Qwen-CLI](#qwen-cli)
  - [Claude Desktop](#claude-desktop)
  - [Other MCP Clients](#other-mcp-clients)
- [Available Tools](#available-tools)
  - [simpletask_get](#simpletask_get)
  - [simpletask_list](#simpletask_list)
- [Usage Examples](#usage-examples)
  - [Example 1: Understanding Task Context](#example-1-understanding-task-context)
  - [Example 2: Checking Progress](#example-2-checking-progress)
  - [Example 3: Multi-Branch Development](#example-3-multi-branch-development)
  - [Example 4: Validating Task Files](#example-4-validating-task-files)
- [Troubleshooting](#troubleshooting)
  - [Server Not Responding](#server-not-responding)
  - [Tool Not Found](#tool-not-found)
  - [Permission Denied](#permission-denied)
  - [Invalid Branch Name](#invalid-branch-name)
  - [Validation Errors](#validation-errors)
- [Technical Details](#technical-details)

## What is MCP?

The Model Context Protocol (MCP) is an open standard for connecting AI assistants to external tools and data sources. MCP enables AI editors to:

- Query structured data from external tools
- Execute operations through well-defined APIs
- Receive typed responses instead of parsing text output

simpletask implements an MCP server that exposes task file operations, allowing AI assistants to read task definitions, check completion status, and understand project requirements without requiring users to manually copy/paste content.

## Why Use MCP with simpletask?

**Without MCP:**
- AI needs task content copy/pasted into chat
- Status updates require manual CLI commands → copy output
- AI cannot independently check task progress
- Responses are unstructured CLI text

**With MCP:**
- AI automatically queries task files when needed
- Structured JSON responses with typed data
- AI can check status, criteria, and constraints independently
- Pre-computed summaries (no arithmetic needed)
- Better context awareness during development

**Use Cases:**
- AI understands acceptance criteria before writing code
- AI checks which tasks are completed/in-progress
- AI reads constraints to avoid invalid implementations
- AI validates task files during development
- AI switches between tasks in multi-branch workflows

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
- Linux/macOS: `~/.config/opencode/settings.json`
- Windows: `%APPDATA%\opencode\settings.json`

**Add this configuration:**

```json
{
  "mcpServers": {
    "simpletask": {
      "command": "simpletask",
      "args": ["serve"]
    }
  }
}
```

**If simpletask is installed in a virtualenv**, use the full path:

```json
{
  "mcpServers": {
    "simpletask": {
      "command": "/path/to/venv/bin/simpletask",
      "args": ["serve"]
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

You should see `simpletask_get` and `simpletask_list` in the response.

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

### Claude Desktop

Claude Desktop supports MCP servers on macOS, Windows, and Linux.

**Configuration file location:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Add this configuration:**

```json
{
  "mcpServers": {
    "simpletask": {
      "command": "simpletask",
      "args": ["serve"]
    }
  }
}
```

**If simpletask is installed in a virtualenv**, use the full path:

```json
{
  "mcpServers": {
    "simpletask": {
      "command": "/home/user/.local/share/uv/tools/simpletask/bin/simpletask",
      "args": ["serve"]
    }
  }
}
```

**Restart Claude Desktop** after adding the configuration.

**Verify connection:**
Ask Claude:
```
"What MCP tools do you have access to?"
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

The simpletask MCP server exposes 2 read-only tools for querying task information.

### simpletask_get

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
    status: "not_started" | "in_progress" | "completed" | "blocked"
    created: string (ISO 8601)
    updated: string (ISO 8601)
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
        status: "not_started" | "in_progress" | "completed" | "blocked"
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

### simpletask_list

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

### Example 3: Multi-Branch Development

**Scenario:** You're working on multiple features and want to switch context.

**User:**
```
"List all my active tasks"
```

**AI workflow:**
1. Calls `simpletask_list()` to get all branch names
2. Optionally calls `simpletask_get(branch=...)` for each to get status
3. Responds with task list

**AI response:**
```
Active tasks in this project:

1. feature/auth - "Add user authentication" (in_progress)
   - 1/3 criteria complete, 5/8 tasks done

2. feature/notifications - "Email notifications" (not_started)
   - 0/4 criteria complete, 0/5 tasks done

3. bugfix/login-redirect - "Fix login redirect loop" (completed)
   - 2/2 criteria complete, 3/3 tasks done

You're currently on: feature/auth
```

**User:**
```
"Switch to the notifications task and tell me what needs to be done"
```

**AI workflow:**
1. Suggests: `git checkout feature/notifications`
2. Calls `simpletask_get(branch="feature/notifications")`
3. Summarizes task requirements

### Example 4: Validating Task Files

**Scenario:** You manually edited a task YAML file and want to verify it's valid.

**User:**
```
"Validate the current task file"
```

**AI workflow:**
1. Calls `simpletask_get(validate=True)`
2. Checks `validation.valid` field
3. Reports errors if any

**AI response (valid):**
```
✓ Task file is valid!

File: .tasks/feature-auth.yml
Schema version: 1.0
All required fields present, no validation errors.
```

**AI response (invalid):**
```
✗ Task file validation failed

File: .tasks/feature-auth.yml

Errors:
1. Missing required field: acceptance_criteria
2. Invalid status value: "done" (must be one of: not_started, in_progress, completed, blocked)
3. Task T003: Invalid prerequisites format (expected array, got string)

Fix these errors and validate again.
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
   - Ensure `"command"` and `"args"` fields are correct

2. **Check server is configured:**
   Look for `"simpletask"` in your editor's MCP servers config.

3. **Restart editor completely:**
   Quit and relaunch (don't just reload window).

4. **Check editor logs:**
   - OpenCode: Help → Toggle Developer Tools → Console
   - Claude Desktop: Check application logs

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
   "command": "/home/user/.local/share/uv/tools/simpletask/bin/simpletask"
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
   Required: `schema_version`, `branch`, `title`, `original_prompt`, `status`, `created`, `updated`, `acceptance_criteria`

4. **Check enum values:**
   - Status: `not_started`, `in_progress`, `completed`, `blocked`
   - No typos or custom values

5. **Validate with CLI:**
   ```sh
   simpletask schema validate
   ```

6. **Reference schema:**
   See [schema/README.md](../schema/README.md) for complete schema documentation.

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
- Read-only operations (Phase 1)
- Cannot create or modify task files via MCP
- Cannot create git branches
- No real-time file watching (must call tools to get updates)

**Future enhancements (Phase 2):**
- Write operations: `simpletask_new`, `simpletask_task_add`, etc.
- Real-time updates via MCP notifications
- Batch operations for multi-task queries

---

For developer/technical documentation, see [AGENTS.md](../AGENTS.md#mcp-server).

For general simpletask usage, see [README.md](../README.md).
