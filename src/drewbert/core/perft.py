"""Perft — Performance Test for move generation correctness.

Counts legal-move-tree leaves at a given depth. Compared against published
reference values to validate move generation. Bugs in special moves
(castling, en passant, promotion) and pin/check handling produce off-by-N
counts that hand-written tests almost never catch.

See `tests/core/test_perft.py` for the standard test suite.
"""

from drewbert.core.position import Position
from drewbert.core.movegen import generate_legal_moves


def perft(position: Position, depth: int) -> int:
    """Recursively count leaf nodes of the legal move tree at the given depth.
    """
    if depth == 0:
        return 1 
    nodes = 0
    for move in generate_legal_moves(position):
        undo = position.make_move(move)
        nodes += perft(position, depth - 1)
        position.unmake_move(undo)
    return nodes
