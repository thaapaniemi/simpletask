# Changelog

All notable changes to simpletask are documented here.

## [0.28.0] - 2026-03-16

Initial public release on GitHub.

### Added

- MCP server (`simpletask serve`) with 11 tools for AI editor integration
- AI workflow slash commands for OpenCode, Qwen CLI, and Gemini CLI
  - `/simpletask.plan` — create task specification from feature description
  - `/simpletask.split` — split complex tasks into atomic subtasks
  - `/simpletask.implement` — execute tasks step-by-step
  - `/simpletask.review` — review implementation against acceptance criteria
- `simpletask-plan` OpenCode agent for autonomous task planning
- Task iterations for grouping related tasks into sprints or work periods
- Root-level and task-level notes (`simpletask note`)
- Implementation constraints (`simpletask constraint`)
- Context key-value store (`simpletask context`)
- Design guidance section with patterns, references, security, and error handling
- Quality requirements with presets for Python, TypeScript, Go, Rust, Java
- Custom quality presets via `.simpletask/presets.yaml`
- Batch task operations (atomic, all-or-nothing)
- JSON schema validation for task files
- Git hooks for version bumping, conventional commits, and pre-push tests
- GitHub Actions CI (Python 3.11 and 3.12)
- Dependabot for automated dependency updates
