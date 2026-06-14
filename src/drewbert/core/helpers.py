from contextlib import contextmanager

from drewbert.core.position import Move, Position


@contextmanager
def move_applied(position: Position, move: Move):
    """Context manager to handle make_move and unmake_move wrapping around
    position evaluation and search functions.
    """
    undo = position.make_move(move)
    try:
        yield
    finally:
        position.unmake_move(undo)
