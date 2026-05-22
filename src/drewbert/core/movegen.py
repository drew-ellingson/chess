from drewbert.core.move import Move
from drewbert.core.position import Position
from drewbert.core.types import Color, Square, Piece, PieceType
from dataclasses import dataclass
from typing import NamedTuple, List, Dict
from itertools import chain

KNIGHT_VECTORS = [(2,1), (2,-1), (1,2), (1,-2), (-1, 2), (-1, -2), (-2, 1), (-2, -1)]
BISHOP_UNIT_VECTORS = [(1,1), (1,-1), (-1,1), (-1, -1)]
ROOK_UNIT_VECTORS = [(1,0), (0,1), (-1,0), (0,-1)]
KING_VECTORS = [(1,0), (1,-1), (0,-1), (-1,-1), (-1,0), (-1,1), (0,1), (1,1)]

class Coord(NamedTuple):
    file: int                                                                                                                                          
    rank: int   


def get_pieces(position: Position) -> Dict[int, Piece]:
    """Return an square:piece dictionary describing pieces of the side currently to move """
    return {i:x for i,x in enumerate(position.squares) if x and x.color == position.side_to_move}
 
def _add(coord: Coord, delta: Coord) -> Coord:
    """From a coord, return coord + delta as a new Coord """
    return Coord(*map(sum, zip(coord, delta)))
                 
def coord_in_bounds(coord: Coord) -> bool:
    """Return whether a given coordinate can represent a valid chess square"""
    return all(0 <= x <= 7 for x in coord)

def sq_to_rank_file(square: Square) -> Coord:
    """produce (rank, file) pair from given square. 0-indexed """
    if not 0 <= square <= 63:
        raise ValueError(f'Square: {square} is not in valid range 0-63')
    return Coord(square // 8, square % 8)

def rank_file_to_sq(coord:Coord) -> Square:
    """produce standard 0-63 square representation from a (rank, file) pair """
    if not coord_in_bounds(coord):
        raise ValueError(f'Coord: {coord} is out of bounds. All coordinate values must be 0-7')
    return 8 * coord.rank + coord.file

def target_piece_is_same_color(position: Position, coord: Coord) -> bool:
    piece = position.piece_at(rank_file_to_sq(coord))
    return piece is not None and piece.color == position.side_to_move 

def slide_along_vector(position: Position, coord:Coord, delta: Coord) -> List[Coord]:
    """Given a start coordinate and a delta, slide along that delta until you encounter the edge of the board or a piece.
        If a piece is encountered: 
            Include the encountered square if its a piece of the opposite color
            Exclude the square if its a piece of the same color.
    """
    piece = position.piece_at(rank_file_to_sq(coord))
    if not piece:
        raise ValueError(f'Coord: {coord} must represent a piece, not an empty squrae')
    
    in_bounds = True
    target_squares = [coord]

    while in_bounds:
        target = _add(target_squares[-1], delta)
        if coord_in_bounds(target) and target_piece_is_same_color(position, target):
            target_squares.append(target)
    
    # remove piece coord itself
    target_squares.pop(0)
    
    return target_squares

def generate_pseudo_legal_knight_moves(position: Position, start_coord: Coord) -> List[Move]:
    """
        From a start coord, generate a list of move candidates for all valid knight moves from the coord
        Respects out of bounds and own-piece collision
    """
    targets = []
    for delta in KNIGHT_VECTORS:
        target = _add(start_coord, Coord(*delta))
        # prevent same piece collisions
        if not target_piece_is_same_color(position, target):
            targets.append(target)

    return [Move(rank_file_to_sq(start_coord), rank_file_to_sq(target)) for target in targets]

def generate_pseudo_legal_bishop_moves(position: Position, start_coord: Coord) -> List[Move]:
    """
        From a start coord, generate a list of move candidates for all valid bishop moves from the coord
        Repsects out of bounds and own-piece collision 
    """
    deltas = [Coord(*x) for x in BISHOP_UNIT_VECTORS]
    targets = list(chain.from_iterable([slide_along_vector(position, start_coord, delta) for delta in deltas]))
    return [Move(rank_file_to_sq(start_coord), rank_file_to_sq(target)) for target in targets]

def generate_pseudo_legal_rook_moves(position: Position, start_coord: Coord) -> List[Move]:
    """
        From a start coord, generate a list of move candidates for all valid rook moves from the coord
        Repsects out of bounds and own-piece collision 
    """
    deltas = [Coord(*x) for x in ROOK_UNIT_VECTORS]
    targets = list(chain.from_iterable([slide_along_vector(position, start_coord, delta) for delta in deltas]))
    return [Move(rank_file_to_sq(start_coord), rank_file_to_sq(target)) for target in targets]

def generate_pseudo_legal_queen_moves(position: Position, start_coord: Coord) -> List[Move]:
    """
        From a start coord, generate a list of move candidates for all valid queen moves from the coord
        Repsects out of bounds and own-piece collision 
    """
    return generate_pseudo_legal_bishop_moves(position, start_coord) + generate_pseudo_legal_rook_moves(position, start_coord)

def generate_pseudo_legal_king_moves(position: Position, start_coord: Coord) -> List[Move]:
    """
        From a start coord, generate a list of move candidates for all king bishop moves from the coord
        Repsects out of bounds and own-piece collision.
    """
    deltas = [Coord(*x) for x in KING_VECTORS]
    targets =  [_add(start_coord, Coord(*delta)) for delta in deltas]

    # Castling: squares slices represent the squares that need to be empty for castling to be legal
    if position.side_to_move == Color.WHITE:
        if position.castling_rights.white_kingside and all(x is None for x in position.squares[5:7]):
            targets.append(Coord(0, 6)) # G1 
        elif position.castling_rights.white_queenside and all(x is None for x in position.squares[1:4]):
            targets.append(Coord(0, 2)) # C1
    elif position.side_to_move == Color.BLACK:
        if position.castling_rights.black_kingside and all(x is None for x in position.squares[61:63]):
            targets.append(Coord(7,6)) # G8
        elif position.castling_rights.black_queenside and all(x is None for x in position.squares[57:60]):
            targets.append(Coord(7,2)) # C8

    return [Move(rank_file_to_sq(start_coord), rank_file_to_sq(target)) for target in targets]

def generate_pseudo_legal_pawn_moves(position: Position, start_coord: Coord) -> List[Move]:
    """
        From a start coord, generate a list of move candidates for all valid pawn moves from the coord
        Repsects out of bounds and own-piece collision
        Handles pawn captures, en_passant, and promotion
    """
    dir = 1 if position.side_to_move == Color.WHITE else -1 
    start_rank = 1 if position.side_to_move == Color.WHITE else 6
    promote_rank = 7 if position.side_to_move == Color.WHITE else 0

    targets = []
    one_sq_forward = _add(start_coord, Coord(0,dir))
    if position.piece_at(rank_file_to_sq(one_sq_forward)) is None:
        targets.append(one_sq_forward)

    if start_coord.rank == start_rank:
        two_sq_forward = _add(start_coord, Coord(0,dir * 2))
        if position.piece_at(rank_file_to_sq(two_sq_forward)) is None and position.piece_at(rank_file_to_sq(one_sq_forward)) is None:
            targets.append(two_sq_forward)

    capture_targets = [                                                                                                                                          
        target                                                                                                                                                 
        for x in [Coord(1, dir), Coord(-1, dir)]                                                                                                                     
        if coord_in_bounds(target := _add(x, start_coord))                                                                                                       
        and (target_piece := position.piece_at(rank_file_to_sq(target))) is not None
        and target_piece.color == position.side_to_move.opposite 
    ]            
    targets.extend(capture_targets)
    # pawn is adjacent to en_passant_target
    if position.en_passant_target and abs(rank_file_to_sq(start_coord) - position.en_passant_target) == 1:
        capture_target = _add(sq_to_rank_file(position.en_passant_target), Coord(0, dir))
        targets.append(capture_target)

    moves: List[Move] = []
    for target in targets:
        from_sq, to_sq = rank_file_to_sq(start_coord), rank_file_to_sq(target)
        if target.rank != promote_rank:
            moves.append(Move(from_sq, to_sq))
        else:
            piece_options = [PieceType.ROOK, PieceType.KNIGHT, PieceType.BISHOP, PieceType.QUEEN]
            moves.extend([Move(from_sq, to_sq, piece) for piece in piece_options])

    return moves 

def generate_piece_pseudo_legal_moves(position: Position, piece: Piece, start_coord: Coord):
    """
        Given a piece and a start coord, fine all pseudo-legal moves
        Respects out of bounds and piece collision 
    """
    movers = {
        PieceType.KNIGHT: generate_pseudo_legal_knight_moves,
        PieceType.BISHOP: generate_pseudo_legal_bishop_moves,
        PieceType.ROOK: generate_pseudo_legal_rook_moves,
        PieceType.QUEEN: generate_pseudo_legal_queen_moves,
        PieceType.KING: generate_pseudo_legal_king_moves,
        PieceType.PAWN: generate_pseudo_legal_pawn_moves,
    }
    return movers[piece.type](position, start_coord)


def generate_pseudo_legal_moves(position: Position) -> list[Move]:
    """All moves that respect piece movement rules, ignoring king safety.

    Pseudo-legal moves may leave the moving side's king in check; legality
    is filtered by `generate_legal_moves`.
    """
    pieces = get_pieces(position)
    return list(chain.from_iterable([generate_piece_pseudo_legal_moves(position, piece, sq_to_rank_file(i)) for i, piece in pieces.items()]))

def is_square_attacked(position: Position, target_square: Square, by: Color) -> bool:
    """True iff `square` is attacked by any piece of color `by`."""
    psuedo_legal_moves = generate_pseudo_legal_moves(position)
    cands = [move for move in psuedo_legal_moves if move.to_square == target_square]
    cand_pieces = (position.piece_at(move.from_square) for move in cands)                                                                                              
    return any(piece is not None and piece.color == by for piece in cand_pieces)

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
        undo = position.make_move(move)
        if not is_in_check(position, position.side_to_move.opposite):
            moves.append(move)
        position.unmake_move(undo)

    return moves