"""Regression tests for the iterative-deepening driver (`best_move`) and the PV state it keeps.

Each test pins a bug that shipped at some point on the PV-ordering branch. None of them are caught by
the mate puzzles in test_negamax.py, because those positions happen to give the right answer at
depth N-1 too, and the first legal move is never checked against the searched move.
"""

import time

import pytest

from drewbert.adapters.fen import parse_fen
from drewbert.core.movegen import generate_legal_moves
from drewbert.eval.eval import materialistic_position_eval
from drewbert.search import negamax as negamax_module
from drewbert.search.negamax import best_move
from drewbert.search.types import SearchContext

# White to move; Rxa4 wins a free queen. The first generated legal move (a quiet rook move) does not,
# so returning an unsearched fallback is distinguishable from returning the depth-1 result.
FREE_QUEEN_FEN = "4k3/8/8/8/q7/8/8/R3K3 w - - 0 1"
FREE_QUEEN_BEST = "a1a4"

KIWIPETE_FEN = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
CHECKMATED_FEN = "R5k1/5ppp/8/8/8/8/8/7K b - - 0 1"
STALEMATED_FEN = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"


def test_depth_limit_returns_result_of_final_depth() -> None:
    """Regression: the final depth's move was dropped when the depth limit `break` ran before the
    best-move update, so depth_limit=1 returned the unsearched first legal move."""
    position = parse_fen(FREE_QUEEN_FEN)
    assert repr(generate_legal_moves(position)[0]) != FREE_QUEEN_BEST  # guards the test's premise

    result = best_move(position, materialistic_position_eval, SearchContext(depth_limit=1))

    assert repr(result.move) == FREE_QUEEN_BEST
    assert result.max_depth_reached == 1


def test_root_pv_is_a_legal_line_from_the_root() -> None:
    """Regression: interior nodes wrote their own lines into the search-level PV, leaving it holding
    a line that starts from some interior position (e.g. a Black move in a White-to-move root)."""
    position = parse_fen(KIWIPETE_FEN)
    context = SearchContext(depth_limit=3)

    result = best_move(position, materialistic_position_eval, context)

    assert context.root_pv, "completed search should leave a non-empty root PV"
    assert context.root_pv[0] == result.move
    assert len(context.root_pv) <= 3
    for move in context.root_pv:
        assert move in generate_legal_moves(position), f"{move!r} is not legal in the PV position"
        position.make_move(move)


def test_pv_ordering_survives_multiple_iterations() -> None:
    """Regression: PV ordering indexed the previous PV by remaining depth instead of ply, and its
    on-PV flag never switched off for sibling moves, so `list.remove` raised ValueError (or the PV
    index went out of range) on the second iteration."""
    result = best_move(parse_fen(KIWIPETE_FEN), materialistic_position_eval, SearchContext(depth_limit=3))

    assert result.max_depth_reached == 3
    assert result.move is not None


def test_deadline_search_returns_a_searched_move() -> None:
    """A deadline that has already passed still returns a move found by search (depth 1 always fits
    inside one deadline-check interval), not the unsearched fallback."""
    context = SearchContext(deadline=time.monotonic())

    result = best_move(parse_fen(FREE_QUEEN_FEN), materialistic_position_eval, context)

    assert repr(result.move) == FREE_QUEEN_BEST


def test_timeout_before_any_root_move_completes_falls_back_to_a_legal_move(monkeypatch: pytest.MonkeyPatch) -> None:
    """If the very first deadline check fires before any root move finishes, there is no searched
    move, and best_move should return its legal-move fallback rather than raise.

    Unreachable through inputs alone: best_move resets the node counter, and depth 1 visits at most
    219 nodes, fewer than one check interval. Forced here by checking the deadline on every node, so
    the root node itself times out against an already-expired deadline."""
    monkeypatch.setattr(negamax_module, "NODE_CHECK_FREQUENCY", 1)
    position = parse_fen(FREE_QUEEN_FEN)
    context = SearchContext(deadline=time.monotonic() - 1)

    result = best_move(position, materialistic_position_eval, context)

    assert result.move in generate_legal_moves(position)
    assert result.max_depth_reached == 0


def test_reused_context_does_not_carry_pv_into_a_new_position() -> None:
    """Regression guard for the defensive reset: a context reused across positions must not order
    moves by the previous position's PV (whose moves are usually illegal in the new one)."""
    context = SearchContext(depth_limit=2)
    best_move(parse_fen(KIWIPETE_FEN), materialistic_position_eval, context)

    result = best_move(parse_fen(FREE_QUEEN_FEN), materialistic_position_eval, context)

    assert repr(result.move) == FREE_QUEEN_BEST


def test_checkmated_root_returns_no_move() -> None:
    result = best_move(parse_fen(CHECKMATED_FEN), materialistic_position_eval, SearchContext(depth_limit=3))

    assert result.move is None
    assert result.max_depth_reached == 0


def test_stalemated_root_returns_no_move() -> None:
    result = best_move(parse_fen(STALEMATED_FEN), materialistic_position_eval, SearchContext(depth_limit=3))

    assert result.move is None
    assert result.max_depth_reached == 0
