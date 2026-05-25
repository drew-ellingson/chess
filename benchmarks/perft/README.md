# perft benchmark

Tracks `perft` (movegen + make/unmake) speed. One JSONL line per run appended
to `results.jsonl`.

For the record schema and the cross-benchmark reader, see
[`benchmarks/README.md`](../README.md).

## Run

```sh
uv run python benchmarks/perft/run.py                     # default: starting position, depth 4, 5 runs
uv run python benchmarks/perft/run.py --depth 3           # faster cycle
uv run python benchmarks/perft/run.py --profile           # also dump a cProfile .prof for snakeviz
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

Pass `--profile` to also dump a `cProfile` file to
`.local/profiles/perft_d<N>_<timestamp>.prof`. View interactively with:

```sh
uv add --dev snakeviz       # one-time
uv run snakeviz .local/profiles/perft_d4_<timestamp>.prof
```

`.local/` is gitignored so dumps stay per-machine.
