from drewbert.core.movegen import generate_legal_moves
from drewbert.core.position import Color, Move, Position
from drewbert.eval.types import PositionEvalFn


def optimization_fn(position):
    return max if position.side_to_move == Color.WHITE else min


def minimax(position: Position, depth: int, position_evaluator: PositionEvalFn) -> int:

    legal_moves = generate_legal_moves(position)

    # root case - end of recursion of checkmate / stalemate
    if depth == 0 or not legal_moves:
        curr_eval = position_evaluator(position)
        return curr_eval

    # recursive case - handle position state management and make the recursive call
    def score_cand_move(position: Position, move):
        undo = position.make_move(move)
        val = minimax(position, depth - 1, position_evaluator)
        position.unmake_move(undo)
        return val

    return optimization_fn(position)(score_cand_move(position, move) for move in legal_moves)


def best_move(position: Position, position_evaluator: PositionEvalFn, depth: int) -> Move:
    """Given a position and a move evaluation function, return the best depth=1 move in the position.
    White is maximizing board eval, Black is minimizing it.
    """

    def score_cand_move(position: Position, move):
        undo = position.make_move(move)
        val = minimax(position, depth, position_evaluator)
        position.unmake_move(undo)
        return val

    return optimization_fn(position)(generate_legal_moves(position), key=lambda m: score_cand_move(position, m))
