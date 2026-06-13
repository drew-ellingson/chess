"""ASCII board rendering. `Position` itself has no display logic per CLAUDE.md."""

from drewbert.core.position import Position


def render(position: Position) -> str:
    """Return an 8x8 ASCII view of the board. White on bottom (rank 1)."""
    lines: list[str] = []
    for rank in range(7, -1, -1):
        row: list[str] = []
        for file in range(8):
            piece = position.squares[rank * 8 + file]
            row.append(repr(piece) if piece is not None else ".")
        lines.append(f"  {rank + 1} | {' '.join(row)}")
    lines.append("    +-----------------")
    lines.append("      a b c d e f g h")
    return "\n".join(lines)
