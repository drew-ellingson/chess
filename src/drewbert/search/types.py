from collections.abc import Callable
from dataclasses import dataclass, field

from drewbert.core.move import Move
from drewbert.core.position import Position

type PositionEvalFn = Callable[[Position], int]


class SearchTimeout(Exception):
    """Raised inside search when the deadline passes, caught by the iterative deepening driver"""


@dataclass
class SearchContext:
    """Context object for tracking running call context information and for storing in-progress search
    values.
    deadline and depth_limit are search params passed in from a call site.

    root_pv is used to track the current principal variation from completed root nodes. Because principal
    variation is used. Any completed node with higher evaluation is guaranteed better than the previous
    iterations best move, and so can be used.

    prev_depth_pv is kept for stable move ordering in the subsequent depth search.
    """

    deadline: float | None = None
    nodes_computed: int = 0
    depth_limit: int | None = None
    root_pv: list[Move] = field(default_factory=list)
    prev_depth_pv: list[Move] = field(default_factory=list)


@dataclass(frozen=True)
class SearchResult:
    """Search result data and metadata. Max depth reached returns the largest _completed_ search depth.
    search_time returns the total search time in seconds, ignoring any latency from the call site."""

    move: Move | None
    nodes_computed: int
    max_depth_reached: int
    search_time: float
