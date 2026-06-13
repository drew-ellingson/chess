from contextlib import contextmanager

from drewbert.core.position import Move, Position


@contextmanager
def move_applied(position: Position, move: Move):
    undo = position.make_move(move)
    try:
        yield
    finally:
        position.unmake_move(undo)
