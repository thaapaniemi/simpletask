# Architecture

High-level system architecture for AI agents working with the codebase.

## Overview

Simpletask is an AI-friendly task definition manager that couples git branches with structured task specifications. Each feature branch has a corresponding YAML task file that serves as the single source of truth for requirements, acceptance criteria, and implementation progress.

**Core Design Principles:**

- **Branch-Task Coupling**: One task file per branch, branch name = task identifier
- **YAML as Single Source of Truth**: All task state lives in `.tasks/<branch>.yml`
- **Strict Validation**: Pydantic models with `extra="forbid"` reject unknown fields
- **Separation of Concerns**: CLI layer separated from core business logic
- **Convention over Configuration**: Fixed directory structure, no config files needed

## System Layers

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
    
    CLI --> CMD
    CMD --> PROJ
    PROJ --> GIT
    PROJ --> TASKS
    CMD --> OPS
    OPS --> YAML
    YAML --> MOD
    YAML --> TASKS
    VAL --> MOD
    GIT --> GITREPO
```

- **CLI Layer**: Handles argument parsing, user interaction, and exit codes via Typer
- **Core Layer**: Pure business logic with no CLI dependencies - models, file I/O, git operations
- **Storage**: Task YAML files in `.tasks/` directory, one per branch

## Domain Model

```mermaid
classDiagram
    class SimpleTaskSpec {
        +str schema_version
        +str branch
        +str title
        +str original_prompt
        +datetime created
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
    
    SimpleTaskSpec "1" *-- "1..*" AcceptanceCriterion : acceptance_criteria
    SimpleTaskSpec "1" *-- "0..*" Task : tasks
    SimpleTaskSpec --> TaskStatus : status
    Task --> TaskStatus : status
```

## Data Flow

Command execution follows this pattern (example: marking a criterion complete):

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
    YAML->>File: write YAML
    Ops-->>CLI: success
    CLI-->>User: "Marked AC1 as completed"
```

## Key Design Decisions

### Branch-Task Coupling

Every task is identified by its git branch name. The task file path is derived from the branch: `.tasks/<branch>.yml`. Checking out a branch switches to that task's context.

### Single Source of Truth

The YAML task file contains everything about a task: original prompt, acceptance criteria, implementation tasks, constraints, and progress. No external database or state management needed.

### Strict Pydantic Validation

All models use `extra="forbid"` to reject unknown fields. This catches typos and ensures data integrity. The `acceptance_criteria` list must have at least one item.

### Layer Separation

- **CLI Layer** (`commands/`): Argument parsing, user interaction, exit codes
- **Core Layer** (`core/`): Pure business logic, no Typer or Rich dependencies
- **Utils** (`utils/`): Cross-cutting concerns like console output
