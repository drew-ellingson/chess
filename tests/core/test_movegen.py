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

from drewbert.adapters.fen import alg_sq_to_int, int_to_alg_sq, parse_fen
from drewbert.core.movegen import (
    Coord,
    file_rank_to_sq,
    generate_legal_moves,
    is_square_attacked,
    sq_to_file_rank,
)
from drewbert.core.types import Color
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


# is_square_attacked is the dedicated attack primitive — independent of
# position.side_to_move. The cases below cover the conceptually distinct
# attack patterns; the oracle test below exhausts every (square, color)
# combination on the canonical positions.
#
# Critical case to keep in mind: a pawn attacks its diagonals even when
# those squares are empty. (This is what makes the primitive different
# from movegen — a pseudo-legal pawn capture requires an enemy piece on
# the diagonal; an attack does not.)


@pytest.mark.parametrize(
    "fen,square,by,expected",
    [
        # White pawn on e4: attacks empty diagonals d5 / f5; does NOT attack the push square e5.
        ("8/8/8/8/4P3/8/8/8 w - - 0 1", "d5", Color.WHITE, True),
        ("8/8/8/8/4P3/8/8/8 w - - 0 1", "f5", Color.WHITE, True),
        ("8/8/8/8/4P3/8/8/8 w - - 0 1", "e5", Color.WHITE, False),
        # Black pawn on e5: attacks empty diagonals d4 / f4.
        ("8/8/8/4p3/8/8/8/8 b - - 0 1", "d4", Color.BLACK, True),
        ("8/8/8/4p3/8/8/8/8 b - - 0 1", "f4", Color.BLACK, True),
        # Asking the wrong color returns False (no black pieces on the board).
        ("8/8/8/8/4P3/8/8/8 w - - 0 1", "d5", Color.BLACK, False),
        # Knight on e4: attacks the eight L-jump squares.
        ("8/8/8/8/4N3/8/8/8 w - - 0 1", "d2", Color.WHITE, True),
        ("8/8/8/8/4N3/8/8/8 w - - 0 1", "g5", Color.WHITE, True),
        ("8/8/8/8/4N3/8/8/8 w - - 0 1", "e3", Color.WHITE, False),
        # Rook on d3, own pawn on d2, own king on d1: rook attacks d2 (its own piece)
        # but the ray is blocked beyond — d1 is not attacked by the rook.
        ("8/8/8/8/8/3R4/3P4/3K4 w - - 0 1", "d2", Color.WHITE, True),
        ("8/8/8/8/8/3R4/3P4/3K4 w - - 0 1", "d1", Color.WHITE, False),
        # Rook on d4, enemy pawn on d5: rook attacks d5 (capture square) but not d6 (blocked).
        ("4k3/8/8/3p4/3R4/8/8/4K3 w - - 0 1", "d5", Color.WHITE, True),
        ("4k3/8/8/3p4/3R4/8/8/4K3 w - - 0 1", "d6", Color.WHITE, False),
        # White king on e4: attacks all 8 adjacent squares, nothing further.
        ("4k3/8/8/8/4K3/8/8/8 w - - 0 1", "e5", Color.WHITE, True),
        ("4k3/8/8/8/4K3/8/8/8 w - - 0 1", "d4", Color.WHITE, True),
        ("4k3/8/8/8/4K3/8/8/8 w - - 0 1", "e6", Color.WHITE, False),
    ],
)
def test_is_square_attacked_known_cases(
    fen: str, square: str, by: Color, expected: bool
) -> None:
    position = parse_fen(fen)
    assert is_square_attacked(position, alg_sq_to_int(square), by) == expected


@pytest.mark.parametrize("fen", ORACLE_FENS)
def test_is_square_attacked_oracle(fen: str) -> None:
    """For every (square, color) combination, our primitive matches python-chess's is_attacked_by."""
    position = parse_fen(fen)
    board = chess.Board(fen)
    for sq in range(64):
        for color in (Color.WHITE, Color.BLACK):
            their_color = chess.WHITE if color == Color.WHITE else chess.BLACK
            ours = is_square_attacked(position, sq, color)
            theirs = board.is_attacked_by(their_color, sq)
            assert ours == theirs, (
                f"{fen}: square {int_to_alg_sq(sq)}, by {color!r}: "
                f"ours={ours}, theirs={theirs}"
            )
