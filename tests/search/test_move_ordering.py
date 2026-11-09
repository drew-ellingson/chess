"""MVV-LVA move ordering: captures sorted by most valuable victim, then least valuable attacker;
non-captures after all captures, in their original (move generation) order.

Ordering never changes search scores, only node counts, so these properties are tested directly on
`mvv_lva_order` rather than through search results.
"""

from drewbert.adapters.fen import parse_fen
from drewbert.core.movegen import generate_legal_moves
from drewbert.search.negamax import mvv_lva_order

# White: Ra1 and pawn b4 both attack the queen on a5; Nc3 attacks the rook on d5.
CAPTURES_FEN = "4k3/8/8/q2r4/1P6/2N5/8/R3K3 w - - 0 1"
EN_PASSANT_FEN = "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1"
PROMOTION_FEN = "4k3/P7/8/8/8/8/8/4K3 w - - 0 1"


def ordered_uci(fen: str) -> list[str]:
    position = parse_fen(fen)
    return [repr(m) for m in mvv_lva_order(generate_legal_moves(position), position)]


def test_captures_ordered_by_victim_then_attacker() -> None:
    ordered = ordered_uci(CAPTURES_FEN)

    # Queen victims first (pawn attacker before rook attacker), then the rook victim.
    assert ordered[:3] == ["b4a5", "a1a5", "c3d5"]


def test_quiet_moves_follow_captures_in_generation_order() -> None:
    position = parse_fen(CAPTURES_FEN)
    generated = [repr(m) for m in generate_legal_moves(position)]
    captures = {"b4a5", "a1a5", "c3d5"}

    ordered = ordered_uci(CAPTURES_FEN)

    assert ordered[3:] == [m for m in generated if m not in captures]


def test_en_passant_scores_as_pawn_capture() -> None:
    assert ordered_uci(EN_PASSANT_FEN)[0] == "e5d6"


def test_queen_promotion_ordered_first() -> None:
    assert ordered_uci(PROMOTION_FEN)[0] == "a7a8q"


def test_ordering_is_a_permutation() -> None:
    position = parse_fen(CAPTURES_FEN)
    legal = generate_legal_moves(position)

    ordered = mvv_lva_order(legal, position)

    assert sorted(map(repr, ordered)) == sorted(map(repr, legal))
