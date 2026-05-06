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
    """From an algebraic notation square, return the [0..63] rank-major index"""
    if sq[0] not in "abcdefgh" or int(sq[1]) < 1 or int(sq[1]) > 8:
        raise ValueError(f"Invalid square: {sq}")

    return 8 * (int(sq[1]) - 1) + (ord(sq[0]) - ord("a"))


def int_to_alg_sq(idx: int) -> str:
    """From a [0..63] rank major index, return the algebra notation square"""
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
        remaining = list(row)
        output = []
        for c in remaining:
            if c.isdigit():
                output.extend(int(c) * [None])
            else:
                try:
                    output.append(FEN_TO_POS[c])
                except KeyError:
                    raise ValueError("invalid piece identifier in FEN input") from None

        if not len(output) == 8:
            raise ValueError(f"malformed FEN row: {remaining}")

        return output

    rows = [parse_row(r) for r in reversed(comps[0].split("/"))]

    if not len(rows) == 8:
        raise ValueError(f"malformed FEN board - invalid number of rows {comps[0]}")

    squares = list(itertools.chain.from_iterable(rows))

    try:
        side_to_move = COLORS[comps[1]]
    except KeyError:
        raise ValueError(f"invalid color in FEN: {comps[1]!r}") from None

    if not set(comps[2]) <= {"K", "Q", "k", "q", "-"}:
        raise ValueError(f"Invalid FEN Castling Rights: {comps[2]}")

    castling_rights = CastlingRights(
        "K" in comps[2], "Q" in comps[2], "k" in comps[2], "q" in comps[2]
    )

    en_passant_target = None if comps[3] == "-" else alg_sq_to_int(comps[3])

    halfmove_clock = int(comps[4])
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

    def parse_row(row: list[Piece | None]) -> str:
        output = ""
        while row:
            if row[0] is None:
                if output == "" or not output[-1].isdigit():
                    output = output + "1"
                else:
                    output = output[:-1] + str(int(output[-1]) + 1)
            else:
                output = output + POS_TO_FEN[row[0]]
            row.pop(0)
        return output

    comps = []
    rows = [[position.squares[8 * i + j] for j in range(8)] for i in range(7, -1, -1)]

    # write the board
    comps.append("/".join(parse_row(r) for r in rows))

    # write active_color
    comps.append("w" if position.side_to_move == Color.WHITE else "b")

    # write castling_rights
    wk = "K" if position.castling_rights.white_kingside else ""
    wq = "Q" if position.castling_rights.white_queenside else ""
    bk = "k" if position.castling_rights.black_kingside else ""
    bq = "q" if position.castling_rights.black_queenside else ""

    castling_rights = wk + wq + bk + bq

    comps.append(castling_rights if castling_rights else "-")

    # write en_passant_target_sq
    comps.append(
        "-" if not position.en_passant_target else int_to_alg_sq(position.en_passant_target)
    )

    # write halfmove_clock

    comps.append(str(position.halfmove_clock))

    # write fullmove_number
    comps.append(str(position.fullmove_number))

    return " ".join(comps)
