from __future__ import annotations
from typing import Tuple, List


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
        self.white_can_castle = True
        self.black_can_castle = True

    def make_move(self, move: Move) -> None:
        """execute a move and make necessary changes to game state"""

        self.board[move.x_0][move.y_0] = "--"
        self.board[move.x_1][move.y_1] = move.piece_moved
        self.white_to_move = not self.white_to_move
        self.move_log.append(move)

    def undo_move(self) -> None:
        if len(self.move_log) != 0:
            last_move = self.move_log.pop()  # removes last move from log as well.
            self.board[last_move.x_0][last_move.y_0] = last_move.piece_moved
            self.board[last_move.x_1][
                last_move.y_1
            ] = last_move.piece_captured  # handles '--' incidentally
            self.white_to_move = not self.white_to_move

        # need to handle castling rights, etc.

    def gen_valid_moves(self):
        valid_moves: List[Move] = []
        helper_lookup = {
            "R": self.gen_rook_moves,
            "N": self.gen_knight_moves,
            "B": self.gen_bishop_moves,
            "Q": self.gen_queen_moves,
            "K": self.gen_king_moves,
            "p": self.gen_pawn_moves,
        }
        whose_turn = "w" if self.white_to_move else "b"

        for r in range(len(self.board)):
            for c in range(len(self.board[0])):
                pc = self.board[r][c]
                if pc[0] == whose_turn:
                    candidate_moves = helper_lookup[pc[-1]](r, c)
                    valid_moves.extend(x for x in candidate_moves if x.is_valid())

        return valid_moves

    def gen_rook_moves(self, r, c):
        pass

    def gen_knight_moves(self, r, c):
        pass

    def gen_bishop_moves(self, r, c):
        pass

    def gen_queen_moves(self, r, c):
        pass

    def gen_king_moves(self, r, c):
        pass

    def gen_pawn_moves(self, r, c):
        if self.white_to_move and r == 6:
            pass


class Move:
    def __init__(
        self, start_sq: Tuple[int, int], end_sq: Tuple[int, int], board: List[List[str]]
    ) -> None:
        self.x_0 = start_sq[0]
        self.y_0 = start_sq[1]
        self.x_1 = end_sq[0]
        self.y_1 = end_sq[1]

        self.piece_moved = board[self.x_0][self.y_0]
        self.piece_captured = board[self.x_1][self.y_1]

        self.notation = self.gen_notation()
        self.intermediate_squares = self.get_intermediate_squares()

    def __repr__(self):
        return self.notation

    def gen_notation(self) -> str:
        """generate algebraic chess notation for the move, eg Nc3, Kxe2, d4, O-O"""

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
        """ For pieces other than knights, return the intermediate squares between the
            start and end locations - start location excluded, end location included.
            To help with determining collisions, captures, and eventual castling
            through check rules.
        """

        int_squares: List[Tuple[str, str]] = []

        if self.piece_moved[-1] in ["R", "B", "Q", "K", "p"]:
            x_dist, y_dist = self.x_1 - self.x_0, self.y_1 - self.y_0
            x_step = 0 if x_dist == 0 else x_dist // abs(x_dist)
            y_step = 0 if y_dist == 0 else y_dist // abs(y_dist)

            int_squares = [
                (self.x_0 + i * x_step, self.y_0 + i * y_step)
                for i in range(1, max(abs(x_dist), abs(y_dist)) + 1)
            ]

        return int_squares

    def is_valid(self):
        """verifies that the move does not put the king in check"""
        return True
