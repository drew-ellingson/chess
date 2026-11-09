"""Play a game against drewbert in the terminal.

Picks search + eval components by name so new ones (alpha-beta, NNUE, etc.)
plug in with one line in the registries below.

Usage:
    uv run python scripts/play.py                           # you play White vs negamax + comprehensive, 2s per move
    uv run python scripts/play.py --side black --move-time 5
    uv run python scripts/play.py --side none --move-time 1 # engine vs engine (self-play)
    uv run python scripts/play.py --fen "<fen>"             # custom start

Move input is UCI: `e2e4`, `g1f3`, promotion `e7e8q`. Type `quit` or `resign`
at the prompt to end the game.
"""

import argparse
import sys
import time
from collections.abc import Callable

from drewbert.adapters.ascii import render
from drewbert.adapters.fen import alg_sq_to_int, parse_fen
from drewbert.core.move import Move
from drewbert.core.movegen import generate_legal_moves, is_in_check
from drewbert.core.position import Color, Position
from drewbert.core.types import PieceType
from drewbert.eval.eval import comprehensive_eval, materialistic_position_eval
from drewbert.search.negamax import best_move
from drewbert.search.types import PositionEvalFn, SearchContext, SearchResult

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
DEFAULT_MOVE_TIME_S = 2.0

# Registries. Add new search/eval modules here to make them selectable from the CLI.
# Search functions must accept (position, eval_fn, context) and return a SearchResult object
EVALS: dict[str, PositionEvalFn] = {
    "comprehensive": comprehensive_eval,
    "material": materialistic_position_eval,
}

SearchFn = Callable[[Position, PositionEvalFn, SearchContext], SearchResult]
SEARCHES: dict[str, SearchFn] = {
    "negamax": best_move,
}

PROMOTION_LETTERS = {
    "q": PieceType.QUEEN,
    "r": PieceType.ROOK,
    "b": PieceType.BISHOP,
    "n": PieceType.KNIGHT,
}


def parse_user_move(text: str, legal_moves: list[Move]) -> Move | None:
    """Parse UCI input and return the matching legal move, or None if invalid."""
    text = text.strip().lower()
    if len(text) not in (4, 5):
        return None
    try:
        from_sq = alg_sq_to_int(text[0:2])
        to_sq = alg_sq_to_int(text[2:4])
    except ValueError:
        return None
    promotion: PieceType | None = None
    if len(text) == 5:
        promotion = PROMOTION_LETTERS.get(text[4])
        if promotion is None:
            return None
    candidate = Move(from_sq, to_sq, promotion)
    return candidate if candidate in legal_moves else None


def prompt_human_move(legal_moves: list[Move]) -> Move | None:
    """Block on stdin until the user enters a legal move. Returns None if they resign/quit."""
    while True:
        try:
            text = input("Your move (UCI, e.g. e2e4): ").strip().lower()
        except EOFError:
            return None
        if text in ("quit", "exit", "resign"):
            return None
        move = parse_user_move(text, legal_moves)
        if move is not None:
            return move
        print("  invalid — try again (UCI like e2e4, or `resign`)")


def announce_terminal(position: Position) -> None:
    if is_in_check(position, position.side_to_move):
        winner = "Black" if position.side_to_move == Color.WHITE else "White"
        print(f"\nCheckmate. {winner} wins.")
    else:
        print("\nStalemate. Draw.")


def positive_seconds(text: str) -> float:
    """argparse type for --move-time: a positive number of seconds."""
    seconds = float(text)
    if seconds <= 0:
        raise argparse.ArgumentTypeError(f"must be positive, got {text}")
    return seconds


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Play a game against drewbert in the terminal.")
    parser.add_argument(
        "--eval", choices=sorted(EVALS), default="comprehensive", help="evaluation function (default: comprehensive)"
    )
    parser.add_argument(
        "--search", choices=sorted(SEARCHES), default="negamax", help="search algorithm (default: negamax)"
    )
    parser.add_argument(
        "--move-time",
        type=positive_seconds,
        default=DEFAULT_MOVE_TIME_S,
        help=f"seconds the engine may think per move (default: {DEFAULT_MOVE_TIME_S:g})",
    )
    parser.add_argument(
        "--side",
        choices=["white", "black", "none"],
        default="white",
        help="which side the human plays; 'none' is engine-vs-engine (default: white)",
    )
    parser.add_argument("--fen", default=STARTING_FEN, help="starting FEN (default: standard)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    eval_fn = EVALS[args.eval]
    search_fn = SEARCHES[args.search]
    human_side: Color | None = {"white": Color.WHITE, "black": Color.BLACK, "none": None}[args.side]

    position = parse_fen(args.fen)

    print(f"\n{args.search} ({args.move_time:g}s per move) / {args.eval} eval")
    print(render(position))

    while True:
        legal_moves = generate_legal_moves(position)
        if not legal_moves:
            announce_terminal(position)
            return 0

        side_label = "White" if position.side_to_move == Color.WHITE else "Black"
        print(f"\n{side_label} to move.")
        # Standard notation: "31." before White's move, "31..." before Black's.
        move_number = f"{position.fullmove_number}{'.' if position.side_to_move == Color.WHITE else '...'}"

        if position.side_to_move == human_side:
            move = prompt_human_move(legal_moves)
            if move is None:
                winner = "White" if position.side_to_move == Color.BLACK else "Black"
                print(f"\nResigned. {winner} wins.")
                return 0
            print(f"  you played: {move_number} {move!r}")
        else:
            print(f"  engine thinking ({args.move_time:g}s)...")
            context = SearchContext(deadline=time.monotonic() + args.move_time)
            result = search_fn(position, eval_fn, context)
            move = result.move
            assert move is not None, "search returned None despite non-empty legal_moves"
            stats = f"depth {result.max_depth_reached}, {result.search_time:.2f}s"
            print(f"  engine plays: {move_number} {move!r} ({stats})")

        position.make_move(move)
        print(render(position))


if __name__ == "__main__":
    sys.exit(main())
