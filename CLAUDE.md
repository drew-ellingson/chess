# drewbert

A chess engine in Python. Owner-driven learning project; Claude is here for software design, scaffolding, code review, and explanation — *not* to write algorithm code.

See `ROADMAP.md` for phases and test gates.

## Role boundary

**Algorithms are the owner's to write.** Move generation, search, evaluation, and any future NNUE training code is his. If asked to implement these, push back and offer to explain, scaffold, or review instead.

**In-scope for Claude:**
- Project structure, package layout, build/tooling setup
- Public API design and class shape (the owner has flagged game state classes as a past pain point)
- Code review on request
- Debugging help when stuck
- Test scaffolding, fixtures, oracle setups
- Architecture and framework decisions
- Algorithm explanations and tradeoff analysis

**Out-of-scope unless explicitly asked:**
- Writing move generation logic
- Writing search algorithms
- Writing evaluation functions
- Writing NNUE training code

## Architecture principles (load-bearing)

1. **`src/drewbert/core/` is pure.** No I/O, no printing, no network. The engine is a library that takes a position and returns moves.
2. **`eval/` and `search/` are siblings.** They depend on `core/`, not on each other. Both are swappable (handcrafted eval → NNUE, minimax → alpha-beta → MCTS).
3. **`adapters/` is where the outside world lives.** FEN, CLI, UCI, web. Each adapter is thin and depends only on `core/` (plus eval/search where needed).
4. **Move generation is a function, not a method on `Position`.** Position is data; movegen is a complex algorithm over that data. Keeping them apart fixes the cumbersome-game-state-class problem.

## Implementation decisions

- **Board representation: mailbox** (`list[Piece | None]` of length 64, rank-major: a1=0, h1=7, a8=56). Bitboards may come later if/when hot paths are ported to a compiled language; not now.
- **Move application: make/unmake pattern.** `Position.make_move(move) -> Undo`, `Position.unmake_move(undo) -> None`. The `Undo` struct captures the captured piece, prev castling rights, prev en passant target, prev halfmove clock, and (phase 3) prev Zobrist hash. This avoids per-move allocation in tight search loops.
- **`Move` is minimal:** `from_square`, `to_square`, optional `promotion`. Castling and en passant are detected from context inside `make_move`. May expand if the design pressures it.
- **`Square` is `int` 0..63** (alias, not a `NewType`). Refactor later if the type confusion bites.
- **`Position` has zero display logic.** ASCII print lives in `adapters/`, FEN lives in `adapters/fen.py`.

## Tooling

```sh
uv sync                      # install deps + create venv
uv run pytest                # run tests (perft is the phase 1 gate)
uv run pytest -m "not slow"  # skip deep perft
uv run ruff check            # lint
uv run ruff format           # format
uv run pyright               # type check
```

`python-chess` is a **dev-only** dependency used as a test oracle. **Never import it from `src/`.**

## Testing strategy

- **Phase 1 gate is perft.** Hand-written test cases will not catch the long-tail bugs in special moves and pin handling; perft does. Match published node counts across the standard 6-position suite.
- **Make/unmake invariant.** For any legal move from any position: `make_move` then `unmake_move` must leave the position bitwise identical to before.
- **python-chess oracle.** On random positions, generate legal moves and compare the set to python-chess's output.
