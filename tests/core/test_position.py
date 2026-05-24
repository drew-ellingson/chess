"""Tests for Position make/unmake invariants.

The fundamental property: `make_move` followed by `unmake_move` must
leave the position bitwise identical to the original. This catches the
hardest class of make/unmake bugs (forgotten state in Undo, wrong
restoration of castling rights, EP target, halfmove clock, etc.).

The invariant must hold for every *pseudo-legal* move, not just legal
ones — `generate_legal_moves` itself uses make/unmake on pseudo-legal
candidates to filter for king safety, so a make/unmake bug at the
pseudo-legal level cascades into the legality filter and from there
into perft.
"""

import copy

import pytest

from drewbert.adapters.fen import alg_sq_to_int, parse_fen
from drewbert.core.move import Move
from drewbert.core.movegen import generate_pseudo_legal_moves
from drewbert.core.position import Position
from drewbert.core.types import Color, Piece, PieceType
from tests.core._helpers import diff_positions

# A spread of positions exercising every special-move case make/unmake
# has to handle: ordinary moves, captures, EP, castling, promotion.
# Kept in sync with the canonical list in tests/adapters/test_fen.py.
FENS = [
    # Starting position
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    # Kiwipete — dense middlegame, all castling rights, captures everywhere
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    # Perft position 3 — sparse, exposes EP and edge-case pawn moves
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    # Perft position 4 — promotions in play, partial castling rights
    "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2pP/R2Q1RK1 w kq - 0 1",
    # Perft position 5 — promotion-heavy
    "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
    # EP target set after 1.e4 — exercises EP capture path
    "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
    # Black to move from starting position
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1",
]


@pytest.mark.parametrize("fen", FENS)
def test_make_unmake_round_trip(fen: str) -> None:
    """make_move then unmake_move restores the position exactly, for every pseudo-legal move."""
    position = parse_fen(fen)
    for move in generate_pseudo_legal_moves(position):
        snapshot = copy.deepcopy(position)
        undo = position.make_move(move)
        position.unmake_move(undo)
        diffs = diff_positions(snapshot, position)
        assert not diffs, f"{fen} / {move}: {diffs}"


@pytest.mark.parametrize("fen", FENS)
def test_make_returns_undo_with_move(fen: str) -> None:
    """Sanity: the returned Undo references the move that was made."""
    position = parse_fen(fen)

    for move in generate_pseudo_legal_moves(position):
        snapshot = copy.deepcopy(position)
        undo = position.make_move(move)
        assert undo.move == move
        position.unmake_move(undo)
        diffs = diff_positions(snapshot, position)
        assert not diffs, f"{fen} / {move}: {diffs}"


# ---------------------------------------------------------------------------
# Targeted unit tests for each branch in make_move.
#
# Round-trip tests catch ASYMMETRIC bugs (make does X, unmake doesn't undo X).
# They cannot catch SYMMETRIC bugs where both halves are wrong in a way that
# cancels — e.g. both halves ignoring castling entirely would still round-trip
# cleanly. The tests below pin specific board state after a single move, so
# they catch both classes. They also serve as documentation of the contract
# each branch in make_move is supposed to satisfy.
# ---------------------------------------------------------------------------


def _apply(fen: str, frm: str, to: str, promotion: PieceType | None = None) -> Position:
    """Parse FEN, apply one move (squares in algebraic), return the resulting Position."""
    position = parse_fen(fen)
    position.make_move(Move(alg_sq_to_int(frm), alg_sq_to_int(to), promotion))
    return position


# Castling --------------------------------------------------------------


def test_castle_kingside_white_moves_king_and_rook() -> None:
    pos = _apply("4k3/8/8/8/8/8/8/4K2R w K - 0 1", "e1", "g1")
    assert pos.piece_at(alg_sq_to_int("g1")) == Piece(PieceType.KING, Color.WHITE)
    assert pos.piece_at(alg_sq_to_int("f1")) == Piece(PieceType.ROOK, Color.WHITE)
    assert pos.piece_at(alg_sq_to_int("e1")) is None
    assert pos.piece_at(alg_sq_to_int("h1")) is None
    assert pos.castling_rights.white_kingside is False


def test_castle_queenside_white_moves_king_and_rook() -> None:
    pos = _apply("4k3/8/8/8/8/8/8/R3K3 w Q - 0 1", "e1", "c1")
    assert pos.piece_at(alg_sq_to_int("c1")) == Piece(PieceType.KING, Color.WHITE)
    assert pos.piece_at(alg_sq_to_int("d1")) == Piece(PieceType.ROOK, Color.WHITE)
    assert pos.piece_at(alg_sq_to_int("e1")) is None
    assert pos.piece_at(alg_sq_to_int("a1")) is None
    assert pos.castling_rights.white_queenside is False


def test_castle_kingside_black_moves_king_and_rook() -> None:
    pos = _apply("4k2r/8/8/8/8/8/8/4K3 b k - 0 1", "e8", "g8")
    assert pos.piece_at(alg_sq_to_int("g8")) == Piece(PieceType.KING, Color.BLACK)
    assert pos.piece_at(alg_sq_to_int("f8")) == Piece(PieceType.ROOK, Color.BLACK)
    assert pos.piece_at(alg_sq_to_int("e8")) is None
    assert pos.piece_at(alg_sq_to_int("h8")) is None
    assert pos.castling_rights.black_kingside is False


def test_castle_queenside_black_moves_king_and_rook() -> None:
    pos = _apply("r3k3/8/8/8/8/8/8/4K3 b q - 0 1", "e8", "c8")
    assert pos.piece_at(alg_sq_to_int("c8")) == Piece(PieceType.KING, Color.BLACK)
    assert pos.piece_at(alg_sq_to_int("d8")) == Piece(PieceType.ROOK, Color.BLACK)
    assert pos.piece_at(alg_sq_to_int("e8")) is None
    assert pos.piece_at(alg_sq_to_int("a8")) is None
    assert pos.castling_rights.black_queenside is False


# Non-castle king moves to file-2 / file-6 squares ---------------------------
# These are the bug the other session traced — a king move ending on g1/c1/g8/c8
# that ISN'T a castle must not trigger the castle branch's rook-relocation.
# The minimal FEN places friendly pieces on the squares the buggy rook-move
# would touch (f2 / h2 etc.) so the corruption is visible.


def test_king_move_to_g_file_is_not_castle() -> None:
    pos = _apply("4k3/8/8/8/8/8/5P1P/6K1 w - - 0 1", "g1", "g2")
    assert pos.piece_at(alg_sq_to_int("g2")) == Piece(PieceType.KING, Color.WHITE)
    assert pos.piece_at(alg_sq_to_int("g1")) is None
    assert pos.piece_at(alg_sq_to_int("f2")) == Piece(PieceType.PAWN, Color.WHITE)
    assert pos.piece_at(alg_sq_to_int("h2")) == Piece(PieceType.PAWN, Color.WHITE)


def test_king_move_to_c_file_is_not_castle() -> None:
    pos = _apply("4k3/8/8/8/8/8/PP6/2K5 w - - 0 1", "c1", "c2")
    assert pos.piece_at(alg_sq_to_int("c2")) == Piece(PieceType.KING, Color.WHITE)
    assert pos.piece_at(alg_sq_to_int("c1")) is None
    assert pos.piece_at(alg_sq_to_int("a2")) == Piece(PieceType.PAWN, Color.WHITE)
    assert pos.piece_at(alg_sq_to_int("b2")) == Piece(PieceType.PAWN, Color.WHITE)


# En passant ----------------------------------------------------------------


def test_en_passant_capture_removes_captured_pawn() -> None:
    """White EP capture e5xd6: pawn lands on d6, captured pawn on d5 is removed."""
    pos = _apply("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1", "e5", "d6")
    assert pos.piece_at(alg_sq_to_int("d6")) == Piece(PieceType.PAWN, Color.WHITE)
    assert pos.piece_at(alg_sq_to_int("e5")) is None
    assert pos.piece_at(alg_sq_to_int("d5")) is None


def test_en_passant_capture_black() -> None:
    """Black EP capture e4xd3: pawn lands on d3, captured pawn on d4 is removed."""
    pos = _apply("4k3/8/8/8/3Pp3/8/8/4K3 b - d3 0 1", "e4", "d3")
    assert pos.piece_at(alg_sq_to_int("d3")) == Piece(PieceType.PAWN, Color.BLACK)
    assert pos.piece_at(alg_sq_to_int("e4")) is None
    assert pos.piece_at(alg_sq_to_int("d4")) is None


# Double pawn push ----------------------------------------------------------


def test_double_push_white_sets_ep_target() -> None:
    pos = _apply("4k3/8/8/8/8/8/4P3/4K3 w - - 0 1", "e2", "e4")
    assert pos.piece_at(alg_sq_to_int("e4")) == Piece(PieceType.PAWN, Color.WHITE)
    assert pos.en_passant_target == alg_sq_to_int("e3")


def test_double_push_black_sets_ep_target() -> None:
    pos = _apply("4k3/4p3/8/8/8/8/8/4K3 b - - 0 1", "e7", "e5")
    assert pos.piece_at(alg_sq_to_int("e5")) == Piece(PieceType.PAWN, Color.BLACK)
    assert pos.en_passant_target == alg_sq_to_int("e6")


def test_single_push_does_not_set_ep_target() -> None:
    """A single-square pawn push must NOT set ep_target."""
    pos = _apply("4k3/8/8/8/8/8/4P3/4K3 w - - 0 1", "e2", "e3")
    assert pos.en_passant_target is None


# Promotion -----------------------------------------------------------------


def test_promotion_replaces_pawn_with_chosen_piece() -> None:
    pos = _apply("4k3/4P3/8/8/8/8/8/4K3 w - - 0 1", "e7", "e8", PieceType.QUEEN)
    assert pos.piece_at(alg_sq_to_int("e8")) == Piece(PieceType.QUEEN, Color.WHITE)
    assert pos.piece_at(alg_sq_to_int("e7")) is None


def test_promotion_to_knight() -> None:
    """Underpromotion: chosen piece type is used, not auto-queen."""
    pos = _apply("4k3/4P3/8/8/8/8/8/4K3 w - - 0 1", "e7", "e8", PieceType.KNIGHT)
    assert pos.piece_at(alg_sq_to_int("e8")) == Piece(PieceType.KNIGHT, Color.WHITE)


# Castling rights updates ---------------------------------------------------


def test_rook_move_from_a1_strips_white_queenside() -> None:
    pos = _apply("4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1", "a1", "a4")
    assert pos.castling_rights.white_queenside is False
    assert pos.castling_rights.white_kingside is True


def test_rook_move_from_h1_strips_white_kingside() -> None:
    pos = _apply("4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1", "h1", "h4")
    assert pos.castling_rights.white_kingside is False
    assert pos.castling_rights.white_queenside is True


def test_rook_capture_on_h8_strips_black_kingside() -> None:
    """Capturing the black rook on its home square strips the corresponding black right."""
    pos = _apply("k6r/8/8/8/8/8/8/4K2R w Kk - 0 1", "h1", "h8")
    assert pos.castling_rights.black_kingside is False


def test_rook_capture_on_a8_strips_black_queenside() -> None:
    pos = _apply("r6k/8/8/8/8/8/8/R3K3 w Qq - 0 1", "a1", "a8")
    assert pos.castling_rights.black_queenside is False


# Halfmove clock ------------------------------------------------------------


def test_halfmove_resets_on_pawn_move() -> None:
    pos = _apply("4k3/8/8/8/8/8/4P3/4K3 w - - 5 1", "e2", "e4")
    assert pos.halfmove_clock == 0


def test_halfmove_resets_on_capture() -> None:
    """Knight captures black pawn: halfmove resets to 0."""
    pos = _apply("4k3/8/8/1p6/8/2N5/8/4K3 w - - 7 1", "c3", "b5")
    assert pos.halfmove_clock == 0


def test_halfmove_increments_on_quiet_move() -> None:
    """Plain king move with no capture and no pawn move: halfmove +1."""
    pos = _apply("4k3/8/8/8/8/8/8/4K3 w - - 5 1", "e1", "e2")
    assert pos.halfmove_clock == 6
