from collections.abc import Callable

from drewbert.core.position import Position

type PositionEvalFn = Callable[[Position], int]
