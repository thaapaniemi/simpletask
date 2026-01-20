# Schema Reference

Task definition schema for simpletask YAML files (JSON Schema Draft 2020-12).

## Table of Contents

- [Overview](#overview)
- [Schema Structure](#schema-structure)
  - [Required Fields](#required-fields)
  - [Optional Fields](#optional-fields)
  - [Acceptance Criterion](#acceptance-criterion)
  - [Task](#task)
  - [File Action](#file-action)
  - [Code Example](#code-example)
- [Status Values](#status-values)
- [Example](#example)

## Overview

SimpleTask uses a JSON Schema to validate task definition files stored in `.tasks/`. The schema ensures consistent structure across all task files and enables tooling support.

Task files are YAML documents that define:
- What the task is (title, original prompt)
- When it's done (acceptance criteria)
- How to implement it (tasks with steps)
- What to avoid (constraints)

## Schema Structure

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | Schema version (e.g., "1.0") |
| `branch` | string | Git branch name / task identifier |
| `title` | string | Human-readable task title |
| `original_prompt` | string | Verbatim user request that initiated the task |
| `acceptance_criteria` | array | Criteria defining task completion (min 1 item) |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `constraints` | array[string] | Boundaries the agent must follow |
| `context` | object | Flexible context (requirements, dependencies, etc.) |
| `tasks` | array | Implementation tasks |

### Acceptance Criterion

```yaml
acceptance_criteria:
  - id: AC1
    description: "What must be true"
    completed: false
```

**Required fields:** `id`, `description`, `completed`

### Task

```yaml
tasks:
  - id: T001
    name: Short task name
    status: not_started
    goal: What this task achieves
    steps:
      - Step one
      - Step two
    done_when:              # optional
      - Condition one
      - "command succeeds"
    prerequisites: [T000]   # optional
    files:                  # optional
      - path: src/file.py
        action: create
    code_examples:          # optional
      - language: python
        code: |
          def example():
              pass
```

**Required fields:** `id`, `name`, `status`, `goal`, `steps`

### File Action

```yaml
files:
  - path: src/example.py
    action: create | modify | delete
```

**Required fields:** `path`, `action`

### Code Example

```yaml
code_examples:
  - language: python
    description: Optional description
    code: |
      # code here
```

**Required fields:** `language`, `code`

## Status Values

Used for `tasks[].status`:

| Value | Description |
|-------|-------------|
| `not_started` | Work has not begun |
| `in_progress` | Currently being worked on |
| `blocked` | Cannot proceed (dependency/issue) |
| `completed` | Done |

## Example

Minimal valid task file:

```yaml
schema_version: "1.0"
branch: fix/typo-readme
title: Fix typo in README
original_prompt: "Fix the typo in README.md line 42"

acceptance_criteria:
  - id: AC1
    description: Typo is corrected
    completed: false
```
