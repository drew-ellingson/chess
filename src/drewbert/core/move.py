from dataclasses import dataclass

from drewbert.core.types import PieceType, Square


@dataclass(frozen=True, slots=True)
class Move:
    from_square: Square
    to_square: Square
    promotion: PieceType | None = None
