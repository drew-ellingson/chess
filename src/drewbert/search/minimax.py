import time
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from typing import Any

from drewbert.core.helpers import move_applied
from drewbert.core.movegen import generate_legal_moves, is_in_check
from drewbert.core.position import Color, Move, Position
from drewbert.search.types import PositionEvalFn

CHECKMATE_SCORE = 10000000
STALEMATE_SCORE = 0


class SearchTimeout(BaseException):
    def __init__(self):
        super().__init__()
        self.message = "Deadline has been exceeded"


@dataclass
class SearchContext:
    deadline: float | None = None
    nodes_computed: int = 0
    depth_limit: int | None = None


def _optimization_fn(position: Position) -> Callable[..., Any]:
    """return max or min depending on side to move. white wants to maximize eval, black to minimize"""
    return max if position.side_to_move == Color.WHITE else min


def _score_cand_move(position: Position, move: Move, search_fn: PositionEvalFn) -> int:
    """Return search evaluation of given move at given position.
    search_fn here is designed to be minimax with different parameters pre-populated
    depending on the recursion state.
    """
    with move_applied(position, move):
        val = search_fn(position)
    return val


def minimax(
    position: Position, position_evaluator: PositionEvalFn, context: SearchContext, depth: int, plies_from_root: int = 0
) -> int:
    """recursively traverse move tree, assuming optimal play at each point by both sides relative to given
    evaluation function.
    Returns +- CHECKMATE_SCORE sentinel in case of checkmate. Returns STALEMATE_SCORE in case of stalemate
    In case of multiple checkmates in the search tree, uses minimal plies_from_root value to prioritize
    faster checkmate.

    CURRENTLY, if deadline is reached prior to move being reached, returns None.
    """

    context.nodes_computed += 1

    if context.deadline and context.nodes_computed % 1000 == 0 and time.monotonic() >= context.deadline:
        raise SearchTimeout()

    legal_moves = generate_legal_moves(position)
    if not legal_moves:
        # handle terminal cases
        if not is_in_check(position, position.side_to_move):
            return STALEMATE_SCORE
        else:
            return (
                -CHECKMATE_SCORE + plies_from_root
                if position.side_to_move == Color.WHITE
                else CHECKMATE_SCORE - plies_from_root
            )

    # base case - end of recursion
    if depth == 0:
        curr_eval = position_evaluator(position)
        return curr_eval

    # recursive case - handle position state management and make the recursive call
    search_fn = partial(
        minimax,
        position_evaluator=position_evaluator,
        context=context,
        depth=depth - 1,
        plies_from_root=plies_from_root + 1,
    )
    return _optimization_fn(position)(_score_cand_move(position, move, search_fn) for move in legal_moves)


def best_move(
    position: Position, position_evaluator: PositionEvalFn, depth: int, context: SearchContext | None = None
) -> Move | None:
    """Given a position and a move evaluation function, return the first move in the optimal branch of
    the minimax search at given depth. White is maximizing board eval, Black is minimizing it.
    """

    # initialize context object if not provided from uci adapter / other drivers
    if not context:
        context = SearchContext()

    legal_moves = generate_legal_moves(position)
    if not legal_moves:
        return None

    search_fn = partial(
        minimax, position_evaluator=position_evaluator, context=context, depth=depth - 1, plies_from_root=1
    )
    return _optimization_fn(position)(legal_moves, key=lambda m: _score_cand_move(position, m, search_fn))


def best_move_iterative_deepening(
    position: Position, position_evaluator: PositionEvalFn, context: SearchContext
) -> Move | None:

    if not context.deadline:
        raise ValueError("Deadline must be set to use iterative deepening")

    # fresh context for depth=1 case so deadline isn't a concern and a move is always returned.
    curr_best_move = best_move(position=position, position_evaluator=position_evaluator, depth=1)

    depth = 2
    while depth >= 1:
        try:
            curr_best_move = best_move(
                position=position, position_evaluator=position_evaluator, context=context, depth=depth
            )
        except SearchTimeout:
            break
        if context.depth_limit and depth == context.depth_limit:
            break

        depth += 1

    return curr_best_move
