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

        self.move_log = []
        self.white_to_move = True
        self.white_can_castle = True
        self.black_can_castle = True

    def make_move(self, move: Move) -> None:
        """execute a move and make necessary changes to game state"""

        self.board[move.x_0][move.y_0] = "--"
        self.board[move.x_1][move.y_1] = move.piece_moved
        self.white_to_move = not self.white_to_move
        self.move_log.append(move)


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
