from collections.abc import Callable

from drewbert.core.move import Move
from drewbert.core.position import Position

type PositionEvalFn = Callable[[Position], int]
type MoveEvalFn = Callable[[Position, Move], int]
