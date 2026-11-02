import time

from drewbert.core.helpers import move_applied
from drewbert.core.movegen import generate_legal_moves, is_in_check
from drewbert.core.position import Color, Position
from drewbert.search.types import PositionEvalFn, SearchContext, SearchResult, SearchTimeout

CHECKMATE_SCORE = 10000000
STALEMATE_SCORE = 0
NODE_CHECK_FREQUENCY = 300


def negamax(
    position: Position,
    position_evaluator: PositionEvalFn,
    context: SearchContext,
    depth: int,
    alpha: int = -CHECKMATE_SCORE,
    beta: int = CHECKMATE_SCORE,
    plies_from_root: int = 0,
) -> int:
    """Recursively traverse move tree, assuming optimal play at each point by both sides relative to given
    evaluation function, and returns score relative to the current player.
    Returns -CHECKMATE_SCORE sentinel in case of checkmate. Returns STALEMATE_SCORE in case of stalemate
    In case of multiple checkmates in the search tree, uses minimal plies_from_root value to prioritize
    faster checkmate.

    Uses alpha/beta pruning to identify branches of the search tree to skip. Values are set internally and don't
    need to be supplied from the call site. (Alpha, Beta) represent score-guarantee bounds. a return value is only
    exact when it falls within in (-inf, alpha) or (beta, inf
    Writes context.curr_best_move on root nodes if score is better than the current visited max_value.
    It's a side effect but sue me.

    context.curr_best_move values in case of truncated search are not trustworth. Needs to be wrapped with
    best_move or similar to return stable values from completed search depths.

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
            return STALEMATE_SCORE
        else:
            return -CHECKMATE_SCORE + plies_from_root

    # base case - end of recursion
    if depth == 0:
        curr_eval = position_evaluator(position)
        return sign * curr_eval

    max_eval = -CHECKMATE_SCORE

    for move in legal_moves:
        with move_applied(position, move):
            move_score = negamax(
                position=position,
                position_evaluator=position_evaluator,
                context=context,
                depth=depth - 1,
                alpha=-beta,
                beta=-alpha,
                plies_from_root=plies_from_root + 1,
            )
        curr_eval = -1 * move_score
        if curr_eval > max_eval:
            max_eval = curr_eval
            if plies_from_root == 0:
                context.curr_best_move = move
        alpha = max(alpha, curr_eval)
        if alpha >= beta:
            break
    return max_eval


def best_move(position: Position, position_evaluator: PositionEvalFn, context: SearchContext) -> SearchResult:
    """Provide a SearchResult object containing best move in the given position, as well as metadata surrounding the
    search. Iterates through increasing depth, storing the best result from each completed depth.

    Terminates based on signals from context.depth_limit or context.deadline that need to be passed in
    by any driver.

    Always completes depth=1 search to return a valid move, regardless of deadline passed by driver.

    Raises a ValueError if neither context.depth_limit nor context.deadline are defined.
    """

    start_time = time.monotonic()

    if context.deadline is None and context.depth_limit is None:
        raise ValueError("Either deadline or depth limit must be set to use iterative deepening")

    # fresh context for depth 1 case to allow depth 1 to always finish regardless of time control
    depth_1_context = SearchContext()
    negamax(position=position, position_evaluator=position_evaluator, context=depth_1_context, depth=1)
    curr_best_move = depth_1_context.curr_best_move

    # return early for terminal positions or low-depth calls
    if curr_best_move is None or (context.depth_limit is not None and context.depth_limit <= 1):
        return SearchResult(
            curr_best_move, context.nodes_computed + depth_1_context.nodes_computed, 1, time.monotonic() - start_time
        )

    depth = 2
    while depth >= 1 and (context.depth_limit is None or depth <= context.depth_limit):
        try:
            negamax(position=position, position_evaluator=position_evaluator, context=context, depth=depth)
            curr_best_move = context.curr_best_move
        except SearchTimeout:
            depth = depth - 1  # decrement 1 to report completed depth only
            break
        if context.depth_limit and depth == context.depth_limit:
            break

        depth += 1

    return SearchResult(
        curr_best_move, context.nodes_computed + depth_1_context.nodes_computed, depth, time.monotonic() - start_time
    )
