"""Chess engine tournament harness.
Runs a cutechess-cli match between N drewbert commits and/or M external UCI
engines. Requires >=2 total engines.

Usage:
    uv run scripts/harness.py --drewbert-sha SHA [SHA ...]
    uv run scripts/harness.py --drewbert-sha HEAD main --external stockfish
    uv run scripts/harness.py --external stockfish /path/to/lc0
    uv run scripts/harness.py --drewbert-sha HEAD=drewbert-head main --external stockfish=stockfish-level-1
    uv run scripts/harness.py --drewbert-sha HEAD=drewbert-head main:materialistic=drewbert-main

Any engine can take an optional `=LABEL` suffix, used as its name in cutechess output and the PGN.
Unlabeled engines default to `drewbert-<short-sha>` or the binary's basename. Labels must be unique,
so the same SHA can play itself under two labels (a useful 50% sanity check).

drewbert engines can also take a `:EVAL` suffix on the ref (before any label) naming the `--eval`
registry entry that commit should run. Without it, DEFAULT_EVAL (the current default eval) is used,
so commits that predate that eval need an explicit suffix, e.g. `main:materialistic`, the one name
every commit's registry has. `:` can't appear in a git ref name, so the split is unambiguous.

Each drewbert engine is started once before the tournament to check its commit accepts the requested
eval, so a typo or a too-old commit fails here with the engine's own error instead of as an opaque
cutechess startup failure.

Tuning parameters (rounds, concurrency, time control, drewbert search arg)
live as constants at the top of this file. Edit in place rather than adding
flags — the two flags are for "which engines" only.
"""

import argparse
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

# ---- Tuning ----

REPO_ROOT = Path(__file__).parent.parent.resolve()
WORKTREE_ROOT = Path("/tmp/drewbert-worktrees")
DREWBERT_MODULE = "drewbert.adapters.uci"

# "minimax" is the one search name every SHA accepts (aliased to negamax after the rename).
DREWBERT_SEARCH = "minimax"
# Eval for drewbert specs without a `:EVAL` suffix: the engine's current default eval. Older commits
# that predate it need an explicit suffix; "materialistic" is the one name every SHA accepts.
DEFAULT_EVAL = "comprehensive"
# Seconds to wait for a drewbert engine to answer `uci` during the preflight check.
PREFLIGHT_TIMEOUT_S = 60
# UCI options set on external engines at init time, keyed by resolved binary
# name. Values are stringified for cute-chess's `option.NAME=VALUE` syntax.
# Empty dict for unlisted engines. Grow as use cases appear.
EXTERNAL_OPTIONS: dict[str, dict[str, str]] = {
    "stockfish": {"Skill Level": "1"},
}

ROUNDS = 50
CONCURRENCY = 8
TIME_CONTROL = "10+0.3"
TOURNAMENT_TYPE = "round-robin"
PGN_OUT = "games.pgn"
OPENINGS_FILE = Path(REPO_ROOT / "opening_books/Unique_v170623.pgn")
GAMES = 2

# Labels become cutechess engine names and PGN player headers, so keep them shell- and PGN-safe.
LABEL_RE = re.compile(r"[A-Za-z0-9._-]+")
# Eval names are registry keys; they also appear in default engine names, so the same rule applies.
EVAL_RE = LABEL_RE


def split_label(spec: str) -> tuple[str, str | None]:
    """Split an engine spec `TARGET[=LABEL]` into (target, label), with label None when absent.

    Splits on the last `=`, so a target may itself contain `=` as long as a label is given.
    Exits with a message if the label is empty or contains characters outside LABEL_RE.
    """
    target, sep, label = spec.rpartition("=")
    if not sep:
        return spec, None
    if not target or not LABEL_RE.fullmatch(label):
        sys.exit(f"Bad engine spec {spec!r}: expected TARGET=LABEL with LABEL matching {LABEL_RE.pattern}")
    return target, label


def split_eval(target: str) -> tuple[str, str]:
    """Split a drewbert target `REF[:EVAL]` into (ref, eval), with eval DEFAULT_EVAL when absent.

    Exits with a message if the ref or eval is empty, or the eval contains characters outside EVAL_RE.
    """
    ref, sep, eval_name = target.partition(":")
    if not sep:
        return ref, DEFAULT_EVAL
    if not ref or not EVAL_RE.fullmatch(eval_name):
        sys.exit(f"Bad drewbert spec {target!r}: expected REF:EVAL with EVAL matching {EVAL_RE.pattern}")
    return ref, eval_name


def drewbert_args(eval_name: str) -> list[str]:
    """Command-line arguments for the drewbert UCI adapter, after `python -m DREWBERT_MODULE`."""
    return ["--eval", eval_name, "--search", DREWBERT_SEARCH]


def preflight_drewbert(name: str, worktree_path: Path, eval_name: str) -> None:
    """Start a drewbert engine once and complete the UCI handshake, or exit with the engine's output.

    Catches an eval or search name the commit's registry doesn't have (the adapter raises KeyError at
    startup) before cutechess launches, where the same failure only shows as a failed engine start.
    """
    cmd = ["uv", "run", "python", "-m", DREWBERT_MODULE, *drewbert_args(eval_name)]
    try:
        proc = subprocess.run(
            cmd,
            cwd=worktree_path,
            input="uci\nquit\n",
            capture_output=True,
            text=True,
            timeout=PREFLIGHT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        sys.exit(f"Engine {name} did not answer `uci` within {PREFLIGHT_TIMEOUT_S}s")
    if proc.returncode != 0 or "uciok" not in proc.stdout:
        output = (proc.stderr or proc.stdout).strip()
        sys.exit(f"Engine {name} (eval {eval_name!r}, {worktree_path}) failed to start:\n{output}")


def resolve_and_provision_sha(ref: str) -> tuple[str, Path]:
    """Resolve `ref` to a short SHA and ensure a worktree exists for it.

    Worktrees are cached at WORKTREE_ROOT/<short-sha>/. If the worktree directory is populated,
    we skip both `git worktree add` and `uv sync`. If the worktree direcotry exists but
    is not populated, we remove the directory and prune worktrees before rebuilding. First
    invocation for a SHA takes ~10s, subsequent invocations are free.
    """
    short_sha = subprocess.run(
        ["git", "rev-parse", "--short=8", ref],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    worktree_path = WORKTREE_ROOT / short_sha
    if worktree_path.exists() and Path.is_file(Path(worktree_path / ".git")):
        return short_sha, worktree_path
    elif worktree_path.exists():
        shutil.rmtree(worktree_path)
        subprocess.run(["git", "worktree", "prune"], cwd=REPO_ROOT)

    WORKTREE_ROOT.mkdir(parents=True, exist_ok=True)
    # --detach avoids polluting the branch list with worktree-owned refs.
    subprocess.run(
        ["git", "worktree", "add", "--detach", str(worktree_path), short_sha],
        cwd=REPO_ROOT,
        check=True,
    )
    # Front-load the venv build so cute-chess doesn't misdiagnose a slow first
    # engine spawn as a handshake failure.
    subprocess.run(["uv", "sync"], cwd=worktree_path, check=True)
    return short_sha, worktree_path


def build_drewbert_engine_block(name: str, worktree_path: Path, eval_name: str) -> list[str]:
    """cutechess-cli -engine block for a drewbert instance in a worktree, running the named eval."""
    parts = [
        "-engine",
        f"name={name}",
        "cmd=uv",
        "arg=run",
        "arg=python",
        "arg=-m",
        f"arg={DREWBERT_MODULE}",
    ]
    parts.extend(f"arg={a}" for a in drewbert_args(eval_name))
    parts.append(f"dir={worktree_path}")
    return parts


def resolve_external(path_or_cmd: str) -> str:
    """Resolve an external engine to an executable path, or exit if it can't be found.

    Accepts an absolute path, a relative path, or a bare command name that
    resolves via PATH (e.g. `stockfish` if installed by brew).
    """
    resolved = shutil.which(path_or_cmd)
    if resolved is None:
        sys.exit(f"External engine not found: {path_or_cmd}")
    return resolved


def build_external_engine_block(name: str, resolved: str) -> list[str]:
    """cutechess-cli -engine block for an external UCI binary at `resolved`.

    Engine-specific UCI options are pulled from EXTERNAL_OPTIONS keyed by binary
    basename, not by `name`, so a label doesn't change which options apply.
    """
    parts = ["-engine", f"name={name}", f"cmd={resolved}"]
    for opt_name, opt_value in EXTERNAL_OPTIONS.get(Path(resolved).name, {}).items():
        parts.append(f"option.{opt_name}={opt_value}")
    return parts


def build_cutechess_command(engine_blocks: list[list[str]]) -> list[str]:
    cmd = ["cutechess-cli"]
    for block in engine_blocks:
        cmd.extend(block)
    cmd.extend(
        [
            "-each",
            "proto=uci",
            f"tc={TIME_CONTROL}",
            "-tournament",
            TOURNAMENT_TYPE,
            "-rounds",
            str(ROUNDS),
            "-repeat",
            "-concurrency",
            str(CONCURRENCY),
            "-pgnout",
            PGN_OUT,
            "-openings",
            f"file={OPENINGS_FILE}",
            "format=pgn",
            "order=random",
            "-games",
            str(GAMES),
        ]
    )
    return cmd


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--drewbert-sha",
        nargs="+",
        default=[],
        metavar="REF[:EVAL][=LABEL]",
        help="commit SHAs or refs to test (e.g. HEAD, main=drewbert-main, HEAD:comprehensive=drewbert-pst)",
    )
    parser.add_argument(
        "--external",
        nargs="+",
        default=[],
        metavar="PATH_OR_CMD[=LABEL]",
        help="paths to external UCI engines, or bare command names on PATH (e.g. stockfish=stockfish-level-1)",
    )
    args = parser.parse_args()

    if len(args.drewbert_sha) + len(args.external) < 2:
        sys.exit("Need at least 2 engines total across --drewbert-sha and --external")

    # Parse labels and resolve external binaries first, so a bad spec or a missing engine exits
    # before any worktree is built. Name collisions need the short SHAs, so they're checked after.
    drewbert_specs = [(*split_eval(target), label) for target, label in map(split_label, args.drewbert_sha)]
    external_specs = [split_label(spec) for spec in args.external]
    resolved_externals = [(resolve_external(target), label) for target, label in external_specs]

    drewbert_engines: list[tuple[str, Path, str]] = []
    for ref, eval_name, label in drewbert_specs:
        short_sha, worktree_path = resolve_and_provision_sha(ref)
        # Non-default evals go in the default name, so `HEAD HEAD:comprehensive` needs no labels.
        default_name = f"drewbert-{short_sha}" + ("" if eval_name == DEFAULT_EVAL else f"-{eval_name}")
        drewbert_engines.append((label or default_name, worktree_path, eval_name))
    external_engines = [(label or Path(resolved).name, resolved) for resolved, label in resolved_externals]

    # cute-chess requires unique engine names. Unlabeled refs at the same commit, or the same
    # unlabeled binary twice, collide; labels resolve that.
    names = [name for name, _, _ in drewbert_engines] + [name for name, _ in external_engines]
    dupes = sorted({n for n in names if names.count(n) > 1})
    if dupes:
        sys.exit(f"Duplicate engine names {dupes}: give the colliding engines distinct =LABELs")

    for name, worktree_path, eval_name in drewbert_engines:
        preflight_drewbert(name, worktree_path, eval_name)

    engine_blocks: list[list[str]] = []
    for name, worktree_path, eval_name in drewbert_engines:
        engine_blocks.append(build_drewbert_engine_block(name, worktree_path, eval_name))
    for name, resolved in external_engines:
        engine_blocks.append(build_external_engine_block(name, resolved))

    cmd = build_cutechess_command(engine_blocks)
    print("Running:", shlex.join(cmd))
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
