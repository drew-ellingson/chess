import time
from dataclasses import dataclass, field

from drewbert.core.helpers import move_applied
from drewbert.core.move import Move
from drewbert.core.movegen import generate_legal_moves, is_in_check
from drewbert.core.position import Color, Position
from drewbert.search.types import PositionEvalFn, SearchContext, SearchResult, SearchTimeout

CHECKMATE_SCORE = 10000000
STALEMATE_SCORE = 0
NODE_CHECK_FREQUENCY = 300


@dataclass()
class NegamaxReturn:
    val: int
    pv: list[Move] = field(default_factory=list)


def order_moves(legal_moves: list[Move], position: Position, plies_from_root: int, context: SearchContext):
    def mvv(move: Move, position: Position):
        pass

    def lva(move: Move, position: Position):
        pass

    moves = sorted(legal_moves, key=lambda m: (mvv(m, position), lva(m, position)), reverse=True)
    return moves


def negamax(
    position: Position,
    position_evaluator: PositionEvalFn,
    context: SearchContext,
    depth: int,
    alpha: int = -CHECKMATE_SCORE,
    beta: int = CHECKMATE_SCORE,
    plies_from_root: int = 0,
    on_pv: bool = True,
) -> NegamaxReturn:
    """Recursively traverse move tree, assuming optimal play at each point by both sides relative to given
    evaluation function.

    Returns score relative to the current player, as well as the principal variation move line required
    to reach that evaluation.

    Returns -CHECKMATE_SCORE sentinel in case of checkmate. Returns STALEMATE_SCORE in case of stalemate
    In case of multiple checkmates in the search tree, uses minimal plies_from_root value to prioritize
    faster checkmate.

    Uses alpha/beta pruning to identify branches of the search tree to skip. Values are set internally and don't
    need to be supplied from the call site. (Alpha, Beta) represent score-guarantee bounds. a return value is only
    exact when it falls within in (Alpha, Beta) window. Every other response is a bound. If value is >= beta,
    value is a lower bound. If value <= alpha, value is an upper bound.

    A principal variation (PV) is tracked in context. Move ordering places the principal variation first to
    improve early search results and achieve better pruning.

    raises SearchTimeout if time.monotonic() exceeds the deadline defined in context.
    """

    sign = 1 if position.side_to_move == Color.WHITE else -1
    context.nodes_computed += 1

    if context.deadline and context.nodes_computed % NODE_CHECK_FREQUENCY == 0 and time.monotonic() >= context.deadline:
        raise SearchTimeout("Deadline has been exceeded")

    legal_moves = generate_legal_moves(position)
    if not legal_moves:
        # handle terminal cases
        if not is_in_check(position, position.side_to_move):
            return NegamaxReturn(STALEMATE_SCORE, [])
        else:
            return NegamaxReturn(-CHECKMATE_SCORE + plies_from_root, [])

    # base case - end of recursion
    if depth == 0:
        curr_eval = position_evaluator(position)
        return NegamaxReturn(sign * curr_eval, [])

    pv_continues = on_pv and len(context.pv) > plies_from_root

    # move the principal variation to the front of the search queue
    if pv_continues:
        legal_moves.remove(context.pv[plies_from_root])

        legal_moves = [context.pv[plies_from_root]] + legal_moves

    max_eval = -CHECKMATE_SCORE
    pv: list[Move] = []

    for move in legal_moves:
        child_on_pv = pv_continues and context.pv[plies_from_root] == move
        with move_applied(position, move):
            move_result = negamax(
                position=position,
                position_evaluator=position_evaluator,
                context=context,
                depth=depth - 1,
                alpha=-beta,
                beta=-alpha,
                plies_from_root=plies_from_root + 1,
                on_pv=child_on_pv,
            )
        curr_eval = -1 * move_result.val
        if curr_eval > max_eval:
            pv = [move] + move_result.pv
            max_eval = curr_eval
        alpha = max(alpha, curr_eval)
        if alpha >= beta:
            break
    return NegamaxReturn(max_eval, pv)


def best_move(position: Position, position_evaluator: PositionEvalFn, context: SearchContext) -> SearchResult:
    """Provide a SearchResult object containing best move in the given position, as well as metadata surrounding the
    search. Iterates through increasing depth, storing the best result from each completed depth.

    Terminates based on signals from context.depth_limit or context.deadline that need to be passed in
    by any driver.

    Raises a ValueError if neither context.depth_limit nor context.deadline are defined.
    """

    if context.deadline is None and context.depth_limit is None:
        raise ValueError("Either deadline or depth limit must be set to use iterative deepening")

    start_time = time.monotonic()

    legal_moves = generate_legal_moves(position)

    if not legal_moves:
        return SearchResult(None, 0, 0, time.monotonic() - start_time)

    # default legal move to use if no depth iteration finishes
    curr_best_move = legal_moves[0]

    depth = 1
    while depth >= 1 and (context.depth_limit is None or depth <= context.depth_limit):
        try:
            result = negamax(position=position, position_evaluator=position_evaluator, context=context, depth=depth)
            curr_best_move = result.pv[0]
            context.pv = result.pv
        except SearchTimeout:
            depth = depth - 1  # decrement 1 to report completed depth only
            break
        if context.depth_limit and depth == context.depth_limit:
            break

        depth += 1

    return SearchResult(curr_best_move, context.nodes_computed, depth, time.monotonic() - start_time)
