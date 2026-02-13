# AGENTS.md - simpletask

AI-friendly task definition manager for branch-based development workflows.

## Tech Stack

| Category | Technology | Notes |
|----------|------------|-------|
| Language | Python 3.11+ | Required minimum version |
| CLI Framework | Typer | Type-hint based CLI with Rich integration |
| Output | Rich | Terminal formatting and colors |
| Data Models | Pydantic v2 | Strict validation with `extra="forbid"` |
| YAML | PyYAML | Task file parsing |
| Git | GitPython | Branch operations and git integration |
| Schema | jsonschema | YAML validation against JSON schema |

### Dev Dependencies

| Tool | Purpose |
|------|---------|
| pytest + pytest-cov | Testing with coverage |
| black | Code formatting (100 char line length) |
| ruff | Linting |
| mypy | Static type checking |

## Git Hooks

Development hooks enforce code quality. Install them after cloning:

```bash
./scripts/install-hooks.sh
```

| Hook | Purpose |
|------|---------|
| `pre-commit` | Verifies version bump when code changes |
| `commit-msg` | Enforces [Conventional Commits](https://conventionalcommits.org/) format |
| `pre-push` | Runs pytest before push |

### Bypassing Hooks

```bash
git commit --no-verify    # Skip pre-commit and commit-msg
git push --no-verify      # Skip pre-push
```

### Conventional Commit Types

| Type | Use for |
|------|---------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no code change |
| `refactor` | Code restructuring |
| `perf` | Performance improvement |
| `test` | Adding/updating tests |
| `build` | Build system changes |
| `ci` | CI configuration |
| `chore` | Maintenance tasks |

### Commit Examples

```bash
feat: add git hooks for development workflow
fix(cli): resolve crash on empty task file
docs: update README with hook installation
refactor(core): simplify yaml parsing logic
test: add unit tests for version validation
```

## Project Structure

```
cli/simpletask/           # Main CLI package
├── __init__.py
├── main.py               # CLI entry point, app initialization
├── commands/             # CLI command groups
│   ├── criteria/         # Acceptance criteria commands
│   │   └── commands.py
│   ├── schema/           # Schema generation commands
│   │   └── commands.py
│   └── task/             # Task management commands
│       └── commands.py
├── core/                 # Core business logic
│   ├── models.py         # Pydantic models (Task, Criterion, etc.)
│   ├── git.py            # Git operations
│   ├── yaml_parser.py    # YAML file handling
│   ├── schema_generator.py
│   └── task_file_manager.py
├── utils/
│   └── console.py        # Rich console output utilities
├── mcp/                  # MCP server integration
│   ├── server.py         # Server implementation
│   └── models.py         # MCP-specific models
├── templates/            # AI workflow templates
│   ├── opencode/         # OpenCode slash commands (.md)
│   │   ├── simpletask.plan.md
│   │   ├── simpletask.split.md      # NEW: Task splitting command
│   │   ├── simpletask.implement.md
│   │   ├── simpletask.review.md
│   │   └── agents/                  # OpenCode agents (.md)
│   │       └── simpletask-plan.md   # NEW: Auto-planning agent
│   ├── qwen/             # Qwen slash commands (.md)
│   │   ├── simpletask.plan.md
│   │   ├── simpletask.split.md      # NEW: Task splitting command
│   │   ├── simpletask.implement.md
│   │   └── simpletask.review.md
│   └── gemini/           # Gemini CLI slash commands (.toml)
│       ├── simpletask.plan.toml
│       ├── simpletask.split.toml    # NEW: Task splitting command
│       ├── simpletask.implement.toml
│       └── simpletask.review.toml
└── schema/
    └── task_schema.json  # JSON schema for validation

schema/                   # Schema documentation
├── README.md
└── examples/

.tasks/                   # Task YAML files (git-ignored, NOT part of project deliverable)
└── *.yml                 # Normalized branch names (feature/auth → feature-auth.yml)

tests/                    # Test suite
├── conftest.py           # Shared fixtures
├── unit/                 # Unit tests
└── integration/          # Integration tests
```

## Branch Name Normalization

Task files are stored in `.tasks/` with normalized filenames derived from branch names:

- **Branch:** `feature/user-auth` → **File:** `.tasks/feature-user-auth.yml`
- **Branch:** `bugfix/issue-123` → **File:** `.tasks/bugfix-issue-123.yml`

The `normalize_branch_name()` function in `cli/simpletask/core/project.py` converts:
- Slashes (`/`) → Hyphens (`-`)
- Special characters → Hyphens
- Uppercase → Lowercase
- Unicode → ASCII
- Double dots (`..`) → Double hyphens (`--`) for security

**Important:** Always use `simpletask` CLI commands instead of manually constructing `.tasks/` paths in bash. The CLI handles normalization automatically.

## AI Workflow Templates (Slash Commands)

simpletask provides AI-assisted workflow templates (slash commands) for OpenCode, Qwen CLI, and Gemini CLI. These templates guide AI models through structured development workflows.

### Available Slash Commands

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/simpletask.plan` | Create lightweight task specification from feature description | Start of a new feature branch |
| `/simpletask.split` | Analyze codebase, enrich tasks with design guidance, and split complex tasks into atomic subtasks | After planning, before implementation |
| `/simpletask.implement` | Execute tasks step-by-step with best practices | Implementation phase |
| `/simpletask.review` | Review completed tasks and generate summary | After all tasks completed |

### `/simpletask.split` - Task Splitting

**Purpose:** Analyzes the codebase to populate design guidance (patterns, constraints, security considerations, quality requirements), then ensures AI models have minimal cognitive load by splitting complex tasks into ultra-atomic units (1-2 steps, 5-10 minutes each).

**Splitting Criteria:**

A task is split if it has ANY of:
- **>2 steps** in the `steps` array
- **>1 file** in the `files` array
- **>3 conditions** in `done_when` array
- **>100 characters** in goal description

**Output:**
- Removes complex tasks
- Adds atomic subtasks (1-2 steps each)
- Renumbers all task IDs sequentially (T001, T002, T003...)
- Updates all prerequisite references

**Example Workflow:**

```bash
# 1. Plan feature (creates lightweight task file with criteria and basic tasks)
/simpletask.plan "Add user authentication with JWT"

# 2. Analyze codebase and split complex tasks into atomic units
# This step populates design guidance (patterns, constraints, security) and splits tasks
/simpletask.split

# 3. Implement atomic tasks
/simpletask.implement

# 4. Review completed work
/simpletask.review
```

**Splitting Patterns:**

The split command recognizes and handles these patterns:

1. **Model/Class Creation** - Split into: file creation → fields → methods → constraints
2. **API Endpoint** - Split into: file → skeleton → validation → logic → token generation → error handling
3. **Multi-File Feature** - Split by file: one subtask per file operation
4. **Testing** - Split by test case: one subtask per test
5. **Configuration + Implementation** - Split into: config → setup → implementation → integration

**Target Metrics:**
- 1-2 steps per subtask
- 5-10 minutes completion time
- No ambiguity or decisions left to implementer

### Template Installation

Install templates for your AI editor:

```bash
# Install for all editors (OpenCode, Qwen, Gemini)
simpletask ai install

# Install for specific editor only
simpletask ai install --opencode
simpletask ai install --qwen
simpletask ai install --gemini

# Install to local directory (.opencode/commands in project)
simpletask ai install --local

# List installed templates
simpletask ai list
```

### Template Files

**OpenCode** (Markdown with YAML frontmatter):
- Commands: `cli/simpletask/templates/opencode/*.md`
  - Installed to: `~/.config/opencode/commands/` or `.opencode/commands/`
- Agents: `cli/simpletask/templates/opencode/agents/*.md`
  - Installed to: `~/.config/opencode/agents/` or `.opencode/agents/`

**Qwen CLI** (Markdown format):
- Commands: `cli/simpletask/templates/qwen/*.md`
  - Installed to: `~/.config/qwen/commands/` or `.qwen/commands/`
- Agents: Not supported (OpenCode-only feature)

**Gemini CLI** (TOML format):
- Commands: `cli/simpletask/templates/gemini/*.toml`
  - Installed to: `~/.gemini/commands/` or `.gemini/commands/`
- Agents: Not supported (OpenCode-only feature)

### AI Agents

Agents are special OpenCode subagents that auto-generate branch names and execute tasks without interactive confirmation. Unlike slash commands which require user confirmation, agents run autonomously when invoked via `@agent-name` or delegated via the `Task()` tool.

**Available Agents:**

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| `simpletask-plan` | Auto-generate branch names and create task specifications | Quickly start planning without confirmation |

**Installation:**

Agents are automatically installed alongside commands when you run:

```bash
simpletask ai install --opencode
```

This installs both:
- Commands to `~/.config/opencode/commands/` (or `.opencode/commands/`)
- Agents to `~/.config/opencode/agents/` (or `.opencode/agents/`)

**Usage in OpenCode:**

```bash
# Invoke agent directly in OpenCode conversation
@simpletask-plan

# Or delegate from parent conversation via Task() tool
# Pass the feature description as context
```

**Key Differences: Agents vs Slash Commands**

| Aspect | Agents | Slash Commands |
|--------|--------|-----------------|
| **Invocation** | `@agent-name` or `Task()` delegation | `/command-name` in OpenCode input |
| **Branch name generation** | Automatic (no user confirmation) | Asks user for branch name |
| **Execution** | Runs autonomously, returns structured output | Interactive, guides user step-by-step |
| **Use case** | Batch automation, programmatic delegation | Interactive exploration and learning |
| **Support** | OpenCode only | OpenCode, Qwen, Gemini |

## Commands

### Earthly Development Environment

**IMPORTANT:** Use Earthly for all development and testing. This ensures a completely isolated, reproducible environment matching CI.

#### Prerequisites

- [Earthly](https://earthly.dev/get-earthly) installed (`earthly --version`)
- Docker running

#### Quick Start

```bash
# Run all tests and quality checks
earthly +all

# Run just tests
earthly +test

# Run just linting
earthly +lint

# Run all quality checks (lint + format + types)
earthly +check

# Interactive development shell
earthly -i +dev
```

#### Available Targets

| Target | Description |
|--------|-------------|
| `+test` | Run pytest with coverage |
| `+lint` | Run ruff linter |
| `+format-check` | Check black formatting |
| `+format` | Fix formatting (black + ruff --fix) |
| `+type-check` | Run mypy type checking |
| `+check` | Run all quality checks |
| `+all` | Run tests + all quality checks |
| `+dev` | Interactive shell for debugging |

#### Testing Local Changes

Your local code is automatically mounted when running Earthly targets:

```bash
# Edit code locally, then test
earthly +test

# Quick lint check after changes
earthly +lint

# Fix formatting issues automatically
earthly +format
```

#### Interactive Development

For exploratory work or debugging:

```bash
# Start interactive shell with all dependencies
earthly -i +dev

# Inside the container:
simpletask --help
pytest tests/unit/test_models.py -v
black .
ruff check .
```

### Development

The simpletask CLI can be tested using Earthly's interactive mode:

```bash
# Start dev shell
earthly -i +dev

# Inside the container, simpletask is available:
simpletask --help
simpletask list
simpletask show <branch-name>
simpletask quality check
simpletask design show
```

### Quality Commands

The `simpletask quality` subcommand group manages quality requirements (linting, type checking, testing, security checks):

```bash
# Show current quality configuration
simpletask quality show

# Run all enabled quality checks
simpletask quality check

# Configure individual quality requirements
simpletask quality set linting --tool ruff --args "check" "."
simpletask quality set testing --tool pytest --min-coverage 80 --timeout 600
simpletask quality set type-checking --tool mypy --args "." --timeout 120
simpletask quality set security --tool bandit --args "-r" "." --timeout 300

# Apply a quality preset (fills gaps only, doesn't overwrite)
simpletask quality preset python
simpletask quality preset typescript
simpletask quality preset --list  # Show available presets

# Available built-in presets:
# - python: ruff, mypy, pytest
# - typescript: eslint, tsc, npm test
# - node: eslint, npm test
# - go: golangci-lint, go test
# - rust: cargo clippy, cargo test
# - java-maven: maven checkstyle, maven test
# - java-gradle: gradle checkstyle, gradle test
```

**Custom Quality Presets:**

You can define custom quality presets in YAML files without modifying source code:

1. **Project-specific presets**: `.simpletask/presets.yaml` (checked into git)
2. **User-specific presets**: `~/.config/simpletask/presets.yaml` (personal config)

Custom presets take precedence over built-in presets with the same name.

**Custom Preset File Format:**

```yaml
# .simpletask/presets.yaml or ~/.config/simpletask/presets.yaml
my-custom-preset:
  linting:
    enabled: true
    tool: ruff
    args: ["check", "src/"]
    timeout: 300
  type_checking:
    enabled: true
    tool: mypy
    args: ["src/", "--strict"]
    timeout: 120
  testing:
    enabled: true
    tool: pytest
    args: ["tests/"]
    min_coverage: 90
    timeout: 600
  security_check:
    enabled: false
    tool: null
    args: []
    timeout: 300

another-preset:
  linting:
    enabled: true
    tool: eslint
    args: [".", "--fix"]
    timeout: 300
  testing:
    enabled: true
    tool: npm
    args: ["test"]
    min_coverage: 75
    timeout: 600
```

**Valid tool names** (from ToolName enum):
- Python: `ruff`, `mypy`, `pytest`, `black`, `pylint`, `bandit`
- TypeScript/Node: `eslint`, `tsc`, `npm`, `yarn`, `jest`
- Go: `go`, `golangci-lint`, `gosec`
- Rust: `cargo`, `clippy`
- Java: `mvn`, `gradle`
- Other: `make`

```bash
# List all available presets (built-in + custom)
simpletask quality preset --list

# Apply custom preset
simpletask quality preset my-custom-preset
```

**Quality Config Structure:**

Quality configurations use structured `tool + args` instead of raw command strings to prevent shell injection:

```yaml
quality_requirements:
  linting:
    enabled: true
    tool: ruff
    args: ["check", "."]
    timeout: 300  # Default: 300 seconds
  type_checking:
    enabled: true
    tool: mypy
    args: ["."]
    timeout: 300
  testing:
    enabled: true
    tool: pytest
    args: ["--cov=cli/simpletask", "--cov-report=term-missing"]
    min_coverage: 80
    timeout: 600  # Longer timeout for tests
  security_check:
    enabled: false
    tool: bandit
    args: ["-r", "."]
    timeout: 300
```

**ToolName Enum** (whitelisted tools for security):
- Python: `ruff`, `mypy`, `pytest`, `black`, `pylint`, `bandit`
- TypeScript/Node: `eslint`, `tsc`, `npm`, `yarn`, `jest`
- Go: `go`, `golangci-lint`, `gosec`
- Rust: `cargo`, `clippy`
- Java: `mvn`, `gradle`
- Other: `make`

### Design Commands

The `simpletask design` subcommand group manages the design section (patterns, references, constraints, security):

```bash
# Show current design section
simpletask design show

# Add patterns to follow
simpletask design set pattern repository
simpletask design set pattern dependency_injection

# Add reference implementations
simpletask design set reference "cli/simpletask/mcp/server.py" "MCP tool pattern to follow"

# Add architectural constraints
simpletask design set constraint "Use Pydantic models with extra='forbid'"
simpletask design set constraint "No shell=True in subprocess calls"

# Add security considerations
simpletask design set security --category input_validation "Validate all user inputs"
simpletask design set security --category input_validation "Use whitelisting for tool execution"

# Set error handling pattern
simpletask design set error-handling exceptions

# Remove design elements
simpletask design remove pattern --index 0  # Remove first pattern
simpletask design remove pattern --all      # Remove all patterns
simpletask design remove reference --index 1
simpletask design remove error-handling     # Remove error handling pattern
simpletask design remove --all              # Clear entire design section
```

**Design Section Structure:**

```yaml
design:
  patterns:
    - repository
    - dependency_injection
  reference_implementations:
    - path: "cli/simpletask/mcp/server.py"
      reason: "MCP tool pattern to follow"
  architectural_constraints:
    - "Use Pydantic models with extra='forbid'"
    - "No shell=True in subprocess calls"
  security:
    - category: input_validation
      description: "Validate all user inputs"
    - category: input_validation
      description: "Use whitelisting for tool execution"
  error_handling: exceptions
```

### Testing

```bash
# Run all tests
earthly +test

# Run just tests and quality checks
earthly +all
```

For interactive testing/debugging:

```bash
# Start dev shell
earthly -i +dev

# Inside the container:
pytest
pytest --cov=cli/simpletask --cov-report=term-missing
pytest tests/unit/test_models.py
pytest tests/unit/test_models.py::TestGetNextCriterionId
pytest -v
```

### Code Quality

```bash
# Run all quality checks
earthly +check

# Run individual checks
earthly +lint          # ruff check .
earthly +format-check  # black --check .
earthly +type-check    # mypy cli/simpletask

# Fix formatting issues
earthly +format        # black . && ruff check --fix .
```

For interactive fixing:

```bash
earthly -i +dev

# Inside container:
black .                    # Format code
ruff check .               # Lint code  
ruff check --fix .         # Auto-fix lint issues
mypy cli/simpletask        # Type checking
```

## MCP Server

simpletask includes a Model Context Protocol (MCP) server for AI editor integration. The server exposes task file operations as tools that AI assistants can use to read and query task definitions.

### Starting the Server

```bash
simpletask serve
```

This starts the MCP server on stdio transport. The server runs until the client disconnects or the process is terminated.

### Configuration

Configure your AI editor to connect to the simpletask MCP server.

#### OpenCode Configuration

Add to `~/.config/opencode/opencode.json`:

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

**Note:** If simpletask is installed in a virtualenv, use the full path to the executable:

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

**Note:** For Qwen CLI and Gemini CLI configuration, see [docs/MCP.md](docs/MCP.md).

### Breaking Changes in v0.18.0

#### MCP Tools No Longer Accept `branch` Parameter

**Affected tools:** `get`, `task`, `criteria`, `quality`, `design`

**What changed:** These MCP tools no longer accept a `branch` parameter. They always auto-detect the current git branch.

**Why:** MCP clients sometimes incorrectly passed the string `"None"` instead of `null`, causing errors. Removing the parameter entirely fixes this at the API level.

**Migration:**

Before (v0.17.x):
```python
simpletask_get(branch=None)  # or branch="feature/xyz"
simpletask_task(action="add", branch=None, name="Task")
simpletask_criteria(action="add", branch=None, description="Criterion")
```

After (v0.18.0):
```python
simpletask_get()  # Always uses current git branch
simpletask_task(action="add", name="Task")
simpletask_criteria(action="add", description="Criterion")
```

**Note:** CLI commands still support the `--branch` flag for flexibility:
```bash
simpletask task list --branch feature/other-branch
```

### Available Tools

The MCP server exposes 10 tools for task management:

**Note:** MCP clients automatically prefix tool names with the server name. When invoked through an MCP client (like OpenCode), these tools become `simpletask_get`, `simpletask_list`, `simpletask_new`, `simpletask_task`, `simpletask_criteria`, `simpletask_quality`, `simpletask_design`, `simpletask_note`, `simpletask_constraint`, and `simpletask_context`.

| Tool | Description | Parameters |
|------|-------------|------------|
| `get` | Get complete task specification with status summary | `validate` (bool, optional): Include schema validation (default: false) |
| `list` | List all task file branch names in the project | None |
| `new` | Create a new task file | `branch` (str): Branch identifier<br>`title` (str): Task title<br>`prompt` (str): Original user request<br>`criteria` (list[str] \| None, optional): Acceptance criteria |
| `task` | Manage implementation tasks (add/update/remove/get/batch) | `action` (str): 'add', 'update', 'remove', 'get', or 'batch'<br>`task_id` (str, optional): Task ID (required for update/remove/get)<br>`name` (str, optional): Task name (required for add)<br>`goal` (str, optional): Task goal/description<br>`status` (str, optional): Status for update ('not_started', 'in_progress', 'completed', 'blocked', 'paused')<br>`steps` (list[str] \| None, optional): Task steps for add action. None or [] adds placeholder ['To be defined']<br>`done_when` (list[str] \| None, optional): Completion verification conditions<br>`prerequisites` (list[str] \| None, optional): Prerequisite task IDs<br>`files` (list[dict] \| None, optional): Files to create/modify/delete<br>`code_examples` (list[dict] \| None, optional): Code patterns to follow<br>`operations` (list[dict], optional): List of BatchTaskOperation dicts (required for batch action) |
| `criteria` | Manage acceptance criteria (add/complete/remove/get/update) | `action` (str): 'add', 'complete', 'remove', 'get', or 'update'<br>`criterion_id` (str, optional): Criterion ID (required for complete/remove/get/update)<br>`description` (str, optional): Description (required for add/update)<br>`completed` (bool, optional): Completion status for 'complete' (default: true) |
| `quality` | Manage quality requirements (check/set/get/preset) | `action` (str): 'check', 'set', 'get', or 'preset'<br>`config_type` (str, optional): 'linting', 'type-checking', 'testing', or 'security' (for set action)<br>`tool` (str, optional): Tool name from ToolName enum (for set action)<br>`args` (str, optional): Comma-separated tool arguments (for set action)<br>`enabled` (bool, optional): Enable/disable check (for set action)<br>`min_coverage` (int, optional): Minimum coverage % (for testing config only)<br>`timeout` (int, optional): Timeout in seconds (default: 300)<br>`preset_name` (str, optional): Preset name (for preset action) |
| `design` | Manage design section (set/get/remove) | `action` (str): 'set', 'get', or 'remove'<br>`field` (str, optional): Field to modify: 'pattern', 'reference', 'constraint', 'security', 'error-handling' (for set/remove)<br>`value` (str, optional): Value to add (for set action)<br>`reason` (str, optional): Reason for reference (required when field='reference')<br>`index` (int, optional): Index to remove (for remove action on list fields)<br>`all` (bool, optional): Remove all items or entire section (for remove action) |
| `note` | Manage notes for root-level and task-level | `action` (str): 'add', 'remove', or 'list'<br>`content` (str, optional): Note content (required for add)<br>`task_id` (str, optional): Task ID for task-level notes; if omitted, operates on root notes<br>`index` (int, optional): Note index to remove (0-based, required for remove unless all=True)<br>`all` (bool, optional): Remove all notes (for remove action)<br>`root_only` (bool, optional): Only return root notes (for list action) |
| `constraint` | Manage implementation constraints (add/remove/list) | `action` (str): 'add', 'remove', or 'list'<br>`value` (str, optional): Constraint text (required for add)<br>`index` (int, optional): Constraint index to remove (0-based, required for remove unless all=True)<br>`all` (bool, optional): Remove all constraints (for remove action) |
| `context` | Manage context key-value pairs (set/remove/show) | `action` (str): 'set', 'remove', or 'show'<br>`key` (str, optional): Context key (required for set/remove)<br>`value` (str, optional): Context value (required for set)<br>`all` (bool, optional): Remove all context entries (for remove action) |

### Tool Details

#### get

Returns enriched task data with pre-computed status counts:

**Parameters:**
- `validate` (optional): Whether to include schema validation result. Default is `false` to reduce overhead.

**Note:** This tool always uses the current git branch. Branch auto-detection prevents MCP clients from incorrectly passing string values like "None".

**Returns:** `SimpleTaskGetResponse` with:
- `spec`: Full `SimpleTaskSpec` (branch, title, acceptance_criteria, tasks, etc.)
- `file_path`: Path to task YAML file
- `summary`: Pre-computed `StatusSummary` with:
  - `branch`, `title`
  - `overall_status`: Computed from task states (blocked > paused > in_progress > completed > not_started)
  - `criteria_total`, `criteria_completed`
  - `tasks_total`, `tasks_completed`, `tasks_in_progress`, `tasks_not_started`, `tasks_blocked`, `tasks_paused`
- `validation` (optional): `ValidationResult` with `valid` (bool) and `errors` (list)

**Example Response Structure:**

```json
{
  "spec": {
    "branch": "feature/mcp-server",
    "title": "Add MCP server support",
    "acceptance_criteria": [...],
    "tasks": [...]
  },
  "file_path": ".tasks/feature-mcp-server.yml",
  "summary": {
    "branch": "feature/mcp-server",
    "title": "Add MCP server support",
    "overall_status": "in_progress",
    "criteria_total": 8,
    "criteria_completed": 0,
    "tasks_total": 11,
    "tasks_completed": 5,
    "tasks_in_progress": 1,
    "tasks_not_started": 5,
    "tasks_blocked": 0,
    "tasks_paused": 0
  },
  "validation": null
}
```

#### list

Returns list of all task branch names (original names, not normalized filenames).

**Returns:** `list[str]` - Branch names sorted alphabetically

**Example:**

```json
[
  "feature/mcp-server-support",
  "bugfix/issue-123",
  "refactor/clean-models"
]
```

#### new

Creates a new task file without creating a git branch (atomic MCP operation).

**Parameters:**
- `branch`: Branch/task identifier (e.g., 'feature/user-auth')
- `title`: Human-readable task title
- `prompt`: Original user prompt/request that led to task creation
- `criteria` (optional): List of acceptance criteria descriptions. If `None` or empty list `[]`, adds a single placeholder criterion. If provided with items, must contain at least one item.

**Returns:** `SimpleTaskWriteResponse` with minimal confirmation and summary

**Response Structure:**
```python
{
  "success": bool,
  "action": str,  # "task_file_created"
  "message": str,  # Human-readable confirmation
  "file_path": str,
  "summary": StatusSummary
}
```

**Example Usage:**

```python
result = new(
    branch="feature/user-auth",
    title="Add user authentication",
    prompt="Implement JWT-based auth with login/logout",
    criteria=[
        "Users can register with email and password",
        "Users can log in and receive JWT token",
        "Protected routes require valid JWT"
    ]
)
```

**Edge Cases:**
- File already exists → raises `FileExistsError`
- `criteria=[]` → creates placeholder criterion `AC1` with description "Task completion criteria (to be filled)"
- `criteria=None` → creates placeholder criterion `AC1` with description "Task completion criteria (to be filled)"

#### task

Unified tool for managing implementation tasks with five actions.

**Parameters:**
- `action`: Operation to perform ('add', 'update', 'remove', 'get', 'batch')
- `task_id` (optional): Task ID (required for update/remove/get, e.g., 'T001')
- `name` (optional): Task name (required for add)
- `goal` (optional): Task goal/description
- `status` (optional): Task status for update only. Valid values: 'not_started', 'in_progress', 'completed', 'blocked', 'paused'. **Note:** 'add' action ignores this parameter - new tasks always start as `not_started`.
- `steps` (optional): List of detailed task steps for add action. None or [] adds placeholder step ['To be defined']. Only applies when action='add'.
- `done_when` (optional): List of completion verification conditions (for add/update)
- `prerequisites` (optional): List of prerequisite task IDs (for add/update)
- `files` (optional): List of FileAction dicts with path and action fields (for add/update)
- `code_examples` (optional): List of CodeExample dicts with path and description fields (for add/update)
- `operations` (optional): List of BatchTaskOperation dicts (required for batch action)

**Note:** This tool always uses the current git branch.

**Returns:** 
- `SimpleTaskWriteResponse` for write operations (add/update/remove)
- `SimpleTaskItemResponse` for get operations
- `SimpleTaskBatchResponse` for batch operations

**Response Structures:**

Write operations return:
```python
{
  "success": bool,
  "action": str,  # e.g., "task_added", "task_updated", "task_removed"
  "message": str,  # Human-readable confirmation
  "file_path": str,
  "summary": StatusSummary
}
```

Get operations return:
```python
{
  "task": Task,  # The requested task object
  "criterion": None,
  "file_path": str,
  "summary": StatusSummary
}
```

**Example Usage:**

```python
# Add a new task
result = task(
    action="add",
    name="Create User model",
    goal="Define database schema for user accounts"
)

# Add a new task with specific steps
result = task(
    action="add",
    name="Implement authentication endpoints",
    goal="Create login and logout API endpoints",
    steps=["Define API routes", "Implement JWT generation", "Add password hashing", "Write tests"]
)

# Update task status
result = task(
    action="update",
    task_id="T001",
    status="completed"
)

# Update task name/goal
result = task(
    action="update",
    task_id="T001",
    name="Updated task name",
    goal="Updated description"
)

# Remove task
result = task(
    action="remove",
    task_id="T001"
)

# Get task details
result = task(
    action="get",
    task_id="T001"
)

# Batch operations (atomic: all succeed or all fail)
result = task(
    action="batch",
    operations=[
        {"op": "remove", "task_id": "T001"},
        {"op": "remove", "task_id": "T002"},
        {"op": "add", "name": "New Task 1", "goal": "First atomic task", "steps": ["Step 1"]},
        {"op": "add", "name": "New Task 2", "goal": "Second atomic task", "steps": ["Step 1"]},
        {"op": "update", "task_id": "T003", "status": "completed"},
    ]
)
# Returns SimpleTaskBatchResponse with new_item_ids: ["T003", "T004"] for the two added tasks
```

**Batch Operation Details:**

The `batch` action provides atomic task operations. All operations in a batch either succeed together or fail together, with no partial updates to the task file.

**BatchTaskOperation Structure:**
```python
{
  "op": str,  # Operation type: "add", "update", or "remove"
  
  # For "add" operations:
  "name": str,  # Task name (required)
  "goal": str,  # Task goal/description (optional, defaults to name)
  "steps": list[str] | None,  # Task steps (optional, None/[] adds placeholder)
  
  # For "update" operations:
  "task_id": str,  # Task ID to update (required)
  "name": str | None,  # New task name (optional)
  "goal": str | None,  # New task goal (optional)
  "status": str | None,  # New status: 'not_started', 'in_progress', 'completed', 'blocked', 'paused' (optional)
  
  # For "remove" operations:
  "task_id": str,  # Task ID to remove (required)
}
```

**Note:** All Task model fields are fully supported in batch operations, including:
- `steps`: Task implementation steps (list[str])
- `done_when`: Completion verification conditions (list[str])
- `prerequisites`: Prerequisite task IDs (list[str])
- `files`: Files to create/modify/delete (list[dict] with `path` and `action` fields)
- `code_examples`: Code patterns to follow (list[dict] with `language`, `description`, `code` fields)

These fields work in both "add" and "update" batch operations, eliminating the need for manual YAML editing.

**Atomicity Guarantee:**
- All operations are validated before any changes are applied
- If any operation is invalid, the entire batch fails with detailed error messages
- Task file is written only once, after all operations succeed
- Prerequisite references are automatically cleaned up when tasks are removed
- New task IDs are generated sequentially after all removals complete

**SimpleTaskBatchResponse Structure:**
```python
{
  "success": bool,
  "action": str,  # "batch_tasks_applied"
  "message": str,  # Summary of operations performed
  "file_path": str,
  "summary": StatusSummary,
  "new_item_ids": list[str]  # IDs of newly added tasks in order
}
```

**Edge Cases:**
- Missing required params → raises `ValueError`
- Task ID not found → raises `ValueError`
- Invalid status value → raises `ValueError`
- Status provided with action='add' → status is ignored, task created as `not_started`
- Batch operation with invalid operations → raises `ValueError` with detailed validation errors

#### criteria

Unified tool for managing acceptance criteria with five actions.

**Parameters:**
- `action`: Operation to perform ('add', 'complete', 'remove', 'get', 'update')
- `criterion_id` (optional): Criterion ID (required for complete/remove/get/update, e.g., 'AC1')
- `description` (optional): Criterion description (required for add/update)
- `completed` (optional): Completion status for 'complete' action (default: true). Set to false to mark as incomplete.

**Note:** This tool always uses the current git branch.

**Returns:**
- `SimpleTaskWriteResponse` for write operations (add/complete/remove/update)
- `SimpleTaskItemResponse` for get operations

**Response Structures:**

Write operations return:
```python
{
  "success": bool,
  "action": str,  # e.g., "criterion_added", "criterion_completed", "criterion_removed", "criterion_updated"
  "message": str,  # Human-readable confirmation
  "file_path": str,
  "summary": StatusSummary
}
```

Get operations return:
```python
{
  "task": None,
  "criterion": AcceptanceCriterion,  # The requested criterion object
  "file_path": str,
  "summary": StatusSummary
}
```

**Example Usage:**

```python
# Add a new criterion
result = criteria(
    action="add",
    description="Users can reset forgotten passwords"
)

# Mark criterion as completed
result = criteria(
    action="complete",
    criterion_id="AC2",
    completed=True
)

# Mark criterion as incomplete
result = criteria(
    action="complete",
    criterion_id="AC2",
    completed=False
)

# Remove criterion
result = criteria(
    action="remove",
    criterion_id="AC3"
)

# Get criterion details
result = criteria(
    action="get",
    criterion_id="AC2"
)

# Update criterion description
result = criteria(
    action="update",
    criterion_id="AC1",
    description="Updated description text"
)
```

**Edge Cases:**
- Missing required params → raises `ValueError`
- Criterion ID not found → raises `ValueError`
- Removing last criterion → raises `InvalidTaskFileError` (schema constraint: min_length=1)
- Update without criterion_id or description → raises `ValueError`

#### quality

Unified tool for managing quality requirements with four actions.

**Parameters:**
- `action`: Operation to perform ('check', 'set', 'get', 'preset')
- `config_type` (optional): Type of quality config to set ('linting', 'type-checking', 'testing', 'security') - required for set action
- `tool` (optional): Tool name from ToolName enum (required for set action)
- `args` (optional): Comma-separated tool arguments string (e.g., 'check,.,--fix') (for set action)
- `enabled` (optional): Enable/disable the quality check (for set action)
- `min_coverage` (optional): Minimum test coverage percentage 0-100 (only for testing config in set action)
- `timeout` (optional): Timeout in seconds for the check (for set action, default: 300)
- `preset_name` (optional): Preset name (required for preset action)

**Note:** This tool always uses the current git branch.

**Returns:**
- `SimpleTaskQualityResponse` for check/get operations
- `SimpleTaskWriteResponse` for set/preset operations

**Response Structures:**

Check/get operations return:
```python
{
  "quality_requirements": QualityRequirements | None,  # The quality configuration
  "check_results": list[QualityCheckResult] | None,  # Only present for check action
  "file_path": str,
  "summary": StatusSummary
}
```

`QualityCheckResult` structure:
```python
{
  "check_name": str,  # e.g., "Linting", "Testing"
  "passed": bool,  # Whether the check passed
  "command": str,  # Command that was executed
  "stdout": str,  # Standard output
  "stderr": str  # Standard error
}
```

**Example Usage:**

```python
# Get current quality configuration
result = quality(action="get")

# Run all enabled quality checks
result = quality(action="check")
# Returns: SimpleTaskQualityResponse with check_results list

# Set linting configuration
result = quality(
    action="set",
    config_type="linting",
    tool="ruff",
    args="check,.",
    enabled=True,
    timeout=300
)

# Set testing configuration with coverage threshold and timeout
result = quality(
    action="set",
    config_type="testing",
    tool="pytest",
    args="--cov=cli/simpletask,--cov-report=term-missing",
    min_coverage=80,
    timeout=600
)

# Apply a quality preset (fills gaps only)
result = quality(action="preset", preset_name="python")
```

**Edge Cases:**
- Missing required params → raises `ValueError`
- Invalid config_type → raises `ValueError`
- Invalid tool name (not in ToolName enum) → raises `ValueError`
- min_coverage provided for non-testing config → raises `ValueError`
- Check action with no enabled checks → returns empty check_results list

#### design

Unified tool for managing the design section with three actions.

**Parameters:**
- `action`: Operation to perform ('set', 'get', 'remove')
- `field` (optional): Field to modify ('pattern', 'reference', 'constraint', 'security', 'error-handling') - required for set/remove
- `value` (optional): Value to add (required for set action). Use ArchitecturalPattern enum values for `pattern` (repository, service_layer, factory, strategy, adapter, observer, command, mvc, clean_architecture, hexagonal, dependency_injection, singleton, builder, decorator) and ErrorHandlingStrategy enum values for `error-handling` (exceptions, result_type, error_codes, callbacks, panic_recover)
- `category` (optional): Security category required when field='security' (authentication, authorization, cryptography, input_validation, output_encoding, session_management, secure_communication, data_protection, audit_logging)
- `reason` (optional): Reason/explanation (required when field='reference' in set action)
- `index` (optional): Index to remove from list fields (for remove action)
- `all` (optional): Remove all items from field or entire design section (for remove action)

**Note:** This tool always uses the current git branch.

**Returns:**
- `SimpleTaskDesignResponse` for get operations
- `SimpleTaskWriteResponse` for set/remove operations

**Response Structures:**

Get operations return:
```python
{
  "design": Design | None,  # The design section
  "file_path": str,
  "summary": StatusSummary
}
```

**Example Usage:**

```python
# Get current design section
result = design(action="get")

# Add a pattern to follow
result = design(
    action="set",
    field="pattern",
    value="repository"
)

# Add a reference implementation
result = design(
    action="set",
    field="reference",
    value="cli/simpletask/mcp/server.py",
    reason="MCP tool pattern to follow"
)

# Add an architectural constraint
result = design(
    action="set",
    field="constraint",
    value="Use Pydantic models with extra='forbid'"
)

# Add security consideration
result = design(
    action="set",
    field="security",
    category="input_validation",
    value="Validate all user inputs"
)

# Set error handling pattern
result = design(
    action="set",
    field="error-handling",
    value="exceptions"
)

# Remove specific pattern by index
result = design(
    action="remove",
    field="pattern",
    index=0
)

# Remove all patterns
result = design(
    action="remove",
    field="pattern",
    all=True
)

# Remove entire design section
result = design(
    action="remove",
    field="all"
)
```

**Edge Cases:**
- Missing required params → raises `ValueError`
- Invalid field name → raises `ValueError`
- Reference without reason → raises `ValueError`
- Invalid index for list field → raises `ValueError`
- Remove from non-existent design section → raises `ValueError`

#### note

Unified tool for managing freeform notes at root-level (SimpleTaskSpec) or task-level (Task).

**Actions:**
- `add`: Add a note to root or task level
- `remove`: Remove note(s) by index or all
- `list`: List notes with optional filtering

**Parameters:**
- `action` (required): Operation to perform ('add', 'remove', 'list')
- `content` (optional): Note text content (required for add action)
- `task_id` (optional): Task ID to operate on task-level notes; if omitted, operates on root-level notes
- `index` (optional): Zero-based index for remove action (required unless all=True)
- `all` (optional): Remove all notes (for remove action, default: false)
- `root_only` (optional): Only return root-level notes (for list action, default: false)

**Note:** This tool always uses the current git branch.

**Returns:**
- For `add` and `remove`: `SimpleTaskWriteResponse` with success confirmation
- For `list`: `SimpleTaskNoteResponse` with:
  - `action`: str ("note_list")
  - `root_notes`: list[str] | None
  - `task_notes`: dict[str, list[str]] (sparse dict, only tasks with notes)
  - `total_count`: int (sum of all notes across root and tasks)
  - `file_path`: str
  - `summary`: StatusSummary (includes notes_total count)

**Example Usage:**

```python
# Add root-level note
result = note(action="add", content="Remember to update docs after release")

# Add note to specific task
result = note(action="add", content="This needs refactoring", task_id="T003")

# List all notes
result = note(action="list")
# result.root_notes = ["Remember to update docs after release"]
# result.task_notes = {"T003": ["This needs refactoring"]}
# result.total_count = 2

# List notes for specific task only
result = note(action="list", task_id="T003")
# result.root_notes = None
# result.task_notes = {"T003": ["This needs refactoring"]}
# result.total_count = 1

# List only root notes
result = note(action="list", root_only=True)
# result.root_notes = ["Remember to update docs after release"]
# result.task_notes = {}
# result.total_count = 1

# Remove specific note by index
result = note(action="remove", index=0)  # Remove first root note
result = note(action="remove", index=1, task_id="T003")  # Remove second note from T003

# Remove all notes
result = note(action="remove", all=True)  # Remove all root notes
result = note(action="remove", all=True, task_id="T003")  # Remove all T003 notes
```

**CLI Commands:**

```bash
# Add notes
simpletask note add "Remember to update docs after release"
simpletask note add "This needs refactoring" --task T003

# List notes
simpletask note list                    # List all notes
simpletask note list --task T003        # List notes for T003 only
simpletask note list --root-only        # List only root notes

# Remove notes
simpletask note remove 0                # Remove first root note
simpletask note remove 1 --task T003    # Remove second note from T003
simpletask note remove --all            # Remove all root notes
simpletask note remove --all --task T003  # Remove all T003 notes
```

**Use Cases:**
- Track implementation decisions and context during development
- Add reminders for future refactoring or improvements
- Document why certain approaches were chosen or rejected
- Leave breadcrumbs for code review or future developers
- Capture technical debt or known limitations
- Record blockers or dependencies discovered during implementation

**Edge Cases:**
- Missing required params → raises `ValueError`
- Invalid index (out of range or negative) → raises `ValueError`
- Task ID not found → raises `ValueError`
- Remove with neither index nor all=True → raises `ValueError`

#### constraint

Unified tool for managing implementation constraints (list of strings).

**Actions:**
- `add`: Add a constraint to the list
- `remove`: Remove constraint(s) by index or all
- `list`: List all constraints

**Parameters:**
- `action` (required): Operation to perform ('add', 'remove', 'list')
- `value` (optional): Constraint text (required for add action)
- `index` (optional): Zero-based index for remove action (required unless all=True)
- `all` (optional): Remove all constraints (for remove action, default: false)

**Note:** This tool always uses the current git branch.

**Returns:**
- For `add` and `remove`: `SimpleTaskWriteResponse` with success confirmation
- For `list`: `SimpleTaskConstraintResponse` with:
  - `action`: str ("constraint_list")
  - `constraints`: list[str] | None
  - `file_path`: str
  - `summary`: StatusSummary

**Example Usage:**

```python
# Add constraint
result = constraint(action="add", value="Use Pydantic models with extra='forbid'")

# List all constraints
result = constraint(action="list")
# result.constraints = ["Use Pydantic models with extra='forbid'", "No shell=True in subprocess calls"]

# Remove specific constraint by index
result = constraint(action="remove", index=0)  # Remove first constraint

# Remove all constraints
result = constraint(action="remove", all=True)
```

**CLI Commands:**

```bash
# Add constraint
simpletask constraint add "Use Pydantic models with extra='forbid'"

# List constraints
simpletask constraint list

# Remove constraint
simpletask constraint remove 0       # Remove first constraint
simpletask constraint remove --all   # Remove all constraints
```

**Use Cases:**
- Document coding standards and conventions
- Define technical requirements and boundaries
- Specify frameworks and libraries to use or avoid
- Enforce architectural decisions (e.g., "No direct database access from views")
- Track technical debt or temporary limitations

**Edge Cases:**
- Missing required params → raises `ValueError`
- Invalid index (out of range or negative) → raises `ValueError`
- Remove with neither index nor all=True → raises `ValueError`

#### context

Unified tool for managing context key-value pairs (flat dictionary).

**Actions:**
- `set`: Set a context key-value pair
- `remove`: Remove context entry by key or all entries
- `show`: Show all context entries

**Parameters:**
- `action` (required): Operation to perform ('set', 'remove', 'show')
- `key` (optional): Context key (required for set/remove actions)
- `value` (optional): Context value (required for set action)
- `all` (optional): Remove all context entries (for remove action, default: false)

**Note:** This tool always uses the current git branch.

**Returns:**
- For `set` and `remove`: `SimpleTaskWriteResponse` with success confirmation
- For `show`: `SimpleTaskContextResponse` with:
  - `action`: str ("context_show")
  - `context`: dict[str, Any] | None
  - `file_path`: str
  - `summary`: StatusSummary

**Example Usage:**

```python
# Set context key-value pairs
result = context(action="set", key="api_version", value="v2")
result = context(action="set", key="database", value="PostgreSQL 14")

# Show all context
result = context(action="show")
# result.context = {"api_version": "v2", "database": "PostgreSQL 14"}

# Remove specific key
result = context(action="remove", key="api_version")

# Remove all context entries
result = context(action="remove", all=True)
```

**CLI Commands:**

```bash
# Set context
simpletask context set api_version v2
simpletask context set database "PostgreSQL 14"

# Show context
simpletask context show

# Remove context
simpletask context remove api_version    # Remove specific key
simpletask context remove --all          # Remove all entries
```

**Use Cases:**
- Store environment-specific configuration (API versions, database engines)
- Track external dependencies (service URLs, API keys locations)
- Record project metadata (team name, project phase, deployment target)
- Document assumptions (expected load, user count, data volume)
- Keep implementation reminders (feature flags, A/B test status)

**Edge Cases:**
- Missing required params → raises `ValueError`
- Key not found in remove action → raises `ValueError`
- Remove with neither key nor all=True → raises `ValueError`

### Error Handling

MCP tools raise exceptions for errors:
- `ValueError`: Not in a git repository, or branch is None and not on a git branch
- `FileNotFoundError`: Task file doesn't exist for the specified branch
- `InvalidTaskFileError`: YAML file is malformed or invalid

MCP handles exception-to-error-response conversion automatically.

### Security

Path traversal attacks via the `branch` parameter are prevented:
- `normalize_branch_name()` converts `..` to `--` (double hyphens)
- Special characters are replaced with hyphens
- All paths are constrained to `.tasks/` directory
- Security tests verify these protections in `tests/unit/test_mcp_tools.py`

## Code Style

### Naming Conventions

- **Functions/Variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private members**: `_leading_underscore`

### Type Hints

Use Python 3.11+ native syntax (not `typing` module equivalents):

```python
# Correct
def process_items(items: list[str], config: dict[str, Any] | None = None) -> bool:
    ...

# Avoid
from typing import List, Dict, Optional
def process_items(items: List[str], config: Optional[Dict[str, Any]] = None) -> bool:
    ...
```

### Pydantic Models

Always use strict validation:

```python
from pydantic import BaseModel, Field

class Task(BaseModel):
    model_config = {"extra": "forbid"}  # Reject unknown fields
    
    id: str = Field(..., description="Unique task identifier")
    title: str
    criteria: list[Criterion] = Field(default_factory=list)
```

### Docstrings

Use Google-style docstrings:

```python
def find_task_by_id(task_id: str, tasks: list[Task]) -> Task | None:
    """Find a task by its identifier.
    
    Args:
        task_id: The unique task identifier to search for.
        tasks: List of tasks to search within.
    
    Returns:
        The matching Task object, or None if not found.
    
    Raises:
        ValueError: If task_id is empty.
    """
```

### Line Length

- Maximum 100 characters (configured in `pyproject.toml`)

### Typer CLI Patterns

Commands use `@app.command()` decorator with type-annotated arguments:

```python
import typer
from typing import Annotated

app = typer.Typer()

@app.command()
def add(
    task_id: Annotated[str, typer.Argument(help="Task identifier")],
    description: Annotated[str, typer.Argument(help="Criterion description")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
) -> None:
    """Add a new acceptance criterion to a task."""
    ...
```

Subcommand groups use separate Typer instances:

```python
# In main.py
from cli.simpletask.commands.task import commands as task_commands

app = typer.Typer()
app.add_typer(task_commands.app, name="task", help="Task operations")
```

## Testing

### Test Organization

Tests are organized in classes by functionality:

```python
# tests/unit/test_models.py
import pytest
from cli.simpletask.core.models import get_next_criterion_id

class TestGetNextCriterionId:
    """Tests for get_next_criterion_id function."""
    
    def test_empty_list_returns_one(self):
        assert get_next_criterion_id([]) == 1
    
    def test_sequential_ids(self):
        criteria = [Criterion(id=1, ...), Criterion(id=2, ...)]
        assert get_next_criterion_id(criteria) == 3
    
    @pytest.mark.parametrize("ids,expected", [
        ([1, 3, 5], 6),
        ([2, 4], 5),
    ])
    def test_gaps_in_ids(self, ids, expected):
        criteria = [Criterion(id=i, ...) for i in ids]
        assert get_next_criterion_id(criteria) == expected
```

### Fixtures

Shared fixtures are defined in `tests/conftest.py`:

```python
import pytest
from cli.simpletask.core.models import Task, Criterion

@pytest.fixture
def sample_task() -> Task:
    """Create a sample task for testing."""
    return Task(
        id="TASK-001",
        title="Sample Task",
        criteria=[
            Criterion(id=1, description="First criterion"),
        ]
    )

@pytest.fixture
def temp_task_file(tmp_path):
    """Create a temporary task YAML file."""
    task_file = tmp_path / "task.yaml"
    task_file.write_text("id: TEST-001\ntitle: Test\n")
    return task_file
```

### Mocking

Use `unittest.mock` for mocking:

```python
from unittest.mock import Mock, patch, MagicMock

class TestGitOperations:
    
    @patch("cli.simpletask.core.git.Repo")
    def test_get_current_branch(self, mock_repo_class):
        mock_repo = MagicMock()
        mock_repo.active_branch.name = "feature/test"
        mock_repo_class.return_value = mock_repo
        
        result = get_current_branch("/path/to/repo")
        
        assert result == "feature/test"
```

## Boundaries

### Schema Version

**Current schema version: 1.0**

SimpleTask uses a simple versioning system for task file schema. Since this project is under active development and has not yet been published, there is currently only one schema version (1.0) and no backward compatibility or migration paths are implemented or needed.

**When the project reaches a stable release, schema versioning will be used to track breaking changes and provide migration paths for users.**

### Task Files (.tasks/ directory)

The `.tasks/` directory contains task definition files used during development but is **NOT part of the project deliverable**. These files are:
- Git-ignored by default
- Used for planning and tracking implementation work  
- Not required to conform to the current schema version
- Can be in any state without affecting project quality

**When reviewing code or running quality checks, IGNORE any issues with files in the `.tasks/` directory.** Only the project code in `cli/simpletask/` and related directories matters for project quality assessment.

### Always Do

- Run `pytest` before committing changes
- Run `black .` and `ruff check .` before committing
- **Version bumping strategy:**
  - **On feature branches:** Bump version ONCE at the end, just before merging to main
  - **On main branch:** Bump version for each commit with code changes
  - Always bump in BOTH `pyproject.toml` and `cli/simpletask/__init__.py`
  - Use `git commit --no-verify` for intermediate commits on feature branches
- Add type hints to all function signatures
- Use Pydantic models for data validation
- Write tests for new functionality
- Follow existing code patterns in the codebase

### Ask First

- Adding new dependencies to `pyproject.toml`
- Changing the task YAML schema structure
- Modifying CLI command names or arguments (breaking changes)
- Changing Pydantic model field names (affects serialization)
- **Merging pull requests or branches to main** - ALWAYS ask for explicit permission before merging

### Never Do

- Commit code that fails `pytest`
- Commit code that fails `mypy` type checking
- Remove or modify existing tests without understanding why they exist
- Use `typing.List`, `typing.Dict`, `typing.Optional` instead of native syntax
- Add `extra="allow"` to Pydantic models (use `"forbid"`)
- Hardcode file paths (use `pathlib.Path`)
- Bump the major version (only bump minor or patch)

## Key Files Reference

| File | Purpose |
|------|---------|
| `cli/simpletask/main.py` | CLI entry point, command registration |
| `cli/simpletask/core/models.py` | Pydantic data models |
| `cli/simpletask/core/yaml_parser.py` | YAML file read/write operations |
| `cli/simpletask/core/git.py` | Git repository operations |
| `cli/simpletask/core/ai_templates.py` | Template installation and management |
| `cli/simpletask/templates/` | AI workflow templates (slash commands for OpenCode/Qwen/Gemini) |
| `cli/simpletask/mcp/server.py` | MCP server implementation |
| `cli/simpletask/schema/task_schema.json` | JSON schema for task validation |
| `tests/conftest.py` | Shared test fixtures |
| `pyproject.toml` | Project configuration, dependencies |
