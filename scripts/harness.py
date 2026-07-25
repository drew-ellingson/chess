"""Chess engine tournament harness.

Runs a cutechess-cli match between N drewbert commits and/or M external UCI
engines. Requires >=2 total engines.

Usage:
    uv run scripts/harness.py --drewbert-sha SHA [SHA ...]
    uv run scripts/harness.py --drewbert-sha HEAD main --external stockfish
    uv run scripts/harness.py --external stockfish /path/to/lc0

Tuning parameters (rounds, concurrency, time control, drewbert engine args)
live as constants at the top of this file. Edit in place rather than adding
flags — the two flags are for "which engines" only.
"""

import argparse
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

# ---- Tuning ----

REPO_ROOT = Path(__file__).parent.parent.resolve()
WORKTREE_ROOT = Path("/tmp/drewbert-worktrees")
DREWBERT_MODULE = "drewbert.adapters.uci"
DREWBERT_ARGS = ["--eval", "materialistic", "--search", "minimax", "--depth", "2"]

ROUNDS = 10
CONCURRENCY = 4
TIME_CONTROL = "inf"
TOURNAMENT_TYPE = "round-robin"
PGN_OUT = "games.pgn"


def resolve_and_provision_sha(ref: str) -> tuple[str, Path]:
    """Resolve `ref` to a short SHA and ensure a worktree exists for it.

    Worktrees are cached at WORKTREE_ROOT/<short-sha>/. If the directory
    already exists we skip both `git worktree add` and `uv sync` — first
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
    if worktree_path.exists():
        return short_sha, worktree_path

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


def build_drewbert_engine_block(short_sha: str, worktree_path: Path) -> list[str]:
    """cutechess-cli -engine block for a drewbert instance in a worktree."""
    parts = [
        "-engine",
        f"name=drewbert-{short_sha}",
        "cmd=uv",
        "arg=run",
        "arg=python",
        "arg=-m",
        f"arg={DREWBERT_MODULE}",
    ]
    parts.extend(f"arg={a}" for a in DREWBERT_ARGS)
    parts.append(f"dir={worktree_path}")
    return parts


def build_external_engine_block(path_or_cmd: str) -> list[str]:
    """cutechess-cli -engine block for an external UCI binary.

    Accepts an absolute path, a relative path, or a bare command name that
    resolves via PATH (e.g. `stockfish` if installed by brew).
    """
    resolved = shutil.which(path_or_cmd)
    if resolved is None:
        sys.exit(f"External engine not found: {path_or_cmd}")
    return ["-engine", f"name={Path(resolved).name}", f"cmd={resolved}"]


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
        metavar="REF",
        help="commit SHAs or refs to test (e.g. HEAD, main, abc1234)",
    )
    parser.add_argument(
        "--external",
        nargs="+",
        default=[],
        metavar="PATH_OR_CMD",
        help="paths to external UCI engines, or bare command names on PATH",
    )
    args = parser.parse_args()

    if len(args.drewbert_sha) + len(args.external) < 2:
        sys.exit("Need at least 2 engines total across --drewbert-sha and --external")

    resolved = [resolve_and_provision_sha(ref) for ref in args.drewbert_sha]

    # cute-chess requires unique engine names; two refs pointing at the same
    # commit would collide. Punt on same-SHA-vs-itself for now — the user can
    # add a `--drewbert-local` sentinel later if that becomes useful.
    short_shas = [s for s, _ in resolved]
    if len(set(short_shas)) != len(short_shas):
        dupes = sorted({s for s in short_shas if short_shas.count(s) > 1})
        sys.exit(f"Duplicate SHAs (refs resolve to same commit): {dupes}")

    engine_blocks: list[list[str]] = []
    for short_sha, worktree_path in resolved:
        engine_blocks.append(build_drewbert_engine_block(short_sha, worktree_path))
    for path_or_cmd in args.external:
        engine_blocks.append(build_external_engine_block(path_or_cmd))

    cmd = build_cutechess_command(engine_blocks)
    print("Running:", shlex.join(cmd))
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
