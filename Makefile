# Task runner for drewbert.
#
# `make fix`     — auto-apply formatting and lint fixes (mutates source).
# `make check`   — verify formatting, lint, types, and tests (read-only).
#                  Safe to wire into CI.
# `make pre-pr`  — fix-then-check; what to run before opening a PR.
#
# Targets are intentionally simple wrappers around `uv run <tool>` so that
# the canonical invocation lives here, not scattered across docs.

.PHONY: fix check pre-pr fmt lint type test

fix:
	uv run ruff format
	uv run ruff check --fix

check: fmt lint type test

fmt:
	uv run ruff format --check

lint:
	uv run ruff check

type:
	uv run pyright

test:
	uv run pytest -m "not slow"

pre-pr: fix check
