from drewbert.core.move import Move
from drewbert.core.position import Position
from drewbert.core.types import Color, Square


def generate_legal_moves(position: Position) -> list[Move]:
    """All legal moves for the side to move.

    A move is legal iff it is pseudo-legal AND does not leave the moving
    side's king in check.
    """
    raise NotImplementedError("phase 1")


def generate_pseudo_legal_moves(position: Position) -> list[Move]:
    """All moves that respect piece movement rules, ignoring king safety.

    Pseudo-legal moves may leave the moving side's king in check; legality
    is filtered by `generate_legal_moves`.
    """
    raise NotImplementedError("phase 1")


def is_in_check(position: Position, color: Color) -> bool:
    """True iff the king of `color` is currently attacked."""
    raise NotImplementedError("phase 1")


def is_square_attacked(position: Position, square: Square, by: Color) -> bool:
    """True iff `square` is attacked by any piece of color `by`."""
    raise NotImplementedError("phase 1")
