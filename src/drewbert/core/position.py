from dataclasses import dataclass

from drewbert.core.move import Move
from drewbert.core.types import CastlingRights, Color, Piece, Square


@dataclass
class Undo:
    """Records everything needed to reverse a move.

    Returned by `Position.make_move` and consumed by `Position.unmake_move`.
    Capturing this state (instead of copying the entire position) is what
    makes search efficient: millions of make/unmake pairs per second don't
    need to allocate a fresh board on each call.
    """

    move: Move
    captured: Piece | None
    prev_castling_rights: CastlingRights
    prev_en_passant_target: Square | None
    prev_halfmove_clock: int
    # Phase 3 will add: prev_zobrist_hash: int


@dataclass
class Position:
    """Full chess game state.

    Mutable. `make_move` modifies in place and returns an `Undo`.
    `unmake_move(undo)` reverses that change. After a make/unmake pair the
    Position is bitwise identical to its prior state.

    `squares` is a list of 64 entries indexed by `Square` (0..63), rank-major.
    Each entry is a `Piece` or `None`.
    """

    squares: list[Piece | None]
    side_to_move: Color
    castling_rights: CastlingRights
    en_passant_target: Square | None
    halfmove_clock: int
    fullmove_number: int

    def piece_at(self, square: Square) -> Piece | None:
        return self.squares[square]

    def king_square(self, color: Color) -> Square:
        """Return the square of the king of the given color.

        Raises ValueError if no king of that color is on the board.
        """
        raise NotImplementedError("phase 1")

    def make_move(self, move: Move) -> Undo:
        """Apply `move` to this position in place; return an Undo token.

        Responsibilities (incomplete or wrong handling here is the most
        common source of perft mismatches):
          - Move the piece from `move.from_square` to `move.to_square`.
          - Handle ordinary captures.
          - Handle en passant capture (the captured pawn is NOT on `to_square`).
          - Handle castling (move both king and rook).
          - Handle promotion (replace the pawn with `move.promotion`).
          - Update castling rights when a king or rook moves, OR when a
            rook is captured on its starting square.
          - Set `en_passant_target` on a double pawn push, otherwise clear it.
          - Reset `halfmove_clock` on pawn move or capture, else increment.
          - Increment `fullmove_number` after Black moves.
          - Toggle `side_to_move`.
          - (Phase 3) Update Zobrist hash incrementally.
        """
        raise NotImplementedError("phase 1")

    def unmake_move(self, undo: Undo) -> None:
        """Reverse the move described by `undo`, restoring all prior state."""
        raise NotImplementedError("phase 1")
