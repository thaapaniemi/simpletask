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
└── *.yaml

tests/                    # Test suite
├── conftest.py           # Shared fixtures
├── unit/                 # Unit tests
└── integration/          # Integration tests
```

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
- Bump version in both `pyproject.toml` and `cli/simpletask/__init__.py` for each commit
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
