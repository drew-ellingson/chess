"""FEN parsing and serialization.

Forsyth-Edwards Notation: the standard text format for a chess position.
Example: "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

Six space-separated fields:
  1. Piece placement (ranks 8 down to 1, '/' between ranks; digits = empty squares)
  2. Active color: 'w' or 'b'
  3. Castling availability: subset of "KQkq" or "-"
  4. En passant target square: algebraic (e.g. "e3") or "-"
  5. Halfmove clock (since last pawn move or capture)
  6. Fullmove number (starts at 1, increments after Black's move)
"""

from drewbert.core.position import Position

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def parse_fen(fen: str) -> Position:
    """Parse a FEN string into a Position. Raises ValueError on malformed input."""
    raise NotImplementedError("phase 1")


def to_fen(position: Position) -> str:
    """Serialize a Position to FEN."""
    raise NotImplementedError("phase 1")
