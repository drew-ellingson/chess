"""Cross-benchmark history reader.

Globs every `benchmarks/*/results.jsonl`, groups records by (benchmark, label),
and prints recent runs with the percent change from the previous entry in the
same group.

Records are expected to follow the shared schema in `benchmarks/README.md`.
Top-level fields used here: `timestamp`, `commit`, `benchmark`, `label`,
`metric.value`, `metric.unit`. Everything else is ignored by this reader
(benchmarks are free to put benchmark-specific data in `params`).

Run:
    uv run python benchmarks/analyze.py                    # all benchmarks, all history
    uv run python benchmarks/analyze.py --benchmark perft  # one benchmark
    uv run python benchmarks/analyze.py --last 10          # only the last N per group
"""

import argparse
import json
import sys
from pathlib import Path

BENCH_DIR = Path(__file__).parent


def load_records(only_benchmark: str | None = None) -> list[dict]:
    """Load every record from benchmarks/*/results.jsonl, optionally filtered by benchmark."""
    records: list[dict] = []
    for results_file in sorted(BENCH_DIR.glob("*/results.jsonl")):
        for lineno, raw in enumerate(results_file.read_text().splitlines(), start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                print(
                    f"warning: skipping malformed line {results_file}:{lineno}: {e}",
                    file=sys.stderr,
                )
                continue
            if only_benchmark and record.get("benchmark") != only_benchmark:
                continue
            records.append(record)
    return records


def group_by_label(records: list[dict]) -> dict[tuple[str, str], list[dict]]:
    """Group records by (benchmark, label). Within each group, sort by timestamp ascending."""
    groups: dict[tuple[str, str], list[dict]] = {}
    for r in records:
        key = (r.get("benchmark", "?"), r.get("label", "?"))
        groups.setdefault(key, []).append(r)
    # ISO 8601 timestamps sort lexicographically — no need to parse.
    for entries in groups.values():
        entries.sort(key=lambda r: r.get("timestamp", ""))
    return groups


def format_value(record: dict) -> str:
    """Format the headline metric value with thousands separators and unit."""
    metric = record.get("metric", {})
    value = metric.get("value")
    unit = metric.get("unit", "")
    if value is None:
        return "—"
    if isinstance(value, int):
        return f"{value:>14,} {unit}"
    return f"{value:>14.3f} {unit}"


def format_delta(curr: dict, prev: dict | None) -> str:
    """Percent change from prev to curr, or '(baseline)' for the first row in a group."""
    if prev is None:
        return "(baseline)"
    curr_v = curr.get("metric", {}).get("value")
    prev_v = prev.get("metric", {}).get("value")
    if curr_v is None or prev_v in (None, 0):
        return ""
    pct = (curr_v - prev_v) / prev_v * 100
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:5.1f}%"


def print_group(key: tuple[str, str], entries: list[dict], last: int | None) -> None:
    """Print one (benchmark, label) group with timestamp / commit / best_seconds / metric / delta."""
    benchmark, label = key
    title = f"{benchmark} / {label}"
    print(title)
    print("─" * max(len(title), 72))

    start = 0 if last is None else max(0, len(entries) - last)

    for i, record in enumerate(entries):
        if i < start:
            continue
        # Delta is always vs. the immediately previous row in the full series,
        # even when tailing. That way the percentages reflect real run-to-run
        # change, not "change since first shown row".
        prev = entries[i - 1] if i > 0 else None
        ts = record.get("timestamp", "?")
        commit = record.get("commit", "?")
        best = record.get("best_seconds")
        best_str = f"{best:6.3f}s" if isinstance(best, (int, float)) else "      —"
        print(f"  {ts:<19}  {commit:<8}  {best_str}  {format_value(record)}   {format_delta(record, prev)}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize benchmark history from benchmarks/*/results.jsonl.")
    parser.add_argument("--benchmark", help="filter to one benchmark id (e.g. 'perft')")
    parser.add_argument(
        "--last",
        type=int,
        help="show only the last N runs per (benchmark, label) group",
    )
    args = parser.parse_args()

    records = load_records(only_benchmark=args.benchmark)
    if not records:
        msg = "no benchmark records found"
        if args.benchmark:
            msg += f" for benchmark={args.benchmark!r}"
        print(msg)
        return 0

    groups = group_by_label(records)
    for key in sorted(groups):
        print_group(key, groups[key], args.last)

    return 0


if __name__ == "__main__":
    sys.exit(main())
