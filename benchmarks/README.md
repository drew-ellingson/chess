# benchmarks

Each subdirectory is one benchmark (e.g. `perft/`, eventually `search/`, `eval/`).
Each appends to its own `results.jsonl`. A single shared reader,
`benchmarks/analyze.py`, summarises history across all of them.

## Shared record schema

Every line in any `results.jsonl` is one JSON object with these top-level fields:

```json
{
  "timestamp": "2026-05-25T10:15:30",   // ISO 8601, lexicographic sort = time sort
  "commit": "3b2f42d",                  // short git SHA
  "benchmark": "perft",                 // benchmark id; matches the subdir name
  "label": "d4",                        // grouping label within the benchmark
  "runs": 5,                            // timed repetitions (post warm-up)
  "best_seconds": 2.341,
  "median_seconds": 2.388,
  "metric": {                           // the headline number
    "name": "nodes_per_sec",
    "value": 84273,
    "unit": "nodes/sec"
  },
  "environment": {                      // for filtering / sanity-checking
    "python_version": "3.12.0",
    "platform": "macOS-14.0-arm64",
    "machine": "arm64"
  },
  "params": {                           // benchmark-specific knobs/results
    "fen": "rnbqkbnr/...",
    "depth": 4,
    "nodes": 197281
  }
}
```

`benchmark` + `label` together form the grouping key that `analyze.py` uses to
show one series at a time. If you run perft on multiple positions, give each a
distinct `--label` so they don't collapse into the same series.

## Reading results

```sh
uv run python benchmarks/analyze.py                    # everything, full history
uv run python benchmarks/analyze.py --benchmark perft  # one benchmark
uv run python benchmarks/analyze.py --last 10          # only the last N per group
```

Sample output:

```
perft / d4
────────────────────────────────────────────────────────────
  2026-05-25T10:15:30  3b2f42d        84,273 nodes/sec   (baseline)
  2026-05-25T14:32:11  a7c3e91        91,540 nodes/sec   + 8.6%
  2026-05-26T09:10:02  bf112de        89,200 nodes/sec   - 2.6%
```

Delta is percent change from the immediately previous run in the same group,
even when tailing with `--last` (so the percentages reflect real run-to-run
change, not "change since first shown row").

## Per-benchmark docs

- [`perft/`](perft/README.md) — movegen + make/unmake throughput

## Why min / median, not mean

A computer can only ever go *slower* than physics — never faster. Variance is
one-sided noise (contention, thermal throttling, GC pauses). The min is closest
to "true" speed; the median is robust against the occasional bad run. The mean
gets dragged by every hiccup.

## Adding a new benchmark

1. Create `benchmarks/<name>/` with a `run.py` that emits records following the
   schema above. Set `benchmark` to the directory name.
2. Pick a meaningful `--label` default (e.g. `d{depth}` for perft).
3. Document it in a sibling `README.md` and link it from this file.

`analyze.py` will pick it up automatically — no changes there.

## Caveats

- These numbers are only directly comparable when run on the same machine. The
  `environment` block makes that auditable but doesn't enforce it.
- Pure-Python perft is slow. Defaults are chosen so a routine run finishes in
  seconds, not minutes.
