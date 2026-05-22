"""Tests for movegen helpers.

Square indices are rank-major: a1=0, h1=7, a8=56, h8=63. Ranks and files
are 0-indexed, so a1 = (rank=0, file=0) and h8 = (rank=7, file=7).
"""

import pytest

from drewbert.core.movegen import rank_file_to_sq, sq_to_rank_file


@pytest.mark.parametrize(
    "square,rank_file",
    [
        (0, (0, 0)),  # a1
        (7, (0, 7)),  # h1
        (56, (7, 0)),  # a8
        (63, (7, 7)),  # h8
        (28, (3, 4)),  # e4
        (43, (5, 3)),  # d6
        (8, (1, 0)),  # a2 — first square of second rank
        (15, (1, 7)),  # h2 — last square of second rank
    ],
)
def test_sq_to_rank_file_known_values(square: int, rank_file: tuple[int, int]) -> None:
    assert sq_to_rank_file(square) == rank_file


@pytest.mark.parametrize(
    "rank_file,square",
    [
        ((0, 0), 0),
        ((0, 7), 7),
        ((7, 0), 56),
        ((7, 7), 63),
        ((3, 4), 28),
        ((5, 3), 43),
        ((1, 0), 8),
        ((1, 7), 15),
    ],
)
def test_rank_file_to_sq_known_values(rank_file: tuple[int, int], square: int) -> None:
    assert rank_file_to_sq(rank_file) == square


def test_helpers_round_trip_all_squares() -> None:
    """sq_to_rank_file and rank_file_to_sq are inverses on every valid square."""
    for sq in range(64):
        assert rank_file_to_sq(sq_to_rank_file(sq)) == sq


def test_helpers_round_trip_all_rank_file_pairs() -> None:
    """Round-trip the other direction: every (rank, file) pair in [0, 8)²."""
    for rank in range(8):
        for file in range(8):
            assert sq_to_rank_file(rank_file_to_sq((rank, file))) == (rank, file)


@pytest.mark.parametrize(
    "bad",
    [
        pytest.param(-1, id="negative_one"),
        pytest.param(64, id="just_above_range"),
        pytest.param(-100, id="far_negative"),
        pytest.param(1000, id="far_above_range"),
    ],
)
def test_sq_to_rank_file_rejects_out_of_range(bad: int) -> None:
    with pytest.raises(ValueError):
        sq_to_rank_file(bad)


@pytest.mark.parametrize(
    "bad",
    [
        pytest.param((-1, 0), id="negative_rank"),
        pytest.param((0, -1), id="negative_file"),
        pytest.param((8, 0), id="rank_just_above_range"),
        pytest.param((0, 8), id="file_just_above_range"),
        pytest.param((-1, -1), id="both_negative"),
        pytest.param((8, 8), id="both_above_range"),
        pytest.param((100, 3), id="rank_far_above_range"),
        pytest.param((3, 100), id="file_far_above_range"),
    ],
)
def test_rank_file_to_sq_rejects_out_of_range(bad: tuple[int, int]) -> None:
    with pytest.raises(ValueError):
        rank_file_to_sq(bad)
