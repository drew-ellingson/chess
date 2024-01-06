from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple, List, Dict

from utilities.valid_moves import DIFFS
from utilities.basic_fns import _add, _mult, _sub, sign


@dataclass
class GameState:
    board: List[List[str]] = field(
        default_factory=lambda: [
            ["BR", "BN", "BB", "BQ", "BK", "BB", "BN", "BR"],
            ["BP", "BP", "BP", "BP", "BP", "BP", "BP", "BP"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["WP", "WP", "WP", "WP", "WP", "WP", "WP", "WP"],
            ["WR", "WN", "WB", "WQ", "WK", "WB", "WN", "WR"],
        ]
    )

    white_to_play: bool = True
    game_over: bool = False

    ks_castle_rights: Dict[str, bool] = field(
        default_factory=lambda: {"W": True, "B": True}
    )
    qs_castle_rights: Dict[str, bool] = field(
        default_factory=lambda: {"W": True, "B": True}
    )

    is_check: bool = field(default = False)
    is_checkmate: bool = field(default=False)

    moves: List[Move] = field(default_factory=lambda: [])

    def get_piece(self, row, col):
        return self.board[row][col]

    def set_piece(self, row, col, pc):
        self.board[row][col] = pc

    def gen_valid_pc_moves(self, sq):
        pc = self.get_piece(*sq)[-1]
        diff_cands = DIFFS[pc[-1]]
        valid_moves = []
        for diff in diff_cands:
            move = Move(self, sq, _add(sq, diff))
            if move.is_legal():
                valid_moves.append(move)

        return valid_moves

    def gen_valid_moves(self):
        valid_moves = []
        for i, row in enumerate(self.board):
            for j, pc in enumerate(row):
                color = "W" if self.white_to_play else "B"
                if pc.startswith(color):
                    valid_moves.extend(self.gen_valid_pc_moves((i, j)))
        return valid_moves


@dataclass
class Move:
    gs: GameState = field(repr=False)
    sq_0: Tuple[int, int]  # = field(repr=False)
    sq_1: Tuple[int, int]  # = field(repr=False)
    pc: str = field(init=False, repr=False)
    notation: str = field(init=False)

    def __post_init__(self):
        self.pc = self.gs.get_piece(*self.sq_0)
        self.notation = self.get_notation()

    @property
    def diff(self):
        return _sub(self.sq_1, self.sq_0)

    @property
    def color(self):
        return "W" if self.gs.white_to_play else "B"

    def get_notation(self):
        pc = self.pc[-1]
        row = 8 - self.sq_1[0]
        col = chr(ord("A") + self.sq_1[1])
        return pc + col + str(row) if pc != "P" else col + str(row)

    def is_other_persons_turn(self):
        return (self.gs.white_to_play and self.pc.startswith("B")) or (
            not self.gs.white_to_play and self.pc.startswith("W")
        )

    def has_illegal_collisions(self):
        if (
            self.gs.get_piece(*self.sq_1)[0] == self.color
        ):  # can't land on same color piece
            return True

        if self.pc[-1] == "N":  # knights dont collide
            return False

        max_diff = max([abs(x) for x in self.diff])
        diff_dir = tuple(sign(x) for x in self.diff)

        # exclude start and end squares
        intermediate_sqs = [
            _add(self.sq_0, _mult(i, diff_dir)) for i in range(1, max_diff)
        ]

        return any(self.gs.get_piece(*i) != "--" for i in intermediate_sqs)

    def out_of_bounds(self, sq):
        return not all(0 <= x <= 7 for x in sq)

    # pawns are still fucked. need to do 2 steps on move 1
    def is_legal_pawn_move(self):
        """assumes pawn candidates passed in from DIFF"""

        home_row = 6 if self.gs.white_to_play else 1

        if self.pc[-1] != "P":
            raise ValueError("This is not a pawn.")

        if (
            self.gs.white_to_play and self.sq_1[0] >= self.sq_0[0]
        ):  # white pawns move up the board
            return False

        if (
            not self.gs.white_to_play and self.sq_1[0] <= self.sq_0[0]
        ):  # black pawns move down the board
            return False

        if (
            max(abs(x) for x in self.diff) == 2 and self.sq_0[0] != home_row
        ):  # can only move two on the first pawn move
            return False

        if (
            self.gs.get_piece(*self.sq_1) != "--" and self.sq_1[1] == self.sq_0[1]
        ):  # pawns can't advance into pieces
            return False

        if (
            self.sq_0[1] != self.sq_1[1]
            and self.gs.get_piece(*self.sq_1) == "--"
            and not self.is_en_pesant()
        ):  # can only capture diagonally into a piece unless en pesant
            return False

        return True

    def is_en_pesant(self):
        other_player_home_row = 1 if self.gs.white_to_play else 6
        # en pesant rules
        try:
            prior_move = self.gs.moves[-1]
        except:
            return False  # en pesant on turn 1 impossible

        match_prev_col = prior_move.sq_1[1] == self.sq_1[1]
        same_row = prior_move.sq_1[0] == self.sq_0[0]
        was_home_row = prior_move.sq_0[0] == other_player_home_row
        empty_target = self.gs.get_piece(*self.sq_1) == "--"

        return match_prev_col and same_row and was_home_row and empty_target

    def is_legal(self):
        if self.is_other_persons_turn():
            return False
        
        if self.out_of_bounds(self.sq_1):
            return False

        if self.diff not in DIFFS[self.pc[-1]]:
            return False

        if self.has_illegal_collisions():
            return False

        if self.pc[-1] == "P" and not self.is_legal_pawn_move():
            return False

        return True

    def execute(self):
        if self.is_legal():
            self.gs.set_piece(*self.sq_0, "--")
            self.gs.set_piece(*self.sq_1, self.pc)
            self.gs.white_to_play = not self.gs.white_to_play
            self.gs.moves.append(self)


# TODO:

# Check: after a move, check whether (r_1, c_1) -> (opponents_king) is a legal move (for all pieces?)

# While in check: can only make moves resulting in (checking_piece(s)) -> opponents_king is not a legal move

# Castle: always looks exactly the same. just hardcode it.

# Checkmate: in_check + no legal moves
            
# Promotion
