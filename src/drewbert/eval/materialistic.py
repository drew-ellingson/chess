from drewbert.core.position import Color, Piece, Position
from drewbert.core.types import PieceType

PIECE_VALUES = {
    PieceType.PAWN: 100,
    PieceType.ROOK: 500,
    PieceType.KNIGHT: 300,
    PieceType.BISHOP: 320,
    PieceType.QUEEN: 900,
    PieceType.KING: 100000,  # sentinel value - king is never captured, just needs to dominate
}


def materialistic_position_eval(position: Position) -> int:
    """Return the sum of all material values of the given position. Positive for white, negative for black"""

    def val(piece: Piece | None) -> int:
        if piece is None:
            return 0
        else:
            unit_dir = 1 if piece.color == Color.WHITE else -1
            return unit_dir * PIECE_VALUES[piece.type]

    return sum(val(square) for square in position.squares)
