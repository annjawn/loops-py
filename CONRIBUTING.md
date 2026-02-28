# Contributing

Thanks for contributing to `loops-py`.

## Development setup

1. Install dependencies:

```bash
uv sync --extra dev
```

2. Run checks:

```bash
uv run ruff check .
uv run pytest
```

## Pull request guidelines

1. Keep changes scoped and focused.
2. Add or update tests for behavior changes.
3. Update docs when public behavior or API changes.
4. Ensure lint and tests pass before opening a PR.

## Commit style

Use clear commit messages that describe what changed and why.

## Reporting issues

When opening an issue, include:

- What you expected
- What happened
- Reproduction steps
- Environment details (Python version, OS)
