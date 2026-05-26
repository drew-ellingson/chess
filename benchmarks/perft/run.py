"""Perft benchmark — measure movegen + make/unmake speed over time.

Runs `perft(position, depth)` repeatedly, records the best and median wall-clock
times, derives nodes/sec, and appends one JSONL record per invocation to
`results.jsonl` (committed; one line per benchmark run, grep-friendly).

Also runs one extra iteration under cProfile and writes the stats to a `.prof`
file *next to* `results.jsonl`, named `<label>.prof`. The `.prof` file is
gitignored (per-machine, per-run) — view it with snakeviz:

    uv run snakeviz benchmarks/perft/d4.prof

This gives you the headline number in `results.jsonl` plus the call-tree
breakdown for the latest run with that label.

The record follows the shared benchmark schema described in
`benchmarks/README.md` so `benchmarks/analyze.py` can read this file alongside
any other benchmark's output.

Run:
    uv run python benchmarks/perft/run.py                  # defaults: starting d=4, 5 runs
    uv run python benchmarks/perft/run.py --depth 3        # faster cycle
    uv run python benchmarks/perft/run.py --no-profile     # skip cProfile (slightly faster)
    uv run python benchmarks/perft/run.py --label custom   # override label (default: "d{depth}")
"""

import argparse
import cProfile
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

from drewbert.adapters.fen import parse_fen
from drewbert.core.perft import perft

# Defaults are chosen so a default invocation finishes in seconds, not minutes.
# Starting depth 4 = 197,281 nodes; comfortable for pure-Python movegen.
DEFAULT_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
DEFAULT_DEPTH = 4
DEFAULT_RUNS = 5

BENCHMARK_NAME = "perft"
RESULTS_DIR = Path(__file__).parent
RESULTS_FILE = RESULTS_DIR / "results.jsonl"


def _git_sha() -> str:
    """Return the short git SHA, or 'unknown' if not in a repo / git missing."""
    try:
        out = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True)
        return out.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def _run_once(fen: str, depth: int) -> tuple[int, float]:
    """One timed perft run. Returns (nodes, elapsed_seconds)."""
    position = parse_fen(fen)
    start = time.perf_counter()
    nodes = perft(position, depth)
    elapsed = time.perf_counter() - start
    return nodes, elapsed


def _median(values: list[float]) -> float:
    """Median of a list. For even N, returns the average of the two middle values."""
    s = sorted(values)
    n = len(s)
    mid = n // 2
    if n % 2 == 1:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2


def benchmark(fen: str, depth: int, runs: int, label: str) -> dict:
    """Run perft `runs` times, return a record dict following the shared schema."""
    # Warm-up: first run is often slower (cold caches, JIT-like effects in
    # the import machinery, etc.). We discard it so the timed runs aren't
    # skewed by startup noise.
    print(f"warm-up: depth={depth} ...")
    warm_nodes, warm_elapsed = _run_once(fen, depth)
    print(f"  {warm_nodes:,} nodes in {warm_elapsed:.3f}s")

    print(f"timing {runs} runs at depth {depth} ...")
    times: list[float] = []
    nodes_each_run: int | None = None
    for i in range(runs):
        nodes, elapsed = _run_once(fen, depth)
        # Sanity: perft must be deterministic. If two runs return different
        # node counts, the engine has nondeterminism (bug in movegen or
        # state restoration) and the rest of the timing is meaningless.
        if nodes_each_run is None:
            nodes_each_run = nodes
        elif nodes != nodes_each_run:
            raise RuntimeError(
                f"non-deterministic perft: run {i + 1} returned {nodes}, previous runs returned {nodes_each_run}"
            )
        times.append(elapsed)
        print(f"  run {i + 1}/{runs}: {elapsed:.3f}s")

    assert nodes_each_run is not None
    best = min(times)
    med = _median(times)

    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "commit": _git_sha(),
        "benchmark": BENCHMARK_NAME,
        "label": label,
        "runs": runs,
        "best_seconds": round(best, 6),
        "median_seconds": round(med, 6),
        "metric": {
            "name": "nodes_per_sec",
            "value": int(nodes_each_run / best) if best > 0 else 0,
            "unit": "nodes/sec",
        },
        "environment": {
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "params": {
            "fen": fen,
            "depth": depth,
            "nodes": nodes_each_run,
        },
    }


def append_record(record: dict) -> None:
    """Append one JSON record as a single line to `results.jsonl`."""
    with RESULTS_FILE.open("a") as f:
        f.write(json.dumps(record) + "\n")


def run_profile(fen: str, depth: int, label: str) -> Path:
    """Run perft once under cProfile, save the .prof file next to results.jsonl.

    The file is named after the label so multiple labels can coexist; each
    run for the same label overwrites the previous .prof. The .prof file is
    gitignored — it's per-machine and per-run, not history.
    """
    prof_path = RESULTS_DIR / f"{label}.prof"

    # runctx lets us pass the locals perft needs without polluting module namespace.
    print(f"\nprofiling depth {depth} (single run; cProfile overhead is ~30%) ...")
    cProfile.runctx(
        "perft(parse_fen(fen), depth)",
        globals(),
        {"perft": perft, "parse_fen": parse_fen, "fen": fen, "depth": depth},
        str(prof_path),
    )
    print(f"saved {prof_path}")
    print(f"view with: uv run snakeviz {prof_path}")
    return prof_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run perft, time it across multiple runs, append results to results.jsonl."
    )
    parser.add_argument("--fen", default=DEFAULT_FEN, help="starting FEN (default: starting position)")
    parser.add_argument("--depth", type=int, default=DEFAULT_DEPTH, help=f"perft depth (default: {DEFAULT_DEPTH})")
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS, help=f"timed repetitions (default: {DEFAULT_RUNS})")
    parser.add_argument(
        "--label",
        default=None,
        help="grouping label for analyze.py (default: 'd{depth}'). Use to distinguish runs on different positions.",
    )
    parser.add_argument(
        "--no-profile",
        action="store_true",
        help="skip the extra cProfile iteration (faster, but no .prof file produced)",
    )
    parser.add_argument(
        "--no-record",
        action="store_true",
        help="skip appending to results.jsonl (use for ad-hoc runs you don't want to persist)",
    )
    args = parser.parse_args()

    label = args.label or f"d{args.depth}"
    record = benchmark(args.fen, args.depth, args.runs, label)

    print()
    print(f"label:     {record['label']}")
    print(f"best:      {record['best_seconds']:.3f}s")
    print(f"median:    {record['median_seconds']:.3f}s")
    metric = record["metric"]
    print(f"{metric['name']}: {metric['value']:,} {metric['unit']} (using best time)")

    if args.no_record:
        print("\n(--no-record passed; not appending to results.jsonl)")
    else:
        append_record(record)
        print(f"\nappended to {RESULTS_FILE}")

    if not args.no_profile:
        run_profile(args.fen, args.depth, label)

    return 0


if __name__ == "__main__":
    sys.exit(main())
