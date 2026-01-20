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
- [AI Integration](#ai-integration)
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

#### Via uv (recommended)

```sh
uv tool install simpletask --from git+https://github.com/thaapaniemi/simpletask.git
```

#### Development installation

```sh
git clone https://github.com/thaapaniemi/simpletask.git
cd simpletask
pip install -e ".[dev]"
```

## Usage

### With AI Tools (Recommended)

The recommended workflow uses slash commands in supported AI editors. These guide the AI through planning, implementing, and reviewing your feature:

| Command | Description |
|---------|-------------|
| `/simpletask.plan <feature>` | Create specification and implementation plan from feature description |
| `/simpletask.implement` | Execute tasks from the plan, updating status as you go |
| `/simpletask.review` | Review implementation against acceptance criteria |

**Workflow:**

```
/simpletask.plan Add user authentication with JWT
  → Creates branch, task file with acceptance criteria and tasks

/simpletask.implement
  → AI executes tasks, marks progress, commits changes

/simpletask.review
  → Reviews code quality, verifies criteria met, adds fix tasks if needed
```

**Supported AI tools:**

- **[OpenCode](https://opencode.ai)** - Install slash commands:
  ```sh
  mkdir -p ~/.config/opencode/commands
  cp cli/simpletask/templates/opencode/*.md ~/.config/opencode/commands/
  ```

Also configure the MCP server for structured AI access to task data. See [MCP Integration Guide](docs/MCP.md) for setup instructions.

### With CLI (Manual Verification)

CLI commands are useful for manual verification, scripting, or when AI tools aren't available.

#### Create a new task

```sh
simpletask new "Add user authentication" --branch feature/auth
```

This creates a task file in `.tasks/feature-auth.yml` linked to the `feature/auth` branch.

#### View current task

```sh
simpletask show
```

Shows the task associated with the current git branch.

#### List all tasks

```sh
simpletask list
```

#### Add acceptance criteria

```sh
simpletask criteria add "Users can log in with email and password"
```

#### Mark criteria as complete

```sh
simpletask criteria complete AC1
```

#### Check task status

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

See [docs/SCHEMA.md](docs/SCHEMA.md) for the complete schema documentation.

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

Task files are stored in the `.tasks/` directory by default. The filename is derived from the branch name with slashes converted to hyphens.

### Editor Integration

Add the schema reference to your YAML files for editor validation and autocomplete:

```yaml
# yaml-language-server: $schema=simpletask.schema.json
```

### Validate with CLI

```sh
ajv validate -s schema/simpletask.schema.json -d .tasks/my-task.yml --spec=draft2020 -c ajv-formats
```

## AI Integration

### MCP Server for AI Editors

simpletask includes a Model Context Protocol (MCP) server for integration with AI editors like OpenCode and Qwen-CLI. The MCP server exposes task file operations as structured tools that AI assistants can use to read task definitions, check status, and understand project context.

**Benefits:**
- **Structured responses**: AI gets typed JSON instead of parsing CLI output
- **Automatic context**: AI can query task files without manual copy/paste
- **Better planning**: AI understands acceptance criteria and constraints
- **Progress tracking**: AI sees task status and completion metrics

**Quick start:**

```sh
# Start the MCP server
simpletask serve
```

Then configure your AI editor to connect to the server. For detailed setup instructions including configuration for OpenCode, Qwen-CLI, Claude Desktop, and other MCP clients, see the [MCP Integration Guide](docs/MCP.md).

## Development

### Setup

```sh
git clone https://github.com/your-org/simpletask.git
cd simpletask
pip install -e ".[dev]"
```

### Install Git Hooks

```sh
./scripts/install-hooks.sh
```

This installs hooks that:
- Enforce version bumping when code changes
- Require [Conventional Commits](https://conventionalcommits.org/) format
- Run tests before push

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
