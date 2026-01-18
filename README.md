# simpletask

CLI tool for managing AI-friendly task definitions in branch-based development workflows.

## Highlights

- **Branch-aware task management** - Automatically links tasks to git branches
- **YAML-based task files** - Human-readable, version-controllable task definitions
- **AI-optimized format** - Structured schema designed for AI agent consumption
- **Acceptance criteria tracking** - Track completion status of task requirements
- **Schema validation** - JSON Schema validation ensures task file integrity

## Table of Contents

- [About](#about)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Task File Format](#task-file-format)
- [Commands](#commands)
- [Configuration](#configuration)
- [Development](#development)
- [License](#license)

## About

simpletask provides a structured way to define development tasks that both humans and AI agents can understand. Each task is stored as a YAML file linked to a git branch, containing the original prompt, acceptance criteria, constraints, and implementation steps.

This approach enables:

- Clear communication between developers and AI coding assistants
- Trackable progress through acceptance criteria
- Reproducible task definitions that can be version controlled
- Consistent task structure across projects

### Built With

- [Typer](https://typer.tiangolo.com/) - CLI framework with type hints
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [GitPython](https://gitpython.readthedocs.io/) - Git integration
- [PyYAML](https://pyyaml.org/) - YAML parsing

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git

### Installation

```sh
pip install simpletask
```

For development installation:

```sh
git clone https://github.com/your-org/simpletask.git
cd simpletask
pip install -e ".[dev]"
```

## Usage

### Create a new task

```sh
simpletask new "Add user authentication" --branch feature/auth
```

This creates a task file in `tasks/feature-auth.yml` linked to the `feature/auth` branch.

### View current task

```sh
simpletask show
```

Shows the task associated with the current git branch.

### List all tasks

```sh
simpletask list
```

### Add acceptance criteria

```sh
simpletask criteria add "Users can log in with email and password"
```

### Mark criteria as complete

```sh
simpletask criteria complete AC1
```

### Check task status

```sh
simpletask status
```

## Task File Format

Task files use YAML format with JSON Schema validation:

```yaml
# yaml-language-server: $schema=simpletask.schema.json
schema_version: "1.0"
branch: feature/add-auth
title: Add user authentication
original_prompt: "Users should be able to log in with email and password"
status: in_progress
created: "2026-01-18T10:00:00Z"
updated: "2026-01-18T14:30:00Z"

acceptance_criteria:
  - id: AC1
    description: Users can log in with email and password
    completed: true
  - id: AC2
    description: Invalid credentials show error message
    completed: false

constraints:
  - "Use existing auth library"
  - "Follow security best practices"

context:
  related_files:
    - src/auth/login.py
    - tests/test_auth.py
  dependencies:
    - name: bcrypt
      purpose: Password hashing

tasks:
  - id: T001
    name: Implement login endpoint
    status: completed
    goal: Create POST /login endpoint
    done_when:
      - Endpoint accepts email and password
      - Returns JWT token on success
```

See [schema/README.md](schema/README.md) for the complete schema documentation.

## Commands

| Command | Description |
|---------|-------------|
| `simpletask new` | Create a new task file |
| `simpletask show` | Display current branch's task |
| `simpletask list` | List all tasks |
| `simpletask status` | Show task completion status |
| `simpletask criteria add` | Add acceptance criterion |
| `simpletask criteria complete` | Mark criterion as complete |
| `simpletask criteria list` | List all criteria |
| `simpletask criteria remove` | Remove a criterion |
| `simpletask task add` | Add implementation task |
| `simpletask task list` | List implementation tasks |
| `simpletask task update` | Update task status |
| `simpletask task remove` | Remove a task |
| `simpletask schema validate` | Validate task file against schema |

Use `simpletask --help` or `simpletask <command> --help` for detailed options.

## Configuration

Task files are stored in the `tasks/` directory by default. The filename is derived from the branch name with slashes converted to hyphens.

### Editor Integration

Add the schema reference to your YAML files for editor validation and autocomplete:

```yaml
# yaml-language-server: $schema=simpletask.schema.json
```

### Validate with CLI

```sh
ajv validate -s schema/simpletask.schema.json -d tasks/my-task.yml --spec=draft2020 -c ajv-formats
```

## Development

### Setup

```sh
git clone https://github.com/your-org/simpletask.git
cd simpletask
pip install -e ".[dev]"
```

### Run tests

```sh
pytest
```

### Code quality

```sh
black .           # Format code
ruff check .      # Lint
mypy cli/simpletask  # Type check
```

### Run with coverage

```sh
pytest --cov=cli/simpletask --cov-report=term-missing
```

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.
