from dataclasses import dataclass, replace

from drewbert.core.move import Move
from drewbert.core.types import CastlingRights, Color, Piece, PieceType, Square


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
        try:
            return min(i for i, x in enumerate(self.squares) if x and x.type == PieceType.KING and x.color == color)
        except ValueError:
            raise ValueError(f"No {color} king found on the board!") from None

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
        prev_castling_rights = self.castling_rights
        prev_en_passant_target = self.en_passant_target
        prev_halfmove_clock = self.halfmove_clock

        # basic updates
        captured = self.piece_at(move.to_square)
        from_piece = self.piece_at(move.from_square)

        self.squares[move.to_square] = self.piece_at(move.from_square)
        self.squares[move.from_square] = None

        # handling castling - can identify by king moving either 2 or 3 spaces horizontally.
        if from_piece is not None and from_piece.type == PieceType.KING and abs(move.from_square - move.to_square) == 2:
            # move the rook and handle castling rights
            if move.to_square % 8 == 6:  # kingside castling:
                self.squares[move.to_square - 1] = self.squares[move.to_square + 1]
                self.squares[move.to_square + 1] = None
                if self.side_to_move == Color.WHITE:
                    self.castling_rights = replace(self.castling_rights, white_kingside=False, white_queenside=False)
                else:
                    self.castling_rights = replace(self.castling_rights, black_kingside=False, black_queenside=False)
            elif move.to_square % 8 == 2:  # queenside castling:
                self.squares[move.to_square + 1] = self.squares[move.to_square - 2]
                self.squares[move.to_square - 2] = None
                if self.side_to_move == Color.WHITE:
                    self.castling_rights = replace(self.castling_rights, white_kingside=False, white_queenside=False)
                else:
                    self.castling_rights = replace(self.castling_rights, black_kingside=False, black_queenside=False)

        # king moves - update castling rights
        if from_piece is not None and from_piece.type == PieceType.KING:
            if self.side_to_move == Color.WHITE:
                self.castling_rights = replace(self.castling_rights, white_kingside=False, white_queenside=False)
            else:
                self.castling_rights = replace(self.castling_rights, black_kingside=False, black_queenside=False)

        # rook moves - update castling rights
        if from_piece is not None and from_piece.type == PieceType.ROOK:
            if self.side_to_move == Color.WHITE:
                if move.from_square % 8 == 0:
                    self.castling_rights = replace(self.castling_rights, white_queenside=False)
                if move.from_square % 8 == 7:
                    self.castling_rights = replace(self.castling_rights, white_kingside=False)
            else:
                if move.from_square % 8 == 0:
                    self.castling_rights = replace(self.castling_rights, black_queenside=False)
                if move.from_square % 8 == 7:
                    self.castling_rights = replace(self.castling_rights, black_kingside=False)

        # rook captured on starting square - update castling rights
        if captured is not None and captured.type == PieceType.ROOK:
            if move.to_square == 56 and self.side_to_move == Color.WHITE:
                self.castling_rights = replace(self.castling_rights, black_queenside=False)
            if move.to_square == 63 and self.side_to_move == Color.WHITE:
                self.castling_rights = replace(self.castling_rights, black_kingside=False)
            if move.to_square == 0 and self.side_to_move == Color.BLACK:
                self.castling_rights = replace(self.castling_rights, white_queenside=False)
            if move.to_square == 7 and self.side_to_move == Color.BLACK:
                self.castling_rights = replace(self.castling_rights, white_kingside=False)

        # handling promotion
        if move.promotion is not None:
            self.squares[move.to_square] = Piece(move.promotion, self.side_to_move)

        # handling en passant captures
        dir = 1 if self.side_to_move == Color.WHITE else -1
        if (
            self.en_passant_target
            and move.to_square == self.en_passant_target
            and from_piece is not None
            and from_piece.type == PieceType.PAWN
        ):
            captured = self.piece_at(self.en_passant_target - (8 * dir))
            self.squares[self.en_passant_target - (8 * dir)] = None

        # set en_passant_target
        dir = +1 if self.side_to_move == Color.WHITE else -1
        if (
            abs(move.from_square - move.to_square) == 16
            and from_piece is not None
            and from_piece.type == PieceType.PAWN
        ):
            self.en_passant_target = move.to_square - (8 * dir)
        else:
            self.en_passant_target = None

        # halfmove update
        if captured is not None or (from_piece is not None and from_piece.type == PieceType.PAWN):
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        # fullmove update
        if self.side_to_move == Color.BLACK:
            self.fullmove_number += 1

        # side_to_move update
        self.side_to_move = self.side_to_move.opposite

        return Undo(move, captured, prev_castling_rights, prev_en_passant_target, prev_halfmove_clock)

    def unmake_move(self, undo: Undo) -> None:
        """Reverse the move described by `undo`, restoring all prior state."""
        move = undo.move

        # undo promotions
        if move.promotion is not None:
            self.squares[move.from_square] = Piece(PieceType.PAWN, self.side_to_move.opposite)
        else:
            self.squares[move.from_square] = self.squares[move.to_square]

        # undo castling - put the rook back
        to_piece = self.piece_at(move.to_square)
        if abs(move.from_square - move.to_square) == 2 and to_piece and to_piece.type == PieceType.KING:
            if move.to_square % 8 == 6:  # kingside castling
                self.squares[move.to_square + 1] = Piece(PieceType.ROOK, self.side_to_move.opposite)
                self.squares[move.to_square - 1] = None
            elif move.to_square % 8 == 2:  # queenside castling.
                self.squares[move.to_square - 2] = Piece(PieceType.ROOK, self.side_to_move.opposite)
                self.squares[move.to_square + 1] = None

        dir = 1 if self.side_to_move == Color.WHITE else -1

        # case when an en passant occurred.
        if (
            undo.prev_en_passant_target is not None
            and move.to_square == undo.prev_en_passant_target
            and undo.captured is not None
            and undo.captured.type == PieceType.PAWN
        ):
            self.squares[undo.prev_en_passant_target - (dir * 8)] = undo.captured
        else:
            self.squares[move.to_square] = undo.captured  # None is possible

        # reset other params
        self.castling_rights = undo.prev_castling_rights
        self.en_passant_target = undo.prev_en_passant_target
        self.halfmove_clock = undo.prev_halfmove_clock
        if self.side_to_move == Color.WHITE:
            self.fullmove_number -= 1

        self.side_to_move = self.side_to_move.opposite
