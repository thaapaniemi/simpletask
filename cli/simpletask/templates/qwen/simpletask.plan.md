---
description: Create specification and implementation plan from feature description using simpletask.
---

User input: $ARGUMENTS

**CRITICAL: This is a PLANNING phase. DO NOT implement code or execute tasks. Your job is to create/update the task file with acceptance criteria and task breakdown - then STOP.**

**Step 0: Determine Branch Name**

1. **Analyze the user prompt to determine branch type prefix:**
   
   | If prompt contains... | Suggest prefix |
   |----------------------|----------------|
   | "fix", "bug", "error", "issue", "broken", "crash" | `fix/` |
   | "refactor", "cleanup", "improve", "optimize" | `refactor/` |
   | "test", "spec", "coverage" | `test/` |
   | "doc", "readme", "documentation" | `docs/` |
   | "chore", "config", "update deps", "upgrade", "bump" | `chore/` |
   | Default (new functionality) | `feature/` |

2. **Generate slug from description:**
   - Convert to lowercase
   - Remove stop words (the, a, an, for, to, of, in, on, at, by, with, from, as, is, are, was, were, be, have, has)
   - Filter words shorter than 3 characters
   - Take first 3-4 meaningful words, join with hyphens
   - Examples:
     - "Add user authentication" → `user-authentication`
     - "Fix login page crash" → `login-page-crash`
     - "Refactor database queries" → `database-queries`

3. **Construct suggested branch name:**
   - Format: `[prefix]/[slug]`
   - Examples:
     - `feature/user-authentication`
     - `fix/login-page-crash`
     - `refactor/database-queries`

4. **ASK USER TO CONFIRM OR CUSTOMIZE:**
   
   Present the suggested branch name and ask user to confirm or provide a custom name:
   
   ```
   Suggested branch name: feature/user-authentication
   
   Common prefixes:
     feature/  - New functionality
     fix/      - Bug fixes
     refactor/ - Code improvements
     chore/    - Maintenance tasks
     docs/     - Documentation
     test/     - Test additions
   
   Accept this branch name, or provide a custom name?
   ```
   
   - If user accepts → use the suggested name
   - If user provides custom name → use the custom name
   - Custom name should follow `prefix/slug` format

5. **Store the confirmed branch name as `[branch-name]` for subsequent steps.**

**Step 1: Check for Existing Task File**

1. Get current git branch name:
   ```bash
   git branch --show-current
   ```

2. Check if already on a feature branch with existing task file:
   
   **Preferred: Use MCP tool** (if simpletask MCP server is available)
   ```
   Use simpletask_get() MCP tool to check for existing task file:
   - Call simpletask_get(branch=None) to use current git branch
   - If successful, task file exists - analyze the response
   - If error occurs, task file does not exist
   ```
   
   **Fallback: Use CLI** (if MCP tools not available)
   ```bash
   simpletask show
   ```

3. If file exists for current branch:
   - Load and analyze the task data
   - If tasks are empty or minimal, proceed to Step 4 to add detailed tasks
   - If tasks already exist, analyze and report current state
   - Use current branch name as `[branch-name]`
   
4. If file does NOT exist:
   - If on main/master/develop: proceed to Step 2 to create new branch
   - If on other branch: ask user if they want to create task file for current branch or create new branch

**Note:** Branch names with slashes (e.g., `feature/user-auth`) are automatically normalized to filenames with hyphens (e.g., `.tasks/feature-user-auth.yml`). The MCP tools and CLI commands handle normalization automatically.

**Step 2: Create Git Branch (if needed)**

If creating a new branch (from Step 0's confirmed `[branch-name]`):
```bash
git checkout -b [branch-name]
```

Examples:
```bash
git checkout -b feature/user-authentication
git checkout -b fix/login-page-crash
git checkout -b refactor/database-queries
```

**Step 3: Create Task File**

Use simpletask CLI to create the task file:

**Preferred: Use MCP tool** (if simpletask MCP server is available)
```
Use simpletask_new() MCP tool to create task file:
- Call simpletask_new(branch="[branch-name]", title="[title]", prompt="[original prompt from $ARGUMENTS]", criteria=None)
- The MCP tool handles branch name normalization automatically
- Returns SimpleTaskWriteResponse with file_path and summary
- If criteria=None, creates placeholder criterion automatically
```

**Fallback: Use CLI** (if MCP tools not available)
```bash
simpletask new [branch-name] "[original prompt from $ARGUMENTS]" -y
```

This creates a task file with the basic structure.

**Note:** The branch name is normalized for the filename - slashes and special characters become hyphens, and it's converted to lowercase. For `feature/user-authentication`, the file will be `.tasks/feature-user-authentication.yml` (flat structure, normalized).

**Step 4: Plan Acceptance Criteria**

Add acceptance criteria using simpletask tools. Each criterion should be:
- Specific and verifiable
- Independent (can be tested individually)
- Focused on WHAT, not HOW

**Preferred: Use MCP tool** (if simpletask MCP server is available)
```
Use simpletask_criteria() MCP tool:
- Call simpletask_criteria(action="add", branch="[branch-name]", description="Criterion description")
- Returns SimpleTaskWriteResponse with updated criteria state
```

**Fallback: Use CLI** (if MCP tools not available)
```bash
simpletask criteria add "Criterion description" -b [branch-name]
```

Example acceptance criteria:
- AC1: "Feature X renders correctly in the UI"
- AC2: "API endpoint returns correct response format"
- AC3: "All existing tests pass"
- AC4: "New functionality is covered by unit tests"

**Step 4.5: Codebase Analysis & Design (MANDATORY)**

**Before creating implementation tasks, you MUST analyze the existing codebase to understand patterns, architecture, and quality requirements. This prevents review-phase issues.**

### 4.5.1: Find Reference Implementations

Search the codebase for similar features that can guide your implementation:

**Preferred: Use MCP tool** (if simpletask MCP server is available)
```
Use Task tool with explore subagent to find reference implementations:
- Search for similar features, components, or patterns
- Analyze how existing code handles similar requirements
- Identify naming conventions and code organization patterns
- Find test patterns to follow
```

**Fallback: Use search commands** (if MCP tools not available)
```bash
# Search for similar features
rg "pattern_name" --type py

# Find test patterns
find tests/ -name "*test_similar*.py"
```

### 4.5.2: Document Patterns to Follow

Use simpletask_design() MCP tool to store design decisions:

```
Use simpletask_design() MCP tool:
- Call simpletask_design(action="set", section="architecture", content="Description of patterns to follow")
- Call simpletask_design(action="set", section="patterns", content="Code patterns and conventions identified")
- Call simpletask_design(action="set", section="testing", content="Test patterns to follow")
```

Example design sections:
- **architecture**: "Follow MVC pattern, controllers in src/api/, models in src/models/"
- **patterns**: "Use dependency injection for services, follow existing error handling with try/except"
- **testing**: "Use pytest fixtures from conftest.py, follow AAA pattern"

### 4.5.3: Define Architectural Constraints

Identify constraints from the codebase:
- File organization rules (where different types of code belong)
- Naming conventions (function names, class names, variables)
- Import patterns (absolute vs relative, organization)
- Dependency rules (what can import what)

Add to task file constraints using simpletask_design():
```
simpletask_design(action="set", section="constraints", content="List of architectural constraints")
```

### 4.5.4: Identify Security Considerations

Check for security patterns in the codebase:
- Authentication/authorization patterns
- Input validation approaches
- Error message handling (don't leak sensitive info)
- Secrets management
- SQL injection prevention
- XSS prevention (if web app)

Document in design section:
```
simpletask_design(action="set", section="security", content="Security considerations and patterns")
```

### 4.5.5: Define Error Handling Pattern

Analyze how errors are handled:
- Custom exception classes?
- Error logging patterns?
- User-facing error messages?
- Validation error handling?

Document the pattern:
```
simpletask_design(action="set", section="error_handling", content="Error handling patterns to follow")
```

### 4.5.6: Define Quality Requirements

**Set quality requirements using simpletask_quality() MCP tool based on tech stack:**

**Option A: Use preset for common stacks**
```
Use simpletask_quality() MCP tool:
- Call simpletask_quality(action="preset", preset_name="[tech-stack]", branch="[branch-name]")
- Available presets: python, typescript, node, go, rust, java-maven, java-gradle
```

**Option B: Configure manually**
```
Use simpletask_quality() MCP tool to configure each requirement:
- simpletask_quality(action="set", config_type="linting", command="ruff check .", enable=True)
- simpletask_quality(action="set", config_type="testing", command="pytest", enable=True, min_coverage=80)
- simpletask_quality(action="set", config_type="type_checking", command="mypy src/", enable=True)
- simpletask_quality(action="set", config_type="formatting", command="black --check .", enable=True)
```

**Fallback: Use CLI** (if MCP tools not available)
```bash
simpletask quality preset python -b [branch-name]
# or manually configure:
simpletask quality set linting --command "ruff check ." --enable -b [branch-name]
simpletask quality set testing --command "pytest" --enable --min-coverage 80 -b [branch-name]
```

**Available presets:** python, typescript, node, go, rust, java-maven, java-gradle

**Step 6: Plan Implementation Tasks**

Add detailed implementation tasks. Each task MUST be:
- Completable in 5-30 minutes
- Detailed enough for ANY LLM to execute without clarification
- Include specific file paths, function names, and code patterns

For each task, use:

**Preferred: Use MCP tool** (if simpletask MCP server is available)
```
Use simpletask_task() MCP tool:
- Call simpletask_task(action="add", branch="[branch-name]", name="Task name", goal="Detailed goal description", steps=["step1", "step2", ...])
- Returns SimpleTaskWriteResponse with updated task state
- If steps parameter is omitted or None, a placeholder step is added automatically
```

**Fallback: Use CLI** (if MCP tools not available)
```bash
simpletask task add "Task name" -g "Detailed goal description" -b [branch-name]
```

**Task Structure Requirements:**

Each task in the YAML should include (edit the file directly for full detail):

```yaml
tasks:
  - id: T001
    name: Short descriptive name
    status: not_started
    goal: One sentence explaining what this task accomplishes
    steps:
      - "First specific action - be explicit about what code to write/change"
      - "Second specific action - include function names, variable names"
      - "Third specific action - mention exact line numbers or sections if applicable"
    done_when:
      - "Specific, verifiable outcome 1"
      - "Test command passes: pytest tests/test_feature.py"
    prerequisites:
      - T001  # List task IDs that must complete first (or omit if none)
    files:
      - path: src/path/to/file.py
        action: create  # or modify, delete
    code_examples:
      - language: python
        description: Pattern to follow for this task
        code: |
          # Example code snippet showing expected pattern
          def example_function():
              pass
```

**Step 7: Add Context and Constraints**

Edit `.tasks/[branch-name].yml` directly to add:

1. **Constraints** - Boundaries the agent must follow:
   ```yaml
   constraints:
     - "Do not modify files in src/core/legacy/"
     - "Follow existing error handling patterns"
     - "No new dependencies without approval"
   ```

2. **Context** - Helpful information for implementation:
   ```yaml
   context:
     technical_approach: "Brief description of implementation approach"
     related_files:
       - src/existing/similar_feature.py
       - tests/test_similar.py
     dependencies:
       - name: library-name
         purpose: What it's used for
     gotchas:
       - "Edge case 1 to watch for"
       - "Known pitfall to avoid"
   ```

**Step 8: Validate and Summarize**

1. Validate the task file:
   
   **Preferred: Use MCP tool** (if simpletask MCP server is available)
   ```
   Use simpletask_get() MCP tool with validation:
   - Call simpletask_get(branch="[branch-name]", validate=True)
   - Check validation.valid in response
   - If validation.valid is False, check validation.errors for details
   ```
   
   **Fallback: Use CLI** (if MCP tools not available)
   ```bash
   simpletask schema validate
   ```

2. Show the complete task:
   
   **Preferred: Use MCP tool** (if simpletask MCP server is available)
   ```
   Use simpletask_get() MCP tool:
   - Display spec.branch, spec.title, spec.status
   - Display summary.criteria_total, summary.tasks_total
   - Show acceptance_criteria and tasks arrays
   ```
   
   **Fallback: Use CLI** (if MCP tools not available)
   ```bash
   simpletask show
   ```

3. Report completion:
   ```
   Task file created/updated: .tasks/[normalized-branch-name].yml
   
   Summary:
   - Branch: [branch-name]
   - Title: [title]
   - Acceptance Criteria: [count]
   - Implementation Tasks: [count]
   - Status: not_started
   
   Ready for implementation:
   - Run /simpletask.implement to execute tasks
   - Run simpletask task list to see all tasks
   - Run simpletask criteria list to see acceptance criteria
   ```

---

## Task Planning Guidelines

### Task Granularity
- Each task should take 5-30 minutes to complete
- Break complex tasks into smaller, focused steps
- One task = one logical unit of work

### Task Prerequisites
- Use `prerequisites: [T001, T002]` to define dependencies
- Tasks without prerequisites can run in parallel
- Build a clear execution DAG (Directed Acyclic Graph)

### File Actions
- `create`: New file that doesn't exist
- `modify`: Changes to existing file
- `delete`: Remove file (rare, use with caution)

### Verification Steps
Every task MUST include `done_when` conditions:
- Test commands to run: `pytest tests/test_X.py`
- Expected outcomes: "Function returns correct value"
- Manual verification: "UI displays correctly"

### Code Examples
Include code examples when:
- The pattern is non-obvious
- Following existing codebase conventions
- Complex logic needs to be shown
- Less capable LLMs need guidance

---

## Example Task File Structure

```yaml
# yaml-language-server: $schema=../../schema/simpletask.schema.json
schema_version: "1.0"
branch: feature/user-auth
title: Add user authentication to the application
original_prompt: "Add user login and registration with JWT tokens"
status: not_started
created: "2026-01-18T10:00:00Z"
updated: "2026-01-18T10:00:00Z"

acceptance_criteria:
  - id: AC1
    description: Users can register with email and password
    completed: false
  - id: AC2
    description: Users can log in and receive JWT token
    completed: false
  - id: AC3
    description: Protected routes require valid JWT
    completed: false
  - id: AC4
    description: All new code has unit test coverage
    completed: false

constraints:
  - "Use existing database connection patterns"
  - "Follow REST API conventions from existing endpoints"
  - "Store passwords using bcrypt hashing"

context:
  technical_approach: "JWT-based authentication with refresh tokens"
  related_files:
    - src/api/routes.py
    - src/models/base.py
  dependencies:
    - name: pyjwt
      purpose: JWT token generation and validation
    - name: bcrypt
      purpose: Password hashing
  gotchas:
    - "Ensure token expiry is configurable"
    - "Handle token refresh edge cases"

tasks:
  - id: T001
    name: Create User model
    status: not_started
    goal: Define User database model with authentication fields
    steps:
      - Create src/models/user.py
      - Define User class with id, email, password_hash, created_at
      - Add unique constraint on email
      - Add password hashing methods
    done_when:
      - File exists at src/models/user.py
      - User model can be imported without errors
      - Password hashing works correctly
    files:
      - path: src/models/user.py
        action: create
    code_examples:
      - language: python
        description: User model pattern
        code: |
          from sqlalchemy import Column, String, DateTime
          from .base import Base
          import bcrypt

          class User(Base):
              __tablename__ = "users"
              # ... fields

  - id: T002
    name: Create auth routes
    status: not_started
    goal: Implement /register and /login API endpoints
    steps:
      - Create src/api/auth.py
      - Implement POST /register endpoint
      - Implement POST /login endpoint
      - Add JWT token generation
    done_when:
      - POST /register creates user and returns token
      - POST /login validates credentials and returns token
      - Invalid credentials return 401
    prerequisites:
      - T001
    files:
      - path: src/api/auth.py
        action: create
      - path: src/api/routes.py
        action: modify

  - id: T003
    name: Add authentication tests
    status: not_started
    goal: Write comprehensive tests for auth functionality
    steps:
      - Create tests/test_auth.py
      - Test user registration success and validation
      - Test login success and failure cases
      - Test JWT token validation
    done_when:
      - pytest tests/test_auth.py passes
      - Coverage includes all auth code paths
    prerequisites:
      - T001
      - T002
    files:
      - path: tests/test_auth.py
        action: create
```

---

## Task Execution Order

After planning, tasks should be executed based on prerequisites:

```
Execution Order:
1. T001 (no prerequisites - start here)
2. T002, T003 (can run in parallel after T001)
3. [Continue based on dependency graph...]

Final Verification:
- All tasks have status: completed
- All acceptance criteria have completed: true
- simpletask schema validate passes
```

---

**STOP HERE. Do NOT proceed to implementation.**

The planning phase is complete when:
1. Task file exists at `.tasks/[normalized-branch-name].yml` (branch name converted to lowercase with special chars as hyphens)
2. All acceptance criteria are defined
3. All implementation tasks are detailed with steps, done_when, and prerequisites
4. `simpletask schema validate` passes
