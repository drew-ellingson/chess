from drewbert.core.move import Move
from drewbert.core.movegen import is_checkmate, is_stalemate
from drewbert.core.position import Color, Piece, Position
from drewbert.core.types import PieceType

PIECE_VALUES = {
    PieceType.PAWN: 100,
    PieceType.ROOK: 500,
    PieceType.KNIGHT: 300,
    PieceType.BISHOP: 320,
    PieceType.QUEEN: 900,
    PieceType.KING: 100000,
}


def materialistic_position_eval(position: Position) -> int:
    """Return the sum of all material values of the given position. Positive for white, negative for black"""
    if is_stalemate(position):
        return 0
    if is_checkmate(position):
        return -10000000 if position.side_to_move == Color.WHITE else 10000000

    def val(piece: Piece | None) -> int:
        if piece is None:
            return 0
        else:
            dir = 1 if piece.color == Color.WHITE else -1
            return dir * PIECE_VALUES[piece.type]

    return sum(val(square) for square in position.squares)


def materialistic_move_eval(position: Position, move: Move) -> int:
    """Return the evaluation of a position after given move is played.
    Handle position state around making the move.
    """
    undo = position.make_move(move)
    val = materialistic_position_eval(position)
    position.unmake_move(undo)
    return val
