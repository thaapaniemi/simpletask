# simpletask in the Spec-Driven Development Landscape

The ecosystem around AI-assisted software development has rapidly stratified into distinct tooling categories. This document positions simpletask within that landscape and provides direct comparisons with named tools in each relevant category.

---

## Where simpletask sits

The emerging SDD (Spec-Driven Development) stack is typically described as four layers:

| Layer | Role | Examples |
|---|---|---|
| **1. Spec Frameworks** | Define requirements, architecture, acceptance criteria | BMAD, cc-sdd, Spec Kit, OpenSpec |
| **2. Planning & Task Systems** | Convert specs into executable task graphs | Taskmaster, Agent OS, Beads, SDD_Flow |
| **3. Execution Agents** | Write and modify code autonomously | Devika, OpenDevin, CrewAI |
| **4. AI IDEs** | Integrate planning and execution into developer tools | Cursor, Windsurf, Claude Code, OpenCode |

**simpletask spans Layers 1 and 2.** It creates structured specifications (Layer 1) and breaks them into tracked, executable task graphs (Layer 2). It then exposes those tasks to Layer 3 agents via MCP — but does not perform execution itself.

---

## 1. Schema-enforced specification vs. freeform markdown

**The comparison:** Spec Kit, OpenSpec, BMAD, and cc-sdd are Layer 1 tools that generate freeform markdown artifacts: `SPEC.md`, `ARCHITECTURE.md`, `TASKS.md`. These are human-readable but structurally ambiguous — an AI agent consuming them must interpret prose.

**What simpletask does differently:** Task files are strictly validated YAML, governed by a JSON Schema and parsed through Pydantic v2 models with `extra="forbid"`. Every field — acceptance criteria, task status, prerequisites, quality thresholds, architectural patterns — is a typed entity, not a paragraph. An AI agent reading a simpletask file via MCP receives structured data objects, not text to interpret.

**Where this matters:** Structured data eliminates a class of hallucination risk where the agent misreads or misinterprets a requirement. It also enables programmatic CRUD operations via MCP tools, which is not practical on freeform markdown.

**Note:** This comparison applies specifically to Layer 1 spec frameworks. Layer 2 tools like Taskmaster use structured JSON internally, so this distinction does not hold uniformly across all 30+ tools in the ecosystem.

---

## 2. Ephemeral branch lifecycle

**The comparison:** Taskmaster stores tasks in tracked JSON files committed to the repository. BMAD commits markdown specs. Agent OS maintains persistent project state. These approaches treat the task definition as a long-lived project artifact.

**What simpletask does differently:** Task files live in `.tasks/` which is git-ignored by default. They are tied to a specific git branch by name (e.g. `feature/auth` → `.tasks/feature-auth.yml`). When the branch is merged and deleted, the task file disappears.

**The design intent:** simpletask treats task definitions as an ephemeral implementation scratchpad, not a permanent project record. The specification is only relevant while the branch exists. This keeps the repository clean — no accumulation of stale task artifacts across dozens of feature branches — and avoids the problem of stale task state misleading future agents or developers.

**Trade-off to be aware of:** This is a deliberate constraint. If you want persistent task history across the project lifetime, simpletask is not the right tool. It is scoped to a single branch's implementation cycle.

---

## 3. MCP provider vs. MCP orchestrator

**The comparison:** Taskmaster and several other Layer 2 tools are also MCP-native — they expose tools to AI editors via the Model Context Protocol. This means the "MCP integration" claim alone is no longer a meaningful differentiator.

**What simpletask does differently:** simpletask is a pure MCP *provider*. It exposes CRUD operations for task state (`simpletask_task`, `simpletask_criteria`, `simpletask_quality`, etc.) and nothing else. It has no execution routing logic, no agent spawning, no workflow orchestration. The execution agent — whether that is OpenCode, Cursor, Claude Code, or any other MCP client — makes all decisions about what to do next.

**Why this distinction matters:** Tools that are both MCP-exposed *and* execution orchestrators (Agent OS, some Taskmaster configurations) create a coupling between task state and the specific orchestration system. simpletask's separation means the same task file can be consumed by any MCP-compatible agent without modification. Switching AI editors does not invalidate your task definitions.

---

## 4. Quality requirements as part of the specification

**The comparison:** Taskmaster, BMAD, SDD_Flow, and similar tools define *what* to build. Verification of the result — running tests, type checking, linting — is left to the developer's existing CI/CD setup or handled manually after the agent completes its work.

**What simpletask does differently:** Quality requirements are a first-class field inside the task spec itself:

```yaml
quality_requirements:
  linting:
    enabled: true
    tool: ruff
    args: ["check", "."]
  type_checking:
    enabled: true
    tool: mypy
    args: ["."]
  testing:
    enabled: true
    tool: pytest
    args: ["--cov=src", "--cov-report=term-missing"]
    min_coverage: 80
```

These are typed, validated fields — not comments or freeform notes. An AI agent can read them via `simpletask_quality(action="get")` and run them via `simpletask_quality(action="check")`, receiving structured pass/fail results back into context. The spec describes not just *what* to build but *how to verify it was built correctly*.

---

## 5. Design guidance as structured data

**The comparison:** Most Layer 1 and Layer 2 tools have no standardised field for architectural guidance. Design decisions either live in freeform prose within the spec, in separate architecture documents, or not at all.

**What simpletask does differently:** The `design` section of a task spec is structured YAML with typed fields:

```yaml
design:
  patterns:
    - repository
    - dependency_injection
  architectural_constraints:
    - "Use Pydantic models with extra='forbid'"
    - "No shell=True in subprocess calls"
  reference_implementations:
    - path: "cli/simpletask/mcp/server.py"
      reason: "MCP tool pattern to follow"
  security:
    - category: input_validation
      description: "Validate all user inputs"
  error_handling: exceptions
```

Architectural patterns come from an enumerated set (repository, service_layer, factory, mvc, hexagonal, etc.). Security categories are enumerated (authentication, authorization, input_validation, etc.). This means an AI agent receives design guidance as structured constraints it can reason about and validate against — not as prose it must extract and interpret.

---

## 6. Cognitive atomicity via task splitting

**The comparison:** Layer 2 tools generally accept tasks as defined by the user or generated by a spec framework, with no built-in mechanism to enforce an upper bound on task complexity before handing to an execution agent.

**What simpletask does differently:** The `/simpletask.split` command enforces objective splitting criteria before execution begins. A task is split if it has any of:

- More than 2 steps in the `steps` array
- More than 1 file in the `files` array
- More than 3 conditions in `done_when`
- More than 100 characters in the goal description

The result is a set of atomic tasks, each targeting 1-2 implementation steps, with all prerequisite chains updated. The split operation also populates the `design` section by analysing the codebase before breaking tasks down.

The purpose is to reduce the surface area of each individual agent execution to a scope where completion can be verified unambiguously — not as a stylistic preference but as a measurable constraint.

---

## 7. What simpletask is not

Being explicit about scope boundaries is useful when evaluating fit.

| Category | Tools | simpletask position |
|---|---|---|
| **Execution agents** | Devika, OpenDevin, CrewAI | simpletask does not write or modify code |
| **Spec-as-source compilers** | Tessl, Intent-driven platforms | simpletask does not generate code from specs |
| **Team project management** | Linear, Jira, GitHub Projects | simpletask has no multi-user or persistent-history model |
| **Cloud-hosted planning platforms** | Various SaaS task systems | simpletask is local-only, no server component |
| **Full-stack orchestrators** | LangGraph, AutoGen | simpletask has no agent routing or multi-agent coordination |

simpletask is a local, branch-scoped, schema-enforced task definition layer. It is intended to be used alongside an execution agent and an AI IDE — not as a replacement for either.

---

## 8. Direct tool comparisons

### Comparison matrix

| Dimension | simpletask | Taskmaster | cc-sdd | BMAD | SDD_Flow |
|---|---|---|---|---|---|
| **Storage format** | YAML (Pydantic-validated) | JSON | Markdown | YAML + Markdown | Markdown templates |
| **Committed to git** | No (git-ignored) | Yes | Yes | Yes | Yes |
| **Scope** | Branch | Project | Feature | Project | Project |
| **MCP tools** | 11 tools | 36 tools | No (slash commands) | No | No |
| **Schema validation** | Yes (JSON Schema + Pydantic) | Partial (internal) | No | No | No |
| **Quality gates** | Typed, machine-executable | No | Manual approval checkpoints | Manual checklists | Manual review phases |
| **Design guidance** | Typed structured fields | Free-form notes only | Prose templates | ADR templates + 12 agents | Design phase templates |
| **Task atomicity enforcement** | Yes (`/simpletask.split`) | AI complexity scoring | Parallel wave labels | No | No |
| **Ephemeral lifecycle** | Yes (dies with branch) | No | No | No | No |
| **Editor support** | OpenCode, Qwen, Gemini | Cursor, Windsurf, Lovable, Roo, VS Code, Claude Code, Codex, Q Developer | OpenCode, Qwen, Gemini, Cursor, Codex, Copilot, Windsurf, Claude Code | Claude Code, Cursor, and others | Any LLM (copy-paste) |

---

### Taskmaster

**What it is:** Taskmaster (also known as `task-master-ai`) is a project-level task management system with 25.9k GitHub stars and broad adoption. Tasks are stored in `.taskmaster/tasks.json`, committed to the repository, and scoped to the entire project rather than individual branches. It exposes 36 MCP tools and is configured to work with multiple AI editors including Cursor, Windsurf, VS Code, and Claude Code.

**Where it overlaps with simpletask:** Both tools use structured data formats (Taskmaster uses JSON, simpletask uses YAML), both expose MCP tools for AI agent consumption, and both support task decomposition. Taskmaster's `expand_task` tool and simpletask's `/simpletask.split` command serve a similar purpose — breaking complex tasks into smaller units before handing them to an execution agent.

**Where Taskmaster goes further:** Taskmaster has a richer task prioritisation model (high/medium/low priority), AI-driven complexity scoring that recommends how many subtasks to generate, multi-model configuration (separate models for generation, research, and fallback), and a significantly larger MCP surface area (36 tools vs. 11). Its `parse_prd` tool can generate an initial task graph directly from a product requirements document.

**Where simpletask differs:** Taskmaster's `tasks.json` is committed to git and scoped to the project — it accumulates state across all features and branches. simpletask's task files are git-ignored and die with the branch. This means simpletask produces no long-lived tracking artifacts in the repository, but also means there is no persistent task history. Taskmaster has no equivalent to simpletask's typed `quality_requirements` or `design` fields — implementation notes live in a free-form `details` string. Taskmaster does not enforce objective splitting criteria; the `expand_task` command uses AI judgment rather than measurable thresholds.

---

### cc-sdd

**What it is:** cc-sdd is a feature-scoped spec framework with 2.8k GitHub stars. It organises work into per-feature directories (`.kiro/specs/<feature>/`) containing phased markdown artifacts: `requirements.md`, `design.md`, and `tasks.md`. It supports 8 AI editors including OpenCode, Qwen, Gemini, Cursor, Codex, Copilot, Windsurf, and Claude Code. Files are committed to git and designed to be long-lived project artifacts.

**Where it overlaps with simpletask:** cc-sdd is the closest conceptual match in the Layer 1 category. It is feature-scoped (closer to branch-scoped than project-scoped tools), supports multiple editors including OpenCode and Qwen, includes a design guidance phase, and provides a structured phased workflow with checkpoints. Its `/simpletask.split`-equivalent is the parallel wave model (P0/P1/P2 task labels) that groups tasks by dependency layer.

**Where cc-sdd goes further:** cc-sdd has broader editor support out of the box (8 editors). It includes a gap analysis command (`/kiro:validate-gap`) for brownfield projects and a steering command (`/kiro:steering`) that captures project-wide architectural memory. Its Kiro-compatible format means specs are portable across any Kiro-compatible tooling.

**Where simpletask differs:** cc-sdd's artifacts are markdown files committed to git — structurally ambiguous and not machine-validated. Approval gates between phases are manual checkpoints that require human sign-off, not machine-executable quality checks. cc-sdd has no MCP server; it operates exclusively through slash commands, meaning an AI agent cannot programmatically query or update task state. It has no equivalent to simpletask's typed `quality_requirements` section — quality verification is a workflow step, not a spec field. Its design guidance lives in prose templates rather than typed YAML fields with enumerated values.

---

### BMAD

**What it is:** BMAD (Breakthrough Method for Agile AI Driven Development) is a project-level methodology framework with 40.3k GitHub stars. It uses 12+ specialised AI agents (PM, Architect, Dev, QA, SM, Analyst, UX Expert, and others) to guide a hybrid Waterfall-Agile workflow from ideation to delivery. Configuration lives in project-local directories as YAML and markdown templates. It includes quality checklists and ADR (Architecture Decision Record) templates. BMAD supports multiple AI IDEs including Claude Code, Cursor, and others.

**Where it differs from simpletask:** BMAD has no MCP server and no programmatic task interface — it is a configuration framework for AI IDE slash commands. Quality gates are manual checklists reviewed by agents, not machine-executable checks. Tasks are project-scoped, committed to git, and not tied to individual branch lifecycles. The extensive agent team and ADR templates make it better suited to teams building large systems from scratch, whereas simpletask targets a single developer working on a defined feature branch.

---

### SDD_Flow

**What it is:** SDD_Flow is a documentation and template library, not a software tool. It provides markdown templates and prompt files for a 7-phase Waterfall-Agile hybrid workflow. Templates are copy-pasted into AI chats or adapted as custom slash commands via symlinks. It has no programmatic interface, no MCP server, and no schema validation.

**Where it differs from simpletask:** SDD_Flow has no machine-readable task state, no programmatic query interface, and no quality gate execution. It is a methodology guide, not a task management system. The comparison is relevant mainly as context — SDD_Flow represents the lowest-infrastructure end of the spectrum (markdown templates + any LLM), while simpletask sits at the structured-data end with schema enforcement and MCP tooling.
