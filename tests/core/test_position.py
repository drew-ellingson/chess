"""Tests for Position make/unmake invariants.

The fundamental property: `make_move` followed by `unmake_move` must
leave the position bitwise identical to the original. This catches the
hardest class of make/unmake bugs (forgotten state in Undo, wrong
restoration of castling rights, EP target, halfmove clock, etc.).

The invariant must hold for every *pseudo-legal* move, not just legal
ones — `generate_legal_moves` itself uses make/unmake on pseudo-legal
candidates to filter for king safety, so a make/unmake bug at the
pseudo-legal level cascades into the legality filter and from there
into perft.
"""

import copy

import pytest

from drewbert.adapters.fen import parse_fen
from drewbert.core.movegen import generate_pseudo_legal_moves
from tests.core._helpers import diff_positions

# A spread of positions exercising every special-move case make/unmake
# has to handle: ordinary moves, captures, EP, castling, promotion.
# Kept in sync with the canonical list in tests/adapters/test_fen.py.
FENS = [
    # Starting position
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    # Kiwipete — dense middlegame, all castling rights, captures everywhere
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    # Perft position 3 — sparse, exposes EP and edge-case pawn moves
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    # Perft position 4 — promotions in play, partial castling rights
    "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2pP/R2Q1RK1 w kq - 0 1",
    # Perft position 5 — promotion-heavy
    "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
    # EP target set after 1.e4 — exercises EP capture path
    "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
    # Black to move from starting position
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1",
]


@pytest.mark.parametrize("fen", FENS)
def test_make_unmake_round_trip(fen: str) -> None:
    """make_move then unmake_move restores the position exactly, for every pseudo-legal move."""
    position = parse_fen(fen)
    for move in generate_pseudo_legal_moves(position):
        snapshot = copy.deepcopy(position)
        undo = position.make_move(move)
        position.unmake_move(undo)
        diffs = diff_positions(snapshot, position)
        assert not diffs, f"{fen} / {move}: {diffs}"


@pytest.mark.parametrize("fen", FENS)
def test_make_returns_undo_with_move(fen: str) -> None:
    """Sanity: the returned Undo references the move that was made."""
    position = parse_fen(fen)

    for move in generate_pseudo_legal_moves(position):
        snapshot = copy.deepcopy(position)
        undo = position.make_move(move)
        assert undo.move == move
        position.unmake_move(undo)
        diffs = diff_positions(snapshot, position)
        assert not diffs, f"{fen} / {move}: {diffs}"
