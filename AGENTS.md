# AGENTS.md - Tramontane Agent Operating Guide

This file adapts `CLAUDE.md` into concise, project-local operating rules for coding agents in this repository.

## Project Identity

- Name: `tramontane`
- Mission: Mistral-native agent orchestration framework
- Stack: Python 3.12+, FastAPI, Pydantic v2, Typer, Rich, asyncio, uv
- Architecture: async-first library, stateless agent cost accounting, router-driven model selection

## Non-Negotiables

- Mistral-only: never add `openai`, `langchain`, or `litellm`.
- Keep library internals async. No `asyncio.run()` in internal modules.
- Use Pydantic v2 patterns.
- Keep agent cost stateless per call; pipeline accumulates total cost.
- Cost unit is EUR.
- Preserve strict typing quality:
  - zero `# noqa` additions
  - zero `# type: ignore` additions
  - fix root causes instead
- No `print()` in library code; use structured logging.

## Python Backend Workflow

For all substantial changes:

1. Implement with explicit type hints and docstrings on public methods.
2. Run:
   - `uv run ruff check .`
   - `uv run mypy .`
   - targeted `uv run pytest ...` (or full suite when needed)
3. Fix issues directly rather than suppressing.

Preferred command intents:

- Lint: `/lint:check` equivalent -> `uv run ruff check .`
- Types: `/types:check` equivalent -> `uv run mypy .`
- Tests first: `/test:first` mindset -> run/author tests before or with implementation

## Installed Plugin Baseline

Available and enabled in this environment:

- `superpowers@superpowers-marketplace`
- `python@python-backend-plugins`
- `fastapi@python-backend-plugins`
- `tech-lead@python-backend-plugins`

Use them to enforce disciplined flow:

- brainstorm -> spec -> plan -> implement -> review
- TDD red/green/refactor when feasible
- keep features isolated and verifiable

## Code Style and Structure

- Import order:
  1) `from __future__ import annotations`
  2) stdlib
  3) third-party
  4) internal `tramontane.*`
- Prefer narrow exceptions and explicit error handling.
- Maintain clear domain boundaries:
  - `core` execution lifecycle
  - `router` model routing logic
  - `gdpr` privacy controls
  - `memory` persistence and recall

## Testing Priorities

- Router selection and budget floor behavior
- Agent run lifecycle (input validation, budget pre-check, retries, cost reporting)
- Pipeline accumulation of `cost_eur`
- GDPR and audit integrity
- Regressions for sync bridge behavior in `core/_sync.py`

## Safe Change Policy

- Do not silently change public behavior without tests.
- Prefer additive changes over breaking API shape.
- Keep docs and examples aligned when behavior changes.
- If uncertain about architecture-level tradeoffs, propose options before large refactors.

