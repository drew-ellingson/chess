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
from drewbert.core.types import CastlingRights, Color, Piece, PieceType

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

FEN_TO_POS = {
    "r": Piece(PieceType.ROOK, Color.BLACK),
    "n": Piece(PieceType.KNIGHT, Color.BLACK),
    "b": Piece(PieceType.BISHOP, Color.BLACK),
    "q": Piece(PieceType.QUEEN, Color.BLACK),
    "k": Piece(PieceType.KING, Color.BLACK),
    "p": Piece(PieceType.PAWN, Color.BLACK),
    "R": Piece(PieceType.ROOK, Color.WHITE),
    "N": Piece(PieceType.KNIGHT, Color.WHITE),
    "B": Piece(PieceType.BISHOP, Color.WHITE),
    "Q": Piece(PieceType.QUEEN, Color.WHITE),
    "K": Piece(PieceType.KING, Color.WHITE),
    "P": Piece(PieceType.PAWN, Color.WHITE),
}

POS_TO_FEN = {v: k for k, v in FEN_TO_POS.items()}

COLORS = {"w": Color.WHITE, "b": Color.BLACK}


def alg_sq_to_int(sq: str) -> int:
    """Return the [0..63] rank-major index for an algebraic square (e.g. "a1", "h8").

    Raises ValueError if `sq` is not a valid two-character algebraic square.
    """
    if len(sq) != 2 or sq[0] not in "abcdefgh" or int(sq[1]) < 1 or int(sq[1]) > 8:
        raise ValueError(f"Invalid square: {sq}")

    return 8 * (int(sq[1]) - 1) + (ord(sq[0]) - ord("a"))


def int_to_alg_sq(idx: int) -> str:
    """Return the algebraic notation square (e.g. "a1", "h8") for a [0..63] rank-major index.

    Raises ValueError if `idx` is outside [0, 63].
    """
    if idx < 0 or idx > 63:
        raise ValueError(f"Invalid square index {idx}")

    return chr(idx % 8 + ord("a")) + str(idx // 8 + 1)


def parse_fen(fen: str) -> Position:
    """Parse a FEN string into a Position. Raises ValueError on malformed input."""
    comps = fen.split(" ")
    if len(comps) != 6:
        raise ValueError("malformed FEN input")

    def parse_row(row: str) -> list[Piece | None]:
        """Helper to parse a single row of FEN input to a list of Pieces"""
        output = []
        for c in row:
            if c.isdigit():
                output.extend(int(c) * [None])
            else:
                try:
                    output.append(FEN_TO_POS[c])
                except KeyError:
                    raise ValueError("invalid piece identifier in FEN input") from None

        if len(output) != 8:
            raise ValueError(f"malformed FEN row: {row}")

        return output

    rows = [parse_row(r) for r in reversed(comps[0].split("/"))]

    if len(rows) != 8:
        raise ValueError(f"malformed FEN board - invalid number of rows {comps[0]}")

    squares = list(itertools.chain.from_iterable(rows))

    try:
        side_to_move = COLORS[comps[1]]
    except KeyError:
        raise ValueError(f"invalid color in FEN: {comps[1]!r}") from None

    if not set(comps[2]) <= {"K", "Q", "k", "q", "-"}:
        raise ValueError(f"Invalid FEN Castling Rights: {comps[2]}")

    castling_rights = CastlingRights(
        white_kingside="K" in comps[2],
        white_queenside="Q" in comps[2],
        black_kingside="k" in comps[2],
        black_queenside="q" in comps[2],
    )

    en_passant_target = None if comps[3] == "-" else alg_sq_to_int(comps[3])

    if int(comps[4]) < 0:
        raise ValueError(f"Halfmove must be greater than or equal to 0. Got {comps[4]}")
    halfmove_clock = int(comps[4])

    if int(comps[5]) < 1:
        raise ValueError(f"Fullmove number must be greater than or equal to 1. Got {comps[5]}")
    fullmove_number = int(comps[5])

    return Position(
        squares=squares,
        side_to_move=side_to_move,
        castling_rights=castling_rights,
        en_passant_target=en_passant_target,
        halfmove_clock=halfmove_clock,
        fullmove_number=fullmove_number,
    )


def to_fen(position: Position) -> str:
    """Serialize a Position to FEN."""

    def format_row(row: list[Piece | None]) -> str:
        """Serialize one rank as the FEN piece-placement substring (e.g. "rnbq1k1r")."""
        empty_count = 0
        parts: list[str] = []
        for piece in row:
            if piece is None:
                empty_count += 1
                continue
            if empty_count > 0:
                parts.append(str(empty_count))
                empty_count = 0
            parts.append(POS_TO_FEN[piece])
        if empty_count > 0:
            parts.append(str(empty_count))
        return "".join(parts)

    comps = []
    rows = [[position.squares[8 * i + j] for j in range(8)] for i in range(7, -1, -1)]

    comps.append("/".join(format_row(r) for r in rows))

    comps.append("w" if position.side_to_move == Color.WHITE else "b")

    wk = "K" if position.castling_rights.white_kingside else ""
    wq = "Q" if position.castling_rights.white_queenside else ""
    bk = "k" if position.castling_rights.black_kingside else ""
    bq = "q" if position.castling_rights.black_queenside else ""

    castling_rights = wk + wq + bk + bq

    comps.append(castling_rights if castling_rights else "-")

    comps.append("-" if position.en_passant_target is None else int_to_alg_sq(position.en_passant_target))

    comps.append(str(position.halfmove_clock))

    comps.append(str(position.fullmove_number))

    return " ".join(comps)
