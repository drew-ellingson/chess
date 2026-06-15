# drewbert roadmap

A phased plan, with explicit test gates between phases. Each gate is a concrete check — not a vibe — because chess engine bugs hide in long tails of move sequences.

## Phase 1 — Foundations

Build the data structures and rules of chess.

- `Position` (mailbox, make/unmake)
- `Move`
- FEN parse/serialize
- ASCII board print
- Legal move generation

**Test gate: perft.** Move generation is correct iff `perft` node counts match published reference values across the standard test suite (starting position, Kiwipete, positions 3-6) at depths 1-3 (default) and 4+ (slow). See `tests/core/test_perft.py`. Bugs in special moves (castling, en passant, promotion) and pin/check handling will be exposed by perft and almost nothing else.

## Phase 2 — Naive engine

Make it play chess, even if poorly.

- Material-only evaluation
- Fixed-depth minimax
- CLI to play against the engine

**Test gate:** plays a full game with zero illegal moves. Finds mate-in-1 at depth 2. Finds mate-in-2 at depth 4. Add a small "find the best move" puzzle suite.

## Phase 3 — Real engine + measurement

Make it play chess well, and make every improvement measurable.

The first two items establish the measurement infrastructure that lets every subsequent change be tested in self-play and (eventually) against rated opponents. UCI is built against the current constant-depth engine — no search improvements required first; the protocol doesn't care what your search does, only that it produces a `bestmove`. From there each engine improvement ships with a self-play Elo delta in its PR body.

- UCI adapter (constant-depth search; time control ignored initially)
- Tournament harness (cute-chess) with self-play A/B + Stockfish skill ladder
- Alpha-beta pruning
- Iterative deepening with time management
- Zobrist hashing
- Transposition table
- Move ordering: MVV-LVA, killer moves, history heuristic
- Quiescence search
- Piece-square tables
- Basic positional evaluation: mobility, pawn structure, king safety

**Test gates:** every PR after the harness lands carries a self-play Elo delta vs. prior tip. End-of-phase: in self-tournament against the phase-2 engine, wins ≥80%. First scoring result against Stockfish skill 0 expected after alpha-beta + iterative deepening (likely with TT) — that becomes the engine's first anchored absolute Elo.

## Phase 4 — Strength climbing

## Phase 5 — Strength climbing

Optional. Pick any combination — these levers compose, each pushes rating from a different direction.

- **Classical refinements:** null-move, late move reductions, futility pruning, aspiration windows.
- **NNUE:** pivot to learned evaluation trained from self-play, replacing the handcrafted eval.
- **Port hot paths to Rust (or another compiled language).** Movegen, `Position`, and parts of search dominate wall-clock in Python. A compiled port lets the same search reach deeper at the same time budget — meaningful Elo just from depth. Typically the *last* lever applied: porting before the algorithms stabilize (≥ end of phase 3) means rewriting twice, and you want a Python baseline to benchmark against. Also natural to defer past phase 6 so a functional engine + app exist before the rewrite churn.

## Phase 5 — Web app

- FastAPI backend
- Websocket for live play
- JS frontend with a board widget (chessboardjs or react-chessboard)

**Test gate:** full game playable in the browser.

## Phase 6 — Offshoots

- Lichess game analysis (pull PGN via API, run through engine, surface mistake patterns)
- Variants (new pieces, possibly drafting)
- Cheat detection (Ken Regan-style statistical analysis over engine top-N agreement)

## Deferred — movegen optimizations

Captured here so they don't get lost; not gating any phase. Most are worth a
second look before phase 3 turns movegen into a tight hot path under alpha-beta.

- **Remove `Coord` NamedTuple from movegen.** Operate on integer square
  indices throughout. Eliminates per-square allocation and the positional /
  named-field ambiguity that bit early code.
- **Dedicated `first_piece_along_ray` attack primitive.** `is_square_attacked`
  currently shares the ray walker with movegen. That walker returns the full
  list of squares — fine for movegen, more work than attack detection needs.
  Attack detection only needs "is there an attacker of color X anywhere along
  this ray?" with short-circuit on the first hit.
- **King-square caching.** Cache `king_square(color)` per position instead of
  scanning all 64 squares each call. Invalidate / update inside `make_move` /
  `unmake_move`. Tricky: king moves *and* king captures both invalidate.
- **`CastlingRights` immutable → mutable.** Currently frozen + `dataclasses.replace`
  in make/unmake to dodge snapshot aliasing. A mutable variant with explicit
  copy semantics in the Undo struct would avoid the per-move dataclass
  allocation. Watch for the aliasing bugs the freezing was protecting against.
