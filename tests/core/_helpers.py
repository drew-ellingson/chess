"""Shared test helpers for tests/core.

Underscore prefix marks this as internal to the test suite — not imported
from `src/` and not part of any public API.
"""

import chess

from drewbert.core.move import Move
from drewbert.core.position import Position
from drewbert.core.types import PieceType

_PIECE_TYPE_FROM_PYCHESS = {
    chess.PAWN: PieceType.PAWN,
    chess.KNIGHT: PieceType.KNIGHT,
    chess.BISHOP: PieceType.BISHOP,
    chess.ROOK: PieceType.ROOK,
    chess.QUEEN: PieceType.QUEEN,
    chess.KING: PieceType.KING,
}


def from_pychess_move(m: chess.Move) -> Move:
    """Translate a python-chess Move to our Move."""
    promotion = _PIECE_TYPE_FROM_PYCHESS[m.promotion] if m.promotion else None
    return Move(m.from_square, m.to_square, promotion)


_POSITION_FIELDS = (
    "side_to_move",
    "castling_rights",
    "en_passant_target",
    "halfmove_clock",
    "fullmove_number",
)


def diff_positions(before: Position, after: Position) -> list[str]:
    """Return one line per field that differs between two Positions.

    Empty list means the two positions are equal. Square diffs report the
    [0..63] index and the before/after Piece (or None). Non-square fields
    are compared by direct equality.
    """
    diffs: list[str] = []
    for i in range(64):
        if before.squares[i] != after.squares[i]:
            diffs.append(f"sq {i}: {before.squares[i]} -> {after.squares[i]}")
    for field in _POSITION_FIELDS:
        b, a = getattr(before, field), getattr(after, field)
        if b != a:
            diffs.append(f"{field}: {b} -> {a}")
    return diffs
