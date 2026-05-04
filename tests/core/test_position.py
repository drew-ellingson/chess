"""Tests for Position make/unmake invariants.

The fundamental property: any sequence of make_move + unmake_move must
leave the position bitwise identical to the original. This catches the
hardest class of make/unmake bugs (forgotten state, wrong restoration of
castling rights, etc.).
"""

import pytest

from drewbert.adapters.fen import parse_fen
from drewbert.core.movegen import generate_legal_moves


@pytest.mark.parametrize(
    "fen",
    [
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    ],
)
def test_make_unmake_round_trip(fen: str) -> None:
    position = parse_fen(fen)
    snapshot = parse_fen(fen)

    for move in generate_legal_moves(position):
        undo = position.make_move(move)
        position.unmake_move(undo)
        assert position == snapshot, f"position differs after make/unmake of {move}"
