from dataclasses import dataclass

from drewbert.core.types import PieceType, Square


def _sq_name(sq: Square) -> str:
    return f"{chr(ord('a') + sq % 8)}{sq // 8 + 1}"


@dataclass(frozen=True, slots=True)
class Move:
    from_square: Square
    to_square: Square
    promotion: PieceType | None = None

    def __repr__(self) -> str:
        base = f"{_sq_name(self.from_square)}{_sq_name(self.to_square)}"
        if self.promotion is None:
            return base
        return f"{base}{repr(self.promotion).lower()}"


