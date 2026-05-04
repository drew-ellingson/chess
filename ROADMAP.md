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

## Phase 3 — Real engine

Make it play chess well.

- Alpha-beta pruning
- Iterative deepening with time management
- Zobrist hashing
- Transposition table
- Move ordering: MVV-LVA, killer moves, history heuristic
- Quiescence search
- Piece-square tables
- Basic positional evaluation: mobility, pawn structure, king safety

**Test gate:** in self-tournament against the phase-2 engine, wins ≥80%. In tournament against Stockfish at low skill levels, settles around club-player strength.

## Phase 4 — UCI

Make it speak the protocol.

- UCI adapter

**Test gate:** Cute Chess (or any UCI GUI) can drive the engine. Engine-vs-engine tournaments can be run from the command line. From here on, every change is measured by tournament Elo, not vibe.

## Phase 5 — Strength climbing or NNUE

Optional. Either classical refinements (null-move, late move reductions, futility pruning, aspiration windows) or pivot to NNUE-style learned evaluation trained from self-play.

## Phase 6 — Web app

- FastAPI backend
- Websocket for live play
- JS frontend with a board widget (chessboardjs or react-chessboard)

**Test gate:** full game playable in the browser.

## Phase 7 — Offshoots

- Lichess game analysis (pull PGN via API, run through engine, surface mistake patterns)
- Variants (new pieces, possibly drafting)
- Cheat detection (Ken Regan-style statistical analysis over engine top-N agreement)
