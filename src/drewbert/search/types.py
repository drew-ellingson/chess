from collections.abc import Callable
from dataclasses import dataclass

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

    curr_best_move is used to track the current best candidate move. It isn't trustworth until and
    unless a given depth of search is completed."""

    deadline: float | None = None
    nodes_computed: int = 0
    depth_limit: int | None = None
    curr_best_move: Move | None = None
    root_best_move: Move | None = None


@dataclass(frozen=True)
class SearchResult:
    """Search result data and metadata. Max depth reached returns the largest _completed_ search depth.
    search_time returns the total search time in seconds, ignoring any latency from the call site."""

    move: Move | None
    nodes_computed: int
    max_depth_reached: int
    search_time: float
