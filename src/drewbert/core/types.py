from dataclasses import dataclass
from enum import IntEnum


class Color(IntEnum):
    WHITE = 0
    BLACK = 1

    def __repr__(self) -> str:
        return "White" if self == Color.WHITE else "Black"

    __str__ = __repr__ 


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

    def __repr__(self) -> str:
        return _PIECE_TYPE_LETTERS[self]


_PIECE_TYPE_LETTERS = {
    PieceType.PAWN: "P",
    PieceType.KNIGHT: "N",
    PieceType.BISHOP: "B",
    PieceType.ROOK: "R",
    PieceType.QUEEN: "Q",
    PieceType.KING: "K",
}


@dataclass(frozen=True, slots=True)
class Piece:
    type: PieceType
    color: Color

    def __repr__(self) -> str:
        letter = _PIECE_TYPE_LETTERS[self.type]
        return letter if self.color == Color.WHITE else letter.lower()


# Square is an int 0..63, rank-major: a1=0, b1=1, ..., h1=7, a2=8, ..., h8=63.
# Kept as a plain alias rather than a NewType for ergonomic arithmetic.
Square = int


@dataclass(frozen=True, slots=True)
class CastlingRights:
    white_kingside: bool = True
    white_queenside: bool = True
    black_kingside: bool = True
    black_queenside: bool = True

    def __repr__(self) -> str:
        flags = (
            ("K", self.white_kingside),
            ("Q", self.white_queenside),
            ("k", self.black_kingside),
            ("q", self.black_queenside),
        )
        s = "".join(letter for letter, enabled in flags if enabled)
        return s or "-"
