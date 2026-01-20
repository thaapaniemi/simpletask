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
└── schema/
    └── task_schema.json  # JSON schema for validation

schema/                   # Schema documentation
├── README.md
└── examples/

.tasks/                   # Task YAML files (git-ignored)
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

#### Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or equivalent:

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

**Note:** If simpletask is installed in a virtualenv, use the full path to the executable:

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

### Available Tools

The MCP server exposes 5 tools for task management:

| Tool | Description | Parameters |
|------|-------------|------------|
| `simpletask_get` | Get complete task specification with status summary | `branch` (str, optional): Branch name or None for current<br>`validate` (bool, optional): Include schema validation (default: false) |
| `simpletask_list` | List all task file branch names in the project | None |
| `simpletask_new` | Create a new task file | `branch` (str): Branch identifier<br>`title` (str): Task title<br>`prompt` (str): Original user request<br>`criteria` (list[str] \| None, optional): Acceptance criteria |
| `simpletask_task` | Manage implementation tasks (add/update/remove) | `action` (str): 'add', 'update', or 'remove'<br>`branch` (str, optional): Branch name or None for current<br>`task_id` (str, optional): Task ID (required for update/remove)<br>`name` (str, optional): Task name (required for add)<br>`goal` (str, optional): Task goal/description<br>`status` (str, optional): Status for update ('not_started', 'in_progress', 'completed', 'blocked') |
| `simpletask_criteria` | Manage acceptance criteria (add/complete/remove) | `action` (str): 'add', 'complete', or 'remove'<br>`branch` (str, optional): Branch name or None for current<br>`criterion_id` (str, optional): Criterion ID (required for complete/remove)<br>`description` (str, optional): Description (required for add)<br>`completed` (bool, optional): Completion status for 'complete' (default: true) |

### Tool Details

#### simpletask_get

Returns enriched task data with pre-computed status counts:

**Parameters:**
- `branch` (optional): Branch name, or omit to use current git branch. The branch name will be normalized (e.g., `feature/auth` → `feature-auth.yml`).
- `validate` (optional): Whether to include schema validation result. Default is `false` to reduce overhead.

**Returns:** `SimpleTaskGetResponse` with:
- `spec`: Full `SimpleTaskSpec` (branch, title, acceptance_criteria, tasks, etc.)
- `file_path`: Path to task YAML file
- `summary`: Pre-computed `StatusSummary` with:
  - `branch`, `title`, `overall_status`
  - `criteria_total`, `criteria_completed`
  - `tasks_total`, `tasks_completed`, `tasks_in_progress`, `tasks_not_started`, `tasks_blocked`
- `validation` (optional): `ValidationResult` with `valid` (bool) and `errors` (list)

**Example Response Structure:**

```json
{
  "spec": {
    "branch": "feature/mcp-server",
    "title": "Add MCP server support",
    "status": "in_progress",
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

#### simpletask_list

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

#### simpletask_new

Creates a new task file without creating a git branch (atomic MCP operation).

**Parameters:**
- `branch`: Branch/task identifier (e.g., 'feature/user-auth')
- `title`: Human-readable task title
- `prompt`: Original user prompt/request that led to task creation
- `criteria` (optional): List of acceptance criteria descriptions. If `None`, adds a single placeholder criterion. If provided, must contain at least one item (empty list raises ValidationError).

**Returns:** `SimpleTaskGetResponse` with created spec and summary

**Example Usage:**

```python
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
```

**Edge Cases:**
- File already exists → raises `FileExistsError`
- `criteria=[]` → raises `ValidationError` (schema requires min_length=1)
- `criteria=None` → creates one placeholder: "Define acceptance criteria"

#### simpletask_task

Unified tool for managing implementation tasks with three actions.

**Parameters:**
- `action`: Operation to perform ('add', 'update', 'remove')
- `branch` (optional): Branch name, or None for current git branch
- `task_id` (optional): Task ID (required for update/remove, e.g., 'T001')
- `name` (optional): Task name (required for add)
- `goal` (optional): Task goal/description
- `status` (optional): Task status for update only. Valid values: 'not_started', 'in_progress', 'completed', 'blocked'. **Note:** 'add' action ignores this parameter - new tasks always start as `not_started`.

**Returns:** `SimpleTaskGetResponse` with updated spec and summary

**Example Usage:**

```python
# Add a new task
result = simpletask_task(
    action="add",
    branch="feature/user-auth",
    task_id="T001",
    name="Create User model",
    goal="Define database schema for user accounts"
)

# Update task status
result = simpletask_task(
    action="update",
    branch="feature/user-auth",
    task_id="T001",
    status="completed"
)

# Update task name/goal
result = simpletask_task(
    action="update",
    task_id="T001",  # Uses current branch
    name="Updated task name",
    goal="Updated description"
)

# Remove task
result = simpletask_task(
    action="remove",
    task_id="T001"
)
```

**Edge Cases:**
- Missing required params → raises `ValueError`
- Task ID not found → raises `ValueError`
- Invalid status value → raises `ValueError`
- Status provided with action='add' → status is ignored, task created as `not_started`

#### simpletask_criteria

Unified tool for managing acceptance criteria with three actions.

**Parameters:**
- `action`: Operation to perform ('add', 'complete', 'remove')
- `branch` (optional): Branch name, or None for current git branch
- `criterion_id` (optional): Criterion ID (required for complete/remove, e.g., 'AC1')
- `description` (optional): Criterion description (required for add)
- `completed` (optional): Completion status for 'complete' action (default: true). Set to false to mark as incomplete.

**Returns:** `SimpleTaskGetResponse` with updated spec and summary

**Example Usage:**

```python
# Add a new criterion
result = simpletask_criteria(
    action="add",
    branch="feature/user-auth",
    description="Users can reset forgotten passwords"
)

# Mark criterion as completed
result = simpletask_criteria(
    action="complete",
    criterion_id="AC2",
    completed=True
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

## Datetime Handling

simpletask follows industry best practices for datetime management: store in UTC, display in local timezone.

### Storage Format

- All timestamps are stored in **UTC** in YAML files
- Format: ISO 8601 strings (e.g., `2026-01-19T11:25:09.319553Z`)
- Generated via `datetime.now(UTC)` in `yaml_parser.py`
- Fields: `created` and `updated` in task files

### Display Format

- CLI displays timestamps in **local timezone**
- Format: "YYYY-MM-DD HH:MM:SS TZ" (e.g., "2026-01-20 10:30:45 EST")
- Conversion handled by `utils/datetime_format.py`
- Function: `format_datetime(dt: datetime | None, include_timezone: bool = True) -> str`

### MCP Server

- Returns raw datetime objects (serialized to ISO 8601 UTC by Pydantic)
- Consumers should handle timezone conversion based on their needs
- This is the correct API behavior - standardized UTC timestamps

### Rationale

- **UTC storage:** Industry best practice, collaboration-friendly, DST-safe, unambiguous
- **Local display:** User-friendly, matches wall clock time
- **Separation of concerns:** Storage layer (UTC) vs. presentation layer (local)
- **Team collaboration:** All team members see the same stored timestamps regardless of location

### Implementation

When displaying timestamps in CLI commands:

```python
from ..utils.datetime_format import format_datetime

# Display with timezone
console.print(f"Created: {format_datetime(spec.created)}")
# Output: Created: 2026-01-20 10:30:45 EST

# Display without timezone indicator
console.print(f"Updated: {format_datetime(spec.updated, include_timezone=False)}")
# Output: Updated: 2026-01-20 10:30:45
```

When storing timestamps:

```python
from datetime import UTC, datetime

# Always use UTC
spec.updated = datetime.now(UTC)
```

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
| `cli/simpletask/schema/task_schema.json` | JSON schema for task validation |
| `tests/conftest.py` | Shared test fixtures |
| `pyproject.toml` | Project configuration, dependencies |
