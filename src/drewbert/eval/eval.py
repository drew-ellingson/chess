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
# follows rank major order. eg. a1 in idx 0, a2 in idx 3, etc.
PIECE_SQUARE_TABLES = {
    PieceType.PAWN: [  
                       0,    0,    0,    0,    0,    0,    0,    0, 
                       0,    0,   -5,  -10,  -10,   -5,    0,    0, 
                       5,    5,   10,   15,   15,   10,    5,    5,
                      30,   10,   20,   40,   40,   20,   10,   30,
                      30,   15,   15,   40,   40,   15,   15,   30,
                      40,   25,   40,   50,   50,   40,   25,   40,
                     100,  100,  100,  100,  100,  100,  100,  100,
                       0,    0,    0,    0,    0,    0,    0,    0, 
                    ],
    PieceType.KNIGHT: [  
                    -100,  -20,    0,    0,    0,    0,  -20, -100, 
                     -50,  -10,   -5,   20,   20,   -5,  -10,  -50, 
                     -30,    0,   40,   40,   40,   40,    5,  -30,
                     -20,    0,   40,   50,   50,   40,   10,  -20,
                     -20,    0,   40,   50,   50,   40,   15,  -20,
                     -30,    0,   40,   40,   40,   40,   25,  -30,
                     -50,    0,  100,  100,  100,  100,  100,  -50,
                    -100,    0,    0,    0,    0,    0,    0, -100, 
                    ],
    PieceType.BISHOP:  [  
                     -30,  -20,  -10,    0,    0,  -10,  -20,  -30, 
                       0,   10,   -5,  -10,  -10,   -5,   10,    0, 
                       5,    5,   20,   40,   40,   20,    5,    5,
                       0,   10,   40,   40,   40,   40,   10,    0,
                       0,   15,   40,   40,   40,   40,   15,    0,
                       5,    5,   20,   40,   40,   20,    5,    5,
                       0,   10,   -5,  -10,  -10,   -5,   10,    0, 
                     -30,  -20,  -10,    0,    0,  -10,  -20,  -30, 
                    ],
    PieceType.ROOK:  [  
                     -10,    0,   20,   30,   30,   20,    0,  -10, 
                       0,    0,    0,   10,   10,    0,    0,    0, 
                       0,    0,    0,    0,    0,    0,    0,    0, 
                       0,    0,    0,    0,    0,    0,    0,    0, 
                       0,    0,    0,    0,    0,    0,    0,    0, 
                       0,    0,    0,    0,    0,    0,    0,    0, 
                      10,   20,   20,   20,   20,   20,   20,   10,
                     100,  100,  100,  100,  100,  100,  100,  100,
                      40,   40,   40,   40,   40,   40,   40,   40, 
                    ],
    PieceType.QUEEN:  [  
                     -20,    0,    0,    0,    0,    0,    0,  -20, 
                       0,    0,    0,    0,    0,    0,    0,    0, 
                       0,    0,   10,   10,   10,   10,    0,    0, 
                       0,    0,   10,   10,   10,   10,    0,    0, 
                       0,    0,   10,   10,   10,   10,    0,    0, 
                       0,    0,   10,   10,   10,   10,    0,    0, 
                       0,    0,    0,    0,    0,    0,    0,    0, 
                     -20,    0,    0,    0,    0,    0,    0,  -20, 
                    ],
    PieceType.KING: [  
                      40,   50,   20,    0,    0,   50,   40,   20, 
                      10,   10,   10,    0,    0,   10,   10,   10, 
                       0,    0,    0,    0,    0,    0,    0,    0, 
                     -30,  -30,  -30,  -30,  -30,  -30,  -30,  -30, 
                     -30,  -30,  -30,  -30,  -30,  -30,  -30,  -30, 
                     -30,  -30,  -30,  -30,  -30,  -30,  -30,  -30, 
                     -30,  -30,  -30,  -30,  -30,  -30,  -30,  -30, 
                     -30,  -30,  -30,  -30,  -30,  -30,  -30,  -30, 
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
