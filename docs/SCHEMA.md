# Schema Reference

Task definition schema for simpletask YAML files (JSON Schema Draft 2020-12).

## Table of Contents

- [Overview](#overview)
- [Schema Evolution](#schema-evolution)
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

## Schema Evolution

SimpleTask schema has evolved through the following versions:

| Version | Released | Key Changes | Breaking? |
|---------|----------|-------------|-----------|
| **v1.0** | 2026-01-15 | Initial schema with basic task structure | - |
| **v1.1** | 2026-01-20 | Added required `created` timestamp field | Yes (requires timestamp) |
| **v1.2** | Skipped | Security issue: used raw command strings | Yes (deprecated immediately) |
| **v1.3** | 2026-01-23 | Added optional `quality_requirements` and `design` fields with structured tool+args | No (fully backward compatible) |

### Why v1.2 Was Skipped

Version 1.2 was introduced in commit `0a9e1fc` but immediately deprecated in commit `e936849` (same day) due to a security vulnerability. It used raw command strings for quality checks:

```yaml
# v1.2 format (INSECURE - do not use)
quality_requirements:
  linting:
    command: "ruff check ."  # Raw shell command - vulnerable to injection
```

This was replaced in v1.3 with structured, validated tool+args:

```yaml
# v1.3 format (SECURE)
quality_requirements:
  linting:
    enabled: true
    tool: ruff  # Whitelisted from ToolName enum
    args: ["check", "."]  # Validated arguments, no shell metacharacters
```

### Backward Compatibility

The current schema (v1.3) maintains backward compatibility:

- **v1.0 files**: Load successfully. Missing `created` field is auto-filled on write operations.
- **v1.1 files**: Load successfully. Work exactly as designed.
- **v1.2 files**: Will fail validation (but none should exist in practice).
- **v1.3 files**: Current format. `quality_requirements` and `design` are optional.

**Migration Strategy**: Since v1.2 never entered production and v1.3 is backward compatible with v1.0/v1.1, no migration tooling is needed. All existing task files continue to work.

## Schema Structure

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | Schema version (current: "1.3") |
| `branch` | string | Git branch name / task identifier |
| `title` | string | Human-readable task title |
| `original_prompt` | string | Verbatim user request that initiated the task |
| `created` | datetime | Task creation timestamp (ISO 8601 format) |
| `acceptance_criteria` | array | Criteria defining task completion (min 1 item) |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `quality_requirements` | object | Quality gates and checks (v1.3+, optional) |
| `design` | object | Design guidance and architectural context (v1.3+, optional) |
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
