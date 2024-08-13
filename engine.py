from __future__ import annotations
from typing import Tuple, List
import utilities as utils


class GameState:
    def __init__(self) -> None:
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"],
        ]

        self.move_log: List[Move] = []
        self.white_to_move = True
        self.castling_rights = {"w": True, "b": True}

        self.king_positions = {"w": (7, 4), "b": (0, 4)}

    def __repr__(self) -> str:
        """Override repr for debuggin"""

        return "\n\t".join([str(a) for a in vars(self).items()])

    def current_player_color(self) -> str:
        """helper to return 'w' or 'b' based on current player color"""
        return "w" if self.white_to_move else "b"

    def other_player_color(self) -> str:
        """helper to return 'b' or 'w' based on other player color"""
        return "b" if self.white_to_move else "w"

    def make_move(self, move: Move) -> None:
        """execute a move and make necessary changes to game state"""

        self.board[move.x_0][move.y_0] = "--"
        self.board[move.x_1][move.y_1] = move.piece_moved
        self.white_to_move = not self.white_to_move
        self.move_log.append(move)

        if move.piece_moved[-1] == "K":
            self.king_positions[move.piece_moved[0]] = (move.x_1, move.y_1)

    def undo_move(self) -> None:
        """Undoes last move and makes necessary reversions to game state"""
        if len(self.move_log) != 0:
            last_move = self.move_log.pop()  # removes last move from log as well.
            self.board[last_move.x_0][last_move.y_0] = last_move.piece_moved
            self.board[last_move.x_1][
                last_move.y_1
            ] = last_move.piece_captured  # handles '--' incidentally
            self.white_to_move = not self.white_to_move

            if last_move.piece_moved[-1] == "K":
                self.king_positions[last_move.piece_moved[0]] = (
                    last_move.x_0,
                    last_move.y_0,
                )

        # need to handle castling rights, etc.

    def gen_possible_moves(self):
        """
        Generate a list of all possible moves for the current player
        Currently omits: en passant, castling, promotion

        Handling for moving while in check / not moving into check happens in
        gen_valid_moves()
        """

        possible_moves: List[Move] = []
        helper_lookup = {
            "R": self.gen_rook_moves,
            "N": self.gen_knight_moves,
            "B": self.gen_bishop_moves,
            "Q": self.gen_queen_moves,
            "K": self.gen_king_moves,
            "p": self.gen_pawn_moves,
        }

        for r in range(len(self.board)):
            for c in range(len(self.board[0])):
                pc = self.board[r][c]
                if pc[0] == self.current_player_color():
                    candidate_moves = helper_lookup[pc[-1]](r, c)
                    possible_moves.extend(x for x in candidate_moves if x.is_valid())

        return possible_moves

    def gen_valid_moves(self) -> List[Move]:
        """Filters possible moves to remove any move that would place you in check"""

        possible_moves = self.gen_possible_moves()

        valid_moves: List[Move] = []

        for m in possible_moves:
            self.make_move(m)
            if not self.is_checking():
                valid_moves.append(m)
            self.undo_move()

        return valid_moves

    def gen_rook_moves(self, r, c):
        """Generate possible rook moves, ignoring colisions and check rules"""

        same_row = [(r, i) for i in range(8) if i != c]
        same_col = [(i, c) for i in range(8) if i != r]

        return [Move((r, c), tgt, self.board) for tgt in same_row + same_col]

    def gen_knight_moves(self, r, c):
        """Generate possible knight moves, ignoring colisions and check rules"""

        dirs = [(1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1)]
        cand_tgts = [utils._add((r, c), delta) for delta in dirs]

        return [
            Move((r, c), tgt, self.board) for tgt in cand_tgts if utils.is_valid_sq(tgt)
        ]

    def gen_bishop_moves(self, r, c):
        """Generate possible bishop moves, ignoring colisions and check rules"""
        dirs = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        cand_tgts = [
            utils._add((r, c), utils._mult(delta, i))
            for delta in dirs
            for i in range(1, 8)
        ]

        return [
            Move((r, c), tgt, self.board) for tgt in cand_tgts if utils.is_valid_sq(tgt)
        ]

    def gen_queen_moves(self, r, c):
        """Generate possible queen moves, ignoring colisions and check rules"""

        return self.gen_bishop_moves(r, c) + self.gen_rook_moves(r, c)

    def gen_king_moves(self, r, c):
        """Generate possible king moves, ignoring colisions and check rules and out of
        bounds errors"""
        dirs = [(1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1)]
        cand_tgts = [utils._add((r, c), delta) for delta in dirs]

        king_moves = [
            Move((r, c), tgt, self.board) for tgt in cand_tgts if utils.is_valid_sq(tgt)
        ]

        return king_moves

    def gen_pawn_moves(self, r, c):
        """Generate possible pawn moves, ignoring colisions and check rules
        Currently does not consider pawn captures or en passant"""

        pawn_color = self.board[r][c][0]
        home_row: bool = (r == 6 and pawn_color == "w") or (
            r == 1 and pawn_color == "b"
        )
        direction = 1 if pawn_color == "b" else -1
        steps = [1, 2] if home_row else [1]

        forwards = [
            Move((r, c), (r + direction * i, c), self.board)
            for i in steps
            if utils.is_valid_sq((r + direction * i, c))
        ]

        captures = [
            Move((r, c), (r + direction, c + k), self.board)
            for k in [1, -1]
            if utils.is_valid_sq((r + direction, c + k))
            and self.board[r + direction][c + k][0]
            == ("b" if pawn_color == "w" else "w")
        ]

        return forwards + captures

    def is_checking(self):
        """checks to see if current player can capture the oponents king immediately"""

        king_pos = self.king_positions[self.other_player_color()]
        possible_moves = self.gen_possible_moves()

        return any((m.x_1, m.y_1) == king_pos for m in possible_moves)


class Move:
    def __init__(
        self, start_sq: Tuple[int, int], end_sq: Tuple[int, int], board: List[List[str]]
    ) -> None:
        self.x_0 = start_sq[0]
        self.y_0 = start_sq[1]
        self.x_1 = end_sq[0]
        self.y_1 = end_sq[1]
        self.board = board

        self.piece_moved = board[self.x_0][self.y_0]
        self.piece_captured = board[self.x_1][self.y_1]
        self.player_color = self.piece_moved[0]
        self.other_player_color = "b" if self.player_color == "w" else "w"

        self.notation = self.gen_notation()

    def __eq__(self, other: Move) -> bool:
        """equality override for use in move validation"""

        return all(
            [
                self.x_0 == other.x_0,
                self.x_1 == other.x_1,
                self.y_0 == other.y_0,
                self.y_1 == other.y_1,
            ]
        )

    def __repr__(self):
        return self.notation

    def gen_notation(self) -> str:
        """generate algebraic chess notation for the move, eg Nc3, Kxe2, d4, O-O
        still needs: Castling, pawn promotion"""

        rows_to_ranks = {k: str(8 - k) for k in range(8)}
        cols_to_files = {k: chr(k + 97) for k in range(8)}

        capture = ""
        if self.piece_captured != "--":
            capture = "x"
            if self.piece_moved[-1] == "p":
                pc = cols_to_files[self.y_0]  # eg cxd4
            else:
                pc = self.piece_moved[-1]  # eg Nxe2
        else:
            pc = self.piece_moved[-1] if self.piece_moved[-1] != "p" else ""

        return pc + capture + cols_to_files[self.y_1] + rows_to_ranks[self.x_1]

    def get_intermediate_squares(self):
        """
        Return the intermediate squares between the start and end locations -
        start location excluded, end location included.

        To help with determining collisions, captures, and eventual castling
        through check rules.
        """

        if self.piece_moved[-1] in ["R", "B", "Q", "K", "p"]:
            x_dist, y_dist = self.x_1 - self.x_0, self.y_1 - self.y_0
            x_step = 0 if x_dist == 0 else x_dist // abs(x_dist)
            y_step = 0 if y_dist == 0 else y_dist // abs(y_dist)

            int_squares = [
                (self.x_0 + i * x_step, self.y_0 + i * y_step)
                for i in range(1, max(abs(x_dist), abs(y_dist)) + 1)
            ]
        elif self.piece_moved[-1] == "N":
            int_squares = [(self.x_1, self.y_1)]
        else:
            raise ValueError("this piece is an alien and i dont know how it moves")

        return int_squares

    def is_valid(self):
        # compute once for use in all colision rules
        intermediate_squares = self.get_intermediate_squares()

        # colisions with pieces of same color
        if any(
            self.board[sq[0]][sq[1]][0] == self.player_color
            for sq in intermediate_squares
        ):
            return False

        # colisions with pieces of opposite color before tgt square
        if any(
            self.board[sq[0]][sq[1]][0] == self.other_player_color
            for sq in intermediate_squares[:-1]
        ):
            return False

        # pawn colisions with pieces of other color.
        if any(
            self.piece_moved[-1] == "p"
            and self.board[sq[0]][sq[1]][0] == self.other_player_color
            and self.y_0 == sq[1]  # pawn captures are allowed colisionss
            for sq in intermediate_squares
        ):
            return False

        # todo does this move place me in check
        return True
