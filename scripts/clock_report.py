"""Per-game clock usage report for one engine in a cutechess PGN.

Reads the move comments cutechess writes (`{+0.21/17 1.4s}`, `{/3 0.63s}`, `{book}`),
reconstructs the engine's clock move by move from the game's TimeControl, and prints
per-game and overall summaries: time per move, depth reached, and the lowest clock.

Usage:
    uv run scripts/clock_report.py games.pgn
    uv run scripts/clock_report.py games.pgn --engine stockfish

Assumptions:
    - Only `base+inc` time controls (e.g. `10+0.3`) are reconstructed. Moves-per-period
      controls (`40/60`) and `inf` are reported without clock figures.
    - Book moves neither consume time nor earn the increment.
    - cutechess omits the comment for an engine that sends no `info` and moves in under
      500ms. Such moves are counted as unrecorded and excluded from timing figures, so
      clock figures for games with unrecorded moves are optimistic.
    - Comment times are cutechess's own measurement (what the clock was charged), but
      rounded for display: 1 decimal at >=1s, 2 below. The ± on clock figures is the
      worst-case accumulated rounding error, so a slightly negative clock is expected
      for engines that run their clock near zero.
"""

import argparse
import re
import statistics
from dataclasses import dataclass, field
from pathlib import Path

import chess
import chess.pgn

# Matches the tail of a cutechess eval comment: optional "<score>/<depth> " then "<time>s".
MOVE_COMMENT_RE = re.compile(r"(?:\S*/(?P<depth>\d+)\s+)?(?P<time>\d+(?:\.(?P<decimals>\d+))?)s\b")
LOW_CLOCK_WARNING_S = 1.0


@dataclass
class GameReport:
    number: int
    colour: str
    outcome: str
    termination: str
    times: list[float] = field(default_factory=list)
    depths: list[int] = field(default_factory=list)
    unrecorded: int = 0
    lowest_clock: float | None = None
    lowest_clock_move: int | None = None
    # cutechess rounds displayed times (1 decimal at >=1s), so the reconstructed clock drifts.
    lowest_clock_error: float = 0.0


def parse_time_control(tc: str) -> tuple[float, float] | None:
    """Return (base_seconds, increment_seconds) for a `base+inc` control, else None."""
    match = re.fullmatch(r"(\d+(?:\.\d+)?)(?:\+(\d+(?:\.\d+)?))?", tc)
    if match is None:
        return None
    return float(match.group(1)), float(match.group(2) or 0)


def outcome_for(result: str, side: chess.Color) -> str:
    if result == "1/2-1/2":
        return "draw"
    if result not in ("1-0", "0-1"):
        return "none"
    won = (result == "1-0") == (side == chess.WHITE)
    return "win" if won else "loss"


def report_game(number: int, game: chess.pgn.Game, engine: str) -> GameReport | None:
    """Build the report for `engine` in `game`, or None if the engine didn't play in it."""
    headers = game.headers
    if headers["White"].startswith(engine):
        side = chess.WHITE
    elif headers["Black"].startswith(engine):
        side = chess.BLACK
    else:
        return None

    report = GameReport(
        number=number,
        colour="W" if side == chess.WHITE else "B",
        outcome=outcome_for(headers.get("Result", "*"), side),
        termination=headers.get("Termination", "normal"),
    )
    tc = parse_time_control(headers.get("TimeControl", ""))
    clock = tc[0] if tc else None
    rounding_error = 0.0

    board = game.board()
    for node in game.mainline():
        if board.turn == side and "book" not in node.comment:
            match = MOVE_COMMENT_RE.search(node.comment)
            if match is None:
                report.unrecorded += 1
            else:
                spent = float(match.group("time"))
                report.times.append(spent)
                if match.group("depth"):
                    report.depths.append(int(match.group("depth")))
                if tc is not None and clock is not None:
                    clock -= spent
                    rounding_error += 0.5 * 10 ** -len(match.group("decimals") or "")
                    if report.lowest_clock is None or clock < report.lowest_clock:
                        report.lowest_clock = clock
                        report.lowest_clock_move = board.fullmove_number
                        report.lowest_clock_error = rounding_error
                    clock += tc[1]
        board.push(node.move)
    return report


def print_reports(reports: list[GameReport], engine: str) -> None:
    print(f"Clock report for engine '{engine}' ({len(reports)} games)\n")
    print("game side result term          moves unrec  avg_t   max_t  depth(min/avg/max)  lowest_clock")
    for r in reports:
        depth = f"{min(r.depths)}/{statistics.mean(r.depths):.1f}/{max(r.depths)}" if r.depths else "-"
        low = (
            f"{r.lowest_clock:6.2f}s ±{r.lowest_clock_error:.2f} @ move {r.lowest_clock_move}"
            if r.lowest_clock is not None
            else "n/a"
        )
        avg_t = f"{statistics.mean(r.times):.2f}s" if r.times else "-"
        max_t = f"{max(r.times):.2f}s" if r.times else "-"
        print(
            f"{r.number:4d} {r.colour:>4} {r.outcome:>6} {r.termination[:13]:13s} "
            f"{len(r.times) + r.unrecorded:5d} {r.unrecorded:5d} {avg_t:>6} {max_t:>7}  {depth:>18}  {low}"
        )

    all_times = [t for r in reports for t in r.times]
    all_depths = [d for r in reports for d in r.depths]
    lows = [r for r in reports if r.lowest_clock is not None]
    forfeits = [r for r in reports if "time" in r.termination.lower()]
    print("\nOverall")
    if all_times:
        print(f"  moves timed: {len(all_times)}, avg {statistics.mean(all_times):.2f}s, max {max(all_times):.2f}s")
    if all_depths:
        counts = {d: all_depths.count(d) for d in sorted(set(all_depths))}
        print(f"  depth reached: {', '.join(f'{d}: {n}' for d, n in counts.items())}")
    if lows:
        worst = min(lows, key=lambda r: r.lowest_clock or 0.0)
        print(
            f"  lowest clock: {worst.lowest_clock:.2f}s ±{worst.lowest_clock_error:.2f} "
            f"(game {worst.number}, move {worst.lowest_clock_move})"
        )
        near_flag = [r.number for r in lows if (r.lowest_clock or 0.0) < LOW_CLOCK_WARNING_S]
        if near_flag:
            print(f"  games under {LOW_CLOCK_WARNING_S:.0f}s: {near_flag}")
    print(f"  time forfeits: {len(forfeits)}" + (f" (games {[r.number for r in forfeits]})" if forfeits else ""))
    unrecorded = sum(r.unrecorded for r in reports)
    if unrecorded:
        print(f"  WARNING: {unrecorded} moves had no time recorded; clock figures for those games are optimistic")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pgn", type=Path, help="PGN file written by cutechess-cli -pgnout")
    parser.add_argument("--engine", default="drewbert", help="engine name prefix to report on (default: drewbert)")
    args = parser.parse_args()

    reports: list[GameReport] = []
    with args.pgn.open() as f:
        number = 0
        while (game := chess.pgn.read_game(f)) is not None:
            number += 1
            report = report_game(number, game, args.engine)
            if report is not None:
                reports.append(report)

    if not reports:
        raise SystemExit(f"No games found for engine prefix '{args.engine}' in {args.pgn}")
    print_reports(reports, args.engine)


if __name__ == "__main__":
    main()
