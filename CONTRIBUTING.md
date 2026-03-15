# Contributing

Thank you for your interest in contributing to TMS Backend!

## Development Setup

Follow the [Getting Started](README.md#getting-started) guide, then:

```bash
pip install -r requirements-test.txt
pre-commit install
```

## Coding Standards

Follow the [Django Styleguide](docs/STYLEGUIDE.md). Key rules:

- All business logic belongs in the **utils layer** (`utils.py`), never in views or serializers
- Use `APIView` (not generic views or viewsets)
- Separate **input** and **output** serializers
- Function naming: `{model}_{action}` (e.g. `project_create`, `translation_key_list`)

## Branch & Commit Conventions

Branch prefixes:

- `feature/` — new functionality
- `fix/` — bug fixes
- `refactor/` — code restructuring
- `docs/` — documentation changes

Commit messages: use imperative mood, keep concise (e.g. "Add translation export caching").

## Testing Requirements

- Write tests for all utils functions and API endpoints
- Use `factory_boy` factories (located in `apps/factories/`)
- Cover both happy path and error cases
- Maintain **80% minimum** code coverage

## Pre-commit & CI

- All pre-commit hooks must pass before pushing
- CI pipeline: **lint** → **test**

## Pull Request Process

- Describe what changed and why
- Note any new migrations
- Link related issues
