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

# fmt: off
# Tomasz Michniewski's Simplified Evaluation Function tables (chessprogramming.org/Simplified_Evaluation_Function),
# from White's perspective; Black reads them vertically mirrored. The king uses the middlegame table only.
# Published board-diagram style (rank 8 first
PIECE_SQUARE_TABLES = {
    PieceType.PAWN: [
          0,   0,   0,   0,   0,   0,   0,   0,  # rank 1
          5,  10,  10, -20, -20,  10,  10,   5,  # rank 2
          5,  -5, -10,   0,   0, -10,  -5,   5,  # rank 3
          0,   0,   0,  20,  20,   0,   0,   0,  # rank 4
          5,   5,  10,  25,  25,  10,   5,   5,  # rank 5
         10,  10,  20,  30,  30,  20,  10,  10,  # rank 6
         50,  50,  50,  50,  50,  50,  50,  50,  # rank 7
          0,   0,   0,   0,   0,   0,   0,   0,  # rank 8
    ],
    PieceType.KNIGHT: [
        -50, -40, -30, -30, -30, -30, -40, -50,  # rank 1
        -40, -20,   0,   5,   5,   0, -20, -40,  # rank 2
        -30,   5,  10,  15,  15,  10,   5, -30,  # rank 3
        -30,   0,  15,  20,  20,  15,   0, -30,  # rank 4
        -30,   5,  15,  20,  20,  15,   5, -30,  # rank 5
        -30,   0,  10,  15,  15,  10,   0, -30,  # rank 6
        -40, -20,   0,   0,   0,   0, -20, -40,  # rank 7
        -50, -40, -30, -30, -30, -30, -40, -50,  # rank 8
    ],
    PieceType.BISHOP: [
        -20, -10, -10, -10, -10, -10, -10, -20,  # rank 1
        -10,   5,   0,   0,   0,   0,   5, -10,  # rank 2
        -10,  10,  10,  10,  10,  10,  10, -10,  # rank 3
        -10,   0,  10,  10,  10,  10,   0, -10,  # rank 4
        -10,   5,   5,  10,  10,   5,   5, -10,  # rank 5
        -10,   0,   5,  10,  10,   5,   0, -10,  # rank 6
        -10,   0,   0,   0,   0,   0,   0, -10,  # rank 7
        -20, -10, -10, -10, -10, -10, -10, -20,  # rank 8
    ],
    PieceType.ROOK: [
          0,   0,   0,   5,   5,   0,   0,   0,  # rank 1
         -5,   0,   0,   0,   0,   0,   0,  -5,  # rank 2
         -5,   0,   0,   0,   0,   0,   0,  -5,  # rank 3
         -5,   0,   0,   0,   0,   0,   0,  -5,  # rank 4
         -5,   0,   0,   0,   0,   0,   0,  -5,  # rank 5
         -5,   0,   0,   0,   0,   0,   0,  -5,  # rank 6
          5,  10,  10,  10,  10,  10,  10,   5,  # rank 7
          0,   0,   0,   0,   0,   0,   0,   0,  # rank 8
    ],
    PieceType.QUEEN: [
        -20, -10, -10,  -5,  -5, -10, -10, -20,  # rank 1
        -10,   0,   5,   0,   0,   0,   0, -10,  # rank 2
        -10,   5,   5,   5,   5,   5,   0, -10,  # rank 3
          0,   0,   5,   5,   5,   5,   0,  -5,  # rank 4
         -5,   0,   5,   5,   5,   5,   0,  -5,  # rank 5
        -10,   0,   5,   5,   5,   5,   0, -10,  # rank 6
        -10,   0,   0,   0,   0,   0,   0, -10,  # rank 7
        -20, -10, -10,  -5,  -5, -10, -10, -20,  # rank 8
    ],
    PieceType.KING: [
         20,  30,  10,   0,   0,  10,  30,  20,  # rank 1
         20,  20,   0,   0,   0,   0,  20,  20,  # rank 2
        -10, -20, -20, -20, -20, -20, -20, -10,  # rank 3
        -20, -30, -30, -40, -40, -30, -30, -20,  # rank 4
        -30, -40, -40, -50, -50, -40, -40, -30,  # rank 5
        -30, -40, -40, -50, -50, -40, -40, -30,  # rank 6
        -30, -40, -40, -50, -50, -40, -40, -30,  # rank 7
        -30, -40, -40, -50, -50, -40, -40, -30,  # rank 8
    ],
}
# fmt: on


def materialistic_position_eval(position: Position) -> int:
    """Return the sum of all material values of the given position. Positive for white, negative for black"""

    def val(piece: Piece | None) -> int:
        if piece is None:
            return 0
        else:
            unit_dir = 1 if piece.color == Color.WHITE else -1
            return unit_dir * PIECE_VALUES[piece.type]

    return sum(val(square) for square in position.squares)


def piece_square_position_eval(position: Position) -> int:
    def sq_val(sq: int) -> int:
        piece = position.piece_at(sq)
        if piece is None:
            return 0
        else:
            sign = 1 if piece.color == Color.WHITE else -1
            # in PST, use the square if white, reflect board vertically if black
            lookup_sq = sq if piece.color == Color.WHITE else 8 * (7 - (sq // 8)) + sq % 8
            return sign * PIECE_SQUARE_TABLES[piece.type][lookup_sq]

    return sum(sq_val(sq) for sq in range(len(position.squares)))


def comprehensive_eval(position: Position) -> int:
    material_weight = 1
    piece_square_weight = 1

    # fmt: off
    return ( 
        material_weight * materialistic_position_eval(position) + 
        piece_square_weight * piece_square_position_eval(position)
    )
    # fmt: on
