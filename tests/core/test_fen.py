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

from drewbert.adapters.fen import parse_fen, to_fen
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


def _assert_matches_oracle(ours: Position, theirs: chess.Board) -> None:
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
    assert ours.en_passant_target == theirs.ep_square
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
    _assert_matches_oracle(parse_fen(fen), chess.Board(fen))


def test_fuzz_oracle() -> None:
    """Play random games; check oracle agreement at every position."""
    rng = random.Random(42)
    for _ in range(10):
        board = chess.Board()
        ply = 0
        while not board.is_game_over() and ply < 80:
            _assert_matches_oracle(parse_fen(board.fen()), board)
            move = rng.choice(list(board.legal_moves))
            board.push(move)
            ply += 1
