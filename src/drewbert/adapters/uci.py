import argparse
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
import sys

from drewbert.core.position import Position
from drewbert.core.move import Move
from drewbert.eval.materialistic import materialistic_position_eval
from drewbert.search.minimax import minimax
from drewbert.adapters.fen import STARTING_FEN, parse_fen


@dataclass
class UciQuit: ...


@dataclass
class UciUci: ...


@dataclass
class UciNewGame: ...


@dataclass
class UciIsReady: ...


@dataclass
class UciSetOption:
    name: str
    value: str | None


@dataclass
class UciPosition:
    fen: str | None
    startpos: bool
    moves: list[str] | None


@dataclass
class UciGo:
    infinite: bool
    depth: int | None
    nodes: int | None
    mate: int | None
    searchmoves: list[str] | None
    wtime: int | None
    btime: int | None
    winc: int | None
    binc: int | None
    movestogo: int | None
    movetime: int | None
    ponder: bool


@dataclass
class UciStop: ...


@dataclass
class UciPonderHit: ...


@dataclass
class UciUnrecognized:
    content: list[str] | None


UciCommand = (
    UciQuit
    | UciUci
    | UciNewGame
    | UciIsReady
    | UciSetOption
    | UciPosition
    | UciGo
    | UciStop
    | UciPonderHit
    | UciUnrecognized
)
ConfiguredSearch = Callable[[Position], int]

SEARCHES = {
    "minimax": minimax,
}
EVALS = {
    "materialistic": materialistic_position_eval,
}


def split_by_starting_words(tokens, start_words):
    current_group = []
    for token in tokens:
        if token in start_words:
            if current_group:
                yield current_group
            else:
                current_group = [token]
    if current_group:
        yield current_group


def get_flag(clause_list, prefix):
    return any(c[0] == prefix for c in clause_list)


def get_value(clause_list, prefix):
    matching = [c for c in clause_list if c[0] == prefix]
    return None if not matching else matching[0][1]


def get_list(clause_list, prefix):
    matching = [c for c in clause_list if c[0] == prefix]
    return None if not matching else matching[0][1:]


def parse(line: str) -> UciCommand:
    tokens = line.split(" ")
    match tokens[0]:
        case "quit":
            return UciQuit()
        case "uci":
            return UciUci()
        case "usinewgame":
            return UciNewGame()
        case "isready":
            return UciIsReady()
        case "setoption":
            return UciSetOption(name=tokens[1], value=None if len(tokens) == 2 else tokens[2])
        case "position":
            groups = split_by_starting_words(tokens, ["position", "fen", "startpos", "moves"])
            return UciPosition(
                fen=get_value(groups, "fen"), startpos=get_flag(groups, "startpos"), moves=get_list(groups, "moves")
            )
        case "go":
            groups = split_by_starting_words(
                tokens,
                [
                    "infinite",
                    "depth",
                    "nodes",
                    "mate",
                    "searchmoves",
                    "ponder",
                    "wtime",
                    "btime",
                    "winc",
                    "binc",
                    "movestogo",
                    "nodes",
                    "movetime",
                    "perft",
                ],
            )
            return UciGo(
                infinite=get_flag(groups, "infinite"),
                depth=get_value(groups, "depth"),
                nodes=get_value(groups, "nodes"),
                mate=get_value(groups, "mate"),
                searchmoves=get_list(groups, "searchmoves"),
                ponder=get_flag(groups, "ponder"),
                wtime=get_value(groups, "wtime"),
                btime=get_value(groups, "btime"),
                winc=get_value(groups, "winc"),
                binc=get_value(groups, "binc"),
                movestogo=get_value(groups, "movestogo"),
                movetime=get_value(groups, "movetime"),
            )
        case "stop":
            return UciStop()
        case "ponderhit":
            return UciPonderHit()
        case _:
            return UciUnrecognized(None if len(tokens) == 1 else tokens[1:])


def emit(line: str) -> None:
    print(line, flush=True)


def main(search_fn: ConfiguredSearch) -> None:
    position = parse_fen(STARTING_FEN)
    while True:
        line = sys.stdin.readline()
        cmd = parse(line.strip())


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Engine Configuration")
    parser.add_argument("eval", metavar="E", help="The evaluation function to be used in the engine")
    parser.add_argument("search", metavar="S", help="The search function to be used in the engine")
    parser.add_argument("depth", metavar="D", help="The fixed depth setting to be used in the search function")

    args = parser.parse_args()  # - --search minimax --eval material --depth 3
    eval = EVALS[args.evals]

    search: ConfiguredSearch = partial(SEARCHES[args.search], depth=args.depth, position_evaluator=eval)
    main(search)
