"""Play a game against drewbert in the terminal.

Picks search + eval components by name so new ones (alpha-beta, NNUE, etc.)
plug in with one line in the registries below.

Usage:
    uv run python scripts/play.py                           # you play White vs minimax + material, depth 3
    uv run python scripts/play.py --side black --depth 4
    uv run python scripts/play.py --side none --depth 4     # engine vs engine (self-play)
    uv run python scripts/play.py --fen "<fen>"             # custom start

Move input is UCI: `e2e4`, `g1f3`, promotion `e7e8q`. Type `quit` or `resign`
at the prompt to end the game.
"""

import argparse
import sys
from collections.abc import Callable

from drewbert.adapters.ascii import render
from drewbert.adapters.fen import alg_sq_to_int, parse_fen
from drewbert.core.move import Move
from drewbert.core.movegen import generate_legal_moves, is_in_check
from drewbert.core.position import Color, Position
from drewbert.core.types import PieceType
from drewbert.eval.materialistic import materialistic_position_eval
from drewbert.search.minimax import best_move
from drewbert.search.types import PositionEvalFn

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

# Registries. Add new search/eval modules here to make them selectable from the CLI.
# Search functions must accept (position, eval_fn, depth) and return a Move (or None for
# terminal positions).
EVALS: dict[str, PositionEvalFn] = {
    "material": materialistic_position_eval,
}
SearchFn = Callable[[Position, PositionEvalFn, int], Move | None]
SEARCHES: dict[str, SearchFn] = {
    "minimax": best_move,
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Play a game against drewbert in the terminal.")
    parser.add_argument(
        "--eval", choices=sorted(EVALS), default="material", help="evaluation function (default: material)"
    )
    parser.add_argument(
        "--search", choices=sorted(SEARCHES), default="minimax", help="search algorithm (default: minimax)"
    )
    parser.add_argument("--depth", type=int, default=3, help="search depth in ply (default: 3)")
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

    print(f"\n{args.search} (depth {args.depth}) / {args.eval} eval")
    print(render(position))

    while True:
        legal_moves = generate_legal_moves(position)
        if not legal_moves:
            announce_terminal(position)
            return 0

        side_label = "White" if position.side_to_move == Color.WHITE else "Black"
        print(f"\n{side_label} to move.")

        if position.side_to_move == human_side:
            move = prompt_human_move(legal_moves)
            if move is None:
                winner = "White" if position.side_to_move == Color.BLACK else "Black"
                print(f"\nResigned. {winner} wins.")
                return 0
            print(f"  you played: {move!r}")
        else:
            print(f"  engine thinking (depth {args.depth})...")
            move = search_fn(position, eval_fn, args.depth)
            assert move is not None, "search returned None despite non-empty legal_moves"
            print(f"  engine plays: {move!r}")

        position.make_move(move)
        print(render(position))


if __name__ == "__main__":
    sys.exit(main())
