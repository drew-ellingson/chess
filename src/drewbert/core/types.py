from dataclasses import dataclass
from enum import IntEnum


class Color(IntEnum):
    WHITE = 0
    BLACK = 1

    @property
    def opposite(self) -> "Color":
        return Color.BLACK if self == Color.WHITE else Color.WHITE


class PieceType(IntEnum):
    PAWN = 0
    KNIGHT = 1
    BISHOP = 2
    ROOK = 3
    QUEEN = 4
    KING = 5


@dataclass(frozen=True, slots=True)
class Piece:
    type: PieceType
    color: Color


# Square is an int 0..63, rank-major: a1=0, b1=1, ..., h1=7, a2=8, ..., h8=63.
# Kept as a plain alias rather than a NewType for ergonomic arithmetic.
Square = int


@dataclass(frozen=True, slots=True)
class CastlingRights:
    white_kingside: bool = True
    white_queenside: bool = True
    black_kingside: bool = True
    black_queenside: bool = True
