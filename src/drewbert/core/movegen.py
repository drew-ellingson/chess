from drewbert.core.move import Move
from drewbert.core.position import Position
from drewbert.core.types import Color, Square, Piece, PieceType
from dataclasses import dataclass
from typing import NamedTuple, List, Dict
from itertools import product, chain

KNIGHT_VECTORS = [(2,1), (2,-1), (1,2), (1,-2), (-1, 2), (-1, -2), (-2, 1), (-2, -1)]

class Coord(NamedTuple):
    file: int                                                                                                                                          
    rank: int   

def get_other_color(color: Color):
    """Color flipper"""
    return Color.WHITE if color == color.BLACK else Color.BLACK 

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

def slide_along_vector(position: Position, coord:Coord, delta: Coord) -> List[Coord]:
    """Given a start coordinate and a delta, slide along that delta until you encounter the edge of the board or a piece.
        If a piece is encountered: 
            Include the encountered square if its a piece of the opposite color
            Exclude the square if its a piece of the same color.
    """
    piece = position.squares[rank_file_to_sq(coord)]
    if not piece:
        raise ValueError(f'Coord: {coord} must represent a piece, not an empty squrae')
    
    in_bounds = True
    target_squares = [coord]

    while in_bounds:
        target = _add(target_squares[-1], delta)
        target_sq = position.squares[rank_file_to_sq(target)]
        not_same_color_piece = target_sq is None or target_sq.color == get_other_color(piece.color)
        if coord_in_bounds(target) and not_same_color_piece:
            target_squares.append(target)
    
    # remove piece coord itself
    target_squares.pop(0)
    
    return target_squares

def generate_pseudo_legal_knight_moves(position: Position, start_coord: Coord) -> List[Move]:
    targets = [_add(start_coord, Coord(*delta)) for delta in KNIGHT_VECTORS]
    return [Move(rank_file_to_sq(start_coord), rank_file_to_sq(target)) for target in targets]

def generate_pseudo_legal_bishop_moves(position: Position, start_coord: Coord) -> List[Move]:
    deltas = [Coord(1,1), Coord(1,-1), Coord(-1,1), Coord(-1,1)]
    targets = list(chain.from_iterable([slide_along_vector(position, start_coord, delta) for delta in deltas]))
    return [Move(rank_file_to_sq(start_coord), rank_file_to_sq(target)) for target in targets]

def generate_pseudo_legal_rook_moves(position: Position, start_coord: Coord) -> List[Move]:
    deltas = [Coord(1,0), Coord(-1,0), Coord(0,1), Coord(0, -1)]
    targets = list(chain.from_iterable([slide_along_vector(position, start_coord, delta) for delta in deltas]))
    return [Move(rank_file_to_sq(start_coord), rank_file_to_sq(target)) for target in targets]

def generate_pseudo_legal_queen_moves(position: Position, start_coord: Coord) -> List[Move]:
    return generate_pseudo_legal_bishop_moves(position, start_coord) + generate_pseudo_legal_rook_moves(position, start_coord)

def generate_pseudo_legal_king_moves(position: Position, start_coord: Coord) -> List[Move]:
    coord_opts = [-1, 0, 1]
    deltas = [Coord(*x) for x in product(coord_opts, repeat=2) if x != (0,0)]
    targets =  [_add(start_coord, Coord(*delta)) for delta in deltas]
    return [Move(rank_file_to_sq(start_coord), rank_file_to_sq(target)) for target in targets]

def generate_pseudo_legal_pawn_moves(position: Position, start_coord: Coord) -> List[Move]:
    pass 


def generate_piece_pseudo_legal_moves(position: Position, piece: Piece, start_coord: Coord):
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
    cand_pieces = (position.squares[move.from_square] for move in cands)                                                                                              
    return any(piece is not None and piece.color == by for piece in cand_pieces)

def is_in_check(position: Position, color: Color) -> bool:
    """True iff the king of `color` is currently attacked."""
    king_pos = min(i for i,x in enumerate(position.squares) if x and x.type == PieceType.KING and x.color == color)
    return is_square_attacked(position, king_pos, get_other_color(color))



def generate_legal_moves(position: Position) -> list[Move]:
    """All legal moves for the side to move.

    A move is legal iff it is pseudo-legal AND does not leave the moving
    side's king in check.
    """
    raise NotImplementedError("phase 1")
