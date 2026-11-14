"""Quiescence search: capture-only search past the depth horizon, with stand pat.

Two layers of tests:
- Through `best_move` at depth_limit=1, where a plain fixed-depth search evaluates the position right after
  a capture and so mistakes a defended capture for a free one (the horizon effect).
- Directly on `quiescence`, with the material-only eval so expected scores are exact centipawn values. Scores
  are from the side to move's perspective, matching negamax.

The material-only eval is used throughout so these tests don't move when PST values are tuned.
"""

import chess
import pytest

from drewbert.adapters.fen import parse_fen
from drewbert.core.movegen import generate_legal_moves
from drewbert.eval.eval import materialistic_position_eval
from drewbert.search.negamax import CHECKMATE_SCORE, best_move, quiescence
from drewbert.search.types import SearchContext

FULL_WINDOW = (-CHECKMATE_SCORE, CHECKMATE_SCORE)

# White Qd1 can take the d5 pawn, but e6 recaptures and wins the queen. With no quiet move that loses
# material, the static eval (+700 for White) is also the quiescence value: White should stand pat.
POISONED_PAWN_FEN = "6k1/8/4p3/3p4/8/8/8/3Q2K1 w - - 0 1"
POISONED_PAWN_STATIC = 900 - 2 * 100

# Two captures for White: Qa2xd5 takes a rook (+500 at the horizon) but e6 recaptures the queen (net -400);
# b4xc5 takes a knight (+300) and loses the pawn back (net +200). Depth 1 without quiescence plays Qxd5.
BAD_VS_GOOD_CAPTURE_FEN = "6k1/8/1p2p3/2nr4/1P6/8/Q7/6K1 w - - 0 1"
GOOD_CAPTURE = "b4c5"

# c4xd5 wins a knight for a pawn after e6xd5: static -300 for White, -100 after the exchange.
EXCHANGE_WHITE_FEN = "6k1/8/4p3/3n4/2P5/8/8/6K1 w - - 0 1"
# The same position mirrored with colours swapped and Black to move, to catch sign errors.
EXCHANGE_BLACK_FEN = "6k1/8/8/2p5/3N4/4P3/8/6K1 b - - 0 1"
EXCHANGE_STATIC = -300
EXCHANGE_VALUE = -100

# Black is checkmated by Ra8 and has no captures. Stand pat would return the static eval instead of a mate score.
CHECKMATED_FEN = "R5k1/5ppp/8/8/8/8/8/7K b - - 0 1"
# Nc7+ forks Ke8 and Ra8. Black has no captures, so stand pat says +200 (rook vs knight), but Black must move
# the king out of check and then Nxa8 leaves Black a knight down: the true quiescence value is -300.
KNIGHT_FORK_IN_CHECK_FEN = "r3k3/2N5/8/8/8/8/8/7K b - - 0 1"


def q(fen: str, alpha: int = FULL_WINDOW[0], beta: int = FULL_WINDOW[1], plies_from_root: int = 0) -> int:
    return quiescence(
        position=parse_fen(fen),
        position_evaluator=materialistic_position_eval,
        context=SearchContext(depth_limit=1),
        alpha=alpha,
        beta=beta,
        plies_from_root=plies_from_root,
    )


# ---- horizon effect, through best_move ----


def test_depth_1_does_not_take_a_defended_pawn_with_the_queen() -> None:
    result = best_move(parse_fen(POISONED_PAWN_FEN), materialistic_position_eval, SearchContext(depth_limit=1))

    assert repr(result.move) != "d1d5"


def test_depth_1_prefers_winning_exchange_over_bigger_but_losing_capture() -> None:
    result = best_move(parse_fen(BAD_VS_GOOD_CAPTURE_FEN), materialistic_position_eval, SearchContext(depth_limit=1))

    assert repr(result.move) == GOOD_CAPTURE


# ---- quiescence values ----


def test_stand_pat_when_every_capture_loses() -> None:
    """The side to move isn't forced to capture: with only losing captures, the value is the static eval."""
    assert q(POISONED_PAWN_FEN) == POISONED_PAWN_STATIC


def test_resolves_an_exchange_white_to_move() -> None:
    assert q(EXCHANGE_WHITE_FEN) == EXCHANGE_VALUE


def test_resolves_an_exchange_black_to_move() -> None:
    """Colour-mirrored twin of the White test: same value from the side to move's perspective."""
    assert q(EXCHANGE_BLACK_FEN) == EXCHANGE_VALUE


def test_stand_pat_at_or_above_beta_cuts_off_without_searching_captures() -> None:
    """If the static eval already meets beta, quiescence returns it from the first node."""
    context = SearchContext(depth_limit=1)
    beta = EXCHANGE_STATIC - 100

    value = quiescence(
        position=parse_fen(EXCHANGE_WHITE_FEN),
        position_evaluator=materialistic_position_eval,
        context=context,
        alpha=-CHECKMATE_SCORE,
        beta=beta,
        plies_from_root=0,
    )

    assert value >= beta
    assert context.nodes_computed == 1


# ---- in check (stand pat is not allowed) ----


def test_checkmate_inside_quiescence_scores_as_mate() -> None:
    assert q(CHECKMATED_FEN, plies_from_root=3) == -CHECKMATE_SCORE + 3


def test_in_check_must_evade_instead_of_standing_pat() -> None:
    assert q(KNIGHT_FORK_IN_CHECK_FEN) == -300


# ---- noisy move generation ----


@pytest.mark.parametrize(
    "fen",
    [
        pytest.param("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", id="start"),
        pytest.param("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", id="kiwipete"),
        pytest.param("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1", id="en-passant"),
        pytest.param("1n2k3/P7/8/8/8/8/8/4K3 w - - 0 1", id="promotions-and-capture-promotions"),
        pytest.param(KNIGHT_FORK_IN_CHECK_FEN, id="in-check"),
    ],
)
def test_noisy_moves_are_exactly_the_legal_captures_and_promotions(fen: str) -> None:
    """python-chess is the oracle for which legal moves are captures (en passant included) or promotions."""
    board = chess.Board(fen)
    expected = {m.uci() for m in board.legal_moves if board.is_capture(m) or m.promotion is not None}

    noisy = {repr(m) for m in generate_legal_moves(parse_fen(fen), noisy_moves_only=True)}

    assert noisy == expected
