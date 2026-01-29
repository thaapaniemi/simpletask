# Task Splitting Patterns for simpletask

This guide provides comprehensive examples of how to split complex tasks into atomic subtasks (1-2 steps, 5-10 minutes each).

## Splitting Criteria

A task **MUST** be split if it meets ANY of these criteria:

1. **Step count:** Has >2 steps in the `steps` array
2. **File actions:** Has >1 file in the `files` array
3. **Done conditions:** Has >3 conditions in `done_when` array
4. **Goal complexity:** Goal description is >100 characters

## Atomic Task Rules

Each atomic subtask MUST have:
- **1-2 steps maximum** (preferably 1 step)
- **Single clear objective**
- **Completable in 5-10 minutes**
- **No ambiguity** - any LLM can execute without clarification

## Common Splitting Patterns

### Pattern 1: Model/Class Creation

Split into: file creation → fields → methods → constraints

**Before:**
```yaml
- id: T001
  name: Create User model
  goal: Define User database model with authentication fields
  steps:
    - Create src/models/user.py
    - Define User class with id, email, password_hash, created_at
    - Add unique constraint on email
    - Add password hashing methods
```

**After (split into 5 atomic subtasks):**
```yaml
- id: T001
  name: Create User model file with base structure
  goal: Create src/models/user.py with SQLAlchemy imports and User class skeleton
  steps:
    - Create file src/models/user.py with imports and User class inheriting from Base
  done_when:
    - File src/models/user.py exists and can be imported without errors
  
- id: T002
  name: Add User model fields
  goal: Add id, email, password_hash, created_at columns to User model
  steps:
    - Define Column fields: id (Integer, primary_key), email (String), password_hash (String), created_at (DateTime)
  done_when:
    - User model has all four fields defined
  prerequisites:
    - T001
  
- id: T003
  name: Add email unique constraint
  goal: Ensure email uniqueness at database level
  steps:
    - Add unique=True parameter to email Column definition
  done_when:
    - Email field has unique constraint in model definition
  prerequisites:
    - T002
  
- id: T004
  name: Implement hash_password method
  goal: Add password hashing using bcrypt
  steps:
    - Add static method hash_password(password: str) -> str to User class using bcrypt.hashpw
  done_when:
    - Method exists and can hash a test password
  prerequisites:
    - T002
  
- id: T005
  name: Implement verify_password method
  goal: Add password verification method
  steps:
    - Add method verify_password(self, password: str) -> bool using bcrypt.checkpw
  done_when:
    - Method exists and can verify hashed passwords
  prerequisites:
    - T004
```

---

### Pattern 2: API Endpoint Implementation

Split into: file → skeleton → validation → logic → token generation → error handling

**Before:**
```yaml
- id: T002
  name: Implement /login endpoint
  goal: Create login endpoint with validation and JWT
  steps:
    - Create src/api/auth.py
    - Add POST /login endpoint skeleton
    - Add request validation
    - Add password verification
    - Add JWT token generation
    - Add error handling
```

**After (split into 6 atomic subtasks):**
```yaml
- id: T006
  name: Create auth routes file
  goal: Create src/api/auth.py with router setup
  steps:
    - Create file src/api/auth.py with FastAPI router initialization
  
- id: T007
  name: Add /login endpoint skeleton
  goal: Define POST /login route with empty handler
  steps:
    - Add @router.post("/login") endpoint returning placeholder response
  prerequisites:
    - T006
  
- id: T008
  name: Add login request validation
  goal: Validate email and password in request body
  steps:
    - Create LoginRequest Pydantic model with email and password fields
    - Update /login endpoint to accept LoginRequest body
  prerequisites:
    - T007
  
- id: T009
  name: Implement password verification logic
  goal: Check user exists and password matches
  steps:
    - Query User by email, return 401 if not found
    - Call user.verify_password(password), return 401 if fails
  prerequisites:
    - T008
  
- id: T010
  name: Add JWT token generation
  goal: Generate and return JWT token on successful login
  steps:
    - Create JWT token with user_id claim using pyjwt
    - Return token in response body
  prerequisites:
    - T009
  
- id: T011
  name: Add login error handling
  goal: Handle exceptions and return appropriate error responses
  steps:
    - Wrap login logic in try/except for database and JWT errors
    - Return 500 with error message on exceptions
  prerequisites:
    - T010
```

---

### Pattern 3: Multi-File Feature

Split by file: one subtask per file operation

**Before:**
```yaml
- id: T003
  name: Add authentication middleware
  goal: Protect API routes with JWT validation
  steps:
    - Create middleware in src/middleware/auth.py
    - Implement token extraction from headers
    - Implement token validation logic
    - Update main.py to register middleware
    - Add middleware tests
```

**After (split into 5 atomic subtasks):**
```yaml
- id: T012
  name: Create auth middleware file
  goal: Create src/middleware/auth.py with middleware skeleton
  steps:
    - Create file with async middleware function accepting request and call_next
  
- id: T013
  name: Implement token extraction
  goal: Extract JWT token from Authorization header
  steps:
    - Add logic to get "Authorization" header and extract Bearer token
    - Return 401 if header missing or format invalid
  prerequisites:
    - T012
  
- id: T014
  name: Implement token validation
  goal: Validate JWT token and extract user_id
  steps:
    - Decode JWT using pyjwt, catch exceptions for invalid/expired tokens
    - Store user_id in request.state.user_id for downstream handlers
  prerequisites:
    - T013
  
- id: T015
  name: Register middleware in main.py
  goal: Wire up auth middleware to FastAPI app
  steps:
    - Import auth_middleware in main.py
    - Add app.middleware("http")(auth_middleware) call
  prerequisites:
    - T014
  
- id: T016
  name: Add middleware unit tests
  goal: Test token extraction and validation logic
  steps:
    - Create tests/test_auth_middleware.py with tests for valid token, missing token, invalid token
  prerequisites:
    - T015
```

---

### Pattern 4: Testing Task

Split by test case: one subtask per test or test group

**Before:**
```yaml
- id: T004
  name: Add authentication tests
  goal: Test all auth endpoints and flows
  steps:
    - Test user registration success
    - Test user registration validation
    - Test login success
    - Test login failure
    - Test protected route access
```

**After (split into 5 atomic subtasks):**
```yaml
- id: T017
  name: Test user registration success
  goal: Verify /register creates user and returns token
  steps:
    - Write test that POSTs valid email/password to /register
    - Assert 200 response and JWT token in body
  
- id: T018
  name: Test registration validation
  goal: Verify /register rejects invalid inputs
  steps:
    - Write test for invalid email format (returns 422)
    - Write test for missing password (returns 422)
  prerequisites:
    - T017
  
- id: T019
  name: Test login success
  goal: Verify /login returns token for valid credentials
  steps:
    - Write test that POSTs correct email/password to /login
    - Assert 200 response and JWT token matches user
  prerequisites:
    - T017
  
- id: T020
  name: Test login failure
  goal: Verify /login rejects invalid credentials
  steps:
    - Write test for wrong password (returns 401)
    - Write test for non-existent user (returns 401)
  prerequisites:
    - T019
  
- id: T021
  name: Test protected route access
  goal: Verify middleware blocks requests without valid token
  steps:
    - Write test accessing protected route without token (returns 401)
    - Write test with valid token (returns 200)
  prerequisites:
    - T020
```

---

### Pattern 5: Configuration + Implementation

Split into: config → setup → implementation → integration

**Before:**
```yaml
- id: T005
  name: Set up database connection
  goal: Configure PostgreSQL connection and create tables
  steps:
    - Add database URL to config
    - Create database connection pool
    - Define database models
    - Create migration script
    - Run migrations
```

**After (split into 5 atomic subtasks):**
```yaml
- id: T022
  name: Add database URL to configuration
  goal: Store PostgreSQL connection string in config
  steps:
    - Add DATABASE_URL to config/settings.py with default value
  
- id: T023
  name: Create database connection pool
  goal: Initialize SQLAlchemy engine and session maker
  steps:
    - Create src/db/connection.py with engine and SessionLocal setup
  prerequisites:
    - T022
  
- id: T024
  name: Define database base model
  goal: Create declarative base for all models
  steps:
    - Create src/db/base.py with Base = declarative_base()
  prerequisites:
    - T023
  
- id: T025
  name: Create initial migration script
  goal: Generate Alembic migration for initial schema
  steps:
    - Run alembic revision --autogenerate -m "Initial schema"
  prerequisites:
    - T024
  
- id: T026
  name: Run database migrations
  goal: Apply migrations to create tables
  steps:
    - Run alembic upgrade head to create all tables
  prerequisites:
    - T025
```

---

## Distributing Task Attributes

When splitting a complex task, properly distribute attributes to subtasks:

### Prerequisites
- **First subtask:** Inherits ALL prerequisites from original task
- **Subsequent subtasks:** Depend on previous subtask in the chain
- **Exception:** Parallel subtasks (e.g., multiple independent tests) can share same prerequisite

### File Actions
- Distribute `files` array entries to relevant subtasks
- Each subtask should typically modify only 1 file
- If subtask creates file: `action: create`
- If subtask modifies file: `action: modify`

### Done When Conditions
- Distribute `done_when` conditions to relevant subtasks
- Each subtask should have 1-2 specific done_when conditions
- Ensure conditions are verifiable (command output, file existence, test passes)

### Code Examples
- Analyze which subtask each `code_examples` entry applies to
- Attach code example to the most relevant subtask
- If code example shows overall pattern, attach to first subtask

---

## Subtask Naming Conventions

### Good Names (Action + Specific Target, <60 chars)
- ✅ "Create User model file with base structure"
- ✅ "Add email field to User model"
- ✅ "Implement hash_password method"

### Bad Names (Too vague or too broad)
- ❌ "Work on User model" (too vague)
- ❌ "Create User model and add all fields and methods" (too broad)

### Goal Convention (One sentence, 30-80 chars)
- ✅ "Create src/models/user.py with SQLAlchemy imports and User class skeleton"
- ✅ "Add id, email, password_hash, created_at columns to User model"
- ❌ "Set up user model" (too vague)

### Steps Convention (1-2 concrete actions with specifics)
- ✅ "Create file src/models/user.py with imports: from sqlalchemy import Column, String, DateTime; from .base import Base"
- ✅ "Define User class inheriting from Base with __tablename__ = 'users'"
- ❌ "Create user model file" (lacks detail)

---

## Edge Cases & Troubleshooting

### Already Atomic Task

If task has 1 simple step like "Add import statement to file.py":
- **Skip it** - do not split
- Keep in atomic_tasks list
- Preserve exactly as-is in final task list

### Task with Multiple Prerequisites

Original task: `prerequisites: [T001, T002, T005]`

**Handling:**
- First subtask inherits all: `prerequisites: [T001, T002, T005]`
- Subsequent subtasks depend on previous subtask

### Parallel vs Sequential Subtasks

**Sequential (default):**
```yaml
- id: T001
  prerequisites: []
- id: T002
  prerequisites: [T001]
- id: T003
  prerequisites: [T002]
```

**Parallel (when subtasks are independent):**
```yaml
- id: T001
  prerequisites: []
- id: T002
  prerequisites: [T001]  # Can run after T001
- id: T003
  prerequisites: [T001]  # Can run parallel with T002
- id: T004
  prerequisites: [T002, T003]  # Waits for both
```

### Circular Dependencies

If splitting creates circular prerequisites:
1. Identify the dependency cycle
2. Reorder subtasks to break the cycle
3. Some subtasks may need to be combined if truly inseparable

---

## Task ID Renumbering

After splitting, ALL task IDs must be renumbered sequentially:

**Before splitting:**
```yaml
tasks:
  - id: T001  # Complex task
  - id: T002  # Another task
  - id: T003  # Third task
```

**After splitting T001 into 3 subtasks:**
```yaml
tasks:
  - id: T001  # First subtask (was part of old T001)
  - id: T002  # Second subtask (was part of old T001)
  - id: T003  # Third subtask (was part of old T001)
  - id: T004  # Second task (was T002)
  - id: T005  # Third task (was T003)
```

**Update all prerequisite references:**
- Old task T002 had `prerequisites: [T001]`
- After split, it becomes T004 with `prerequisites: [T003]` (last subtask of split T001)

---

## Quality Checklist

Before considering splitting complete, verify:

- [ ] All complex tasks have been split (>2 steps, >1 file, >3 done_when, >100 char goal)
- [ ] Each subtask has 1-2 steps maximum
- [ ] Each subtask is completable in 5-10 minutes
- [ ] Task IDs are sequential (T001, T002, T003...)
- [ ] All prerequisite references are updated
- [ ] No circular dependencies exist
- [ ] File actions are distributed (1 file per subtask preferred)
- [ ] Done_when conditions are distributed and verifiable
- [ ] Code examples are attached to relevant subtasks
- [ ] Task names follow naming conventions (<60 chars, action + target)
- [ ] Task goals are clear and specific (30-80 chars)
- [ ] Steps are concrete with file paths, function names, specifics

---

## References

- **AGENTS.md** - Full simpletask development guide
- **README.md** - User-facing documentation for AI workflow templates
- **/simpletask.split** - The slash command that uses these patterns
