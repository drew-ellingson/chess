def budget_time(
    remaining_ms: int | None, increment_ms: int | None, move_time: int | None, moves_to_go: int | None = None
) -> int | None:
    """Calculate how much time to spend on a given move from information contained in the UCI Go command. Return time in ms
    if the result is well determined; return None if not.

    If multiple contexts exist in the UCI Go for time calculation, return the smallest provided budget value"""

    latency_budget_ms = 100
    moves_remaining_default = 30

    calc_time = None
    increment_ms = increment_ms if increment_ms else 0

    if remaining_ms is not None:
        moves_remaining_guess = moves_to_go if moves_to_go else moves_remaining_default
        calc_time = min(
            remaining_ms - latency_budget_ms, increment_ms + remaining_ms // moves_remaining_guess - latency_budget_ms
        )
        calc_time = max(calc_time, 0)

    candidates = [t for t in [move_time, calc_time] if t is not None]
    return min(candidates, default=None)
