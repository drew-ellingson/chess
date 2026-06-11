"""Mate puzzles — engine should find the mating move at the stated depth.

Puzzles are FEN + the expected first move in UCI-ish form ("e2e4"). Mate-in-1
needs depth 2; mate-in-2 needs depth 4. (Roadmap test gate for phase 2.)

Adding new puzzles: verify the FEN is legal, the expected move is the unique
mating move at the stated depth, and the forcing line is clean. The
verification helper in `tests/search/_verify_puzzle.py`-style scratch is
optional — `python-chess` makes this a one-liner if you want a sanity check
when adding more.
"""

import pytest

from drewbert.adapters.fen import parse_fen
from drewbert.eval.materialistic import materialistic_position_eval
from drewbert.search.minimax import best_move

MATE_IN_1_PUZZLES = [
    # Back-rank: rook lift to a8, king smothered by own pawns.
    pytest.param("6k1/5ppp/8/8/8/8/8/R6K w - - 0 1", "a1a8", id="back-rank-Ra8"),
    # K+Q vs K corner mate.
    pytest.param("7k/8/6K1/Q7/8/8/8/8 w - - 0 1", "a5a8", id="KQ-vs-K-Qa8"),
    # K+R vs K corner mate.
    pytest.param("7k/8/7K/8/8/8/8/2R5 w - - 0 1", "c1c8", id="KR-vs-K-Rc8"),
]

MATE_IN_2_PUZZLES = [
    # 1. Rd8+ Kh7 (only legal) 2. Rh8# (pawn on g7 covers Kxh8).
    pytest.param("6k1/6P1/5K2/8/8/8/8/3R4 w - - 0 1", "d1d8", id="rook-pawn-corner"),
]


@pytest.mark.parametrize("fen,expected_uci", MATE_IN_1_PUZZLES)
def test_finds_mate_in_1_at_depth_2(fen: str, expected_uci: str) -> None:
    position = parse_fen(fen)
    move = best_move(position, materialistic_position_eval, depth=2)
    assert repr(move) == expected_uci


@pytest.mark.parametrize("fen,expected_uci", MATE_IN_2_PUZZLES)
def test_finds_mate_in_2_at_depth_4(fen: str, expected_uci: str) -> None:
    position = parse_fen(fen)
    move = best_move(position, materialistic_position_eval, depth=4)
    assert repr(move) == expected_uci
