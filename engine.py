from __future__ import annotations
from typing import Tuple, List, Optional
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
        self.castling_rights = {
            "w": {"ks": True, "qs": True},
            "b": {"ks": True, "qs": True},
        }
        self.king_positions = {"w": (7, 4), "b": (0, 4)}

        self.en_passant_sq: Optional[Tuple[int, int]] = None

        self.stalemate = False
        self.checkmate = False

    def __repr__(self) -> str:
        """Override repr for debugging"""

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

        # promotion handling. current case is autoqueen
        if move.is_pawn_promotion:
            self.board[move.x_1][move.y_1] = move.player_color + "Q"

        # en passant handling
        direction = 1 if self.current_player_color() == "b" else -1

        if move.is_en_passant:
            move.piece_captured = self.board[move.x_1 + direction][move.y_1]
            self.board[move.x_1 + direction][move.y_1] = "--"

        if move.piece_moved[-1] == "p" and abs(move.x_1 - move.x_0) == 2:
            self.en_passant_sq = ((move.x_0 + move.x_1) // 2, move.y_0)
        else:
            self.en_passant_sq = None

    def undo_move(self) -> None:
        """Undoes last move and makes necessary reversions to game state"""

        # this logic handles pawn promotion incidentally
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

        direction = 1 if self.current_player_color() == "b" else -1

        # pawn promotion is handled incidentally in the above

        # en passant handling
        if last_move.is_en_passant:
            self.en_passant_sq = (last_move.x_1, last_move.y_1)

            # doesn't feel like i should explicitly need this
            self.board[last_move.x_1][last_move.y_1] = "--"
            # not sure why its -direction here and + in make_move
            self.board[last_move.x_1 - direction][
                last_move.y_1
            ] = last_move.piece_captured

        # need to handle castling rights, etc.

    def gen_possible_moves(self, color: str) -> List[Move]:
        """
        Generate possible moves for the given color. If no color is provided,
        use the current_player_color.

        In_check validation happens subsequently in gen_valid_moves()
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
                if pc[0] == color:
                    candidate_moves = helper_lookup[pc[-1]](r, c)
                    possible_moves.extend(x for x in candidate_moves if x.is_valid())

        return possible_moves

    def gen_valid_moves(self, color: str) -> List[Move]:
        """Filters possible moves to remove any move that would place you in check"""

        # store en passant sq to reset after hypotheticals. this feels dumb but it works
        saved_en_passant_sq = self.en_passant_sq

        possible_moves = self.gen_possible_moves(color=color)

        valid_moves: List[Move] = []
        current_color = color

        if color != current_color:
            self.white_to_move = not self.white_to_move

        for m in possible_moves:

            # corner case to disallow self-en-passant in hypotheticals. shouldn't matter
            if m.is_en_passant and color != self.current_player_color():
                continue

            self.make_move(m)

            # colors have swapped
            if not self.in_check(color):
                valid_moves.append(m)
            self.undo_move()

        valid_moves = possible_moves

        if color != current_color:
            self.white_to_move = not self.white_to_move

        if len(valid_moves) == 0 and self.in_check(color=color):
            self.checkmate = True
        elif len(valid_moves) == 0:
            self.stalemate = True

        self.en_passant_sq = saved_en_passant_sq

        return valid_moves

    def in_check(self, color: str) -> bool:
        """checks to see if `color` king can be captured immediately"""

        king_pos = self.king_positions[color]

        other_color = "b" if color == "w" else "w"

        opp_moves = self.gen_possible_moves(other_color)

        return any((m.x_1, m.y_1) == king_pos for m in opp_moves)

    def gen_rook_moves(self, r: int, c: int) -> List[Move]:
        """Generate possible rook moves, ignoring colisions and check rules"""

        same_row = [(r, i) for i in range(8) if i != c]
        same_col = [(i, c) for i in range(8) if i != r]

        return [Move((r, c), tgt, self.board) for tgt in same_row + same_col]

    def gen_knight_moves(self, r: int, c: int) -> List[Move]:
        """Generate possible knight moves, ignoring colisions and check rules"""

        dirs = [(1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1)]
        cand_tgts = [utils._add((r, c), delta) for delta in dirs]

        return [
            Move((r, c), tgt, self.board) for tgt in cand_tgts if utils.is_valid_sq(tgt)
        ]

    def gen_bishop_moves(self, r: int, c: int) -> List[Move]:
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

    def gen_queen_moves(self, r: int, c: int) -> List[Move]:
        """Generate possible queen moves, ignoring colisions and check rules"""

        return self.gen_bishop_moves(r, c) + self.gen_rook_moves(r, c)

    def gen_king_moves(self, r: int, c: int) -> List[Move]:
        """Generate possible king moves, ignoring colisions and check rules and out of
        bounds errors"""
        dirs = [(1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1)]
        cand_tgts = [utils._add((r, c), delta) for delta in dirs]

        king_moves = [
            Move((r, c), tgt, self.board) for tgt in cand_tgts if utils.is_valid_sq(tgt)
        ]

        return king_moves

    def gen_pawn_moves(self, r: int, c: int) -> List[Move]:
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

        capture_cands = [
            Move((r, c), (r + direction, c + k), self.board)
            for k in [1, -1]
            if utils.is_valid_sq((r + direction, c + k))
        ]

        captures: List[Move] = []

        for m in capture_cands:
            if (m.x_1, m.y_1) == self.en_passant_sq:
                m.is_en_passant = True
                captures.append(m)
            if self.board[m.x_1][m.y_1][0] == ("b" if pawn_color == "w" else "w"):
                captures.append(m)

        return forwards + captures


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

        self.player_color = self.piece_moved[0]
        self.other_player_color = "b" if self.player_color == "w" else "w"

        far_row = 0 if self.player_color == "w" else 7

        self.is_pawn_promotion = self.piece_moved[-1] == "p" and self.x_1 == far_row
        self.is_castling = False
        self.is_en_passant = False

        self.piece_captured = board[self.x_1][self.y_1]

        self.notation = self.gen_notation()

    def __eq__(self, other: object) -> bool:
        """equality override for use in move validation"""

        if not isinstance(other, Move):
            return NotImplemented

        return all(
            [
                self.x_0 == other.x_0,
                self.x_1 == other.x_1,
                self.y_0 == other.y_0,
                self.y_1 == other.y_1,
            ]
        )

    def __repr__(self) -> str:
        return f"{self.player_color}: {self.notation}"

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

    def get_intermediate_squares(self) -> List[Tuple[int, int]]:
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

    def is_valid(self) -> bool:
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

        # check validation happens in the GameState class since we need context outside
        # the move itself
        return True
