---
name: drewbert-review
description: Review pending changes on the drewbert chess engine against its defined quality bar. Invoked as /drewbert-review, or when the user asks for a code review on this project.
---

# Drewbert code review

Review changes on this chess engine against the project's defined quality bar. The bar is high but specific — this is NOT general "pristine" code review. Stay within the criteria below.

## Context

See `CLAUDE.md` for project architecture, role boundary, and tooling commands. drewbert is a learning project; the owner writes algorithm code (move generation, search, evaluation, NNUE training). Claude's role is software design, scaffolding, test infrastructure, and code review — not implementation of core algorithms.

## The quality bar (five items)

A finding that doesn't map to one of these is not a finding.

1. **Documentation.** Clear docstrings for public API. `Raises` clauses where the contract matters to callers. Architectural decisions captured where non-obvious. Stale comments fixed or removed.
2. **Architecture.** Separation of concerns per `CLAUDE.md`. No leaks across module boundaries — notably:
   - nothing in `core/` may import from `adapters/`
   - nothing in `src/` may import `python-chess` (dev-only test oracle)
   - movegen stays as functions over `Position`, not methods on it
3. **Performance — algorithmic only.** No obviously suboptimal algorithms: `pop(0)` in hot loops, accidental O(n²), unnecessary list materialization in tight paths, repeated work that could be cached once. NOT micro-optimization.
4. **No hacky solutions.** No clever tricks that obscure intent. No magic constants without context. No workarounds that fight the type system or the architecture. No silent failures or unexplained fallbacks.
5. **Lint / format / typecheck.** Verify `uv run ruff check`, `uv run ruff format --check`, `uv run pyright` all pass.

## Do flag

- Missing docstrings on public functions/classes
- Missing `Raises` clauses where the function raises meaningfully
- Hot-loop perf bugs
- Hacky workarounds — magic numbers, type-system end-runs, architectural shortcuts
- Lint, format, or type errors
- Architectural leaks (core ↔ adapters, src ↔ python-chess)
- Stale comments or docstrings that misrepresent current code
- Real correctness bugs (with the failing case if non-obvious)

## Do NOT flag

The owner explicitly retracted earlier "pristine" framing as overreach. These are out of scope:

- Cosmetic style without functional benefit (`len(x) != 8` vs `not len(x) == 8`, etc.)
- Pedantic naming consistency
- Polish-for-polish-sake
- Micro-optimizations
- `__all__` declarations as a hard requirement
- Single-line public docstrings (one line that says what's needed is fine)
- Comprehension-vs-loop refactors that are only stylistic
- Different-but-equivalent patterns

## How to run

1. **Determine scope.** The skill takes an optional argument:
   - `/drewbert-review <PR-number>` — review the GitHub PR. Use `gh pr view <N>` for context (title, body, commits) and `gh pr diff <N>` for the full diff. Also fetch the PR branch and check out the head commit if you need to run checkers against the actual code.
   - `/drewbert-review` (no arg) — review the current branch against main (`git diff main...HEAD`). If you're on `main` and there are unstaged changes, fall back to `git diff` / `git status`. If scope is genuinely unclear, ask before proceeding.
2. **Run checkers in parallel.** `uv run ruff check`, `uv run ruff format --check`, `uv run pyright`. Report failures up front, before substantive review — they're often the cheapest fixes and they anchor the rest of the review.
3. **Read changes file by file.** Cite `path:line` for every finding so the user can navigate.
4. **Group findings under the five-item bar.** Skip headings with no findings; don't manufacture filler.
5. **End with a one-paragraph summary.** Blockers vs nits. Ship-ready or not. If there are zero findings, say so plainly — don't pad.
6. **PR mode only:** at the end, ask whether to post the review as a PR comment (`gh pr comment` or `gh pr review --comment`). Do not post automatically.

## Role boundary in review mode

Same as everywhere on this project: flag bugs but let the owner fix them. If a fix is non-obvious, describe the failure mode and the conditions that trigger it, then stop. Do NOT write the corrected algorithm code or volunteer helper decompositions. The owner's learning is in writing the fix.

If you find yourself wanting to type "the canonical shape is..." or "you'll want a helper that...", stop. The constraint is on unsolicited implementation guidance, not on guidance per se — wait for the owner to ask.
