"""UCI compliance tests via python-chess as oracle.

Spawns the engine as a subprocess through `chess.engine.SimpleEngine.popen_uci`
and exercises the full I/O loop: handshake, position setup, search, bestmove
emission. python-chess refuses to interact with engines that send malformed
UCI, so a passing `play()` call is strong evidence the protocol implementation
is compliant.

python-chess is a dev-only oracle, NOT imported anywhere in src/ — these tests
sit alongside the FEN oracle tests that use the same pattern.
"""

import sys
from collections.abc import Iterator

import chess
import chess.engine
import pytest

# Command to spawn the engine. `sys.executable` resolves to the uv-managed
# Python in the venv that's running pytest, so no `uv run` prefix is needed.
ENGINE_CMD: list[str] = [
    sys.executable,
    "-m",
    "drewbert.adapters.uci",
    "--eval",
    "materialistic",
    "--search",
    "minimax",
    "--depth",
    "2",  # shallow enough to keep test wall-clock low
]


@pytest.fixture
def engine() -> Iterator[chess.engine.SimpleEngine]:
    """One spawned engine per test, cleanly torn down via the context manager.

    SimpleEngine.popen_uci performs the full UCI handshake (uci → uciok)
    during construction; if the engine fails to respond correctly here, the
    fixture itself raises and the test errors before running.

    If the engine subprocess has already died (e.g. an in-test crash made it
    exit), `quit()` raises EngineTerminatedError because there's nothing left
    to send `quit` to. That's expected — the real signal is the test failure
    upstream, not the teardown — so we swallow it here to keep the report
    clean.
    """
    eng = chess.engine.SimpleEngine.popen_uci(ENGINE_CMD)
    try:
        yield eng
    finally:
        try:
            eng.quit()
        except chess.engine.EngineTerminatedError:
            pass


def test_handshake_succeeds(engine: chess.engine.SimpleEngine) -> None:
    """If the fixture set up cleanly, the handshake worked.

    This test exists so that handshake failures surface as a clear
    'test_handshake_succeeds errored' rather than getting buried in
    unrelated downstream tests.
    """
    assert engine.id is not None


def test_isready_responds(engine: chess.engine.SimpleEngine) -> None:
    """ping() sends `isready` and waits for `readyok`."""
    engine.ping()


def test_bestmove_from_startpos_is_legal(engine: chess.engine.SimpleEngine) -> None:
    board = chess.Board()
    result = engine.play(board, chess.engine.Limit(depth=2))
    assert result.move is not None
    assert result.move in board.legal_moves


# Spread across position types to catch FEN-handling bugs and check the engine
# can emit moves from non-trivial states (mid-game, endgame, in check).
LEGAL_MOVE_POSITIONS = [
    pytest.param(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        id="startpos",
    ),
    pytest.param(
        "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
        id="mid-game-open",
    ),
    pytest.param(
        "8/8/8/8/8/8/k1K5/4R3 w - - 0 1",
        id="endgame-KRk",
    ),
    pytest.param(
        "rnbqkbnr/ppp2ppp/8/3pp3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 3",
        id="early-tactical",
    ),
]


@pytest.mark.parametrize("fen", LEGAL_MOVE_POSITIONS)
def test_bestmove_is_legal(engine: chess.engine.SimpleEngine, fen: str) -> None:
    board = chess.Board(fen)
    result = engine.play(board, chess.engine.Limit(depth=2))
    assert result.move is not None
    assert result.move in board.legal_moves


def test_position_command_actually_updates_state(engine: chess.engine.SimpleEngine) -> None:
    """Regression test: the engine must respect the position sent by the GUI,
    not always play from the initial state. We give it a position where the
    only legal move is forced — if state isn't tracked, the engine will play
    a startpos move that's illegal on this board."""
    # White king has only one legal move: Kg1 (escape from check on h1).
    board = chess.Board("7k/8/8/8/8/8/6q1/7K w - - 0 1")
    result = engine.play(board, chess.engine.Limit(depth=2))
    assert result.move is not None
    assert result.move in board.legal_moves


def test_consecutive_searches_from_different_positions(engine: chess.engine.SimpleEngine) -> None:
    """One engine process should handle multiple position+go cycles.
    Catches engines that hang after the first search or fail to reset state."""
    positions = [
        chess.Board(),
        chess.Board("r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"),
        chess.Board("8/8/8/8/8/8/k1K5/4R3 w - - 0 1"),
    ]
    for board in positions:
        result = engine.play(board, chess.engine.Limit(depth=2))
        assert result.move is not None
        assert result.move in board.legal_moves
