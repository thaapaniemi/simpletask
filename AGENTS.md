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
│   └── qwen/             # Qwen slash commands (.toml)
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

## Commands

### Development

```bash
# Install in editable mode
pip install -e .

# Run the CLI
simpletask --help
simpletask task list
simpletask criteria add <task-id> "New criterion"
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=cli/simpletask --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_models.py

# Run specific test class
pytest tests/unit/test_models.py::TestGetNextCriterionId

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code
black .

# Lint code
ruff check .

# Fix auto-fixable lint issues
ruff check --fix .

# Type checking
mypy cli/simpletask
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

### Available Tools

The MCP server exposes 5 tools for task management:

**Note:** MCP clients automatically prefix tool names with the server name. When invoked through an MCP client (like OpenCode), these tools become `simpletask_get`, `simpletask_list`, `simpletask_new`, `simpletask_task`, and `simpletask_criteria`.

| Tool | Description | Parameters |
|------|-------------|------------|
| `get` | Get complete task specification with status summary | `branch` (str, optional): Branch name or None for current<br>`validate` (bool, optional): Include schema validation (default: false) |
| `list` | List all task file branch names in the project | None |
| `new` | Create a new task file | `branch` (str): Branch identifier<br>`title` (str): Task title<br>`prompt` (str): Original user request<br>`criteria` (list[str] \| None, optional): Acceptance criteria |
| `task` | Manage implementation tasks (add/update/remove) | `action` (str): 'add', 'update', or 'remove'<br>`branch` (str, optional): Branch name or None for current<br>`task_id` (str, optional): Task ID (required for update/remove)<br>`name` (str, optional): Task name (required for add)<br>`goal` (str, optional): Task goal/description<br>`status` (str, optional): Status for update ('not_started', 'in_progress', 'completed', 'blocked')<br>`steps` (list[str] \| None, optional): Task steps for add action. None or [] adds placeholder ['To be defined'] |
| `criteria` | Manage acceptance criteria (add/complete/remove) | `action` (str): 'add', 'complete', or 'remove'<br>`branch` (str, optional): Branch name or None for current<br>`criterion_id` (str, optional): Criterion ID (required for complete/remove)<br>`description` (str, optional): Description (required for add)<br>`completed` (bool, optional): Completion status for 'complete' (default: true) |

### Tool Details

#### get

Returns enriched task data with pre-computed status counts:

**Parameters:**
- `branch` (optional): Branch name, or omit to use current git branch. The branch name will be normalized (e.g., `feature/auth` → `feature-auth.yml`).
- `validate` (optional): Whether to include schema validation result. Default is `false` to reduce overhead.

**Returns:** `SimpleTaskGetResponse` with:
- `spec`: Full `SimpleTaskSpec` (branch, title, acceptance_criteria, tasks, etc.)
- `file_path`: Path to task YAML file
- `summary`: Pre-computed `StatusSummary` with:
  - `branch`, `title`
  - `overall_status`: Computed from task states (blocked > in_progress > completed > not_started)
  - `criteria_total`, `criteria_completed`
  - `tasks_total`, `tasks_completed`, `tasks_in_progress`, `tasks_not_started`, `tasks_blocked`
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
    "tasks_blocked": 0
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
- `criteria` (optional): List of acceptance criteria descriptions. If `None`, adds a single placeholder criterion. If provided, must contain at least one item (empty list raises ValidationError).

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

Unified tool for managing implementation tasks with four actions.

**Parameters:**
- `action`: Operation to perform ('add', 'update', 'remove', 'get')
- `branch` (optional): Branch name, or None for current git branch
- `task_id` (optional): Task ID (required for update/remove/get, e.g., 'T001')
- `name` (optional): Task name (required for add)
- `goal` (optional): Task goal/description
- `status` (optional): Task status for update only. Valid values: 'not_started', 'in_progress', 'completed', 'blocked'. **Note:** 'add' action ignores this parameter - new tasks always start as `not_started`.
- `steps` (optional): List of detailed task steps for add action. None or [] adds placeholder step ['To be defined']. Only applies when action='add'.

**Returns:** 
- `SimpleTaskWriteResponse` for write operations (add/update/remove)
- `SimpleTaskItemResponse` for get operations

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
    branch="feature/user-auth",
    task_id="T001",
    name="Create User model",
    goal="Define database schema for user accounts"
)

# Add a new task with specific steps
result = task(
    action="add",
    branch="feature/user-auth",
    task_id="T002",
    name="Implement authentication endpoints",
    goal="Create login and logout API endpoints",
    steps=["Define API routes", "Implement JWT generation", "Add password hashing", "Write tests"]
)

# Update task status
result = task(
    action="update",
    branch="feature/user-auth",
    task_id="T001",
    status="completed"
)

# Update task name/goal
result = task(
    action="update",
    task_id="T001",  # Uses current branch
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
```

**Edge Cases:**
- Missing required params → raises `ValueError`
- Task ID not found → raises `ValueError`
- Invalid status value → raises `ValueError`
- Status provided with action='add' → status is ignored, task created as `not_started`

#### criteria

Unified tool for managing acceptance criteria with four actions.

**Parameters:**
- `action`: Operation to perform ('add', 'complete', 'remove', 'get')
- `branch` (optional): Branch name, or None for current git branch
- `criterion_id` (optional): Criterion ID (required for complete/remove/get, e.g., 'AC1')
- `description` (optional): Criterion description (required for add)
- `completed` (optional): Completion status for 'complete' action (default: true). Set to false to mark as incomplete.

**Returns:**
- `SimpleTaskWriteResponse` for write operations (add/complete/remove)
- `SimpleTaskItemResponse` for get operations

**Response Structures:**

Write operations return:
```python
{
  "success": bool,
  "action": str,  # e.g., "criterion_added", "criterion_completed", "criterion_removed"
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
    branch="feature/user-auth",
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
```

**Edge Cases:**
- Missing required params → raises `ValueError`
- Criterion ID not found → raises `ValueError`
- Removing last criterion → raises `InvalidTaskFileError` (schema constraint: min_length=1)

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
| `cli/simpletask/templates/` | AI workflow templates (slash commands for OpenCode/Qwen) |
| `cli/simpletask/mcp/server.py` | MCP server implementation |
| `cli/simpletask/schema/task_schema.json` | JSON schema for task validation |
| `tests/conftest.py` | Shared test fixtures |
| `pyproject.toml` | Project configuration, dependencies |
