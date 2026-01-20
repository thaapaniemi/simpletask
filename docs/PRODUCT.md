# simpletask Product Overview

**AI-friendly task definitions for branch-based development workflows**

## What is simpletask?

simpletask is a CLI tool that bridges the gap between human developers and AI coding assistants. It provides a structured way to define, track, and communicate development tasks through YAML files automatically linked to git branches.

Rather than relying on scattered notes, chat histories, or ambiguous instructions, simpletask creates a single source of truth for each development task that both humans and AI can understand and act upon.

## The Problem

When working with AI coding assistants, developers face common challenges:

- **Context loss** - AI assistants forget context between sessions
- **Ambiguous requirements** - Natural language instructions lack precision
- **Progress tracking** - No clear way to track what's done vs. what remains
- **Reproducibility** - Task definitions live in chat logs, not version control

simpletask solves these by providing structured, version-controllable task definitions that persist across sessions and can be directly consumed by AI tools.

## Key Features

### Branch-Aware Task Management

Every task file is automatically linked to a git branch. When you switch branches, simpletask knows which task you're working on.

```
feature/user-auth  -->  .tasks/feature-user-auth.yml
bugfix/issue-123   -->  .tasks/bugfix-issue-123.yml
```

### Structured Task Definitions

Task files capture everything needed to complete work:

| Component | Purpose |
|-----------|---------|
| **Title & Prompt** | What was requested and why |
| **Acceptance Criteria** | Measurable conditions for completion |
| **Constraints** | Boundaries and requirements to follow |
| **Implementation Tasks** | Step-by-step breakdown with status |
| **Context** | Related files, dependencies, examples |

### Progress Tracking

Track completion at two levels:

- **Acceptance Criteria** - High-level "definition of done" items
- **Implementation Tasks** - Granular work items with status (`not_started`, `in_progress`, `completed`, `blocked`)

### AI-Native Integration

simpletask includes an MCP (Model Context Protocol) server that exposes task operations as structured tools. AI editors like Claude Desktop and OpenCode can:

- Query current task status and acceptance criteria
- Understand implementation steps and constraints
- Track progress as work completes
- Access task context without manual copy/paste

---

## How It Works

### Task Lifecycle

```
1. CREATE    simpletask new "Add user authentication" --branch feature/auth
2. DEFINE    Add acceptance criteria and constraints
3. PLAN      Break down into implementation tasks
4. EXECUTE   Work through tasks, updating status
5. COMPLETE  Mark criteria complete as conditions are met
```

### Task File Structure

```yaml
schema_version: "1.0"
branch: feature/user-auth
title: Add user authentication
original_prompt: "Implement JWT-based login with email/password"
status: in_progress

acceptance_criteria:
  - id: AC1
    description: Users can log in with email and password
    completed: true
  - id: AC2
    description: Invalid credentials return appropriate error
    completed: false

constraints:
  - Use existing bcrypt library for password hashing
  - Follow OWASP authentication guidelines

tasks:
  - id: T001
    name: Create login endpoint
    status: completed
    goal: POST /api/login accepts credentials and returns JWT
  - id: T002
    name: Add password validation
    status: in_progress
    goal: Validate password against stored hash
```

### AI Assistant Integration

With the MCP server running (`simpletask serve`), AI assistants receive structured task data:

```json
{
  "title": "Add user authentication",
  "status": "in_progress",
  "criteria_completed": 1,
  "criteria_total": 2,
  "tasks_completed": 1,
  "tasks_in_progress": 1
}
```

This enables AI to:
- Understand the full scope before starting work
- Know exactly which acceptance criteria remain
- Follow defined constraints automatically
- Update task status as work progresses

## Use Cases

### Solo Developer + AI Assistant

Define tasks once, then seamlessly continue work across multiple AI sessions. The task file persists context that would otherwise be lost.

### Feature Development

Break complex features into tracked implementation tasks. Both you and your AI assistant can see what's done, what's next, and what's blocked.

### Code Review Preparation

Task files document the "why" behind changes. Reviewers can reference acceptance criteria to understand intent.

### Team Handoffs

When passing work between developers or AI agents, the task file captures full context: original requirements, constraints, progress, and remaining work.

## Summary

| Aspect | simpletask Approach |
|--------|---------------------|
| **Storage** | YAML files in `.tasks/` directory |
| **Linking** | Automatic git branch association |
| **Tracking** | Acceptance criteria + implementation tasks |
| **Validation** | JSON Schema ensures consistency |
| **AI Access** | MCP server with structured tools |
| **Version Control** | Human-readable, diff-friendly format |

simpletask transforms ad-hoc AI interactions into structured, trackable, reproducible development workflows.
