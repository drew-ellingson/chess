from typing import Callable
from drewbert.core.position import Position
from drewbert.core.move import Move 

type PositionEvalFn = Callable[[Position], int]
type MoveEvalFn = Callable[[Position, Move], int]