"""FEN parsing and serialization.

Forsyth-Edwards Notation: the standard text format for a chess position.
Example: "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

Ref: https://en.wikipedia.org/wiki/Forsyth%E2%80%93Edwards_Notation

Six space-separated fields:
  1. Piece placement (ranks 8 down to 1, '/' between ranks; digits = empty squares)
  2. Active color: 'w' or 'b'
  3. Castling availability: subset of "KQkq" or "-"
  4. En passant target square: algebraic (e.g. "e3") or "-"
  5. Halfmove clock (since last pawn move or capture)
  6. Fullmove number (starts at 1, increments after Black's move)
"""
import itertools 
from drewbert.core.position import Position
from drewbert.core.types import Piece, PieceType, Color

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

FEN_TO_POS = { 
  'r': Piece(PieceType.ROOK, Color.BLACK),
  'n': Piece(PieceType.KNIGHT, Color.BLACK),
  'b': Piece(PieceType.BISHOP, Color.BLACK),
  'q': Piece(PieceType.QUEEN, Color.BLACK),
  'k': Piece(PieceType.KING, Color.BLACK),
  'p': Piece(PieceType.PAWN, Color.BLACK),
  'R': Piece(PieceType.ROOK, Color.WHITE),
  'N': Piece(PieceType.KNIGHT, Color.WHITE),
  'B': Piece(PieceType.BISHOP, Color.WHITE),
  'Q': Piece(PieceType.QUEEN, Color.WHITE),
  'K': Piece(PieceType.KING, Color.WHITE),
  'P': Piece(PieceType.PAWN, Color.WHITE),
}

def parse_fen(fen: str) -> Position:
    """Parse a FEN string into a Position. Raises ValueError on malformed input."""
    comps = fen.split(' ')
    if len(comps) != 8:
        raise ValueError('malformed FEN input')

    def parse_row(row: str) -> list[Piece | None]:
        input = list(row)
        output = []
        while input:
          if input[0].isdigit():
            output.append(int(input[0]) * [None])
          else: 
            output.append([FEN_TO_POS[input[0]]])
          input.pop(0)

    rows = [parse_row(r) for r in reversed(comps[0].split('/'))]
    pieces = list(itertools.chain.from_iterable(rows))
    
    raise NotImplementedError


def to_fen(position: Position) -> str:
    """Serialize a Position to FEN."""
    raise NotImplementedError("phase 1")
