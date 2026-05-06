"""FEN parse/serialize tests.

Three test patterns:
1. Round-trip: parse → serialize → parse must produce an equal Position.
2. Canonical equality: serialize(parse(s)) == s for already-canonical FENs.
3. Oracle: our parsed Position matches python-chess's Board, field by field.

Plus a fuzz test that walks random games via python-chess and asserts
oracle agreement at every position. Deterministic seed for reproducibility.
"""

import random

import chess
import pytest

from drewbert.adapters.fen import alg_sq_to_int, int_to_alg_sq, parse_fen, to_fen
from drewbert.core.position import Position
from drewbert.core.types import Color, PieceType

# Canonical FENs covering common edge cases.
# The first six are the standard perft suite; the rest exercise EP targets,
# clocks, and minimal-piece endgames.
CANONICAL_FENS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2pP/R2Q1RK1 w kq - 0 1",
    "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
    "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10",
    # En passant target after 1.e4
    "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
    # En passant target, white to move
    "rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2",
    # Near the 50-move rule
    "8/8/4k3/8/4K3/8/8/8 w - - 99 100",
    # KP endgame, no castling
    "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1",
    # Black to move from the starting position
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1",
]


_PIECE_TYPE_FROM_PYCHESS = {
    chess.PAWN: PieceType.PAWN,
    chess.KNIGHT: PieceType.KNIGHT,
    chess.BISHOP: PieceType.BISHOP,
    chess.ROOK: PieceType.ROOK,
    chess.QUEEN: PieceType.QUEEN,
    chess.KING: PieceType.KING,
}


def _to_our_color(c: chess.Color) -> Color:
    return Color.WHITE if c == chess.WHITE else Color.BLACK


def _assert_matches_oracle(ours: Position, theirs: chess.Board, fen: str) -> None:
    """Compare every observable field of our Position against python-chess."""
    for square in range(64):
        their_piece = theirs.piece_at(square)
        our_piece = ours.piece_at(square)
        if their_piece is None:
            assert our_piece is None, f"square {square}: theirs empty, ours has {our_piece}"
        else:
            assert our_piece is not None, f"square {square}: theirs has piece, ours empty"
            assert our_piece.type == _PIECE_TYPE_FROM_PYCHESS[their_piece.piece_type]
            assert our_piece.color == _to_our_color(their_piece.color)

    assert ours.side_to_move == _to_our_color(theirs.turn)
    assert ours.castling_rights.white_kingside == bool(theirs.castling_rights & chess.BB_H1)
    assert ours.castling_rights.white_queenside == bool(theirs.castling_rights & chess.BB_A1)
    assert ours.castling_rights.black_kingside == bool(theirs.castling_rights & chess.BB_H8)
    assert ours.castling_rights.black_queenside == bool(theirs.castling_rights & chess.BB_A8)

    # Compare ep against the FEN literal: python-chess's ep_square diverges from
    # board.fen()'s legal-mode emission, so neither side alone is a faithful oracle.
    ep_field = fen.split()[3]
    expected_ep = None if ep_field == "-" else chess.parse_square(ep_field)
    assert ours.en_passant_target == expected_ep

    assert ours.halfmove_clock == theirs.halfmove_clock
    assert ours.fullmove_number == theirs.fullmove_number


@pytest.mark.parametrize("fen", CANONICAL_FENS)
def test_round_trip(fen: str) -> None:
    pos1 = parse_fen(fen)
    pos2 = parse_fen(to_fen(pos1))
    assert pos1 == pos2


@pytest.mark.parametrize("fen", CANONICAL_FENS)
def test_serialization_is_canonical(fen: str) -> None:
    """For canonical inputs, to_fen(parse_fen(s)) == s exactly."""
    assert to_fen(parse_fen(fen)) == fen


@pytest.mark.parametrize("fen", CANONICAL_FENS)
def test_oracle_match(fen: str) -> None:
    _assert_matches_oracle(parse_fen(fen), chess.Board(fen), fen)


def test_fuzz_oracle() -> None:
    """Play random games; check oracle agreement at every position."""
    rng = random.Random(42)
    for _ in range(10):
        board = chess.Board()
        ply = 0
        while not board.is_game_over() and ply < 80:
            fen = board.fen()
            _assert_matches_oracle(parse_fen(fen), board, fen)
            move = rng.choice(list(board.legal_moves))
            board.push(move)
            ply += 1


# Malformed inputs that parse_fen must reject with ValueError per its docstring.
# Each case targets one specific failure mode. Some currently pass, some
# currently fail — they collectively define the contract.
MALFORMED_FENS = [
    # Field count
    pytest.param("", id="empty"),
    pytest.param(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0",
        id="five_fields",
    ),
    pytest.param(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 extra",
        id="seven_fields",
    ),
    # Board placement — wrong rank count
    pytest.param(
        "rnbqkbnr/pppppppp/8/8/8/8/RNBQKBNR w KQkq - 0 1",
        id="seven_ranks",
    ),
    pytest.param(
        "rnbqkbnr/pppppppp/8/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        id="nine_ranks",
    ),
    # Board placement — wrong squares-per-rank
    pytest.param(
        "rnbqkbn/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        id="rank_seven_squares",
    ),
    pytest.param(
        "rnbqkbnrr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        id="rank_nine_squares",
    ),
    # Board placement — invalid characters
    pytest.param(
        "rnbqkbXr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        id="invalid_piece_char",
    ),
    pytest.param("9/8/8/8/8/8/8/8 w - - 0 1", id="digit_out_of_range"),
    # Side to move
    pytest.param(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR x KQkq - 0 1",
        id="invalid_color",
    ),
    # Castling field
    pytest.param(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w abcd - 0 1",
        id="garbage_castling_field",
    ),
    # En passant
    pytest.param(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq z3 0 1",
        id="ep_invalid_file",
    ),
    pytest.param(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq a9 0 1",
        id="ep_invalid_rank",
    ),
    # Clocks
    pytest.param(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - x 1",
        id="non_numeric_halfmove",
    ),
]


@pytest.mark.parametrize("fen", MALFORMED_FENS)
def test_parse_fen_rejects_malformed(fen: str) -> None:
    """parse_fen must raise ValueError on any malformed input.

    These cases define the contract; some will fail until the corresponding
    validation is added.
    """
    with pytest.raises(ValueError):
        parse_fen(fen)


# Direct tests for the algebraic↔index helpers. Corner squares plus a couple
# of middle-board cases; the all-squares round-trip below catches off-by-one.
@pytest.mark.parametrize(
    "alg,idx",
    [
        ("a1", 0),
        ("h1", 7),
        ("a8", 56),
        ("h8", 63),
        ("e4", 28),
        ("d6", 43),
    ],
)
def test_alg_sq_to_int_known_values(alg: str, idx: int) -> None:
    assert alg_sq_to_int(alg) == idx


@pytest.mark.parametrize(
    "idx,alg",
    [
        (0, "a1"),
        (7, "h1"),
        (56, "a8"),
        (63, "h8"),
        (28, "e4"),
        (43, "d6"),
    ],
)
def test_int_to_alg_sq_known_values(idx: int, alg: str) -> None:
    assert int_to_alg_sq(idx) == alg


def test_helpers_round_trip_all_squares() -> None:
    """alg_sq_to_int and int_to_alg_sq are inverses on every valid square."""
    for idx in range(64):
        assert alg_sq_to_int(int_to_alg_sq(idx)) == idx


@pytest.mark.parametrize(
    "bad",
    [
        pytest.param("", id="empty"),
        pytest.param("a", id="too_short"),
        pytest.param("a1a", id="too_long"),
        pytest.param("z1", id="invalid_file"),
        pytest.param("A1", id="uppercase_file"),
        pytest.param("a0", id="rank_below_range"),
        pytest.param("a9", id="rank_above_range"),
        pytest.param("ab", id="non_digit_rank"),
        pytest.param("11", id="non_letter_file"),
    ],
)
def test_alg_sq_to_int_rejects_malformed(bad: str) -> None:
    with pytest.raises(ValueError):
        alg_sq_to_int(bad)


@pytest.mark.parametrize(
    "bad",
    [
        pytest.param(-1, id="negative_one"),
        pytest.param(64, id="just_above_range"),
        pytest.param(-100, id="far_negative"),
        pytest.param(1000, id="far_above_range"),
    ],
)
def test_int_to_alg_sq_rejects_out_of_range(bad: int) -> None:
    with pytest.raises(ValueError):
        int_to_alg_sq(bad)
