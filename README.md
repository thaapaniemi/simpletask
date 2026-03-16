# simpletask

Schema-enforced, branch-scoped task definitions that AI agents can query and execute — not markdown templates to interpret.

## Highlights

- **Structured data, not prose** — YAML validated by JSON Schema and Pydantic v2; AI agents receive typed objects via MCP, not text to interpret
- **Branch-scoped by design** — task files are tied to the branch by name and scoped to a single implementation cycle; whether they are committed to git is up to you
- **Quality gates in the spec** — linting, type checking, and test coverage thresholds are typed fields the AI can execute and verify, not external CI concerns
- **Design guidance as typed constraints** — architectural patterns, security categories, and error-handling strategies are enumerated fields, not comments or prose
- **Objective task atomicity** — `/simpletask.split` enforces measurable thresholds (≤2 steps, ≤1 file, ≤100-char goal) before execution begins
- **Editor-agnostic MCP provider** — 11 typed tools with no orchestration coupling; switching AI editors doesn't invalidate your task definitions

## Table of Contents

- [Why simpletask?](#why-simpletask)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Task File Format](#task-file-format)
- [Commands](#commands)
- [Configuration](#configuration)
- [AI Integration](#ai-integration)
- [Development](#development)
- [License](#license)

## Why simpletask?

**Structured data, not prose.** Task files are strictly validated YAML, governed by a JSON Schema and parsed through Pydantic v2 models with `extra="forbid"`. Every field — acceptance criteria, task status, prerequisites, quality thresholds, architectural patterns — is a typed entity. An AI agent reading a task file via MCP receives structured data objects, not paragraphs to interpret. This eliminates a class of hallucination risk where the agent misreads or misinterprets a requirement.

**Branch-scoped by design.** Task files live in `.tasks/` and are linked to a branch by name (`feature/auth` → `.tasks/feature-auth.yml`). Whether you commit them to git is your choice — add `.tasks/` to `.gitignore` to treat them as ephemeral local scratch space, or commit them to share task state with your team and preserve history. simpletask does not impose a policy either way.

**Quality gates inside the spec.** Linting, type checking, test coverage thresholds, and security scans are first-class typed fields in the task spec itself. An AI agent can read them via `simpletask_quality(action="get")` and execute them via `simpletask_quality(action="check")`, receiving structured pass/fail results back into context. The spec describes not just *what* to build but *how to verify it was built correctly* — no manual CI handoff required.

**Design guidance as typed constraints.** Architectural patterns come from an enumerated set (repository, service_layer, factory, mvc, hexagonal, dependency_injection, etc.). Security categories are enumerated (authentication, authorization, input_validation, etc.). Reference implementations point to specific files with a required reason. This means an AI agent receives design guidance as structured constraints it can reason about and validate against — not as prose it must extract and interpret.

**Objective task atomicity.** The `/simpletask.split` command enforces measurable splitting criteria before execution begins. A task is split if it has more than 2 steps, more than 1 file, more than 3 done-when conditions, or more than 100 characters in the goal description. The result is a set of atomic tasks, each targeting 1–2 implementation steps, with all prerequisite chains updated. The purpose is to reduce each agent execution to a scope where completion can be verified unambiguously.

**Editor-agnostic MCP provider.** simpletask exposes 11 typed CRUD tools via the Model Context Protocol and nothing else. It has no execution routing, no agent spawning, no workflow orchestration. The execution agent — whether OpenCode, Cursor, Claude Code, or any other MCP client — makes all decisions. Switching AI editors does not invalidate your task definitions.

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
| `/simpletask.split` | Split complex tasks into atomic subtasks for easier AI execution |
| `/simpletask.implement` | Execute tasks from the plan, updating status as you go |
| `/simpletask.review` | Review implementation against acceptance criteria |

**Workflow:**

```
/simpletask.plan Add user authentication with JWT
  → Creates branch, task file with acceptance criteria and tasks

/simpletask.split
  → (Optional) Splits complex tasks into atomic subtasks (1-2 steps each)
  → Reduces cognitive load for AI execution

/simpletask.implement
  → AI executes tasks, marks progress, commits changes

/simpletask.review
  → Reviews code quality, verifies criteria met, adds fix tasks if needed
```

**Supported AI tools:**

- **[OpenCode](https://opencode.ai)**, **[Qwen](https://github.com/QwenLM/qwen-code)**, and **[Gemini CLI](https://github.com/google-gemini/gemini-cli)** - Install workflow commands:
  ```sh
  simpletask ai install              # All three editors
  simpletask ai install --opencode   # OpenCode only
  simpletask ai install --qwen       # Qwen only
  simpletask ai install --gemini     # Gemini CLI only
  simpletask ai install --local      # Project-local installation
  ```

The three workflow commands are:
- `/simpletask.plan` - Create specification and implementation plan
- `/simpletask.split` - Split complex tasks into atomic subtasks (optional)
- `/simpletask.implement` - Execute tasks from the plan
- `/simpletask.review` - Review implementation against acceptance criteria

See the [MCP Integration Guide](docs/MCP.md) for MCP server configuration and detailed setup instructions.

**Check installation status:**
```sh
simpletask ai list
```

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

Shows a table with all tasks, their completion progress, sorted by most recently modified.

For scripting, use the `--simple` flag to output just branch names:

```sh
simpletask list --simple
```

#### Add acceptance criteria

```sh
simpletask criteria add "Users can log in with email and password"
```

#### Mark criteria as complete

```sh
simpletask criteria complete AC1
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
| `simpletask list` | List all tasks with status (use --simple for plain output) |
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

simpletask includes a Model Context Protocol (MCP) server for integration with AI editors like OpenCode, Qwen-CLI, and Gemini CLI. The MCP server exposes task file operations as structured tools that AI assistants can use to read task definitions, check status, and understand project context.

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

Then configure your AI editor to connect to the server. For detailed setup instructions including configuration for OpenCode, Qwen-CLI, Gemini CLI, and other MCP clients, see the [MCP Integration Guide](docs/MCP.md).

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
