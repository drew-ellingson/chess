import argparse
import sys
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from typing import assert_never

from drewbert.adapters.fen import FEN_TO_POS, STARTING_FEN, alg_sq_to_int, parse_fen
from drewbert.core.move import Move
from drewbert.core.position import Position
from drewbert.eval.materialistic import materialistic_position_eval
from drewbert.search.minimax import best_move


@dataclass(frozen=True)
class UciQuit: ...


@dataclass(frozen=True)
class UciUci: ...


@dataclass(frozen=True)
class UciNewGame: ...


@dataclass(frozen=True)
class UciIsReady: ...


@dataclass(frozen=True)
class UciSetOption:
    name: str
    value: str | None


@dataclass(frozen=True)
class UciPosition:
    fen: str | None
    startpos: bool
    moves: str | None


@dataclass(frozen=True)
class UciGo:
    infinite: bool
    depth: int | None
    nodes: int | None
    mate: int | None
    searchmoves: str | None
    wtime: int | None
    btime: int | None
    winc: int | None
    binc: int | None
    movestogo: int | None
    movetime: int | None
    ponder: bool


@dataclass(frozen=True)
class UciStop: ...


@dataclass(frozen=True)
class UciPonderHit: ...


@dataclass(frozen=True)
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
ConfiguredSearch = Callable[[Position], Move | None]

SEARCHES = {
    "minimax": best_move,
}
EVALS = {
    "materialistic": materialistic_position_eval,
}


def uci_to_move(move: str) -> Move:
    from_square, to_square = alg_sq_to_int(move[:2]), alg_sq_to_int(move[2:4])
    promotion = FEN_TO_POS[move[-1]].type if len(move) > 4 else None
    return Move(from_square, to_square, promotion)


def split_by_starting_words(tokens, start_words):
    current_group = []
    for token in tokens:
        if token in start_words:
            if current_group:
                yield current_group
            current_group = [token]
        else:
            current_group.append(token)
    if current_group:
        yield current_group


def get_flag(clause_list, prefix):
    return any(c[0] == prefix for c in clause_list)


def get_value[T](clause_list, prefix, convert: Callable[[str], T]) -> T | None:
    matching = [c for c in clause_list if c[0] == prefix]
    
    if not matching:
        return None
    else:
        try:
            return convert(matching[0][1])
        except ValueError:
            return None  # allow malformed input without raising, per UCI guidance.


def get_list(clause_list, prefix):
    matching = [c for c in clause_list if c[0] == prefix]
    return None if not matching else ' '.join(matching[0][1:])


def parse(line: str) -> UciCommand:
    tokens = line.split(" ")
    match tokens[0]:
        case "quit":
            return UciQuit()
        case "uci":
            return UciUci()
        case "ucinewgame":
            return UciNewGame()
        case "isready":
            return UciIsReady()
        case "setoption":
            return UciSetOption(name=tokens[1], value=None if len(tokens) == 2 else tokens[2])
        case "position":
            groups = list(split_by_starting_words(tokens, ["position", "fen", "startpos", "moves"]))
            return UciPosition(
                fen=get_list(groups, "fen"),
                startpos=get_flag(groups, "startpos"),
                moves=get_list(groups, "moves"),
            )
        case "go":
            groups = list(split_by_starting_words(
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
            ))
            return UciGo(
                infinite=get_flag(groups, "infinite"),
                depth=get_value(groups, "depth", int),
                nodes=get_value(groups, "nodes", int),
                mate=get_value(groups, "mate", int),
                searchmoves=get_list(groups, "searchmoves"),
                ponder=get_flag(groups, "ponder"),
                wtime=get_value(groups, "wtime", int),
                btime=get_value(groups, "btime", int),
                winc=get_value(groups, "winc", int),
                binc=get_value(groups, "binc", int),
                movestogo=get_value(groups, "movestogo", int),
                movetime=get_value(groups, "movetime", int),
            )
        case "stop":
            return UciStop()
        case "ponderhit":
            return UciPonderHit()
        case _:
            return UciUnrecognized(tokens)


def emit(line: str) -> None:
    print(line, flush=True)


def apply_uci_go_cmd(go: UciGo, position: Position, search_fn: ConfiguredSearch) -> None:
    move = search_fn(position)
    emit(f"bestmove {str(move)}")


def apply_uci_position_cmd(uci_position: UciPosition, position: Position) -> Position:
    if uci_position.fen:
        position = parse_fen(uci_position.fen)
    elif uci_position.startpos:
        position = parse_fen(STARTING_FEN)
    if uci_position.moves:
        for move in uci_position.moves.split(' '):
            position.make_move(uci_to_move(move))
    return position


def apply_uci_set_option_cmd(setoption: UciSetOption):
    pass


def main(search_fn: ConfiguredSearch) -> None:
    position = parse_fen(STARTING_FEN)
    while True:
        line = sys.stdin.readline()
        cmd = parse(line.strip())
        
        match cmd:
            case UciQuit():
                sys.exit()
            case UciUci():
                emit("id name drewbert")
                emit("id author drew")
                emit("uciok")
            case UciNewGame():
                pass
            case UciIsReady():
                emit("readyok")
            case UciSetOption():
                apply_uci_set_option_cmd(cmd)
            case UciPosition():
                position = apply_uci_position_cmd(cmd, position)
            case UciGo():
                apply_uci_go_cmd(cmd, position, search_fn)
            case UciPonderHit():
                pass
            case UciStop():
                pass
            case UciUnrecognized():
                pass
            case _:  # defensive check against future parse additions not mirrored on implementation
                assert_never(cmd)  # pyright: ignore


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Engine Configuration")
    parser.add_argument("--eval", required=True, help="The evaluation function to be used in the engine")
    parser.add_argument("--search", required=True, help="The search function to be used in the engine")
    parser.add_argument(
        "--depth", type=int, default=3, help="The fixed depth setting to be used in the search function"
    )

    args = parser.parse_args()  # - --search minimax --eval material --depth 3
    eval = EVALS[args.eval]

    search: ConfiguredSearch = partial(SEARCHES[args.search], depth=args.depth, position_evaluator=eval)
    main(search)
