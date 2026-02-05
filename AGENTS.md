# AGENTS.md

## Project overview
- Wenyan programming language implementation in Python.

## Setup commands
- Use uv for environment and dependencies:
  - `uv sync`
  - `uv add <package>`
  - `uv remove <package>`
- Run tests with unittest:
  - `uv run python -m unittest discover -s tests -p "test_*.py"`

## Coding guidelines
- Target Python 3.8+.
- Prefer the smallest, simplest implementation that delivers the same features; avoid over-designed abstractions.
- Performance is critical; consider algorithmic complexity and allocations.
- Docstrings must follow Google style.

## Typing
- Use `ty` for type checking (Astral's tool alongside uv), e.g. `uv run ty` or `ty check`.

## Testing instructions
- Use tox.
- Prefer doctest-style examples in docstrings when a module already uses docstring tests; otherwise add regular unittest tests.
- Update or add tests for any behavior changes.
