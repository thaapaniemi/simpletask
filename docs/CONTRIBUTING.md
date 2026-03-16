# Contributing to simpletask

## Quick Start

```sh
git clone https://github.com/thaapaniemi/simpletask.git
cd simpletask
pip install -e ".[dev]"
./scripts/install-hooks.sh
pytest  # Verify setup
```

## Development Commands

| Task | Command |
|------|---------|
| Format | `ruff format .` |
| Lint | `ruff check .` |
| Type check | `mypy cli/simpletask` |
| Test | `pytest` |
| Test + coverage | `pytest --cov=cli/simpletask --cov-report=term-missing` |

## Code Standards

- **Type hints**: Python 3.11+ native syntax (`list[str]`, `dict[str, Any] | None`)
- **Pydantic**: Use `extra="forbid"` on all models
- **Docstrings**: Google style
- **Line length**: 100 characters max

## Commit Guidelines

[Conventional Commits](https://conventionalcommits.org/) format required (enforced by git hooks).

| Type | Use for |
|------|---------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `refactor` | Code restructuring |
| `test` | Adding/updating tests |
| `chore` | Maintenance tasks |

**Examples:** `feat: add export command`, `fix(cli): handle empty input`

## Version Bumping

- **Feature branches**: Bump version once, just before merging to main
- **Main branch**: Bump for each commit with code changes
- Update **both** `pyproject.toml` and `cli/simpletask/__init__.py`

## Submitting Changes

1. Create a feature branch from `main`
2. Make changes following code standards above
3. Ensure all checks pass: `pytest`, `ruff format .`, `ruff check .`, `mypy cli/simpletask`
4. Submit a pull request with a clear description of changes

## Boundaries

| | |
|---|---|
| **Always** | Run tests before committing, add type hints, write tests for new functionality |
| **Ask first** | Adding dependencies, changing CLI interface, modifying YAML schema |
| **Never** | Commit failing tests, use `typing.List`/`Dict`/`Optional`, bump major version |

## License

Contributions are licensed under the MIT License. See [LICENSE](../LICENSE).
