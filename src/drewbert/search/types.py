from collections.abc import Callable
from dataclasses import dataclass

from drewbert.core.move import Move
from drewbert.core.position import Position

type PositionEvalFn = Callable[[Position], int]
type SearchFn = Callable[[Position, int], int]


class SearchTimeout(Exception):
    """Raised inside search when the deadline passes, caught by the iterative deepening driver"""


@dataclass
class SearchContext:
    deadline: float | None = None
    nodes_computed: int = 0
    depth_limit: int | None = None
    curr_best_move: Move | None = None


@dataclass(frozen=True)
class SearchResult:
    """Search result data and metadata. Max depth reached returns the largest _completed_ search depth.
    search_time returns the total search time in seconds, ignoring any latency from the call site."""

    move: Move | None
    nodes_computed: int
    max_depth_reached: int
    search_time: float
