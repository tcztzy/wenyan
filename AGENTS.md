# AGENTS.md

## Project overview
- Wenyan programming language implementation in Python.

## Setup commands
- Use uv for environment and dependencies:
  - `uv sync`
  - `uv add <package>`
  - `uv remove <package>`
- Run tests with pytest:
  - `uv run pytest`

## Coding guidelines
- Target Python 3.8+.
- Avoid `from __future__ import <any>`.
- Prefer the smallest, simplest implementation that delivers the same features; avoid over-designed abstractions.
- Performance is critical; consider algorithmic complexity and allocations.
- If feasible, keep changes compatible with Python 2.7 (e.g., avoid syntax that blocks backports); call out when this isn't possible.
- Docstrings must follow Google style.

## Typing
- Use `ty` for type checking (Astral's tool alongside uv), e.g. `uv run ty` or `ty check`.

## Testing instructions
- Use pytest.
- Prefer doctest-style examples in docstrings when a module already uses docstring tests; otherwise add regular pytest tests.
- Update or add tests for any behavior changes.
