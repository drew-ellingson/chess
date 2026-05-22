"""Tests for movegen.

Two layers:
  - Coord/square helper round-trips (cheap, isolates one bug class)
  - python-chess legal-move oracle (catches movegen bugs at the root)

Square indices are rank-major: a1=0, h1=7, a8=56, h8=63. Ranks and files
are 0-indexed, so a1 = Coord(rank=0, file=0) and h8 = Coord(rank=7, file=7).

Coord is constructed with kwargs throughout so the tests don't depend on
the positional field order in the NamedTuple definition.
"""

import random

import chess
import pytest

from drewbert.adapters.fen import parse_fen
from drewbert.core.movegen import (
    Coord,
    file_rank_to_sq,
    generate_legal_moves,
    sq_to_file_rank,
)
from tests.core._helpers import from_pychess_move


@pytest.mark.parametrize(
    "square,rank,file",
    [
        (0, 0, 0),  # a1
        (7, 0, 7),  # h1
        (56, 7, 0),  # a8
        (63, 7, 7),  # h8
        (28, 3, 4),  # e4
        (43, 5, 3),  # d6
        (8, 1, 0),  # a2 — first square of second rank
        (15, 1, 7),  # h2 — last square of second rank
    ],
)
def test_sq_to_file_rank_known_values(square: int, rank: int, file: int) -> None:
    assert sq_to_file_rank(square) == Coord(rank=rank, file=file)


@pytest.mark.parametrize(
    "rank,file,square",
    [
        (0, 0, 0),
        (0, 7, 7),
        (7, 0, 56),
        (7, 7, 63),
        (3, 4, 28),
        (5, 3, 43),
        (1, 0, 8),
        (1, 7, 15),
    ],
)
def test_file_rank_to_sq_known_values(rank: int, file: int, square: int) -> None:
    assert file_rank_to_sq(Coord(rank=rank, file=file)) == square


def test_helpers_round_trip_all_squares() -> None:
    """sq_to_file_rank and file_rank_to_sq are inverses on every valid square."""
    for sq in range(64):
        assert file_rank_to_sq(sq_to_file_rank(sq)) == sq


def test_helpers_round_trip_all_coords() -> None:
    """Round-trip the other direction: every Coord in [0, 8)²."""
    for rank in range(8):
        for file in range(8):
            coord = Coord(rank=rank, file=file)
            assert sq_to_file_rank(file_rank_to_sq(coord)) == coord


@pytest.mark.parametrize(
    "bad",
    [
        pytest.param(-1, id="negative_one"),
        pytest.param(64, id="just_above_range"),
        pytest.param(-100, id="far_negative"),
        pytest.param(1000, id="far_above_range"),
    ],
)
def test_sq_to_file_rank_rejects_out_of_range(bad: int) -> None:
    with pytest.raises(ValueError):
        sq_to_file_rank(bad)


@pytest.mark.parametrize(
    "rank,file",
    [
        pytest.param(-1, 0, id="negative_rank"),
        pytest.param(0, -1, id="negative_file"),
        pytest.param(8, 0, id="rank_just_above_range"),
        pytest.param(0, 8, id="file_just_above_range"),
        pytest.param(-1, -1, id="both_negative"),
        pytest.param(8, 8, id="both_above_range"),
        pytest.param(100, 3, id="rank_far_above_range"),
        pytest.param(3, 100, id="file_far_above_range"),
    ],
)
def test_file_rank_to_sq_rejects_out_of_range(rank: int, file: int) -> None:
    with pytest.raises(ValueError):
        file_rank_to_sq(Coord(rank=rank, file=file))


# Positions exercising every special-move case at the root: ordinary moves,
# captures, EP, castling, promotion. Kept in sync with tests/core/test_position.py.
ORACLE_FENS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2pP/R2Q1RK1 w kq - 0 1",
    "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
    "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1",
]


def _diff_move_sets(ours: set, theirs: set) -> str:
    """Format the symmetric difference between two move sets for an assertion message."""
    missing = sorted(theirs - ours, key=lambda m: (m.from_square, m.to_square))
    extra = sorted(ours - theirs, key=lambda m: (m.from_square, m.to_square))
    return f"missing={missing or 'none'}, extra={extra or 'none'}"


@pytest.mark.parametrize("fen", ORACLE_FENS)
def test_legal_moves_match_python_chess(fen: str) -> None:
    """Our generate_legal_moves matches python-chess's board.legal_moves at the root."""
    ours = set(generate_legal_moves(parse_fen(fen)))
    theirs = {from_pychess_move(m) for m in chess.Board(fen).legal_moves}
    assert ours == theirs, f"{fen}: {_diff_move_sets(ours, theirs)}"


def test_legal_moves_fuzz_oracle() -> None:
    """Play random games via python-chess; oracle agreement at every ply.

    Catches movegen bugs in transient positions that aren't in the canonical
    list. Deterministic seed for reproducibility.
    """
    rng = random.Random(42)
    for _ in range(10):
        board = chess.Board()
        ply = 0
        while not board.is_game_over() and ply < 80:
            fen = board.fen()
            ours = set(generate_legal_moves(parse_fen(fen)))
            theirs = {from_pychess_move(m) for m in board.legal_moves}
            assert ours == theirs, f"{fen}: {_diff_move_sets(ours, theirs)}"
            board.push(rng.choice(list(board.legal_moves)))
            ply += 1
