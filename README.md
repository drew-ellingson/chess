# drewbert

A chess engine written from scratch in Python as a learning project.

## Setup

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```sh
uv sync
```

## Development

```sh
uv run pytest                # run tests
uv run pytest -m "not slow"  # skip slow tests (deep perft)
uv run ruff check            # lint
uv run ruff format           # format
uv run pyright               # type check
```

See `ROADMAP.md` for the phased development plan and `CLAUDE.md` for project context.
