from itertools import chain
from typing import NamedTuple

from drewbert.core.move import Move
from drewbert.core.position import Position
from drewbert.core.types import Color, Piece, PieceType, Square


class Coord(NamedTuple):
    file: int
    rank: int


KNIGHT_VECTORS = [
    Coord(2, 1),
    Coord(2, -1),
    Coord(1, 2),
    Coord(1, -2),
    Coord(-1, 2),
    Coord(-1, -2),
    Coord(-2, 1),
    Coord(-2, -1),
]
BISHOP_UNIT_VECTORS = [Coord(1, 1), Coord(1, -1), Coord(-1, 1), Coord(-1, -1)]
ROOK_UNIT_VECTORS = [Coord(1, 0), Coord(0, 1), Coord(-1, 0), Coord(0, -1)]
KING_VECTORS = [
    Coord(1, 0),
    Coord(1, -1),
    Coord(0, -1),
    Coord(-1, -1),
    Coord(-1, 0),
    Coord(-1, 1),
    Coord(0, 1),
    Coord(1, 1),
]

# Module-level aliases for PieceType / Color members. Bound once at import;
# using these in hot paths avoids a per-call LOAD_GLOBAL + LOAD_ATTR pair.
PT_PAWN = PieceType.PAWN
PT_KNIGHT = PieceType.KNIGHT
PT_BISHOP = PieceType.BISHOP
PT_ROOK = PieceType.ROOK
PT_QUEEN = PieceType.QUEEN
PT_KING = PieceType.KING
C_WHITE = Color.WHITE


def get_pieces(position: Position) -> dict[Square, Piece]:
    """Return an square:piece dictionary describing pieces of the side currently to move"""
    return {i: x for i, x in enumerate(position.squares) if x and x.color == position.side_to_move}


def _add(coord: Coord, delta: Coord) -> Coord:
    """From a coord, return coord + delta as a new Coord"""
    return Coord(coord.file + delta.file, coord.rank + delta.rank)


def coord_in_bounds(coord: Coord) -> bool:
    """Return whether a given coordinate can represent a valid chess square"""
    return 0 <= coord.file <= 7 and 0 <= coord.rank <= 7


def sq_to_file_rank(square: Square) -> Coord:
    """produce (file, rank) pair from given square. 0-indexed"""
    if not 0 <= square <= 63:
        raise ValueError(f"Square: {square} is not in valid range 0-63")
    return Coord(square % 8, square // 8)


def file_rank_to_sq(coord: Coord) -> Square:
    """produce standard 0-63 square representation from a (file, rank) pair"""
    if not coord_in_bounds(coord):
        raise ValueError(f"Coord: {coord} is out of bounds. All coordinate values must be 0-7")
    return 8 * coord.rank + coord.file


def target_piece_is_color(position: Position, target: Coord, color: Color) -> bool:
    """Return whether the piece at target coord is given color. Return False if the square is empty."""
    target_piece = position.piece_at(file_rank_to_sq(target))
    return target_piece is not None and target_piece.color == color


def first_piece_along_ray(position: Position, coord: Coord, delta: Coord) -> Piece | None:
    """Walk a ray from start coordinate along a given delta. Return first piece encountered on ray
    or None if no piece is encountered.
    """
    current = coord
    while True:
        current = _add(current, delta)
        if not coord_in_bounds(current):
            return None

        target = position.piece_at(file_rank_to_sq(current))
        if target is not None:
            return target


def walk_ray(position: Position, coord: Coord, delta: Coord) -> list[Coord]:
    """Return a list of squares starting from coord and walking by delta
    Stop either when you hit the edge of the board or a piece (inclusive).
    """
    target_squares = []
    current = coord
    while True:
        current = _add(current, delta)
        if coord_in_bounds(current):
            target_squares.append(current)
        else:
            break

        if position.piece_at(file_rank_to_sq(current)):
            break

    return target_squares


def attack_along_ray(position: Position, coord: Coord, delta: Coord, attack_color: Color) -> list[Coord]:
    """Uses above function, but makes decision about whether to keep or omit the piece
    in the case where the last element of the array is a piece.
    """
    targets = walk_ray(position, coord, delta)

    # remove the last item in the list if its a piece of the attacker color
    if targets and target_piece_is_color(position, targets[-1], attack_color):
        targets.pop()

    return targets


def generate_pseudo_legal_knight_moves(position: Position, start_coord: Coord) -> list[Move]:
    """
    From a start coord, generate a list of move candidates for all valid knight moves from the coord
    Respects out of bounds and own-piece collision
    """
    targets = []
    for delta in KNIGHT_VECTORS:
        target = _add(start_coord, delta)
        # prevent same piece collisions
        if coord_in_bounds(target) and not target_piece_is_color(position, target, position.side_to_move):
            targets.append(target)

    return [Move(file_rank_to_sq(start_coord), file_rank_to_sq(target)) for target in targets]


def generate_pseudo_legal_bishop_moves(position: Position, start_coord: Coord) -> list[Move]:
    """
    From a start coord, generate a list of move candidates for all valid bishop moves from the coord
    Respects out of bounds and own-piece collision
    """
    targets = list(
        chain.from_iterable(
            [attack_along_ray(position, start_coord, delta, position.side_to_move) for delta in BISHOP_UNIT_VECTORS]
        )
    )
    return [Move(file_rank_to_sq(start_coord), file_rank_to_sq(target)) for target in targets]


def generate_pseudo_legal_rook_moves(position: Position, start_coord: Coord) -> list[Move]:
    """
    From a start coord, generate a list of move candidates for all valid rook moves from the coord
    Respects out of bounds and own-piece collision
    """
    targets = list(
        chain.from_iterable(
            [attack_along_ray(position, start_coord, delta, position.side_to_move) for delta in ROOK_UNIT_VECTORS]
        )
    )
    moves = [Move(file_rank_to_sq(start_coord), file_rank_to_sq(target)) for target in targets]
    return moves


def generate_pseudo_legal_queen_moves(position: Position, start_coord: Coord) -> list[Move]:
    """
    From a start coord, generate a list of move candidates for all valid queen moves from the coord
    Respects out of bounds and own-piece collision
    """
    return generate_pseudo_legal_bishop_moves(position, start_coord) + generate_pseudo_legal_rook_moves(
        position, start_coord
    )


def generate_pseudo_legal_king_moves(position: Position, start_coord: Coord) -> list[Move]:
    """
    From a start coord, generate a list of move candidates for all king moves from the coord
    Respects out of bounds and own-piece collision.
    """
    targets = []
    for delta in KING_VECTORS:
        target = _add(start_coord, delta)
        if coord_in_bounds(target) and not target_piece_is_color(position, target, position.side_to_move):
            targets.append(target)

    # Castling: squares slices represent the squares that need to be empty for castling to be legal
    if position.side_to_move == C_WHITE:
        if position.castling_rights.white_kingside and position.squares[5] is None and position.squares[6] is None:
            targets.append(Coord(6, 0))  # G1
        if (
            position.castling_rights.white_queenside
            and position.squares[1] is None
            and position.squares[2] is None
            and position.squares[3] is None
        ):
            targets.append(Coord(2, 0))  # C1
    else:
        if position.castling_rights.black_kingside and position.squares[61] is None and position.squares[62] is None:
            targets.append(Coord(6, 7))  # G8
        if (
            position.castling_rights.black_queenside
            and position.squares[57] is None
            and position.squares[58] is None
            and position.squares[59] is None
        ):
            targets.append(Coord(2, 7))  # C8

    return [Move(file_rank_to_sq(start_coord), file_rank_to_sq(target)) for target in targets]


def generate_pseudo_legal_pawn_moves(position: Position, start_coord: Coord) -> list[Move]:
    """
    From a start coord, generate a list of move candidates for all valid pawn moves from the coord
    Respects out of bounds and own-piece collision
    Handles pawn captures, en_passant, and promotion
    """
    dir = 1 if position.side_to_move == C_WHITE else -1
    start_rank = 1 if position.side_to_move == C_WHITE else 6
    promote_rank = 7 if position.side_to_move == C_WHITE else 0

    targets = []
    one_sq_forward = _add(start_coord, Coord(0, dir))
    if position.piece_at(file_rank_to_sq(one_sq_forward)) is None:
        targets.append(one_sq_forward)

    if start_coord.rank == start_rank:
        two_sq_forward = _add(start_coord, Coord(0, dir * 2))
        if (
            position.piece_at(file_rank_to_sq(two_sq_forward)) is None
            and position.piece_at(file_rank_to_sq(one_sq_forward)) is None
        ):
            targets.append(two_sq_forward)

    capture_targets = [
        target
        for x in [Coord(1, dir), Coord(-1, dir)]
        if coord_in_bounds(target := _add(x, start_coord))
        and (target_piece := position.piece_at(file_rank_to_sq(target))) is not None
        and (target_piece.color == position.side_to_move.opposite)
    ]
    targets.extend(capture_targets)

    ep_target = [
        target
        for x in [Coord(1, dir), Coord(-1, dir)]
        if coord_in_bounds(target := _add(x, start_coord)) and file_rank_to_sq(target) == position.en_passant_target
    ]

    targets.extend(ep_target)

    moves: list[Move] = []
    for target in targets:
        from_sq, to_sq = file_rank_to_sq(start_coord), file_rank_to_sq(target)
        if target.rank != promote_rank:
            moves.append(Move(from_sq, to_sq))
        else:
            piece_options = [PT_ROOK, PT_KNIGHT, PT_BISHOP, PT_QUEEN]
            moves.extend([Move(from_sq, to_sq, piece) for piece in piece_options])

    return moves


MOVERS = {
    PT_KNIGHT: generate_pseudo_legal_knight_moves,
    PT_BISHOP: generate_pseudo_legal_bishop_moves,
    PT_ROOK: generate_pseudo_legal_rook_moves,
    PT_QUEEN: generate_pseudo_legal_queen_moves,
    PT_KING: generate_pseudo_legal_king_moves,
    PT_PAWN: generate_pseudo_legal_pawn_moves,
}


def generate_piece_pseudo_legal_moves(position: Position, piece: Piece, start_coord: Coord) -> list[Move]:
    """
    Given a piece and a start coord, find all pseudo-legal moves
    Respects out of bounds and piece collision
    """

    return MOVERS[piece.type](position, start_coord)


def generate_pseudo_legal_moves(position: Position) -> list[Move]:
    """All moves that respect piece movement rules, ignoring king safety.

    Pseudo-legal moves may leave the moving side's king in check; legality
    is filtered by `generate_legal_moves`.
    """

    pieces = get_pieces(position)
    return list(
        chain.from_iterable(
            [generate_piece_pseudo_legal_moves(position, piece, sq_to_file_rank(i)) for i, piece in pieces.items()]
        )
    )


def is_square_attacked(position: Position, target_square: Square, by: Color) -> bool:
    """True iff `square` is attacked by any piece of color `by`."""

    dir = -1 if by == C_WHITE else 1
    coord = sq_to_file_rank(target_square)

    piece_at = position.piece_at

    PAWN_VECTORS = [Coord(1, dir), Coord(-1, dir)]

    for delta in PAWN_VECTORS:
        target_coord = _add(coord, delta)
        if not coord_in_bounds(target_coord):
            continue

        target_piece = piece_at(file_rank_to_sq(target_coord))
        if target_piece and target_piece.type == PT_PAWN and target_piece.color == by:
            return True

    for delta in KNIGHT_VECTORS:
        target_coord = _add(coord, delta)
        if not coord_in_bounds(target_coord):
            continue

        target_piece = piece_at(file_rank_to_sq(target_coord))
        if target_piece and target_piece.type == PT_KNIGHT and target_piece.color == by:
            return True

    for delta in KING_VECTORS:
        target_coord = _add(coord, delta)
        if not coord_in_bounds(target_coord):
            continue

        target_piece = piece_at(file_rank_to_sq(target_coord))
        if target_piece and target_piece.type == PT_KING and target_piece.color == by:
            return True

    # slide along vector until you hit a piece or the end of the board. check if the last
    # thing hit is an enemy bishop or queen
    for delta in BISHOP_UNIT_VECTORS:
        target_piece = first_piece_along_ray(position, coord, delta)

        if not target_piece or target_piece.color != by:
            continue

        if target_piece.type == PT_BISHOP or target_piece.type == PT_QUEEN:
            return True

    # slide along vector until you hit a piece or the end of the board. check if the last
    # thing hit is an enemy rook or queen
    for delta in ROOK_UNIT_VECTORS:
        target_piece = first_piece_along_ray(position, coord, delta)

        if not target_piece or target_piece.color != by:
            continue

        if target_piece.type == PT_ROOK or target_piece.type == PT_QUEEN:
            return True

    return False


def is_in_check(position: Position, color: Color) -> bool:
    """True iff the king of `color` is currently attacked."""
    return is_square_attacked(position, position.king_square(color), color.opposite)


def generate_legal_moves(position: Position) -> list[Move]:
    """All legal moves for the side to move.

    A move is legal iff it is pseudo-legal AND does not leave the moving
    side's king in check.
    """
    candidate_moves = generate_pseudo_legal_moves(position)
    moves = []

    for move in candidate_moves:
        piece = position.piece_at(move.from_square)
        undo = position.make_move(move)

        # check if we castled through check, skip move if so.
        if piece and piece.type == PT_KING and abs(move.from_square - move.to_square) == 2:
            if move.to_square > move.from_square:  # kingside castling
                if any(is_square_attacked(position, move.from_square + i, position.side_to_move) for i in range(3)):
                    position.unmake_move(undo)
                    continue
            else:  # queenside castling
                if any(is_square_attacked(position, move.from_square - i, position.side_to_move) for i in range(3)):
                    position.unmake_move(undo)
                    continue

        if not is_in_check(position, position.side_to_move.opposite):
            moves.append(move)
        position.unmake_move(undo)

    return moves
