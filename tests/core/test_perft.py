"""Standard perft test suite.

Reference values from the Chess Programming Wiki (Perft Results page).

These tests will fail until move generation is implemented. Tests at
depth >= 4 are marked `slow` because pure-Python move generation will take
seconds-to-minutes at those depths.

    pytest                       # all (slow runs are slow)
    pytest -m "not slow"         # fast feedback during development
"""

import pytest

from drewbert.adapters.fen import parse_fen
from drewbert.core.perft import perft

PERFT_POSITIONS: list[tuple[str, str, list[tuple[int, int]]]] = [
    (
        "starting",
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        [(1, 20), (2, 400), (3, 8902), (4, 197281), (5, 4865609)],
    ),
    (
        "kiwipete",
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        [(1, 48), (2, 2039), (3, 97862), (4, 4085603)],
    ),
    (
        "position_3",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        [(1, 14), (2, 191), (3, 2812), (4, 43238), (5, 674624)],
    ),
    (
        "position_4",
        "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",
        [(1, 6), (2, 264), (3, 9467), (4, 422333)],
    ),
    (
        "position_5",
        "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
        [(1, 44), (2, 1486), (3, 62379), (4, 2103487)],
    ),
    (
        "position_6",
        "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10",
        [(1, 46), (2, 2079), (3, 89890), (4, 3894594)],
    ),
]

SLOW_DEPTH_THRESHOLD = 4


@pytest.mark.parametrize(
    "fen,depth,expected",
    [
        pytest.param(
            fen,
            depth,
            expected,
            marks=[pytest.mark.slow] if depth >= SLOW_DEPTH_THRESHOLD else [],
            id=f"{name}-d{depth}",
        )
        for name, fen, pairs in PERFT_POSITIONS
        for depth, expected in pairs
    ],
)
def test_perft(fen: str, depth: int, expected: int) -> None:
    position = parse_fen(fen)
    assert perft(position, depth) == expected
