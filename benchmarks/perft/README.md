# perft benchmark

Tracks `perft` (movegen + make/unmake) speed. One JSONL line per run appended
to `results.jsonl`.

For the record schema and the cross-benchmark reader, see
[`benchmarks/README.md`](../README.md).

## Run

```sh
uv run python benchmarks/perft/run.py                     # default: starting position, depth 4, 5 runs
uv run python benchmarks/perft/run.py --depth 3           # faster cycle
uv run python benchmarks/perft/run.py --no-profile        # skip cProfile (no .prof produced)
uv run python benchmarks/perft/run.py --no-record         # ad-hoc; don't pollute results.jsonl
uv run python benchmarks/perft/run.py --label kiwipete-d3 \
    --fen "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1" \
    --depth 3
```

The default label is `d{depth}` — if you run different positions, override
`--label` so they don't collapse into the same series in `analyze.py`.

## Headline metric

`nodes_per_sec` computed from the best (minimum) time across the timed runs.
See the top-level README for why min, not mean.

## Profiling

By default, every run also dumps a `cProfile` file named `<label>.prof` next
to `results.jsonl`. The file is gitignored — it's per-machine and reflects
only the most recent run for that label (subsequent runs overwrite it).

```sh
uv add --dev snakeviz       # one-time
uv run snakeviz benchmarks/perft/d4.prof
```

If you want to skip profiling (slightly faster, no `.prof` produced), pass
`--no-profile`.
