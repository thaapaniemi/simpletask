# Simpletask Architecture

This document provides a high-level overview of simpletask's architecture for developers and AI agents working with the codebase.

> **Related documentation**: See [AGENTS.md](../AGENTS.md) for contribution guidelines, code style, and development commands.

## Overview

Simpletask is an AI-friendly task definition manager that couples git branches with structured task specifications. Each feature branch has a corresponding YAML task file that serves as the single source of truth for requirements, acceptance criteria, and implementation progress.

**Core Design Principles:**
- **Branch-Task Coupling**: One task file per branch, branch name = task identifier
- **YAML as Single Source of Truth**: All task state lives in `.tasks/<branch>.yml`
- **Strict Validation**: Pydantic models with `extra="forbid"` reject unknown fields
- **Separation of Concerns**: CLI layer separated from core business logic
- **Convention over Configuration**: Fixed directory structure, no config files needed

## System Architecture

```mermaid
graph TB
    subgraph "CLI Layer"
        CLI[__init__.py<br/>Typer App]
        CMD[commands/*<br/>Command Handlers]
    end
    
    subgraph "Core Layer"
        PROJ[project.py<br/>Project Discovery]
        YAML[yaml_parser.py<br/>File I/O]
        MOD[models.py<br/>Pydantic Models]
        GIT[git.py<br/>Git Operations]
        OPS[task_ops.py<br/>criteria_ops.py]
        VAL[validation.py<br/>Schema Validation]
    end
    
    subgraph "Storage"
        TASKS[.tasks/*.yml<br/>Task Files]
        GITREPO[.git/<br/>Repository]
    end
    
    subgraph "Utils"
        CON[console.py<br/>Rich Output]
    end
    
    CLI --> CMD
    CMD --> PROJ
    CMD --> CON
    PROJ --> GIT
    PROJ --> TASKS
    CMD --> OPS
    OPS --> YAML
    YAML --> MOD
    YAML --> TASKS
    VAL --> MOD
    GIT --> GITREPO
```

## Component Overview

| Module | Purpose | Key Exports |
|--------|---------|-------------|
| `core/models.py` | Pydantic data models for task files | `SimpleTaskSpec`, `Task`, `AcceptanceCriterion`, `TaskStatus` |
| `core/project.py` | Project root discovery, task file paths | `Project`, `find_project()`, `ensure_project()` |
| `core/yaml_parser.py` | YAML read/write with validation | `parse_task_file()`, `write_task_file()` |
| `core/git.py` | GitPython wrapper for branch ops | `current_branch()`, `create_branch()`, `is_main_branch()` |
| `core/task_ops.py` | CRUD for implementation tasks | `add_implementation_task()`, `update_implementation_task()` |
| `core/criteria_ops.py` | CRUD for acceptance criteria | `add_acceptance_criterion()`, `mark_criterion_complete()` |
| `core/validation.py` | JSON Schema validation | `validate_task_file()`, `get_bundled_schema()` |
| `core/ai_templates.py` | AI editor template management | `install_templates()`, `install_qwen_templates()` |
| `utils/console.py` | Rich console output helpers | `success()`, `error()`, `info()`, `warning()` |

## Domain Model

```mermaid
classDiagram
    class SimpleTaskSpec {
        +str schema_version
        +str branch
        +str title
        +str original_prompt
        +TaskStatus status
        +datetime created
        +datetime updated
        +list~AcceptanceCriterion~ acceptance_criteria
        +list~str~ constraints
        +dict context
        +list~Task~ tasks
    }
    
    class AcceptanceCriterion {
        +int id
        +str description
        +bool completed
    }
    
    class Task {
        +str id
        +str name
        +TaskStatus status
        +str goal
        +list~str~ steps
        +str done_when
        +list~str~ prerequisites
        +list~FileAction~ files
        +list~CodeExample~ code_examples
    }
    
    class TaskStatus {
        <<enumeration>>
        NOT_STARTED
        IN_PROGRESS
        COMPLETED
        BLOCKED
    }
    
    class FileAction {
        +str path
        +str action
    }
    
    class CodeExample {
        +str language
        +str description
        +str code
    }
    
    SimpleTaskSpec "1" *-- "1..*" AcceptanceCriterion : acceptance_criteria
    SimpleTaskSpec "1" *-- "0..*" Task : tasks
    SimpleTaskSpec --> TaskStatus : status
    Task --> TaskStatus : status
    Task "1" *-- "0..*" FileAction : files
    Task "1" *-- "0..*" CodeExample : code_examples
```

## Data Flow

### Command Execution Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI as CLI Layer
    participant Proj as project.py
    participant Ops as *_ops.py
    participant YAML as yaml_parser.py
    participant File as .tasks/*.yml
    
    User->>CLI: simpletask criteria complete AC1
    CLI->>Proj: get_task_file_path(branch=None)
    Proj->>Proj: current_branch()
    Proj-->>CLI: .tasks/feature-x.yml
    CLI->>Ops: mark_criterion_complete(path, "AC1", True)
    Ops->>YAML: parse_task_file(path)
    YAML->>File: read YAML
    YAML->>YAML: validate with Pydantic
    YAML-->>Ops: SimpleTaskSpec
    Ops->>Ops: find criterion, set completed=True
    Ops->>YAML: write_task_file(path, spec)
    YAML->>YAML: update timestamp
    YAML->>File: write YAML
    Ops-->>CLI: success
    CLI-->>User: "Marked AC1 as completed"
```

### Task Creation Flow

```mermaid
sequenceDiagram
    participant User
    participant New as new.py
    participant Proj as Project
    participant Git as git.py
    participant YAML as yaml_parser.py
    participant File as .tasks/
    
    User->>New: simpletask new add-auth "Add user authentication"
    New->>Proj: ensure_project()
    Proj-->>New: Project instance
    New->>Proj: has_task("add-auth")
    Proj-->>New: False
    New->>New: create SimpleTaskSpec(branch="add-auth", ...)
    New->>Proj: ensure_tasks_dir()
    Proj->>File: mkdir .tasks/
    New->>YAML: write_task_file(.tasks/add-auth.yml, spec)
    YAML->>File: write YAML
    New->>Git: create_branch("add-auth")
    Git->>Git: checkout new branch
    New-->>User: "Created task and switched to branch"
```

## Key Design Decisions

### 1. Branch-Task Coupling
Every task is identified by its git branch name. The task file path is derived from the branch: `.tasks/<branch>.yml`. This enables automatic context switching - checking out a branch switches to that task's context.

### 2. Single Source of Truth
The YAML task file contains everything about a task: original prompt, acceptance criteria, implementation tasks, constraints, and progress. No external database or state management needed.

### 3. Strict Pydantic Validation
All models use `extra="forbid"` to reject unknown fields. This catches typos and ensures data integrity. The `acceptance_criteria` list must have at least one item.

### 4. Layer Separation
- **CLI Layer** (`commands/`): Handles argument parsing, user interaction, exit codes
- **Core Layer** (`core/`): Pure business logic, no Typer or Rich dependencies
- **Utils** (`utils/`): Cross-cutting concerns like console output

### 5. Graceful Git Degradation
Git operations return `None` or `False` on failure rather than raising exceptions. The `GIT_AVAILABLE` flag allows operation without GitPython installed.

### 6. Dual Validation Strategy
- **Pydantic**: Runtime validation during object creation (enforced)
- **JSON Schema**: Explicit validation via `simpletask schema validate` command (optional)

## Extension Points

### Adding a New CLI Command

1. Create module in `commands/` (e.g., `commands/report.py`)
2. Define function with Typer annotations
3. Register in `__init__.py`:
   ```python
   app.command(name="report")(report.report_command)
   ```

### Adding a New Subcommand Group

1. Create directory `commands/newgroup/`
2. Create `__init__.py` with `app = typer.Typer()`
3. Create command modules and register them
4. Register group in main `__init__.py`:
   ```python
   app.add_typer(newgroup.app, name="newgroup")
   ```

### Adding AI Editor Support

1. Create template directory: `cli/simpletask/templates/<editor>/`
2. Add template files in editor's format
3. Add functions in `core/ai_templates.py`:
   - `get_bundled_<editor>_templates()` - returns list of bundled template paths
   - `get_global_<editor>_commands_dir()` - returns global installation target (e.g., `~/.config/<editor>/commands/`)
   - `get_local_<editor>_commands_dir()` - returns local installation target (e.g., `./<editor>/commands/`)
   - `install_<editor>_templates()` - copies templates to target directory
   - `get_<editor>_installed_status()` - checks which templates are installed
4. Update `commands/ai/install.py` to add new `--<editor>` flag
5. Update `commands/ai/list.py` to show installation status

**Template Installation Targets** (examples):
- OpenCode: `~/.config/opencode/commands/` (global), `.opencode/commands/` (local)
- Qwen: `~/.qwen/commands/` (global), `.qwen/commands/` (local)

### Adding New Model Fields

1. Update `core/models.py` with new field (use default for backward compatibility)
2. Update JSON Schema in `cli/simpletask/schema/simpletask.schema.json`
3. Update reference schema in `schema/simpletask.schema.json`

## File Locations Reference

| Path | Purpose |
|------|---------|
| `.tasks/` | Task YAML files (one per branch) |
| `.tasks/<branch>.yml` | Task specification for a branch |
| `cli/simpletask/templates/opencode/` | Bundled OpenCode template files (`.md`) |
| `cli/simpletask/templates/qwen/` | Bundled Qwen template files (`.toml`) |
| `cli/simpletask/schema/task_schema.json` | JSON Schema for validation (bundled) |
| `schema/simpletask.schema.json` | JSON Schema for IDE integration (repository) |
