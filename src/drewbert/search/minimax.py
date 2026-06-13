from collections.abc import Callable
from typing import Any

from drewbert.core.helpers import move_applied
from drewbert.core.movegen import generate_legal_moves, is_in_check
from drewbert.core.position import Color, Move, Position
from drewbert.search.types import PositionEvalFn

CHECKMATE_SCORE = 10000000
STALEMATE_SCORE = 0


def _optimization_fn(position: Position) -> Callable[..., Any]:
    """return max or min depending on side to move. white wants to maximize eval, black to minimize"""
    return max if position.side_to_move == Color.WHITE else min


def minimax(position: Position, position_evaluator: PositionEvalFn, depth: int, plies_from_root: int = 0) -> int:
    """recursively traverse move tree, assuming optimal play at each point by both sides relative to given
    evaluation function"""

    legal_moves = generate_legal_moves(position)
    if not legal_moves:
        # handle terminal cases
        if not is_in_check(position, position.side_to_move):
            return STALEMATE_SCORE
        else:
            return (
                -CHECKMATE_SCORE - plies_from_root
                if position.side_to_move == Color.WHITE
                else CHECKMATE_SCORE + plies_from_root
            )

    # root case - end of recursion
    if depth == 0:
        curr_eval = position_evaluator(position)
        return curr_eval

    # recursive case - handle position state management and make the recursive call
    def score_cand_move(position: Position, move):
        with move_applied(position, move):
            val = minimax(position, position_evaluator, depth - 1, plies_from_root + 1)
        return val

    return _optimization_fn(position)(score_cand_move(position, move) for move in legal_moves)


def best_move(position: Position, position_evaluator: PositionEvalFn, depth: int) -> Move:
    """Given a position and a move evaluation function, return the first move in the optimal branch of
    the minimax search at given depth. White is maximizing board eval, Black is minimizing it.
    """

    def score_cand_move(position: Position, move):
        with move_applied(position, move):
            val = minimax(position, position_evaluator, depth - 1)
        return val

    return _optimization_fn(position)(generate_legal_moves(position), key=lambda m: score_cand_move(position, m))
