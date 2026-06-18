"""UCI parser unit tests.

Pure-function tests on `parse()` — no subprocess, no engine state. Validates
that each UCI command line maps to the expected dataclass variant with the
expected field values. Edge cases (malformed input, unknown commands) should
route to UciUnrecognized per Postel's-law handling.
"""

import pytest

from drewbert.adapters.uci import (
    UciGo,
    UciIsReady,
    UciNewGame,
    UciPonderHit,
    UciPosition,
    UciQuit,
    UciSetOption,
    UciStop,
    UciUci,
    UciUnrecognized,
    parse,
)


# --- Parameterless commands ---


@pytest.mark.parametrize(
    "line,expected_type",
    [
        ("uci", UciUci),
        ("isready", UciIsReady),
        ("ucinewgame", UciNewGame),
        ("quit", UciQuit),
        ("stop", UciStop),
        ("ponderhit", UciPonderHit),
    ],
)
def test_parameterless_commands(line: str, expected_type: type) -> None:
    cmd = parse(line)
    assert isinstance(cmd, expected_type)


# --- setoption ---


def test_setoption_with_value() -> None:
    cmd = parse("setoption Hash 128")
    assert isinstance(cmd, UciSetOption)
    assert cmd.name == "Hash"
    assert cmd.value == "128"


def test_setoption_without_value() -> None:
    cmd = parse("setoption ClearHash")
    assert isinstance(cmd, UciSetOption)
    assert cmd.name == "ClearHash"
    assert cmd.value is None


# --- position ---


def test_position_startpos() -> None:
    cmd = parse("position startpos")
    assert isinstance(cmd, UciPosition)
    assert cmd.startpos is True
    assert cmd.fen is None
    assert cmd.moves is None


def test_position_startpos_with_moves() -> None:
    cmd = parse("position startpos moves e2e4 e7e5 g1f3")
    assert isinstance(cmd, UciPosition)
    assert cmd.startpos is True
    # `moves` is captured as the raw space-separated substring after the
    # `moves` keyword; consumers split when they need individual tokens.
    assert cmd.moves == "e2e4 e7e5 g1f3"


def test_position_fen() -> None:
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    cmd = parse(f"position fen {fen}")
    assert isinstance(cmd, UciPosition)
    assert cmd.startpos is False
    # The fen clause should capture the rest of the FEN string.
    # (Exact field assertion depends on how the parser stitches multi-token FENs;
    # at minimum, the parsed value should not be None.)
    assert cmd.fen is not None


def test_position_fen_with_moves() -> None:
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    cmd = parse(f"position fen {fen} moves e2e4")
    assert isinstance(cmd, UciPosition)
    assert cmd.fen == fen
    assert cmd.moves == "e2e4"


# --- go ---


def test_go_with_no_args() -> None:
    cmd = parse("go")
    assert isinstance(cmd, UciGo)
    assert cmd.infinite is False
    assert cmd.depth is None


def test_go_depth() -> None:
    cmd = parse("go depth 5")
    assert isinstance(cmd, UciGo)
    assert cmd.depth == 5
    assert cmd.infinite is False


def test_go_infinite() -> None:
    cmd = parse("go infinite")
    assert isinstance(cmd, UciGo)
    assert cmd.infinite is True
    assert cmd.depth is None


def test_go_nodes_and_mate_are_ints() -> None:
    """Regression test for the Wikipedia synopsis bug where nodes/mate
    were typed as bool. UCI spec has both as value-taking int params."""
    cmd = parse("go nodes 10000 mate 3")
    assert isinstance(cmd, UciGo)
    assert cmd.nodes == 10000
    assert cmd.mate == 3


def test_go_tournament_time_control() -> None:
    cmd = parse("go wtime 60000 btime 60000 winc 600 binc 600")
    assert isinstance(cmd, UciGo)
    assert cmd.wtime == 60000
    assert cmd.btime == 60000
    assert cmd.winc == 600
    assert cmd.binc == 600


def test_go_movetime() -> None:
    cmd = parse("go movetime 5000")
    assert isinstance(cmd, UciGo)
    assert cmd.movetime == 5000


def test_go_combined_params() -> None:
    """Real GUIs combine time control with depth or movetime."""
    cmd = parse("go wtime 60000 btime 60000 depth 10")
    assert isinstance(cmd, UciGo)
    assert cmd.wtime == 60000
    assert cmd.btime == 60000
    assert cmd.depth == 10


def test_go_malformed_int_returns_none() -> None:
    """Per Postel's law, malformed values become None rather than raising."""
    cmd = parse("go depth abc")
    assert isinstance(cmd, UciGo)
    assert cmd.depth is None


# --- Unrecognized ---


def test_unknown_command_returns_unrecognized() -> None:
    cmd = parse("frobnicate the widget")
    assert isinstance(cmd, UciUnrecognized)


def test_empty_input_returns_unrecognized() -> None:
    # Empty line splits to [''] — first token is empty string, which matches
    # no UCI command name.
    cmd = parse("")
    assert isinstance(cmd, UciUnrecognized)
